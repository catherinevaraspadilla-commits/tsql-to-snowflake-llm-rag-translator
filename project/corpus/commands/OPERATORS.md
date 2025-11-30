---
topic: commands
page_title: Operators
section_path: "SQL Reference > Operators"
tags: [operators, arithmetic, comparison, logical, set, subquery, exists, in, any, all, union, intersect, minus, except, expansion, flow]
url: TODO
version: "2025-10-22"
---

# Query operators

Snowflake supports most of the standard operators defined in SQL:1999. These include arithmetic operators (such as `+` and `-`), set operators (such as `UNION`), subquery operators (such as `ANY`), and more.

## Categories and operators

### Arithmetic operators
- `+`, `-`, `*`, `/`, `%`

### Comparison operators
- `=`, `!=`, `<>`, `<`, `<=`, `>`, `>=`

### Expansion operators
- `**`

### Flow operators
- `->>`

### Logical operators
- `AND`, `NOT`, `OR`

### Set operators
- `INTERSECT`, `MINUS`, `EXCEPT`, `UNION`

### Subquery operators
- `[NOT] EXISTS`, `ANY` / `ALL`, `[NOT] IN`

## Notes

- `<>` and `!=` are both “not equal to”.
- Set operators combine result sets; matching column counts and compatible types are required.
- Subquery operators evaluate membership or comparisons against a subquery result.
- Use parentheses to control evaluation order when mixing logical operators.

## Translator guidance (LLM-facing)

- Preserve operator semantics; do not replace set operators unless the target dialect demands a specific keyword.  
- For membership tests, prefer `IN (...)`/`NOT IN (...)` or `EXISTS`/`NOT EXISTS` as in the source; avoid inventing scalar rewrites.  
- When translating comparisons against subqueries, map `= ANY(...)` to “IN” and `= ALL(...)` to “equals every” patterns only when logically equivalent and unambiguous; otherwise retain `ANY`/`ALL`.
