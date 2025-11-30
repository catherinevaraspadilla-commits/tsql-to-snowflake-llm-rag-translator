# Chunk Generation (Phase 3)

This module performs Phase 3: chunk generation for a Markdown-based Snowflake corpus.
Its job is only to generate text chunks (JSONL) from Markdown files — no embeddings,
no retrieval, and no vector-store operations.

All behaviour strictly follows the local chunking_spec.json file in the corpus.

## 1. Overview

The script scans Markdown files under:

* {corpus}/commands
* {corpus}/datatypes
* {corpus}/scripting

Then it:

* Loads a user-defined chunking_spec.json
* Applies front-matter parsing (if present)
* Splits documents by heading structure (##, ###)
* Respects block-level structures (code blocks, tables)
* Chunks text using a token-approximation heuristic
* Writes output to:
    * {corpus}/chunks/<DocName>.jsonl
* Updates a chunk_manifest.json to avoid reprocessing unchanged files
* Writes detailed logs to a fixed log file

This phase is designed as a deterministic, minimal, function-based chunking engine.

## 2. Fixed Paths

The module uses two hardcoded paths:

```
CORPUS_DIR = C:\Users\CatherineVaras\Downloads\snowflake\corpus
LOG_FILE   = C:\Users\CatherineVaras\Downloads\snowflake\logs\chunk.log
```

The CLI entrypoint always uses CORPUS_DIR.

These should not be renamed unless the code is updated.

## 3. Main Entry Point

### build_chunks(corpus_dir, force=False) -> Dict

This is the public function that drives Phase 3.

Responsibilities

* Load chunking_spec.json
* Create or update the manifest
* Discover Markdown files
* Detect whether a file has changed (mtime + SHA-1 of body)
* Chunk the document into segments
* Write JSONL chunk files
* Update the manifest with:
    * mtime
    * SHA-1 hash of the body
    * total chunks written
* Produce summary metrics

Returned dictionary:

```
{
  "processed_files": <int>,
  "skipped_files": <int>,
  "total_chunks": <int>,
  "output_dir": "<corpus>/chunks"
}
```

## 4. Logging

Logging is configured once per session using _get_logger().

### File handler
* Path: LOG_FILE
* Level: DEBUG
* Format includes timestamps and levels
* Appends to file

### Console handler
* Level: INFO
* Shows minimal progress messages

## 5. Manifest Logic

Purpose

The manifest (chunk_manifest.json) prevents unnecessary recomputation.

A document is considered unchanged if:

* Its last modification time matches the manifest, and
* SHA-1 of its body (after removing front-matter) matches

Skipping saves time when re-running the pipeline.

## 6. Markdown Processing

### 6.1 Front-Matter

_parse_front_matter() looks for:

```
---
key: value
...
---
```

The function returns:

* front_matter_dict
* body_without_front_matter

If no front-matter exists, the entire text is treated as body.

### 6.2 Heading-Based Splitting

_split_by_headings() splits content using:

* ## (H2)
* ### (H3)

For each block, a heading_path string is generated:

* "H2"
* "H2 > H3"
* "" (no headings)

### 6.3 Code-Block / Table Handling

_respect_code_and_tables() is currently a no-op but preserves future extensibility.

The system avoids cutting inside fenced code or tables by relying on paragraph-aware chunking.

## 7. Chunking Algorithm

Chunking is handled by _chunk_text():

* Uses paragraphs (\n\n) as safe boundaries
* Token approximation: 1 token ≈ 4 characters
* Uses:
    * target_tokens from spec (default: 600)
    * overlap_tokens from spec (default: 80)

Internal slicing priority:

1. Double newline (\n\n)
2. Single newline (\n)
3. Period + space (. )

Each final piece is written to the JSONL file with fields:

```
{
  "chunk_id": "<sha1>",
  "doc_id": "<relative_path>",
  "page_title": "<front matter or filename>",
  "heading_path": "H2 > H3",
  "chunk_index": <int>,
  "text": "<chunk content>",
  "approx_tokens": <int>
}
```

chunk_id is SHA-1 of:

```
<relative_md_path>::<heading_path>::<chunk_index>
```

## 8. Output Format

For each Markdown document:

```
{corpus}/chunks/<DocName>.jsonl
```

Each line is a JSON record representing a chunk.

Example filename:

```
commands/CALL.md → chunks/CALL.jsonl
```

## 9. Directory Structure Required

```
corpus/
│
├── commands/
├── datatypes/
├── scripting/
│
├── chunking_spec.json
├── chunks/
│   ├── <DocName>.jsonl
│   └── chunk_manifest.json
└── ...
```

If topic folders are missing, they are silently skipped.

## 10. CLI Execution

You can run the script directly:

```
python chunk.py
```

This will:

* Use the fixed CORPUS_DIR
* Log start and end of the process
* Print a minimal summary:

```
[Phase 3] Chunks built. processed=X skipped=Y total_chunks=Z
```

## 11. Error Handling

The script logs all errors:

* File read errors
* Manifest load errors
* Spec load errors
* Unexpected exceptions (with traceback to log)

Top-level exceptions are re-raised after logging.

## 12. Key Internal Utilities

| Function | Purpose |
|---------|---------|
| _get_logger() | Configure and return the logger |
| _load_spec() | Load required chunking_spec.json |
| _load_manifest() | Load or initialize manifest JSON |
| _save_manifest() | Write manifest back to disk |
| _iter_markdown_docs() | Yield markdown files under topic folders |
| _is_unchanged() | Check manifest-based skip logic |
| _parse_front_matter() | Extract YAML-style front matter |
| _split_by_headings() | Create hierarchical blocks based on H2/H3 |
| _respect_code_and_tables() | Placeholder for preserving code blocks/tables |
| _chunk_text() | Token-aware paragraph chunking |
| _slice_with_overlap() | Slice long paragraphs with overlap |
| _extract_body() | Remove front-matter |
| _sha1() | SHA-1 wrapper used for IDs and manifest |

## 13. Summary

This script provides a deterministic, configurable, Phase-3 chunking engine for a Markdown corpus.

It emphasizes:

* Repeatability via manifest
* Configurability via chunking_spec.json
* Clean hierarchical chunking based on headings
* Safe paragraph-aware slicing
* Detailed logging
* Simple CLI usability

The output is ready for downstream embedding or indexing, but this script intentiona
