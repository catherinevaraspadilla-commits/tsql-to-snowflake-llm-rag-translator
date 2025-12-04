# tsql-to-snowflake-llm-rag-translator
AI-powered engine that transforms legacy T-SQL into modern Snowflake SQL using Retrieval-Augmented Generation (RAG), Large Language Models (LLM reasoning), and deterministic validators for safe, reliable migration.

# T-SQL to Snowflake LLM + RAG Translator

This project demonstrates my ability to design and implement AI-driven, production-oriented solutions that combine LLM reasoning, a custom RAG pipeline, SQL transformation, and deterministic validation. It reflects the technical range I can bring to Data, AI, and Software Engineering teams.

## What this project shows about my skills

- LLM Engineering: two-stage generation (draft + repair), grounded inference, controlled use of the model.
- Custom RAG Design: a retrieval layer from scratch (corpus design, chunking, embeddings, search, and citation wiring).
- Data Engineering: SQL parsing, dialect migration, schema alignment, legacy-to-cloud modernization patterns.
- Software Engineering: modular architecture, validation layers, clean separation of concerns.
- Cloud & AI Tooling: Azure OpenAI, embeddings, retrieval pipelines, scalable execution patterns.
- Problem-Solving: turning ambiguous legacy SQL into reliable, testable, cloud-compatible output.

## How the system works

1. Retrieval layer (RAG)  
   - Indexes a Snowflake reference corpus (documentation, patterns, compatibility rules).  
   - Uses embeddings + similarity search to fetch only the most relevant guidance for each query.  

2. Language Large Models  
   - Uses the LLM with retrieved context to generate an initial Snowflake SQL draft.  
   - Applies deterministic fixes, validates syntax, and only calls the LLM again when validator signals require it.

This design keeps output grounded, consistent, and migration-ready.

## Example

**Input (T-SQL)**  
```sql
SELECT TOP 10 * FROM Sales WITH (NOLOCK)
```

**Output (Snowflake)**  
```sql
SELECT * FROM Sales LIMIT 10;
```

## Why this matters

The architecture follows the same principles used in real-world AI systems:
a custom RAG layer to ground the model, deterministic validators to protect correctness, and clear separation between AI and rule-based logic.

## Tech Stack

Python • Azure OpenAI • Custom RAG pipeline (corpus + chunking + embeddings + retrieval) • SQL Normalization • Validation Pipelines

## My role

I designed and implemented the end-to-end system: the RAG pipeline from scratch, LLM prompts, retrieval logic, deterministic validators, and the two-stage translation mechanism.
