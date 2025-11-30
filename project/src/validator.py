# validator.py
# Phase 4: Deterministic inter-pass signals (no LLM).
# - Input: SQL text (ideally Pass-1 draft) + object_type ("view" | "procedure" | None)
# - Output: { "object_type": str|None, "errors":[], "warnings":[], "suggestions":[] }
# - Logging: creates ...\logs\validator.log if missing; minimal console.

from __future__ import annotations
import re
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# ---------- Fixed paths ----------
LOG_FILE = r"C:\Users\CatherineVaras\Downloads\snowflake\logs\validator.log"

# ---------- Logger ----------
def _get_logger() -> logging.Logger:
    logger = logging.getLogger("validator_phase4")
    if getattr(logger, "_configured", False):
        return logger
    logger.setLevel(logging.DEBUG)
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)  # ensure folder
    fh = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"))
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger._configured = True  # type: ignore[attr-defined]
    logger.debug("validator logger initialized")
    return logger

# ---------- Strip comments & strings ----------
_COMMENT_BLOCK_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_COMMENT_LINE_RE  = re.compile(r"--[^\n]*")
# single-quoted strings with '' escapes
_SQ_RE            = re.compile(r"'(?:''|[^'])*'", re.DOTALL)
# dollar-quoted blocks: $$ ... $$
_DOLLAR_RE        = re.compile(r"\$\$.*?\$\$", re.DOTALL | re.IGNORECASE)

def _strip_comments(sql: str) -> str:
    s = _COMMENT_BLOCK_RE.sub(" ", sql)
    s = _COMMENT_LINE_RE.sub(" ", s)
    return s

def _mask_strings(sql: str) -> str:
    s = _SQ_RE.sub(" '' ", sql)
    # keep $$ markers presence detectable but mask content
    s = _DOLLAR_RE.sub(" $$ $$ ", s)
    return s

def _prep(sql: str) -> str:
    return _mask_strings(_strip_comments(sql))

# ---------- Helpers ----------
def _add(lst: List[Dict[str, str]], code: str, msg: str) -> None:
    lst.append({"code": code, "msg": msg})

def _has(pattern: str, s: str, flags=re.IGNORECASE) -> bool:
    return re.search(pattern, s, flags) is not None

# ---------- Core validation ----------
def make_signals(sql: str, object_type: str | None) -> Dict[str, Any]:
    """
    Returns:
      {
        "object_type": "...",
        "errors": [{"code","msg"}],
        "warnings": [{"code","msg"}],
        "suggestions": [{"code","msg"}]
      }
    """
    logger = _get_logger()
    try:
        cleaned = _prep(sql)
        otype = (object_type or "").lower() or None

        errors: List[Dict[str, str]] = []
        warnings: List[Dict[str, str]] = []
        suggestions: List[Dict[str, str]] = []

        # --------------------
        # Common detections
        # --------------------
        has_top          = _has(r"\bTOP\s+\d+\b", cleaned)
        has_begin        = _has(r"\bBEGIN\b", cleaned)
        has_end          = _has(r"\bEND\b", cleaned)
        has_over         = _has(r"\bOVER\s*\(", cleaned)
        has_qualify      = _has(r"\bQUALIFY\b", cleaned)
        has_getdate_like = _has(r"\b(GETDATE|GETUTCDATE|CURRENT_TIMESTAMP)\s*\(", cleaned)
        has_proc_tokens  = _has(r"\b(DECLARE|RETURN|RAISERROR|TRY|CATCH)\b", cleaned)
        has_dollars_as   = _has(r"\bAS\s*\$\$\b", cleaned) and _has(r"\$\$", cleaned)
        has_language_sql = _has(r"\bLANGUAGE\s+SQL\b", cleaned)
        has_language_js  = _has(r"\bLANGUAGE\s+JAVASCRIPT\b", cleaned)
        has_js_tokens    = _has(r"\b(var|let|const|function)\b", cleaned)
        has_sql_tokens   = _has(r"\b(SELECT|INSERT|UPDATE|DELETE|MERGE|WITH)\b", cleaned)

        # --------------------
        # VIEW checks
        # --------------------
        if otype == "view":
            if has_top:
                _add(warnings, "TOP_IN_VIEW", "Use LIMIT instead of TOP in views.")
            if has_proc_tokens:
                _add(warnings, "PROC_TOKENS_IN_VIEW", "Procedure-like tokens found in a VIEW definition; verify logic belongs in a procedure.")
            # QUALIFY hint: if windowing is used but QUALIFY missing, suggest it
            if has_over and not has_qualify:
                _add(suggestions, "MOVE_TO_QUALIFY", "Windowed expressions detected; consider filtering with QUALIFY instead of WHERE.")
            # Timestamp casting ambiguity
            if has_getdate_like:
                _add(suggestions, "TS_CAST_AMBIGUOUS", "Timestamp function detected; cast explicitly to TIMESTAMP_NTZ/TZ or DATE to avoid implicit conversions.")

        # --------------------
        # PROCEDURE checks
        # --------------------
        if otype == "procedure":
            # Snowflake requires RETURNS <type>
            if not _has(r"\bRETURNS\b\s+[A-Z_][A-Z0-9_]*", cleaned):
                _add(errors, "MISSING_RETURNS", "Snowflake PROCEDURE must declare RETURNS <type> (e.g., RETURNS STRING).")
            # Body delimiter AS $$ ... $$ (common style, esp. with LANGUAGE SQL/JS)
            if not has_dollars_as:
                _add(warnings, "MISSING_DOLLARS", "Procedure body not found between AS $$ $$; ensure correct body delimiter for LANGUAGE SQL/JAVASCRIPT.")
            # Language mismatch heuristics
            if has_language_js and has_sql_tokens and not has_js_tokens:
                _add(warnings, "LANGUAGE_MISMATCH", "LANGUAGE JAVASCRIPT declared but body looks like SQL.")
            if has_language_sql and has_js_tokens:
                _add(warnings, "LANGUAGE_MISMATCH", "LANGUAGE SQL declared but body contains JavaScript-like tokens.")
            # Control-flow without clear scoping (heuristic)
            has_if     = _has(r"\bIF\b", cleaned)
            has_while  = _has(r"\bWHILE\b", cleaned)
            has_loop   = _has(r"\bLOOP\b", cleaned)
            if (has_if or has_while or has_loop) and not (has_begin and has_end) and not has_language_js:
                _add(warnings, "UNSCOPED_CONTROL", "Control-flow tokens found without BEGIN...END block (Snowflake SQL Scripting) or JS function scope.")

        res = {
            "object_type": otype,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }
        logger.info(
            "make_signals: type=%s e=%d w=%d s=%d",
            otype, len(errors), len(warnings), len(suggestions)
        )
        return res

    except Exception as e:
        logger.error(f"Unhandled error in make_signals: {e}")
        raise

# ---------- Minimal CLI ----------
# Usage:
#   python validator.py --text "CREATE VIEW dbo.v AS SELECT TOP 10 * FROM t;"
#   python validator.py --file "C:\path\proc.sql" procedure
if __name__ == "__main__":
    logger = _get_logger()
    try:
        if len(sys.argv) < 3:
            print(
                "Usage:\n"
                "  python validator.py --text \"<sql>\" view|procedure|unknown\n"
                "  python validator.py --file \"C:\\path\\to.sql\" view|procedure|unknown"
            )
            sys.exit(0)

        mode = sys.argv[1]
        otype = (sys.argv[3] if len(sys.argv) > 3 else None)
        if mode == "--text":
            sql_text = sys.argv[2]
        elif mode == "--file":
            p = Path(sys.argv[2])
            sql_text = p.read_text(encoding="utf-8", errors="ignore")
        else:
            print("First arg must be --text or --file")
            sys.exit(1)

        result = make_signals(sql_text, otype)
        print(json.dumps(result, indent=2))
    except Exception as ex:
        logger.error(f"Fatal error in CLI: {ex}")
        raise
