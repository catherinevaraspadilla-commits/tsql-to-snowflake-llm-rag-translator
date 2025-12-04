# detector.py
# Phase 4: Object detector (function-based, no classes).
# - Confirms object type (view|procedure|None)
# - Extracts object name if present (schema.name allowed, quoted/bracketed)
# - Emits quick boolean hints used by validator/translators.
#
# Logging: creates C:\Users\CatherineVaras\Downloads\snowflake\logs\detector.log if missing.

from __future__ import annotations
import re
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

# -------- Fixed paths --------
LOG_FILE = r"C:\Users\CatherineVaras\Downloads\tsql-to-snowflake-llm-rag-translator\project\logs\detector.log"

# -------- Logger --------
def _get_logger() -> logging.Logger:
    logger = logging.getLogger("detector_phase4")
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
    logger.debug("detector logger initialized")
    return logger

# -------- Utilities --------
# Remove /* */ and -- EOL comments, and single-quoted string literals.
_COMMENT_BLOCK_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_COMMENT_LINE_RE  = re.compile(r"--[^\n]*")
# Handles escaped single quotes '' inside strings.
_STRING_RE        = re.compile(r"('(?:''|[^'])*')", re.DOTALL)

def _strip_comments_and_strings(sql: str) -> str:
    s = _COMMENT_BLOCK_RE.sub(" ", sql)
    s = _COMMENT_LINE_RE.sub(" ", s)
    # Replace string literals with a placeholder to avoid false keyword hits
    s = _STRING_RE.sub(" '' ", s)
    return s

# Identifier pieces: bare, [bracketed], or "quoted"
_IDENT_PART = r'(?:\[.*?\]|".*?"|[A-Za-z_][A-Za-z0-9_\$]*)'
# Full (optionally schema-qualified) name: part(.part){0,2}
_FULL_NAME = rf"{_IDENT_PART}(?:\s*\.\s*{_IDENT_PART}){{0,2}}"

# CREATE VIEW / PROCEDURE patterns (tolerate OR REPLACE, CREATE PROC shorthand)
_VIEW_RE = re.compile(
    rf"^\s*CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+(?P<name>{_FULL_NAME})",
    re.IGNORECASE | re.MULTILINE
)
_PROC_RE = re.compile(
    rf"^\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:PROCEDURE|PROC)\s+(?P<name>{_FULL_NAME})",
    re.IGNORECASE | re.MULTILINE
)

def _normalize_name(raw: str | None) -> str | None:
    """Flatten whitespace around dots and strip outer quotes/brackets on each part."""
    if not raw:
        return None
    parts = [p.strip() for p in re.split(r"\s*\.\s*", raw)]
    norm_parts = []
    for p in parts:
        if p.startswith("[") and p.endswith("]"):
            p = p[1:-1]
        elif p.startswith('"') and p.endswith('"'):
            p = p[1:-1]
        norm_parts.append(p)
    return ".".join(norm_parts)

# -------- Public API --------
def detect_object(sql: str) -> Dict[str, Any]:
    """
    -> {
         "object_type": "view" | "procedure" | None,
         "name": "schema.obj" | None,
         "hints": {
            "has_top": bool,
            "has_begin": bool,
            "has_dollar_quotes": bool,
            "has_proc_tokens_in_view": bool,
            "has_getdate": bool,
            "has_over_clause": bool,
            "has_qualify": bool
         }
       }
    """
    logger = _get_logger()
    try:
        cleaned = _strip_comments_and_strings(sql)

        # Type + name
        m_view = _VIEW_RE.search(cleaned)
        m_proc = _PROC_RE.search(cleaned)

        if m_view and not m_proc:
            otype = "view"
            name = _normalize_name(m_view.group("name"))
        elif m_proc and not m_view:
            otype = "procedure"
            name = _normalize_name(m_proc.group("name"))
        elif m_view and m_proc:
            # If both appear, pick the earliest occurrence
            otype = "view" if m_view.start() < m_proc.start() else "procedure"
            name = _normalize_name((m_view if otype == "view" else m_proc).group("name"))
        else:
            otype, name = None, None

        # Hints (fast booleans, on cleaned text)
        # TOP keyword (standalone)
        has_top = bool(re.search(r"\bTOP\s+\d+", cleaned, re.IGNORECASE))
        # BEGIN token (likely T-SQL proc)
        has_begin = bool(re.search(r"\bBEGIN\b", cleaned, re.IGNORECASE))
        # $$ dollar-quoted blocks (often pg-like scripting)
        has_dollar_quotes = "$$" in cleaned
        # proc-ish tokens in what appears to be a view (BEGIN, DECLARE, RETURN, etc.)
        has_proc_tokens = bool(re.search(r"\b(DECLARE|RETURN|BEGIN|END|RAISERROR|TRY|CATCH)\b", cleaned, re.IGNORECASE))
        has_proc_tokens_in_view = (otype == "view" and has_proc_tokens)

        # time functions common in T-SQL
        has_getdate = bool(re.search(r"\b(GETDATE|GETUTCDATE)\s*\(", cleaned, re.IGNORECASE))

        # windowing / filtering cues
        has_over_clause = bool(re.search(r"\bOVER\s*\(", cleaned, re.IGNORECASE))
        has_qualify     = bool(re.search(r"\bQUALIFY\b", cleaned, re.IGNORECASE))

        res = {
            "object_type": otype,
            "name": name,
            "hints": {
                "has_top": has_top,
                "has_begin": has_begin,
                "has_dollar_quotes": has_dollar_quotes,
                "has_proc_tokens_in_view": has_proc_tokens_in_view,
                "has_getdate": has_getdate,
                "has_over_clause": has_over_clause,
                "has_qualify": has_qualify,
            },
        }
        logger.info(f"detect_object: type={otype} name={name} hints={{top:{has_top}, begin:{has_begin}, $$:{has_dollar_quotes}}}")
        return res

    except Exception as e:
        logger.error(f"Unhandled error in detect_object: {e}")
        raise

# -------- Minimal CLI --------
# Usage:
#   python detector.py "C:\path\to\file.sql"
#   python detector.py --text "CREATE VIEW dbo.v AS SELECT TOP 10 * FROM t;"
if __name__ == "__main__":
    logger = _get_logger()
    try:
        if len(sys.argv) < 2:
            print("Usage:\n  python detector.py <sql-file>\n  python detector.py --text \"<inline sql>\"")
            sys.exit(0)

        if sys.argv[1] == "--text":
            sql_text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        else:
            p = Path(sys.argv[1])
            sql_text = p.read_text(encoding="utf-8", errors="ignore")

        result = detect_object(sql_text)
        print(json.dumps(result, indent=2))
    except Exception as ex:
        logger.error(f"Fatal error in CLI: {ex}")
        raise
