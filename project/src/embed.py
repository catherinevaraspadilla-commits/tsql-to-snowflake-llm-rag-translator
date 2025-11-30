# embed.py
# Phase 4: Embeddings + Retrieval (function-based, Azure OpenAI).
# - Reads chunks from corpus/chunks/*.jsonl (created by Phase 3)
# - Writes vectors & manifests under corpus/.embed/
# - Provides build_embeddings(...) and retrieve(...)

from __future__ import annotations
import json, os, re, math, logging, traceback
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime

# ======================
# Fixed paths / settings
# ======================

# Corpus root (static, per your spec)
CORPUS_DIR = Path(r"C:\Users\CatherineVaras\Downloads\snowflake\corpus")

# Logs (append, UTF-8)
EMBED_LOG_FILE = r"C:\Users\CatherineVaras\Downloads\snowflake\logs\embed.log"

# Store for embedding artifacts (.embed)
CHUNK_CACHE_DIR = CORPUS_DIR / "embed"
CHUNK_CACHE_DIR.mkdir(parents=True, exist_ok=True)

EMBEDS_JSONL = CHUNK_CACHE_DIR / "embeds.jsonl"           # lines: {"chunk_id","vector":[...],"dim":...}
META_JSONL   = CHUNK_CACHE_DIR / "meta.jsonl"             # lines: {"chunk_id","doc_id","page_title","heading_path","approx_tokens"}
EMBEDS_MANIFEST = CHUNK_CACHE_DIR / "embeds_manifest.json"  # to skip unchanged chunks

# Retrieval constants
WEIGHT_COSINE = 0.7
WEIGHT_KEYWORD = 0.3
WEAK_SIMILARITY_THRESHOLD = 0.25
HARD_CAP_DEFAULT = 8

# ======================
# Logging
# ======================

def _get_logger() -> logging.Logger:
    logger = logging.getLogger("embed_phase4")
    if getattr(logger, "_configured", False):
        return logger
    logger.setLevel(logging.DEBUG)

    # Ensure log dir exists
    Path(EMBED_LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

    fh = logging.FileHandler(EMBED_LOG_FILE, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)  # minimal console
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(ch)

    logger._configured = True  # type: ignore[attr-defined]
    logger.debug("embed logger initialized")
    return logger

# ======================
# Settings & Azure client
# ======================


def load_settings(path: str | None = None) -> dict:
    """Load settings.json from a fixed path (Windows-safe)."""
    default_path = "C:/Users/CatherineVaras/Downloads/snowflake/settings.json"
    # If no path or a relative path was given, fall back to the fixed one
    if path is None or not Path(path).is_absolute():
        path = default_path

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"settings.json not found at {p}")
    return json.loads(p.read_text(encoding="utf-8"))

def initialize_azure_openai_client(api_key=None, azure_endpoint=None):
    # Lazy import so file can be imported without this dependency until used
    from openai import AzureOpenAI  # requires openai>=1.0
    client = AzureOpenAI(
        api_key=api_key,
        api_version="2024-12-01-preview",
        azure_endpoint=azure_endpoint
    )
    return client

# ======================
# I/O helpers
# ======================

def _load_embeds_manifest() -> Dict[str, Any]:
    if not EMBEDS_MANIFEST.exists():
        return {"chunks": {}}   # chunk_id -> {"doc_id","sha1","dim"}
    try:
        return json.loads(EMBEDS_MANIFEST.read_text(encoding="utf-8"))
    except Exception:
        return {"chunks": {}}

def _save_embeds_manifest(m: Dict[str, Any]) -> None:
    EMBEDS_MANIFEST.write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")

def _append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    out: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out

def _iter_chunk_files() -> List[Path]:
    chunks_dir = CORPUS_DIR / "chunks"
    return sorted(chunks_dir.glob("*.jsonl"))

def _sha1(s: str) -> str:
    import hashlib
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()

# ======================
# Text utils (no deps)
# ======================

_WORD_RE = re.compile(r"[A-Za-z0-9_]+")

def _tokenize(s: str) -> List[str]:
    return [w.lower() for w in _WORD_RE.findall(s)]

def _keyword_overlap(query_tokens: List[str], text_tokens: List[str]) -> float:
    if not query_tokens or not text_tokens:
        return 0.0
    qs = set(query_tokens)
    ts = set(text_tokens)
    inter = len(qs & ts)
    denom = len(qs | ts)
    return inter / denom if denom > 0 else 0.0

def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)

# ======================
# Embeddings (Azure OpenAI)
# ======================

def _azure_embed_batch(client, deployment: str, texts: List[str]) -> List[List[float]]:
    """
    Call Azure OpenAI embeddings for a batch of texts.
    """
    # new OpenAI SDK returns .data with embeddings for each input in order
    resp = client.embeddings.create(model=deployment, input=texts)
    return [row.embedding for row in resp.data]

def build_embeddings(force: bool = False, batch_size: int = 64) -> Dict[str, Any]:
    """
    Build embeddings for all chunks (incremental).
    - Reads corpus/chunks/*.jsonl
    - Writes vectors to corpus/.embed/ (embeds.jsonl, meta.jsonl, embeds_manifest.json)
    - Uses Azure OpenAI embedding deployment from settings.json
      Expected keys in settings.json:
        { "api_key", "azure_endpoint", "embedding_deployment", "chat_deployment" }
 
    Returns summary dict.
    """
    # ensure we have a logger here even if the earlier one failed
    try:
        logger = _get_logger()
    except Exception:
        # last-ditch print; re-raise for visibility to caller/CLI
        print(f"[ERROR] Unhandled error in retrieve: {e}")
    try:
        settings = load_settings()
        api_key = settings["api_key"]
        endpoint = settings["azure_endpoint"]
        deployment = settings["embedding_deployment"]  # e.g., "text-embedding-3-small"

        client = initialize_azure_openai_client(api_key=api_key, azure_endpoint=endpoint)
        logger.info(f"Starting build_embeddings with deployment={deployment}")

        manifest = _load_embeds_manifest()
        known = manifest.get("chunks", {})

        processed, skipped, new_vectors = 0, 0, 0

        # We’ll rewrite embeds/meta files only if force=True; otherwise append for new chunks
        if force:
            if EMBEDS_JSONL.exists():
                EMBEDS_JSONL.unlink()
            if META_JSONL.exists():
                META_JSONL.unlink()
            logger.info("Force mode: cleared existing embeds/meta JSONL files.")

        # Pass 1: collect all chunks to embed
        to_embed: List[Tuple[str, str, str, str, int]] = []  # (chunk_id, text, doc_id, page_title_heading, approx_tokens)

        for file in _iter_chunk_files():
            for rec in _read_jsonl(file):
                chunk_id = rec["chunk_id"]
                text = rec["text"]
                doc_id = rec["doc_id"]
                page_title = rec.get("page_title", "")
                heading_path = rec.get("heading_path", "")
                approx_tokens = int(rec.get("approx_tokens", max(1, len(text)//4)))
                content_hash = _sha1(text)

                # Skip if unchanged and not forcing
                prev = known.get(chunk_id)
                if (not force) and prev and prev.get("sha1") == content_hash:
                    skipped += 1
                    continue

                # Save meta line now (idempotent: appending duplicates is okay; we keep latest usage in manifest)
                meta_line = {
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "page_title": page_title,
                    "heading_path": heading_path,
                    "approx_tokens": approx_tokens
                }
                _append_jsonl(META_JSONL, meta_line)
                to_embed.append((chunk_id, text, doc_id, f"{page_title} > {heading_path}".strip(" >"), approx_tokens))

        logger.info(f"Collected {len(to_embed)} chunks to embed (skipped={skipped}).")

        # Pass 2: embed in batches
        i = 0
        while i < len(to_embed):
            batch = to_embed[i:i+batch_size]
            texts = [b[1] for b in batch]
            try:
                vecs = _azure_embed_batch(client, deployment, texts)
            except Exception as e:
                logger.error(f"Embedding batch failed at i={i}: {e}")
                logger.debug(traceback.format_exc())
                raise

            for (chunk_id, text, doc_id, _title_heading, _tok), vec in zip(batch, vecs):
                dim = len(vec)
                _append_jsonl(EMBEDS_JSONL, {"chunk_id": chunk_id, "dim": dim, "vector": vec})
                # Update manifest record
                known[chunk_id] = {"doc_id": doc_id, "sha1": _sha1(text), "dim": dim}
                new_vectors += 1

            processed += len(batch)
            logger.info(f"Embedded {processed}/{len(to_embed)}")

            i += batch_size

        # Save manifest
        manifest["chunks"] = known
        _save_embeds_manifest(manifest)

        summary = {
            "embedded": new_vectors,
            "skipped": skipped,
            "total_known": len(known),
            "embeds_file": EMBEDS_JSONL.as_posix(),
            "meta_file": META_JSONL.as_posix(),
            "manifest_file": EMBEDS_MANIFEST.as_posix()
        }
        print(f"[Phase 4] Embeddings built. embedded={new_vectors} skipped={skipped} total_known={len(known)}")
        logger.info(f"Completed build_embeddings: {summary}")
        return summary

    except Exception as e:
        logger.error(f"Unhandled error in build_embeddings: {e}")
        logger.debug(traceback.format_exc())
        raise

# ======================
# Retrieval
# ======================

def _load_vectors_and_meta() -> Tuple[Dict[str, List[float]], Dict[str, Dict[str, Any]]]:
    """
    Returns:
      vectors: chunk_id -> vector
      meta:    chunk_id -> {doc_id,page_title,heading_path,approx_tokens}
    """
    # Read vectors
    vectors: Dict[str, List[float]] = {}
    for row in _read_jsonl(EMBEDS_JSONL):
        vectors[row["chunk_id"]] = row["vector"]

    # Read meta
    meta: Dict[str, Dict[str, Any]] = {}
    for row in _read_jsonl(META_JSONL):
        cid = row["chunk_id"]
        meta[cid] = {
            "doc_id": row["doc_id"],
            "page_title": row.get("page_title", ""),
            "heading_path": row.get("heading_path", ""),
            "approx_tokens": row.get("approx_tokens", 0)
        }
    return vectors, meta

def _object_type_bias(doc_id: str, object_type: str | None) -> float:
    """
    Light prefilter/bias per your rule:
      - "view" → prefer commands/ and datatypes/
      - "procedure" → prefer scripting/, then commands/ + datatypes/
    Returns a small bonus to cosine score.
    """
    if not object_type:
        return 0.0
    if object_type == "view":
        if doc_id.startswith("commands/") or doc_id.startswith("datatypes/"):
            return 0.02
        return 0.0
    if object_type == "procedure":
        if doc_id.startswith("scripting/"):
            return 0.03
        if doc_id.startswith("commands/") or doc_id.startswith("datatypes/"):
            return 0.01
        return 0.0
    return 0.0

def retrieve(query: str, object_type: str | None = None,
             k_per_folder: int = 6, hard_cap: int = HARD_CAP_DEFAULT) -> Dict[str, Any]:
    """
    Retrieve top chunks by cosine + keyword_overlap (0.7/0.3), dedupe by page_title+heading_path, cap to hard_cap.
    Requires built embeddings (run build_embeddings first).
    """
    logger = _get_logger()
    try:
        vectors, meta = _load_vectors_and_meta()
        if not vectors:
            raise RuntimeError("No vectors loaded. Run build_embeddings() first.")

        # Build a simple "query vector" by embedding the query text again?
        # We don't have the model here; instead we synthesize a pseudo-vector
        # by averaging top-N chunk vectors that match keywords. To keep it minimal
        # AND deterministic without another API call, we do:
        # 1) Tokenize query
        # 2) Score keyword overlap against each meta text proxy (page_title + heading_path)
        # 3) Take top 50 by keyword score, average their vectors as query vector.
        q_tokens = _tokenize(query)
        if not q_tokens:
            return {"chunks": [], "retrieval_weak": True, "stats": {"reason": "empty_query"}}

        # Build a tiny text proxy for each chunk from meta only (no raw text stored here)
        proxies: List[Tuple[str, float]] = []  # (chunk_id, kw_overlap)
        for cid, m in meta.items():
            proxy_text = (m.get("page_title","") + " " + m.get("heading_path","")).strip()
            kw = _keyword_overlap(q_tokens, _tokenize(proxy_text))
            # Small boost if object_type bias applies
            kw += _object_type_bias(m.get("doc_id",""), object_type)
            if kw > 0:
                proxies.append((cid, kw))

        # If no keyword hits via proxies, fallback to all chunks with zero keyword score
        if not proxies:
            proxies = [(cid, 0.0) for cid in meta.keys()]

        proxies.sort(key=lambda x: x[1], reverse=True)
        seed_ids = [cid for cid, _ in proxies[:50]]  # top 50 proxies to form a query vector

        # Average vectors for a seed query vector
        dim = None
        qvec = None
        count = 0
        for cid in seed_ids:
            vec = vectors.get(cid)
            if vec is None:
                continue
            if dim is None:
                dim = len(vec)
                qvec = [0.0]*dim
            # accumulate
            for i, v in enumerate(vec):
                qvec[i] += v
            count += 1
        if not qvec or count == 0:
            return {"chunks": [], "retrieval_weak": True, "stats": {"reason": "no_seed_vectors"}}
        qvec = [x / max(1, count) for x in qvec]

        # Score all candidates
        scored: List[Tuple[str, float, float]] = []  # (cid, cosine, kw)
        for cid, m in meta.items():
            vec = vectors.get(cid)
            if not vec:
                continue
            cos = _cosine(qvec, vec)
            # keyword overlap against fuller proxy: page_title + heading_path (kept minimal on purpose)
            kw = _keyword_overlap(q_tokens, _tokenize(m.get("page_title","") + " " + m.get("heading_path","")))
            cos += _object_type_bias(m.get("doc_id",""), object_type)  # tiny cosine bump for bias
            scored.append((cid, cos, kw))

        # Re-rank
        reranked: List[Tuple[str, float, float, float]] = []  # (cid, score, cos, kw)
        for cid, cos, kw in scored:
            score = WEIGHT_COSINE * cos + WEIGHT_KEYWORD * kw
            reranked.append((cid, score, cos, kw))
        reranked.sort(key=lambda x: x[1], reverse=True)

        # Dedupe by (page_title + heading_path)
        seen_keys = set()
        final_items = []
        for cid, score, cos, kw in reranked:
            m = meta[cid]
            dedupe_key = (m.get("page_title","") + " | " + m.get("heading_path","")).strip()
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            final_items.append((cid, score, cos, kw))
            if len(final_items) >= hard_cap:
                break

        retrieval_weak = False
        if final_items:
            # Look at top item's cosine component as signal
            top_cos = final_items[0][2]
            retrieval_weak = (top_cos < WEAK_SIMILARITY_THRESHOLD)

        # Build response payload
        chunks = []
        for cid, score, cos, kw in final_items:
            m = meta[cid]
            chunks.append({
                "doc_id": m["doc_id"],
                "page_title": m["page_title"],
                "heading_path": m["heading_path"],
                "chunk_id": cid,
                "score": round(score, 4),
                "cosine": round(cos, 4),
                "keyword_overlap": round(kw, 4),
                "citation": f"{m['page_title']} > {m['heading_path']}".strip(" >")
            })

        res = {
            "chunks": chunks,
            "retrieval_weak": retrieval_weak,
            "stats": {
                "candidates": len(scored),
                "after_dedupe": len(chunks),
                "threshold": WEAK_SIMILARITY_THRESHOLD
            }
        }
        print(f"[Phase 4] Retrieved {len(chunks)} chunks (weak={retrieval_weak})")
        logger.info(f"retrieve: query='{query[:100]}...' -> {len(chunks)} chunks; weak={retrieval_weak}")
        logger.debug(f"retrieve stats: {res['stats']}")
        return res

    except Exception as e:
        logger = _get_logger()
        logger.error(f"Unhandled error in retrieve: {e}")
        logger.debug(traceback.format_exc())
        raise

# ======================
# CLI convenience
# ======================

if __name__ == "__main__":
    # Minimal CLI:
    #   python embed.py build
    #   python embed.py retrieve "TOP 10 with GETDATE in a VIEW"
    import sys
    logger = _get_logger()
    try:
        if len(sys.argv) < 2:
            print("Usage:\n  python embed.py build\n  python embed.py retrieve \"your query\" [view|procedure]")
            sys.exit(0)

        cmd = sys.argv[1].lower()
        if cmd == "build":
            summary = build_embeddings(force=False)
            # Console already prints a short line
        elif cmd == "retrieve":
            query = sys.argv[2] if len(sys.argv) > 2 else ""
            objt = sys.argv[3].lower() if len(sys.argv) > 3 else None
            res = retrieve(query=query, object_type=objt)
            print(json.dumps(res, indent=2))
        else:
            print("Unknown command. Use 'build' or 'retrieve'.")
    except Exception as e:
        logger.error(f"Fatal error in CLI: {e}")
        logger.debug(traceback.format_exc())
        raise
