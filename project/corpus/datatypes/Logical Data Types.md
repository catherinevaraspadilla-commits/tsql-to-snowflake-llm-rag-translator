```md
---
topic: datatypes
page_title: Logical Data Types
section_path: "SQL Data Types > Logical"
tags: [boolean, logic, true, false, null, ternary, predicates, where, expressions]
url: TODO
version: "2025-10-22"
---

# Logical data types

This topic describes the logical data types supported in Snowflake.

## Data types

Snowflake supports a single logical data type: **BOOLEAN**.

### BOOLEAN

`BOOLEAN` can have `TRUE` or `FALSE` values.  
It can also have an `UNKNOWN` value, represented by `NULL`.

BOOLEAN values can be used in both **expressions** (e.g., SELECT lists) and **predicates** (e.g., WHERE clauses).  
The BOOLEAN type enables **ternary logic** in Snowflake.

### Examples

Create a table and insert values:

```sql
CREATE OR REPLACE TABLE test_boolean(
  b BOOLEAN,
  n NUMBER,
  s STRING);

INSERT INTO test_boolean VALUES
  (true, 1, 'yes'),
  (false, 0, 'no'),
  (NULL, NULL, NULL);
```

Query using BOOLEAN expressions:

```sql
SELECT b, n, s
  FROM test_boolean
  WHERE b IS NOT NULL;
```

### Translator guidance (LLM-facing)

- Map T-SQL `BIT` values to Snowflake `BOOLEAN`.  
- When encountering numeric booleans (`0`/`1`) in conditions, replace with `FALSE`/`TRUE` respectively.  
- For unknown or nullable logic, retain `NULL` (don’t assume default to FALSE).  
- Always ensure BOOLEAN comparisons are explicit in translated Snowflake code (e.g., `WHERE flag = TRUE` or `IS NULL`).
```
