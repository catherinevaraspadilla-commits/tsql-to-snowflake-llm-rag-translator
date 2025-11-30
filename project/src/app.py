# app.py
# Streamlit UI to browse Snowflake translation pipeline outputs and run the pipeline.
# Works even if there's no prior output — shows a Getting Started panel.

import json
import traceback
from pathlib import Path
import pandas as pd
import streamlit as st

# ---------- Fixed paths (must match orchestrator.py) ----------
ROOT = Path(r"C:\Users\CatherineVaras\Downloads\snowflake")
INPUT_DIR = ROOT / "scripts_input"
OUTPUT = ROOT / "output"
FINAL_DIR = OUTPUT / "final"
MANIFESTS = OUTPUT / "manifests"

STAGES = {
    "splitter": OUTPUT / "splitter",
    "detector": OUTPUT / "detector",
    "retrieve": OUTPUT / "retrieve",
    "translator_pass1": OUTPUT / "translator_pass1",
    "validator": OUTPUT / "validator",
    "translator_pass2": OUTPUT / "translator_pass2",
}

# ---------- Small utils ----------
def ensure_dirs():
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    for p in STAGES.values():
        p.mkdir(parents=True, exist_ok=True)

def list_bases() -> list[str]:
    bases = set()
    if FINAL_DIR.exists():
        for p in FINAL_DIR.glob("*_snowflake.sql"):
            bases.add(p.stem.replace("_snowflake", ""))
        for p in FINAL_DIR.iterdir():
            if p.is_dir():
                bases.add(p.name)
    sp = STAGES["splitter"]
    if sp.exists():
        for d in sp.iterdir():
            if d.is_dir():
                bases.add(d.name)
    return sorted(b for b in bases if b.strip())

def read_text(p: Path) -> str | None:
    try:
        if p.exists():
            return p.read_text(encoding="utf-8", errors="ignore")
        return None
    except Exception:
        return f"-- Error reading file: {p}\n-- {traceback.format_exc()}"

def read_json(p: Path):
    try:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return None
    except Exception:
        return {"__error__": f"Failed to parse JSON at {p.as_posix()}"}

def list_stage_files(stage_root: Path, base: str) -> list[Path]:
    d = stage_root / base
    if not d.exists():
        return []
    return sorted([p for p in d.rglob("*") if p.is_file()])

def download_button(label: str, filepath: Path, mime: str = "text/plain"):
    content = read_text(filepath)
    if content is None:
        st.caption(f"Not found: {filepath.as_posix()}")
        return
    st.download_button(
        label=label,
        data=content,
        file_name=filepath.name,
        mime=mime,
        use_container_width=True
    )

# ---------- Page config ----------
st.set_page_config(page_title="Snowflake Translator – Artifacts", layout="wide")
st.title("Snowflake Translator (from TSQL)")

# ---------- Snowflake blue theme (CSS only; logic unchanged) ----------
# Palette:
#   Primary (Snowflake-like): #29ABE2
#   Dark text:                #0B2A3B
#   Page bg (very light):     #F5FAFF
#   Panels bg:                #EAF5FF
#   Soft border:              #BFE6FA
st.markdown("""
<style>
:root {
  --sf-primary: #29ABE2;
  --sf-text: #0B2A3B;
  --sf-bg: #F5FAFF;
  --sf-panel: #EAF5FF;
  --sf-border: #BFE6FA;
}

/* App + text */
.stApp { background: var(--sf-bg); color: var(--sf-text); }
h1, h2, h3, h4, h5, h6 { color: var(--sf-text) !important; }

/* Sidebar */
section[data-testid="stSidebar"] > div {
  background: var(--sf-panel);
  border-right: 1px solid var(--sf-border);
}

/* Tabs accent */
.stTabs [data-baseweb="tab-list"] { border-bottom: 1px solid var(--sf-border) !important; }
.stTabs [role="tab"] { color: var(--sf-text) !important; }
.stTabs [aria-selected="true"] {
  border-bottom: 3px solid var(--sf-primary) !important;
}

/* Buttons (primary + default) */
.stButton > button, .stDownloadButton > button {
  background: var(--sf-primary) !important;
  color: white !important;
  border: 1px solid var(--sf-primary) !important;
  border-radius: 10px !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  filter: brightness(0.92);
  border-color: var(--sf-primary) !important;
}

/* File uploader + select widgets */
div[data-baseweb="select"] > div { border-color: var(--sf-border) !important; }
div[data-baseweb="select"] svg { color: var(--sf-primary) !important; }
.stSelectbox > div > div { border-color: var(--sf-border) !important; }

/* Metrics */
.css-1xarl3l, .stMetric {
  background: var(--sf-panel) !important;
  border: 1px solid var(--sf-border) !important;
  border-radius: 12px !important;
  padding: 10px !important;
}
.stMetric label, .stMetric span {
  color: var(--sf-text) !important;
}
            
/* Make metric number visible (Snowflake blue highlight) */
[data-testid="stMetricValue"], .stMetric [data-testid="stMetricValue"] {
  color: var(--sf-primary) !important;   /* bright Snowflake blue */
  font-weight: 700 !important;
}
       
/* DataFrame / table borders */
[data-testid="stTable"] table, .stDataFrame div[role="table"] {
  border: 1px solid var(--sf-border) !important;
  border-radius: 8px !important;
}

/* Code blocks */
code, pre {
  background: #E9F6FF !important;
  border: 1px solid var(--sf-border) !important;
  color: #06283D !important;
  border-radius: 8px !important;
}

/* Alerts (info/warning) */
[data-testid="stAlert"] {
  background: var(--sf-panel) !important;
  border: 1px solid var(--sf-border) !important;
}
</style>
""", unsafe_allow_html=True)

ensure_dirs()

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Controls")

    # Upload a .sql into scripts_input
    uploaded = st.file_uploader("Upload a .sql to scripts_input/", type=["sql"])
    if uploaded is not None:
        dest = INPUT_DIR / uploaded.name
        dest.write_bytes(uploaded.getbuffer())
        st.success(f"Uploaded to {dest.as_posix()}")

    # Orchestrator runner
    run_clicked = st.button("Run Orchestrator", type="primary", use_container_width=True)
    if run_clicked:
        try:
            with st.spinner("Running orchestrator..."):
                from orchestrator import process_all_inputs
                rep = process_all_inputs()
                st.session_state["_last_run"] = "ok"
                st.success(f"Done. Processed {rep.get('total_inputs')} file(s).")
        except Exception as e:
            st.session_state["_last_run"] = f"error: {e}"
            st.error(f"Orchestrator failed: {e}")
            st.exception(e)

    # Refresh button (recompute base list)
    if st.button("Refresh", use_container_width=True):
        st.experimental_rerun()

    st.divider()
    st.caption(f"ROOT: `{ROOT.as_posix()}`")
    st.caption(f"Outputs: `{OUTPUT.as_posix()}`")

# ---------- Discover bases ----------
bases = list_bases()
base = st.selectbox("Select input base", bases, index=0 if bases else None, placeholder="Choose an input…")

# ---------- Getting Started / Empty state ----------
if not bases:
    st.info(
        "No outputs found yet. Upload a `.sql` in the sidebar (it will be saved to "
        f"`{INPUT_DIR.as_posix()}`) and click **Run Orchestrator**.\n\n"
        "When outputs exist, tabs will appear here to browse final SQL and per-stage artifacts."
    )
    # Show existing files in scripts_input for convenience
    st.subheader("scripts_input/ (pending files)")
    pending = sorted(INPUT_DIR.glob("*.sql"))
    if pending:
        st.write(pd.DataFrame({"file": [p.name for p in pending], "path": [p.as_posix() for p in pending]}))
    else:
        st.caption("No .sql files in scripts_input/")
    st.stop()

# ---------- Manifest metrics (if present) ----------
manifest = read_json(MANIFESTS / f"{base}.json")
mcols = st.columns(4)
with mcols[0]:
    st.metric("Translate parts", manifest.get("translate_parts") if manifest else "—")
with mcols[1]:
    st.metric("Not translate", manifest.get("dont_translate_parts") if manifest else "—")
with mcols[2]:
    st.metric("OK parts", manifest.get("ok_parts") if manifest else "—")
with mcols[3]:
    st.metric("Fallback parts", manifest.get("fallback_parts") if manifest else "—")

st.caption(f"Base: **{base}**  •  Output root: `{OUTPUT.as_posix()}`")

# ---------- Tabs (visible once a base exists) ----------
tab_final, tab_doc, tab_notx, tab_parts, tab_stages, tab_diag = st.tabs(
    ["Final (SQL-only)", "Documented (Explain)", "Not Translated", "Parts & Index", "Stages Browser", "Diagnostics"]
)

# --- Final (SQL-only) ---
with tab_final:
    final_sql_path = FINAL_DIR / f"{base}_snowflake.sql"
    st.subheader("Clean deployable SQL")
    txt = read_text(final_sql_path)
    if txt is None:
        st.warning("Final SQL not found.")
    else:
        st.code(txt, language="sql")
        download_button("Download final SQL", final_sql_path, mime="text/sql")

# --- Documented (Explain) ---
with tab_doc:
    doc_path = FINAL_DIR / base / "explain_summary.sql"
    st.subheader("Documented version (summary, citations, TODOs)")
    txt = read_text(doc_path)
    if txt is None:
        st.info("No documented file found (this is optional).")
    else:
        st.code(txt, language="sql")
        download_button("Download documented SQL", doc_path, mime="text/sql")

# --- Not Translated ---
with tab_notx:
    notx_path = FINAL_DIR / base / "not_translated.sql"
    st.subheader("Skipped blocks (admin/metadata/unknown)")
    txt = read_text(notx_path)
    if txt is None:
        st.info("No not_translated file found.")
    else:
        st.code(txt, language="sql")
        download_button("Download not_translated.sql", notx_path, mime="text/sql")

# --- Parts & Index (from splitter) ---
with tab_parts:
    st.subheader("splitter/parts.json")
    parts_index = read_json(STAGES["splitter"] / base / "parts.json")
    if not parts_index:
        st.info("No parts.json found under splitter.")
    else:
        t_count = sum(1 for p in parts_index if p.get("category") == "translate")
        d_count = sum(1 for p in parts_index if p.get("category") != "translate")
        st.caption(f"Translate: **{t_count}**  •  Dont-translate: **{d_count}**")
        df = pd.DataFrame(parts_index)[
            ["idx", "category", "object_type", "reason", "name", "span_index"]
        ].sort_values("idx")
        st.dataframe(df, use_container_width=True, hide_index=True, height=350)

        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Translate parts (raw)**")
            tdir = STAGES["splitter"] / base / "translate"
            for p in sorted(tdir.glob("part_*.sql")):
                st.write(f"• {p.name}")
        with c2:
            st.markdown("**Dont-translate parts (raw)**")
            ddir = STAGES["splitter"] / base / "dont_translate"
            for p in sorted(ddir.glob("part_*.sql")):
                st.write(f"• {p.name}")

# --- Stages Browser ---
with tab_stages:
    st.subheader("Per-stage artifacts")
    stage_name = st.selectbox("Stage", list(STAGES.keys()), index=0)
    files = list_stage_files(STAGES[stage_name], base)
    if not files:
        st.info("No artifacts found for this stage.")
    else:
        left, right = st.columns([0.4, 0.6])
        with left:
            options = [f.relative_to(OUTPUT).as_posix() for f in files]
            chosen = st.selectbox("Files", options=options, index=0)
            chosen_path = OUTPUT / chosen
            download_button("Download selected", chosen_path)
        with right:
            if chosen_path.suffix.lower() == ".json":
                obj = read_json(chosen_path)
                st.json(obj if obj is not None else {})
            else:
                lang = "sql" if chosen_path.suffix.lower() == ".sql" else "text"
                st.code(read_text(chosen_path) or "", language=lang)

# --- Diagnostics ---
with tab_diag:
    st.subheader("Diagnostics")
    st.write({
        "ROOT": ROOT.as_posix(),
        "INPUT_DIR": INPUT_DIR.as_posix(),
        "FINAL_DIR": FINAL_DIR.as_posix(),
        "MANIFESTS": MANIFESTS.as_posix(),
        "Stages": {k: v.as_posix() for k, v in STAGES.items()},
        "Last run": st.session_state.get("_last_run", "—"),
    })
    # Show orchestrator/main log tail if present
    main_log = ROOT / "logs" / "main.log"
    if main_log.exists():
        st.caption(f"logs/main.log (last 2000 chars)")
        tail = read_text(main_log)
        st.code((tail[-2000:] if tail else ""), language="text")
    else:
        st.caption("No main.log yet.")
