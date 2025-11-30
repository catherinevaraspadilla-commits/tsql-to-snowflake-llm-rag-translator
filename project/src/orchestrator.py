# orchestrator.py
# Phase 4: End-to-end orchestrator with per-stage traceability.
# - Reads scripts_input/*.sql
# - Splits & classifies into "translate" vs "dont_translate"
# - For translate parts: detector -> retrieve -> pass1 -> validator -> pass2 -> prepend summary
# - Writes stage artifacts under output/<stage>/<base>/...
# - Final:
#     output/final/<base>_snowflake.sql
#     output/final/<base>/not_translated.sql   (folder: output/final/<base>/)
#
# Logging: creates C:\Users\CatherineVaras\Downloads\snowflake\logs\main.log if missing.

from __future__ import annotations
import re
import json
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any

# ---- Fixed paths ----
ROOT = Path(r"C:\Users\CatherineVaras\Downloads\snowflake")
INPUT_DIR  = ROOT / "scripts_input"
FINAL_DIR  = ROOT / "output" / "final"
MANIFESTS  = ROOT / "output" / "manifests"
LOG_FILE   = ROOT / "logs" / "main.log"
SETTINGS   = ROOT / "settings.json"

# Stage roots
STAGES = {
    "splitter": ROOT / "output" / "splitter",
    "detector": ROOT / "output" / "detector",
    "retrieve": ROOT / "output" / "retrieve",
    "translator_pass1": ROOT / "output" / "translator_pass1",
    "validator": ROOT / "output" / "validator",
    "translator_pass2": ROOT / "output" / "translator_pass2",
}

# ---- Imports from other modules ----
from detector import detect_object
from embed import retrieve
from validator import make_signals
from translator import pass1_translate, pass2_repair, prepend_summary

# ---- Logger ----
def _get_logger() -> logging.Logger:
    logger = logging.getLogger("main_orchestrator")
    if getattr(logger, "_configured", False):
        return logger
    logger.setLevel(logging.DEBUG)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"))
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)   # minimal console
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger._configured = True  # type: ignore[attr-defined]
    logger.debug("main logger initialized")
    return logger

# ---- Settings ----
def _load_settings() -> Dict[str, Any]:
    if not SETTINGS.exists():
        return {}
    try:
        return json.loads(SETTINGS.read_text(encoding="utf-8"))
    except Exception:
        return {}

# ---- File IO helpers ----
def _stage_dir(stage: str, base: str, clean: bool = False) -> Path:
    """Return stage/<base> dir; if clean, delete and recreate."""
    root = STAGES[stage]
    d = root / base
    if clean and d.exists():
        shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True, exist_ok=True)
    return d

def _write_text(stage: str, base: str, rel_name: str, content: str) -> Path:
    d = _stage_dir(stage, base)  # ensure exists
    p = d / rel_name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p

def _write_json(stage: str, base: str, rel_name: str, obj: Any) -> Path:
    d = _stage_dir(stage, base)  # ensure exists
    p = d / rel_name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    return p

def list_input_files() -> List[Path]:
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(INPUT_DIR.glob("*.sql"))

def read_sql_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def write_final_output(base_name: str, content: str) -> Path:
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FINAL_DIR / f"{base_name}_snowflake.sql"
    out_path.write_text(content, encoding="utf-8")
    return out_path

# ---- Splitter & classifier ----
# Starts of CREATE objects
_OBJ_START_RE = re.compile(r"(?im)^\s*CREATE\s+(?:OR\s+REPLACE\s+)?(VIEW|PROCEDURE|PROC)\s+[^\n]+")
# Dollar-quoted blocks
_DOLLAR_BLOCK_RE = re.compile(r"(?is)\$\$.*?\$\$")
# Exec extended property
_EXTPROP_RE = re.compile(r"(?im)^\s*EXEC\s+sys\.sp_addextendedproperty\b")
# Top-level admin tokens
_ADMIN_RE = re.compile(r"(?im)^\s*(USE|SET|GO|ALTER\s+SESSION)\b")

def _mask_dollar_blocks(s: str) -> str:
    return _DOLLAR_BLOCK_RE.sub(lambda m: " " * (m.end() - m.start()), s)

def _zero(n: int) -> str:
    return f"{n:04d}"

def split_into_objects(tsql: str) -> List[Dict[str, Any]]:
    """
    Produce coarse parts around CREATE blocks; anything outside becomes separate parts.
    """
    text = tsql
    masked = _mask_dollar_blocks(text)

    parts: List[Dict[str, Any]] = []
    starts = [m.start() for m in _OBJ_START_RE.finditer(masked)]
    starts.sort()

    def add_part(idx: int, span_text: str, is_preamble: bool = False):
        head = span_text[:400]
        m = re.search(r"(?is)^\s*CREATE\s+(?:OR\s+REPLACE\s+)?(VIEW|PROCEDURE|PROC)\s+([^\s\(;]+)", head)
        obj_type = None
        name = None
        if m:
            t = m.group(1).lower()
            obj_type = "view" if t == "view" else "procedure"
            name = m.group(2).strip().strip("[]\"")
        parts.append({
            "span_index": idx,
            "text": span_text.strip(),
            "object_type": obj_type if not is_preamble else "unknown",
            "name": name if not is_preamble else None,
            "preamble": bool(is_preamble),
        })

    if not starts:
        # single preamble-like part
        add_part(0, text, is_preamble=True)
        return parts

    # leading non-object (preamble/admin/metadata may be here)
    if starts[0] > 0:
        add_part(0, text[:starts[0]], is_preamble=True)

    # objects plus any text between them
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        block = text[start:end]

        # split on GO only if not inside $$...$$
        block_masked = _mask_dollar_blocks(block)
        go_positions = [m.start() for m in re.finditer(r"(?im)^\s*GO\s*$", block_masked)]

        if not go_positions:
            add_part(start, block, is_preamble=False)
        else:
            last = 0
            for gpos in go_positions:
                segment = block[last:gpos]
                if segment.strip():
                    add_part(start + last, segment, is_preamble=False)
                # skip the GO line itself
                # advance to just after the GO line end
                nl_pos = block.find("\n", gpos)
                last = (nl_pos + 1) if nl_pos != -1 else len(block)
            tail = block[last:]
            if tail.strip():
                add_part(start + last, tail, is_preamble=False)

    return parts

def _classify_part(part: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine translate vs dont_translate, object_type/admin/metadata/unknown, and reason.
    """
    txt = part.get("text", "")
    first_line = txt.lstrip().splitlines()[0] if txt.strip() else ""
    reason = ""
    category = "dont_translate"
    otype = part.get("object_type") or None

    if part.get("preamble"):
        reason = "preamble/top-level"
        return {**part, "object_type": "admin", "category": "dont_translate", "reason": reason}

    if _OBJ_START_RE.match(first_line):
        # CREATE VIEW/PROCEDURE => translate
        kind = re.match(r"(?im)^\s*CREATE\s+(?:OR\s+REPLACE\s+)?(VIEW|PROCEDURE|PROC)\b", first_line).group(1).lower()
        otype = "view" if kind == "view" else "procedure"
        reason = f"CREATE {kind.upper()}"
        category = "translate"
    elif _EXTPROP_RE.match(first_line):
        reason = "EXEC sp_addextendedproperty"
        otype = "metadata"
        category = "dont_translate"
    elif _ADMIN_RE.match(first_line) or not first_line or first_line.startswith("--"):
        reason = "Top-level admin/comment"
        otype = "admin"
        category = "dont_translate"
    else:
        reason = "Unknown top-level statement"
        otype = "unknown"
        category = "dont_translate"

    return {**part, "object_type": otype, "category": category, "reason": reason}

# ---- Assembly helpers ----
def _commentify(s: str) -> str:
    lines = [ln.rstrip() for ln in s.splitlines()]
    return "\n".join(f"-- {ln}" if ln.strip() else "--" for ln in lines)

def assemble_file_sql_only(parts_results: List[Dict[str, Any]]) -> str:
    """
    Join only the clean SQL blocks (no preamble, no long headers).
    We keep a single short marker per object to separate blocks.
    """
    out: List[str] = []
    for idx, res in enumerate(parts_results):
        name = res.get("meta", {}).get("name") or f"part_{idx+1}"
        otype = (res.get("meta", {}).get("type") or "UNKNOWN").upper()
        out.append(f"-- {name} ({otype})")  # short, one-line
        out.append(res["final_sql_clean"].rstrip())
        out.append("")  # blank line
    return "\n".join(out).rstrip() + "\n"

# ---- Per-part translation ----
def translate_part(part: Dict[str, Any], settings: Dict[str, Any], base: str, part_idx: int) -> Dict[str, Any]:
    logger = _get_logger()
    try:
        det = detect_object(part["text"])
        otype = det.get("object_type") or part.get("object_type") or "unknown"
        _write_json("detector", base, f"part_{_zero(part_idx)}.json", det)

        r = retrieve(query=part["text"], object_type=otype)
        _write_json("retrieve", base, f"part_{_zero(part_idx)}.json", r)

        model = settings.get("chat_deployment")
        p1 = pass1_translate(part["text"], r, otype, model=model)
        _write_text("translator_pass1", base, f"part_{_zero(part_idx)}.sql", p1["draft_sql"])
        _write_json("translator_pass1", base, f"part_{_zero(part_idx)}_meta.json",
                    {"citations": p1["citations"], "todos": p1["todos"], "notes": p1["notes"], "retrieval_weak": p1["retrieval_weak"]})

        sig = make_signals(p1["draft_sql"], otype)
        _write_json("validator", base, f"part_{_zero(part_idx)}.json", sig)

        p2 = pass2_repair(p1["draft_sql"], r, sig, otype, model=model)

        # ---- NEW: build both variants ----
        clean_sql = p2["final_sql"]  # SQL-only
        doc_sql   = prepend_summary(
            p2["final_sql"], p1["citations"], p2["remaining_todos"], p2["applied_fixes"]
        )

        # Write both per-part artifacts
        _write_text("translator_pass2", base, f"part_{_zero(part_idx)}.sql", clean_sql)            # clean
        _write_text("translator_pass2", base, f"part_{_zero(part_idx)}_doc.sql", doc_sql)          # documented
        _write_json("translator_pass2", base, f"part_{_zero(part_idx)}_meta.json",
                    {"applied_fixes": p2["applied_fixes"], "remaining_todos": p2["remaining_todos"]})

        meta = {
            "name": det.get("name") or part.get("name"),
            "type": otype,
            "citations": p1["citations"],
            "todos": p2["remaining_todos"],
            "applied_fixes": p2["applied_fixes"],
            "retrieval_weak": bool(r.get("retrieval_weak", False)),
        }
        # Return both variants
        return {"ok": True, "final_sql_clean": clean_sql, "final_sql_doc": doc_sql, "meta": meta}

    except Exception as e:
        logger.error(f"translate_part failed: {e}")
        fallback = (
            f"-- ERROR: Failed translating part (see logs)\n"
            f"/* Original T-SQL preserved: */\n{part['text']}\n"
        )
        _write_text("translator_pass2", base, f"part_{_zero(part_idx)}.sql", fallback)
        _write_json("translator_pass2", base, f"part_{_zero(part_idx)}_meta.json", {"error": str(e)})
        return {"ok": False, "final_sql_clean": fallback, "final_sql_doc": fallback, "meta": {"error": str(e)}}

# ---- End-to-end ----
def process_all_inputs() -> Dict[str, Any]:
    logger = _get_logger()
    settings = _load_settings()
    files = list_input_files()
    summary: Dict[str, Any] = {"files": [], "total_inputs": len(files)}
    logger.info(f"Discovered {len(files)} input file(s) in {INPUT_DIR.as_posix()}")

    for f in files:
        base = f.stem
        logger.info(f"Processing: {base}.sql")
        raw = read_sql_file(f)

        # Clean stage dirs for this base to allow overwrite on re-run
        for stage in STAGES:
            _stage_dir(stage, base, clean=True)
        MANIFESTS.mkdir(parents=True, exist_ok=True)
        (FINAL_DIR / base).mkdir(parents=True, exist_ok=True)  # for not_translated.sql

        # Split
        parts = split_into_objects(raw)

        # Classify + write splitter artifacts
        split_dir = _stage_dir("splitter", base)
        (split_dir / "translate").mkdir(parents=True, exist_ok=True)
        (split_dir / "dont_translate").mkdir(parents=True, exist_ok=True)

        parts_index: List[Dict[str, Any]] = []
        preamble_text = ""
        translate_parts: List[Dict[str, Any]] = []
        dont_parts: List[Dict[str, Any]] = []

        for i, p in enumerate(sorted(parts, key=lambda x: x["span_index"])):
            idx = i + 1
            classified = _classify_part(p)
            classified["idx"] = idx  # stable index for filenames

            # Save raw part text to the appropriate splitter subfolder
            if classified["category"] == "translate":
                (split_dir / "translate").mkdir(exist_ok=True)
                (split_dir / "translate" / f"part_{_zero(idx)}.sql").write_text(
                    classified["text"], encoding="utf-8"
                )
                translate_parts.append(classified)
            else:
                (split_dir / "dont_translate").mkdir(exist_ok=True)
                (split_dir / "dont_translate" / f"part_{_zero(idx)}.sql").write_text(
                    classified["text"], encoding="utf-8"
                )
                dont_parts.append(classified)
                if classified.get("preamble"):
                    preamble_text += (classified.get("text", "") + "\n")

            parts_index.append({
                "idx": idx,
                "span_index": classified["span_index"],
                "object_type": classified["object_type"],
                "category": classified["category"],
                "reason": classified["reason"],
                "name": classified.get("name"),
                "file_offset": classified["span_index"]
            })

        _write_json("splitter", base, "parts.json", parts_index)
        if preamble_text.strip():
            (split_dir / "preamble.sql").write_text(preamble_text, encoding="utf-8")

        # Translate only "translate" parts
        results: List[Dict[str, Any]] = []
        for part in translate_parts:
            out = translate_part(part, settings, base, part["idx"])
            results.append(out)

        # Build not_translated.sql (final/<base>/not_translated.sql)
        non_translated_summary = [{"idx": p["idx"], "reason": p["reason"]} for p in dont_parts]
        not_translated_path = FINAL_DIR / base / "not_translated.sql"
        lines = []
        for p in dont_parts:
            lines.append(f"-- part_{_zero(p['idx'])}: {p['reason']}")
            lines.append(p["text"].rstrip())
            lines.append("")  # blank line
        not_translated_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

        # ---- NEW: assemble clean SQL-only final file
        final_sql_clean = assemble_file_sql_only(results)
        out_path = write_final_output(base, final_sql_clean)

        # ---- NEW: also write a documented version (optional)
        explain_path = FINAL_DIR / base / "explain_summary.sql"
        doc_lines = []
        for idx, r in enumerate(results):
            name = r.get("meta", {}).get("name") or f"part_{idx+1}"
            otype = (r.get("meta", {}).get("type") or "UNKNOWN").upper()
            doc_lines.append(f"-- {name} ({otype})")
            doc_lines.append(r["final_sql_doc"].rstrip())
            doc_lines.append("")
        explain_path.write_text("\n".join(doc_lines).rstrip() + "\n", encoding="utf-8")

        logger.info(f"Wrote final(clean): {out_path.as_posix()}  |  documented: {explain_path.as_posix()}  |  not-translated: {not_translated_path.as_posix()}")

        file_report = {
            "input": f.as_posix(),
            "output": out_path.as_posix(),
            "not_translated": not_translated_path.as_posix(),
            "parts_total": len(parts_index),
            "translate_parts": len(translate_parts),
            "dont_translate_parts": len(dont_parts),
            "ok_parts": sum(1 for r in results if r["ok"]),
            "fallback_parts": sum(1 for r in results if not r["ok"]),
            "stage_paths": {k: (v / base).as_posix() for k, v in STAGES.items()},
            "splitter_path": (STAGES["splitter"] / base).as_posix()
        }
        (MANIFESTS / f"{base}.json").write_text(json.dumps(file_report, indent=2), encoding="utf-8")
        summary["files"].append(file_report)

    return summary

# ---- CLI ----
if __name__ == "__main__":
    log = _get_logger()
    try:
        rep = process_all_inputs()
        print(f"[Phase 4] Orchestrator finished. files={rep['total_inputs']}")
    except Exception as e:
        log.error(f"Fatal error in orchestrator: {e}")
        raise
