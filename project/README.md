# 🖥️ Streamlit UI Overview

# To run the front-end
pip install streamlit 
pip install pandas
streamlit run app.py

The `app.py` provides a **visual frontend** for the Snowflake Translator pipeline.  
It’s divided into three main zones:

---

## 🧭 Sidebar (Control Panel)

This is the main control area where you interact with the pipeline.

| **Feature** | **Description** |
|--------------|-----------------|
| **Upload SQL** | Upload `.sql` files — they’re automatically saved into `scripts_input/` for processing. |
| **Run Orchestrator** | Calls `process_all_inputs()` from `orchestrator.py`, triggering the full end-to-end translation pipeline. |
| **Refresh Button** | Refreshes the UI (reloads `output/` and `manifests/` folders). Useful after new runs. |
| **ROOT / OUTPUT Paths** | Displays fixed folder paths used by all modules for transparency. |

💡 *If there are no outputs yet, the sidebar remains active and the main area shows a “Getting Started” info message (no more blank screen).*

---

## 🧱 Main Tabs (Results Viewer)

Once the orchestrator runs and produces outputs, the main area displays the following tabs:

| **Tab** | **Purpose** |
|----------|--------------|
| 🧩 **Final (SQL-only)** | Displays the clean, deployable Snowflake SQL file — only translated code, minimal comments.<br>**File:** `output/final/<base>_snowflake.sql` |
| 📘 **Documented (Explain)** | Displays the annotated version with citations, TODOs, and fix summaries.<br>**File:** `output/final/<base>/explain_summary.sql` |
| 🚫 **Not Translated** | Shows skipped blocks (`EXEC`, `USE`, `SET`, comments, etc.).<br>**File:** `output/final/<base>/not_translated.sql` |
| 📂 **Parts & Index** | Lists how the original T-SQL file was split using `output/splitter/<base>/parts.json`.<br>Shows:<br>• category (translate / don’t translate)<br>• object_type (view / procedure)<br>• reason<br>• name<br>Also lists the raw pieces in `translate/` and `dont_translate/`. |
| ⚙️ **Stages Browser** | Lets you explore intermediate results for each stage (`detector`, `retrieve`, `validator`, etc.). You can select a stage → choose a file → view or download its content. |
| 🧾 **Diagnostics** | Displays system paths, last orchestrator run status, and the tail of `logs/main.log` for debugging. |

---

## ⚙️ Pipeline Stages (Backend Process Flow)

When you click **Run Orchestrator**, the backend executes the following sequence:

### 1️⃣ Splitter
**Input:** `scripts_input/<file>.sql`  
**Output:** `output/splitter/<base>/`  
- `parts.json` → metadata per part (index, type, reason)  
- `translate/` → pieces to be processed  
- `dont_translate/` → pieces to be preserved as-is  

**Purpose:** separates `CREATE VIEW` / `CREATE PROCEDURE` from metadata or admin commands.

---

### 2️⃣ Detector
**Input:** each “translate” block  
**Output:** `output/detector/<base>/part_####.json`  

Extracts object name (`vw_*` or `usp_*`), confirms type, and flags patterns (e.g., `TOP`, `TRY/CATCH`, etc.).

---

### 3️⃣ Retriever (RAG)
**Input:** text of that SQL object  
**Output:** `output/retrieve/<base>/part_####.json`  

Uses embeddings from `embed.py` to find relevant Snowflake documentation chunks (from your corpus).  
Returns top chunks + citations.

---

### 4️⃣ Translator – Pass 1
**Input:** SQL + retrieved docs  
**Output:**  
- `output/translator_pass1/<base>/part_####.sql`  
- `output/translator_pass1/<base>/part_####_meta.json`  

Generates a **draft Snowflake SQL translation** using the LLM (e.g., Azure Chat model).

---

### 5️⃣ Validator
**Input:** draft SQL  
**Output:** `output/validator/<base>/part_####.json`  

Adds deterministic signals (e.g., warnings like “`TOP → LIMIT`”, “missing `RETURNS`”) for the next phase.

---

### 6️⃣ Translator – Pass 2
**Input:** draft SQL + validation signals  
**Output:**  
- `output/translator_pass2/<base>/part_####.sql` → clean final code  
- `output/translator_pass2/<base>/part_####_doc.sql` → annotated version  

Repairs deterministic issues, applies normalization, and finalizes fixes.

---

### 7️⃣ Assembly
Collects and consolidates outputs into final deliverables:

| **Type** | **File** |
|-----------|-----------|
| Clean SQL | `output/final/<base>_snowflake.sql` |
| Annotated SQL | `output/final/<base>/explain_summary.sql` |
| Skipped Blocks | `output/final/<base>/not_translated.sql` |
| Summary Manifest | `output/manifests/<base>.json` |

---

**✅ Summary:**  
This Streamlit frontend provides a **complete visualization layer** for the Snowflake translator pipeline — from uploading `.sql` inputs to exploring intermediate results and final translations, all styled in Snowflake blue.

## 📂 Project Directory Structure

All modules, outputs, and configuration files are organized under:

C:\Users\CatherineVaras\Downloads\snowflake\
│
├─ scripts_input\
│    └─ <base>.sql
│
├─ corpus\
│    ├─ commands\  datatypes\  scripting\     (Markdown sources)
│    ├─ chunks\                        (Phase-3 output)
│    │    └─ <DocName>.jsonl
│    └─ .rag\                          (Phase-3 manifest)
│         └─ chunk_manifest.json
│
├─ output\
│    ├─ splitter\<base>\
│    │    ├─ parts.json
│    │    ├─ preamble.sql                 (optional)
│    │    ├─ translate\part_0001.sql ...
│    │    └─ dont_translate\part_0002.sql ...
│    │
│    ├─ detector\<base>\part_0001.json ...
│    ├─ retrieve\<base>\part_0001.json ...
│    ├─ translator_pass1\<base>\
│    │    ├─ part_0001.sql                (draft)
│    │    └─ part_0001_meta.json
│    ├─ validator\<base>\part_0001.json
│    ├─ translator_pass2\<base>\
│    │    ├─ part_0001.sql                (clean)
│    │    ├─ part_0001_doc.sql            (documented)
│    │    └─ part_0001_meta.json
│    │
│    ├─ final\
│    │    ├─ <base>_snowflake.sql         (clean-only final, concatenated)
│    │    └─ <base>\
│    │         ├─ explain_summary.sql     (documented final)
│    │         └─ not_translated.sql      (all skipped blocks)
│    │
│    └─ manifests\<base>.json             (run report)
│
├─ logs\
│    ├─ main.log
│    ├─ chunk.log
│    └─ embed.log
│
├─ settings.json
│
├─ chunk.py
├─ embed.py
├─ detector.py
├─ validator.py
├─ translator.py
├─ orchestrator.py
└─ app.py

# 🧩 Snowflake Translator Pipeline

## Module Overview

| Module | Description |
|---------|-------------|
| **chunk.py** | Phase 3 – Chunk generator (inputs: Markdown corpus; outputs: JSONL chunks). |
| **embed.py** | Phase 4 – Embeddings + retrieval (reads chunks, writes vectors, serves retrieve). |
| **detector.py** | Confirms object type + name + fast hints. |
| **validator.py** | Deterministic inter-pass signals from SQL (no LLM). |
| **translator.py** | Pass-1 draft + Pass-2 repair/normalize + summary header. |
| **main.py** | Orchestrator that wires modules in sequence for each SQL object. |

All modules are **function-based** (no classes), independently runnable from the terminal, and importable by `main.py`.  
Each module auto-creates its own log file under:

    C:\Users\CatherineVaras\Downloads\snowflake\logs\

---

### 🧭 Folder Summary

| **Folder / File** | **Purpose** |
|--------------------|-------------|
| `scripts_input/` | Where you drop original `.sql` inputs to be translated. |
| `corpus/` | Reference documentation for retrieval (Markdown corpus + embedding outputs). |
| `output/` | Contains all intermediate and final translation artifacts for each run. |
| `output/splitter/` | Holds per-file parts: `translate/` vs `dont_translate/` + `parts.json`. |
| `output/detector/` | JSON metadata identifying object types and names (VIEW/PROC). |
| `output/retrieve/` | RAG-retrieved documentation chunks relevant to each SQL part. |
| `output/translator_pass1/` | Draft LLM translations and metadata. |
| `output/validator/` | Deterministic validation signals for fixes. |
| `output/translator_pass2/` | Final cleaned and documented SQL parts. |
| `output/final/` | Consolidated final outputs (clean `.sql`, documented `.sql`, skipped blocks). |
| `output/manifests/` | JSON summary of each run (counts, errors, etc.). |
| `logs/` | Contains logs from each processing module (main, chunk, embed). |
| `settings.json` | Global configuration (API keys, model, corpus paths). |
| `chunk.py` – `translator.py` | Independent pipeline modules for chunking, embedding, translation, etc. |
| `orchestrator.py` | Orchestrates the full multi-stage translation pipeline. |
| `app.py` | Streamlit frontend to upload `.sql`, run orchestrator, and visualize results. |

---

## ⚙️ Settings

**File:**

    C:\Users\CatherineVaras\Downloads\snowflake\settings.json

**Required keys:**
    
    {
      "api_key": "YOUR_AZURE_OPENAI_KEY",
      "azure_endpoint": "https://your-resource.openai.azure.com/",
      "embedding_deployment": "text-embedding-3-small",
      "chat_deployment": "gpt-4o-mini"
    }

**Used by:**
- `embed.py` → `api_key`, `azure_endpoint`, `embedding_deployment`
- `translator.py` → `api_key`, `azure_endpoint`, `chat_deployment`

---

## 🧾 Data Contracts (Shared Types)

### Part (from `split_into_objects` in `main.py`)
    
    {
      "span_index": 0,
      "text": "CREATE VIEW ...",
      "object_type": "view|procedure|unknown",
      "name": "dbo.v",
      "preamble": false
    }

### Retrieved (from `embed.retrieve`)
    
    {
      "chunks": [
        {
          "doc_id": "commands/SELECT.md",
          "page_title": "SELECT",
          "heading_path": "LIMIT",
          "chunk_id": "...",
          "score": 0.83,
          "cosine": 0.87,
          "keyword_overlap": 0.72,
          "citation": "SELECT > LIMIT"
        }
      ],
      "retrieval_weak": false,
      "stats": {"candidates": 90, "after_dedupe": 8, "threshold": 0.25}
    }

### Signals (from `validator.make_signals`)
    
    {
      "object_type": "view",
      "errors": [],
      "warnings": [{"code": "TOP_IN_VIEW", "msg": "Use LIMIT instead of TOP"}],
      "suggestions": [{"code": "MOVE_TO_QUALIFY", "msg": "Window filter in WHERE"}]
    }

### Translator Results

**Pass 1**
    
    {
      "draft_sql": "...",
      "citations": ["SELECT > LIMIT"],
      "todos": [],
      "notes": ["conservative", "phase4-pass1"],
      "retrieval_weak": false
    }

**Pass 2**
    
    {
      "final_sql": "...",
      "applied_fixes": ["TOP→LIMIT"],
      "remaining_todos": []
    }

---

## 🧱 chunk.py — Chunk Generation

**Purpose:** Build paragraph-aware JSONL chunks from curated Markdown docs.

**Function:**
    
    build_chunks(corpus_dir: str|Path, force: bool=False) -> dict

- Scans `corpus/{commands,datatypes,scripting}/**/*.md`
- Splits by `##/###`, paragraph-aware (~600 tokens + 80 overlap)
- Writes to `corpus/chunks/*.jsonl`

**Output:** summary dict with counts, output dir.  
**Manifest:** `corpus/chunks/chunk_manifest.json` stores `mtime`, `sha1_of_body`, `total_chunks`.

**Artifacts**

    C:\Users\CatherineVaras\Downloads\snowflake\corpus\chunks\*.jsonl
    C:\Users\CatherineVaras\Downloads\snowflake\corpus\chunks\chunk_manifest.json
    C:\Users\CatherineVaras\Downloads\snowflake\logs\chunk.log

**CLI**

    python C:\Users\CatherineVaras\Downloads\snowflake\src\chunk.py
    # prints: [Phase 3] Chunks built. processed=N skipped=M total_chunks=K

---

## 🧮 embed.py — Embeddings & Retrieval

**Purpose:** Build embeddings from chunks (incremental) and retrieve relevant documentation sections.

**Functions:**
    
    build_embeddings(force: bool=False, batch_size: int=64) -> dict
    retrieve(query: str, object_type: str|None=None, k_per_folder: int=6, hard_cap: int=8) -> dict

**Artifacts**

    C:\Users\CatherineVaras\Downloads\snowflake\corpus\embed\
      embeds.jsonl
      meta.jsonl
      embeds_manifest.json
    C:\Users\CatherineVaras\Downloads\snowflake\logs\embed.log

**CLI**

    python C:\Users\CatherineVaras\Downloads\snowflake\src\embed.py build
    python C:\Users\CatherineVaras\Downloads\snowflake\src\embed.py retrieve "Replace TOP with LIMIT and GETDATE in a view" view

---

## 🔍 detector.py — Object Detector

**Purpose:** Confirm object type and extract name; emit quick hints.

**Function:**
    
    detect_object(sql: str) -> dict

**Example Output**
    
    {
      "object_type": "view|procedure|null",
      "name": "schema.obj|name|null",
      "hints": {
        "has_top": true,
        "has_begin": false,
        "has_dollar_quotes": false,
        "has_proc_tokens_in_view": false,
        "has_getdate": true,
        "has_over_clause": true,
        "has_qualify": false
      }
    }

**Log:**

    C:\Users\CatherineVaras\Downloads\snowflake\logs\detector.log

**CLI**

    python C:\Users\CatherineVaras\Downloads\snowflake\src\detector.py --text "CREATE VIEW dbo.v AS SELECT TOP 10 * FROM t;"

---

## ✅ validator.py — Inter-Pass Signals (Deterministic)

**Purpose:** Produce non-LLM checks for Pass-2 guidance.

**Function:**
    
    make_signals(sql: str, object_type: str|None) -> dict

**View signals:**  
`TOP_IN_VIEW`, `PROC_TOKENS_IN_VIEW`, `MOVE_TO_QUALIFY`, `TS_CAST_AMBIGUOUS`  

**Procedure signals:**  
`MISSING_RETURNS`, `MISSING_DOLLARS`, `LANGUAGE_MISMATCH`, `UNSCOPED_CONTROL`

**Log:**

    C:\Users\CatherineVaras\Downloads\snowflake\logs\validator.log

**CLI**

    python C:\Users\CatherineVaras\Downloads\snowflake\src\validator.py --text "CREATE VIEW dbo.v AS SELECT TOP 10 * FROM t;" view

---

## 🧠 translator.py — Two-Pass Translation

**Purpose:** Generate a Snowflake SQL draft (Pass-1) then repair/normalize (Pass-2) using validator signals and retrieved context.

**Functions**
    
    pass1_translate(input_sql, retrieved, object_type, model=None) -> dict
    pass2_repair(draft_sql, retrieved, signals, object_type, model=None) -> dict
    prepend_summary(final_sql, citations, todos, applied_fixes) -> str

**Log:**

    C:\Users\CatherineVaras\Downloads\snowflake\logs\translator.log
