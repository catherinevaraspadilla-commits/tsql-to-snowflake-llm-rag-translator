---
topic: commands
page_title: SELECT
section_path: "SQL Command Reference > SELECT"
tags: [select, all, distinct, top, limit, replace, rename, exclude, ilike, projection, qualify]
url: TODO
version: "2025-10-22"
---

# SELECT

SELECT can be used as either a statement or as a clause within other statements:

- As a statement, the SELECT statement is the most commonly executed SQL statement; it queries the database and retrieves a set of rows.
- As a clause, SELECT defines the set of columns returned by a query.

See also: Query syntax

## Syntax — selecting all columns

    [ ... ]
    SELECT [ { ALL | DISTINCT } ]
           [ TOP <n> ]
           [{<object_name>|<alias>}.]*
           [ ILIKE '<pattern>' ]
           [ EXCLUDE
             {
               <col_name> | ( <col_name>, <col_name>, ... )
             }
           ]
           [ REPLACE
             {
               ( <expr> AS <col_name> [ , <expr> AS <col_name>, ... ] )
             }
           ]
           [ RENAME
             {
               <col_name> AS <col_alias>
               | ( <col_name> AS <col_alias>, <col_name> AS <col_alias>, ... )
             }
           ]

## Notes

- `ALL` (default) returns all qualifying rows; `DISTINCT` removes duplicates in the projection.
- `TOP <n>` appears in some dialects. In Snowflake, prefer `LIMIT <n>` at the end of the query (see LIMIT / FETCH).
- `[{<object_name>|<alias>}.]*` projects all columns from a table or alias.
- `ILIKE '<pattern>'` supports case-insensitive matching in certain projection patterns.
- `EXCLUDE` removes columns from `*`.
- `REPLACE` re-computes or re-aliases columns in the output.
- `RENAME` changes output column names without altering expressions.

## Translator guidance (LLM-facing)

- Replace `TOP <n>` with `LIMIT <n>` and position it after `ORDER BY` (if present).
- When the source filters on window functions in `WHERE`, rewrite using `QUALIFY` (see QUALIFY command).
- Preserve `EXCLUDE`, `REPLACE`, and `RENAME` semantics; avoid inventing columns. If uncertain about names or expressions, add a `-- TODO:` and keep a compiling projection.
