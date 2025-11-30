# translator.py
# Phase 4: Two-pass translation (function-based, no classes).
# - pass1_translate: produce a conservative Snowflake SQL draft grounded by retrieved chunks
# - pass2_repair: apply deterministic fixes + (optionally) LLM repair using validator signals
# - prepend_summary: add a top comment with citations, TODOs, and applied fixes
#
# Logging: creates C:\Users\CatherineVaras\Downloads\snowflake\logs\translator.log if missing.

from __future__ import annotations
import json
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# -------- Fixed paths --------
LOG_FILE = r"C:\Users\CatherineVaras\Downloads\snowflake\logs\translator.log"
SETTINGS_PATH = r"C:\Users\CatherineVaras\Downloads\snowflake\settings.json"

# -------- Logger --------
def _get_logger() -> logging.Logger:
    logger = logging.getLogger("translator_phase4")
    if getattr(logger, "_configured", False):
        return logger
    logger.setLevel(logging.DEBUG)
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S"))
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger._configured = True  # type: ignore[attr-defined]
    logger.debug("translator logger initialized")
    return logger

# -------- Settings / Azure client --------
def _load_settings(path: str = SETTINGS_PATH) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"settings.json not found at {p}")
    return json.loads(p.read_text(encoding="utf-8"))

def _get_azure_client():
    # Lazy import to keep module importable without the package
    from openai import AzureOpenAI
    settings = _load_settings()
    client = AzureOpenAI(
        api_key=settings["api_key"],
        api_version="2024-12-01-preview",
        azure_endpoint=settings["azure_endpoint"],
    )
    return client, settings

# -------- Small helpers --------
def _extract_citations(retrieved: Dict[str, Any], cap: int = 8) -> List[str]:
    items = retrieved.get("chunks", []) or []
    cites = []
    for ch in items[:cap]:
        c = ch.get("citation")
        if c and c not in cites:
            cites.append(c)
    return cites

_TODO_RE = re.compile(r"(?im)^\s*--\s*TODO:.*$")

def _scan_todos(sql: str) -> List[str]:
    return [m.group(0).strip() for m in _TODO_RE.finditer(sql)]

def _strip_trailing_semicolons(sql: str) -> str:
    return re.sub(r"[ \t]*;[ \t]*$", "", sql.strip())

def _ensure_ends_with_semicolon(sql: str) -> str:
    s = sql.rstrip()
    return s if s.endswith(";") else s + ";"

# A conservative TOP->LIMIT transform for SELECT statements.
# Notes:
# - Only transforms patterns like: SELECT TOP 10 ... FROM ...
# - If a LIMIT already exists, do nothing.
# - Appends LIMIT at the end of the outer-most query (naive but safe-ish for views).
_TOP_RE = re.compile(r"(?is)^\s*SELECT\s+TOP\s+(\d+)\s+", re.IGNORECASE)

def _apply_safe_fixes(sql: str, object_type: Optional[str], applied: List[str]) -> str:
    s = sql
    # Avoid double-limiting
    if re.search(r"(?i)\bLIMIT\s+\d+\b", s):
        pass
    else:
        m = _TOP_RE.search(s)
        if m and (object_type == "view" or object_type is None):
            n = m.group(1)
            # remove TOP N token
            s = _TOP_RE.sub("SELECT ", s, count=1)
            # append LIMIT N to the outer statement
            s = _strip_trailing_semicolons(s)
            s = s + f"\nLIMIT {n};"
            applied.append("TOP→LIMIT")
    return s

def _llm_chat(messages: List[Dict[str, str]], model: Optional[str]) -> str:
    logger = _get_logger()
    if not model:
        # Try settings.json
        try:
            _, settings = _get_azure_client()
            model = settings.get("chat_deployment")
        except Exception as e:
            logger.warning(f"LLM disabled: {e}")
            return ""
    try:
        client, settings = _get_azure_client()
        deployment = model or settings.get("chat_deployment")
        if not deployment:
            return ""
        resp = client.chat.completions.create(
            model=deployment,
            messages=messages,
            temperature=0.1,
            max_tokens=2000,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return ""

# -------- Public API --------
def pass1_translate(input_sql: str,
                    retrieved: Dict[str, Any],
                    object_type: Optional[str],
                    model: Optional[str] = None) -> Dict[str, Any]:
    """
    -> {"draft_sql": "...", "citations": [...], "todos": [...], "notes": [...], "retrieval_weak": bool}
    """
    logger = _get_logger()
    citations = _extract_citations(retrieved)
    retrieval_weak = bool(retrieved.get("retrieval_weak", False))

    system_prompt = (
        "You translate T-SQL (and similar SQL) to Snowflake.\n"
        "OUTPUT CONTRACT (must follow exactly):\n"
        "- Return a SINGLE executable Snowflake script. No explanations. No markdown fences.\n"
        "- Detect the object type (VIEW vs PROCEDURE) from either the provided object_type or the input code.\n"
        "\n"
        "VIEW RULES:\n"
        "- Output MUST start with: CREATE OR REPLACE VIEW <schema>.<name> [COPY GRANTS]\n"
        "- Then the keyword AS on its own line, then a SELECT body, then a single semicolon.\n"
        "- Never return a bare SELECT.\n"
        "- Prefer unquoted identifiers unless quoted/mixed-case exists in the source; preserve explicit schema qualifiers in FROM/JOIN.\n"
        "- Keep semantics exactly (columns, filters, windowing). Use QUALIFY only when strictly required (e.g., to deduplicate ties with ROW_NUMBER).\n"
        "\n"
        "PROCEDURE RULES (Snowflake SQL language):\n"
        "- Output MUST start with: CREATE OR REPLACE PROCEDURE <schema>.<name>(<args>)\n"
        "- Include: RETURNS <type>  LANGUAGE SQL  EXECUTE AS CALLER\n"
        "- Body wrapped in $$ ... $$ with a BEGIN ... END block and a RETURN statement. End with $$; (note the semicolon after $$).\n"
        "- If the original procedure returns nothing, return 'OK'::STRING.\n"
        "- Map variables/flow from T-SQL to Snowflake (DECLARE, SET, IF, WHILE, TRY/CATCH→EXCEPTION handler if needed). Prefer TEMP/TEMPORARY tables for #temp.\n"
        "\n"
        "GENERAL RULES:\n"
        "1) Output Snowflake SQL only.\n"
        "2) Prefer ANSI joins and Snowflake-native functions; if uncertain, add a line starting with '-- TODO:' stating the uncertainty.\n"
        "3) Do not invent objects/columns. Keep ordering/semantics.\n"
        "4) If CREATE name/sig cannot be inferred, emit a valid placeholder (e.g., <schema>.<name>) and add a '-- TODO:' line, but still emit full DDL (no bare SELECT).\n"
        "5) Terminate statements properly (view ends with ';', procedure ends with '$$;').\n"
    )

    # Provide minimal context: list of relevant sections (titles only)
    ctx_sections = "\n".join(f"- {c}" for c in citations) if citations else "- (no relevant sections)"

    user_prompt = f"""Source object type: {object_type or 'unknown'}.

Use these Snowflake doc sections as your grounding (titles):
{ctx_sections}

Now translate the following to **Snowflake SQL only**. If unsure: add `-- TODO:` lines.

---BEGIN SOURCE---
{input_sql}
---END SOURCE---"""

    # Try LLM; fall back to echo with TODO if unavailable
    draft_sql = _llm_chat(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=model,
    )
    if not draft_sql:
        draft_sql = f"""-- TODO: Model unavailable; conservative pass-through. Review manually.
{input_sql}"""

    todos = _scan_todos(draft_sql)
    notes = ["conservative", "phase4-pass1"]
    logger.info(f"pass1_translate: citations={len(citations)} weak={retrieval_weak} todos={len(todos)}")
    return {
        "draft_sql": draft_sql.strip(),
        "citations": citations,
        "todos": todos,
        "notes": notes,
        "retrieval_weak": retrieval_weak,
    }

def pass2_repair(draft_sql: str,
                 retrieved: Dict[str, Any],
                 signals: Dict[str, Any],
                 object_type: Optional[str],
                 model: Optional[str] = None) -> Dict[str, Any]:
    """
    -> {"final_sql": "...", "applied_fixes": [...], "remaining_todos": [...]}
    """
    logger = _get_logger()
    applied_fixes: List[str] = []

    # 1) Apply small deterministic fixes (very conservative)
    repaired = _apply_safe_fixes(draft_sql, object_type, applied_fixes)

    # 2) If an LLM is available, ask it to normalize/repair using validator signals + retrieved citations
    sig_errors = signals.get("errors", [])
    sig_warnings = signals.get("warnings", [])
    sig_suggestions = signals.get("suggestions", [])
    citations = _extract_citations(retrieved)

    require_llm = bool(sig_errors or sig_warnings or sig_suggestions)  # only call if there's something to fix
    if require_llm:
        system_prompt = (
            "You are a careful Snowflake SQL fixer. Normalize/repair the input into ONE executable Snowflake script.\n"
            "No explanations. No markdown fences.\n"
            "\n"
            "HARD REQUIREMENTS:\n"
            "A) If the object is a VIEW:\n"
            "   - Script MUST begin with 'CREATE OR REPLACE VIEW ' followed by <schema>.<name> [COPY GRANTS]\n"
            "   - Then 'AS' on a new line, then the SELECT body, then a single semicolon at the end.\n"
            "   - If the input is a bare SELECT, wrap it accordingly.\n"
            "\n"
            "B) If the object is a PROCEDURE:\n"
            "   - Script MUST begin with 'CREATE OR REPLACE PROCEDURE ' followed by <schema>.<name>(<args>)\n"
            "   - MUST include: RETURNS <type>, LANGUAGE SQL, EXECUTE AS CALLER\n"
            "   - Body wrapped in $$ ... $$, with BEGIN ... END, and at least one RETURN. End with $$; (semicolon after $$).\n"
            "\n"
            "SAFE FIXES:\n"
            "- Apply validator suggestions when unambiguous (e.g., TOP→LIMIT, use QUALIFY for tie-breaking if needed, bracket→identifier, function equivalences).\n"
            "- Preserve semantics and explicit schema qualification; do not invent columns/tables.\n"
            "- If anything remains uncertain, keep original and add '-- TODO:' explaining the ambiguity.\n"
            "- Ensure final output compiles in Snowflake as-is.\n"
        )
        guide = {
            "object_type": object_type,
            "validator": {
                "errors": sig_errors,
                "warnings": sig_warnings,
                "suggestions": sig_suggestions,
            },
            "citations": citations,
        }
        user_prompt = f"""Repair and normalize this draft for Snowflake:

Guidance (JSON):
{json.dumps(guide, indent=2)}

---BEGIN DRAFT---
{repaired}
---END DRAFT---

Output Snowflake SQL only. If unsure about any fix, add `-- TODO:` and leave the original structure."""
        llm_out = _llm_chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=model,
        )
        if llm_out:
            repaired = llm_out

    # 3) Post-process formatting hygiene
    repaired = repaired.strip()
    # Ensure one terminal semicolon for single statements (best-effort; safe for views)
    if object_type == "view":
        repaired = _ensure_ends_with_semicolon(_strip_trailing_semicolons(repaired))

    remaining_todos = _scan_todos(repaired)
    logger.info(f"pass2_repair: fixes={applied_fixes} todos_left={len(remaining_todos)}")
    return {
        "final_sql": repaired,
        "applied_fixes": applied_fixes,
        "remaining_todos": remaining_todos,
    }

def prepend_summary(final_sql: str,
                    citations: List[str],
                    todos: List[str],
                    applied_fixes: List[str]) -> str:
    """
    -> "<comment block>\\n<final snowflake sql>"
    """
    lines: List[str] = []
    lines.append("-- ===============================================")
    lines.append("-- Translation summary (Phase 4)")
    if citations:
        lines.append("-- Citations:")
        for c in citations:
            lines.append(f"--   - {c}")
    else:
        lines.append("-- Citations: (none)")
    if applied_fixes:
        lines.append("-- Applied fixes:")
        for f in applied_fixes:
            lines.append(f"--   - {f}")
    else:
        lines.append("-- Applied fixes: (none)")
    if todos:
        lines.append("-- TODOs:")
        for t in todos:
            lines.append(f"--   {t}")
    else:
        lines.append("-- TODOs: (none)")
    lines.append("-- ===============================================")
    summary = "\n".join(lines)
    return f"{summary}\n{final_sql.strip()}"
