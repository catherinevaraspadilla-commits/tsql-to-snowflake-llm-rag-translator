---
topic: commands
page_title: ORDER BY
section_path: "SQL Command Reference > ORDER BY"
tags: [order-by, sort, asc, desc, nulls-first, nulls-last, all, position, column-alias, select-order]
url: TODO
version: "2025-10-22"
---

# ORDER BY

Specifies the ordering of the rows in the result set of a SELECT query.

## Syntax

### Sorting by specific columns

    SELECT ...
      FROM ...
      ORDER BY orderItem [ , orderItem , ... ]
      [ ... ]

Where:

    orderItem ::= { <column_alias> | <position> | <expr> } [ { ASC | DESC } ] [ NULLS { FIRST | LAST } ]

### Sorting by all columns

    SELECT ...
      FROM ...
      ORDER BY ALL [ { ASC | DESC } ] [ NULLS { FIRST | LAST } ]
      [ ... ]

## Parameters

column_alias — Column alias appearing in the query block’s SELECT list.  
position — Position of an expression in the SELECT list (1-based).  
expr — Any valid expression using tables or aliases in the current scope.  
ASC | DESC — Specifies ascending or descending order. Default is ASC.  
NULLS { FIRST | LAST } — Controls placement of NULLs relative to non-NULL values.  
Default depends on the sort order (ASC or DESC).  
ALL — Sorts by all columns in the SELECT list in the same order as they appear.

Example:

    SELECT col_1, col_2, col_3
      FROM my_table
      ORDER BY ALL;

The result is sorted first by col_1, then col_2, then col_3.

## Usage notes

- ORDER BY is evaluated **after** the SELECT list has been computed.  
- You can sort by column aliases defined in the SELECT projection.  
- Sorting by position (e.g., ORDER BY 1) is supported but less readable—use aliases when possible.  
- NULL placement defaults depend on direction:
  - ASC → NULLS LAST by default
  - DESC → NULLS FIRST by default
- ORDER BY ALL cannot be used if a SELECT column uses an aggregate function.

## Translator guidance (LLM-facing)

- Preserve explicit ORDER BY order and NULLs placement; do not omit ASC/DESC if meaning could change.
- If T-SQL uses “TOP n ORDER BY”, rewrite as “ORDER BY ... LIMIT n”.
- Ensure ORDER BY appears **after** QUALIFY when both clauses exist in the Snowflake translation.
