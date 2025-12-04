# chunk.py
# Phase 3: Chunk generation only (no embeddings, no retrieval).
# Function-based, minimal, with logging to the exact path requested.

from __future__ import annotations
import json
import re
import hashlib
import logging
import traceback
from pathlib import Path
from typing import Iterator, List, Tuple, Dict, Any
from datetime import datetime

# ---------- Constants & Config ----------

CORPUS_DIR = r"C:\Users\CatherineVaras\Downloads\tsql-to-snowflake-llm-rag-translator\project\corpus"

# Fixed log file path (do not rename)
LOG_FILE = r"C:\Users\CatherineVaras\Downloads\tsql-to-snowflake-llm-rag-translator\project\logs\chunk.log"

# Front matter regex
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

# ---------- Public entry point ----------

def build_chunks(corpus_dir: str | Path, force: bool = False) -> Dict[str, Any]:
    """
    Scans Markdown docs under {corpus}/commands, {corpus}/datatypes, {corpus}/scripting,
    and writes chunk files to {corpus}/chunks/<DocName>.jsonl following chunking_spec.json.

    Returns a stats dict and logs progress to file + minimal console.
    """
    logger = _get_logger()

    try:
        corpus = Path(corpus_dir)
        spec = _load_spec(corpus / "chunking_spec.json")

        chunks_dir = corpus / "chunks"
        chunks_dir.mkdir(parents=True, exist_ok=True)

        # Manifest co-located with produced chunks to avoid hidden folders
        manifest_path = chunks_dir / "chunk_manifest.json"
        manifest = _load_manifest(manifest_path)

        logger.info(f"Starting Phase 3 chunk build for corpus: {corpus.as_posix()}")
        logger.debug(f"Spec loaded: {spec}")

        processed = 0
        skipped = 0
        total_chunks = 0

        for md_path in _iter_markdown_docs(corpus):
            rel = md_path.relative_to(corpus).as_posix()
            try:
                text = md_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                logger.error(f"Failed to read {rel}: {e}")
                logger.debug(traceback.format_exc())
                continue

            body_hash = _sha1(_extract_body(text))  # only the body

            if not force and _is_unchanged(manifest, rel, md_path.stat().st_mtime, body_hash):
                skipped += 1
                logger.debug(f"Skipping (unchanged): {rel}")
                continue

            fm, body = _parse_front_matter(text)
            page_title = fm.get("page_title", md_path.stem)

            # Split by headings (##, ###), then chunk
            blocks = _split_by_headings(body)
            out_path = chunks_dir / f"{md_path.stem}.jsonl"
            written_for_doc = 0

            with out_path.open("w", encoding="utf-8") as f:
                for block_text, heading_path in blocks:
                    segments = _respect_code_and_tables(
                        block_text,
                        respect_code_blocks=spec.get("respect_code_blocks", True),
                        respect_tables=spec.get("respect_tables", True),
                    )
                    for seg in segments:
                        pieces = _chunk_text(
                            seg,
                            target_tokens=spec.get("target_tokens", 600),
                            overlap_tokens=spec.get("overlap_tokens", 80),
                        )
                        for i, piece in enumerate(pieces):
                            approx_tokens = max(1, len(piece) // 4)  # quick estimate
                            base = f"{rel}::{heading_path}::{i}"
                            chunk_id = _sha1(base)
                            record = {
                                "chunk_id": chunk_id,
                                "doc_id": rel,
                                "page_title": page_title,
                                "heading_path": heading_path,
                                "chunk_index": i,
                                "text": piece,
                                "approx_tokens": approx_tokens
                            }
                            f.write(json.dumps(record, ensure_ascii=False) + "\n")
                            written_for_doc += 1

            # Update manifest
            manifest.setdefault("source_docs", {})[rel] = {
                "mtime": md_path.stat().st_mtime,
                "total_chunks": written_for_doc,
                "sha1_of_body": body_hash
            }

            processed += 1
            total_chunks += written_for_doc
            logger.info(f"Chunked {rel} → {written_for_doc} chunks")

        _save_manifest(manifest_path, manifest)
        logger.info(f"Manifest updated at {manifest_path.as_posix()}")

        summary = {
            "processed_files": processed,
            "skipped_files": skipped,
            "total_chunks": total_chunks,
            "output_dir": (corpus / "chunks").as_posix()
        }

        # Minimal console output
        print(f"[Phase 3] Chunks built. processed={processed} skipped={skipped} total_chunks={total_chunks}")

        logger.info(f"Completed Phase 3 chunk build: processed={processed}, skipped={skipped}, total_chunks={total_chunks}")
        logger.debug(f"Summary: {summary}")
        return summary

    except Exception as e:
        # Log unexpected top-level errors
        logger.error(f"Unhandled error in build_chunks: {e}")
        logger.debug(traceback.format_exc())
        raise


# ---------- Logging setup ----------

def _get_logger() -> logging.Logger:
    """
    Configure a singleton logger:
    - File handler: INFO/DEBUG/ERROR to fixed LOG_FILE (append).
    - Console handler: minimal INFO messages (generic progress).
    """
    logger = logging.getLogger("rag_phase3")
    if getattr(logger, "_configured", False):
        return logger

    logger.setLevel(logging.DEBUG)  # capture all; handlers will filter

    # Ensure log directory exists
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # File handler (append)
    fh = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)  # capture DEBUG+INFO+ERROR
    fh.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(fh)

    # Console handler (minimal, generic)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(ch)

    logger._configured = True  # type: ignore[attr-defined]
    logger.debug(f"Logger initialized, writing to: {LOG_FILE}")
    return logger


# ---------- Helpers: IO & manifest ----------

def _load_spec(spec_path: Path) -> Dict[str, Any]:
    logger = _get_logger()
    if not spec_path.exists():
        msg = f"Missing chunking_spec.json at: {spec_path.as_posix()}"
        logger.error(msg)
        raise FileNotFoundError(msg)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    logger.debug(f"Loaded spec from {spec_path.as_posix()}")
    return spec

def _load_manifest(path: Path) -> Dict[str, Any]:
    logger = _get_logger()
    if not path.exists():
        logger.debug("No existing manifest; starting fresh.")
        return {"source_docs": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        logger.debug(f"Loaded manifest from {path.as_posix()}")
        return data
    except Exception as e:
        logger.error(f"Failed to load manifest (will reset): {e}")
        logger.debug(traceback.format_exc())
        return {"source_docs": {}}

def _save_manifest(path: Path, manifest: Dict[str, Any]) -> None:
    logger = _get_logger()
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.debug(f"Saved manifest to {path.as_posix()}")


def _iter_markdown_docs(corpus: Path) -> Iterator[Path]:
    logger = _get_logger()
    for topic in ("commands", "datatypes", "scripting"):
        base = corpus / topic
        if not base.exists():
            logger.debug(f"Topic folder missing (skipped): {base.as_posix()}")
            continue
        for p in base.rglob("*.md"):
            logger.debug(f"Discovered markdown: {p.as_posix()}")
            yield p


def _is_unchanged(manifest: Dict[str, Any], rel: str, mtime: float, body_hash: str) -> bool:
    rec = manifest.get("source_docs", {}).get(rel)
    if not rec:
        return False
    return abs(rec.get("mtime", 0) - mtime) < 1e-6 and rec.get("sha1_of_body") == body_hash


# ---------- Helpers: parsing & splitting ----------

def _parse_front_matter(text: str) -> Tuple[Dict[str, Any], str]:
    """
    Minimal YAML-ish parser for front-matter block.
    Returns ({}, original_text) if missing. No validation here.
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    block = m.group(1)
    body = text[m.end():]
    data: Dict[str, Any] = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            data[k] = [] if inner == "" else [i.strip().strip("'\"") for i in inner.split(",")]
        else:
            data[k] = v.strip().strip("'\"")
    return data, body


def _split_by_headings(text: str) -> List[Tuple[str, str]]:
    """
    Split by ## (H2) and ### (H3).
    Returns list of (block_text, heading_path) where heading_path is "H2 > H3" or just "H2".
    If no headings, returns one block with empty path.
    """
    lines = text.splitlines()
    blocks: List[Tuple[str, str]] = []
    current: List[str] = []
    h2: str | None = None
    h3: str | None = None

    def flush():
        if current:
            path = ""
            if h2 and h3:
                path = f"{h2} > {h3}"
            elif h2:
                path = h2
            blocks.append(("\n".join(current).strip(), path))

    for ln in lines:
        if ln.startswith("## "):   # H2
            flush()
            current = [ln]
            h2 = ln[3:].strip()
            h3 = None
        elif ln.startswith("### "): # H3
            flush()
            current = [ln]
            h3 = ln[4:].strip()
            if h2 is None:  # H3 without H2 → treat as H2
                h2 = h3
                h3 = None
        else:
            current.append(ln)
    flush()
    if not blocks:
        blocks.append((text.strip(), ""))
    return blocks


def _respect_code_and_tables(block: str, respect_code_blocks: bool, respect_tables: bool) -> List[str]:
    """
    Hook for future hardening. For now we keep the block intact because chunking
    cuts on paragraph-friendly boundaries, which naturally preserves fenced code and tables.
    """
    return [block]


def _chunk_text(text: str, target_tokens: int, overlap_tokens: int) -> List[str]:
    """
    Paragraph-aware slicing with overlap. Token ≈ char/4 heuristic.
    """
    s = text.strip()
    if not s:
        return []
    paragraphs = s.split("\n\n")

    target_chars = max(1, target_tokens) * 4
    overlap_chars = max(0, overlap_tokens) * 4

    chunks: List[str] = []
    buf = ""
    for para in paragraphs:
        candidate = (buf + ("\n\n" if buf else "")) + para

        if len(candidate) <= target_chars:
            buf = candidate
            continue

        # Flush buffered content into sized pieces
        if buf:
            chunks.extend(_slice_with_overlap(buf, target_chars, overlap_chars))
        # The paragraph itself may exceed target size
        chunks.extend(_slice_with_overlap(para, target_chars, overlap_chars))
        buf = ""  # reset

    if buf:
        chunks.extend(_slice_with_overlap(buf, target_chars, overlap_chars))

    return [c.strip() for c in chunks if c.strip()]


def _slice_with_overlap(text: str, target_chars: int, overlap_chars: int) -> List[str]:
    """
    Slice a single block to ~target_chars with overlap, preferring friendly boundaries.
    """
    if len(text) <= target_chars:
        return [text]

    pieces: List[str] = []
    start = 0
    n = len(text)

    while start < n:
        end = min(n, start + target_chars)
        slice_text = text[start:end]

        # Prefer boundaries: double newline, then single newline, then period+space.
        cut = max(slice_text.rfind("\n\n"), slice_text.rfind("\n"), slice_text.rfind(". "))
        if cut != -1 and end != n:
            end = start + cut + 1  # keep boundary char

        pieces.append(text[start:end].strip())
        if end == n:
            break

        # Overlap
        start = max(0, end - overlap_chars)

    return pieces


def _extract_body(text: str) -> str:
    m = _FRONTMATTER_RE.match(text)
    return text[m.end():] if m else text


def _sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()


# ---------- CLI convenience ----------

if __name__ == "__main__":
    logger = _get_logger()
    try:
        # Usar siempre la ruta fija del corpus
        corpus_root = Path(CORPUS_DIR)
        logger.info(f"CLI invoked. corpus_root={corpus_root.as_posix()}")
        stats = build_chunks(corpus_root, force=False)
        print(f"[Phase 3] Chunks built. processed={stats['processed_files']} skipped={stats['skipped_files']} total_chunks={stats['total_chunks']}")
    except Exception as e:
        logger.error(f"Fatal error from CLI: {e}")
        logger.debug(__import__("traceback").format_exc())
        raise
