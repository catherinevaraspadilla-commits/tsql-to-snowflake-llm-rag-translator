```md
---
topic: datatypes
page_title: Semi-Structured Data Types
section_path: "SQL Data Types > Semi-Structured"
tags: [variant, object, array, semi-structured, json, parse_json, object_construct, array_construct, key-value, flexible-schema]
url: TODO
version: "2025-10-22"
---

# Semi-structured data types

Snowflake provides three **semi-structured data types** that can store flexible, hierarchical data structures similar to JSON:

- `VARIANT`
- `OBJECT`
- `ARRAY`

These types can contain nested values, including one another.

---

## VARIANT

A `VARIANT` value can store data of **any type**, including other semi-structured types (`OBJECT`, `ARRAY`).

### Characteristics

- Maximum size: up to **128 MB** of uncompressed data (practically smaller due to overhead).  
- The actual limit depends on the structure and content of the object being stored.  
- Values are stored in a compressed binary format optimized for query performance.

### Example — inserting VARIANT data

To insert JSON-formatted data into a `VARIANT` column:

```sql
CREATE OR REPLACE TABLE variant_insert (v VARIANT);

INSERT INTO variant_insert (v)
  SELECT PARSE_JSON('{"key3": "value3", "key4": "value4"}');

SELECT * FROM variant_insert;
```

---

## OBJECT

An `OBJECT` is analogous to a JSON **object** — a collection of key-value pairs.  
In other languages, this corresponds to a “dictionary”, “hash”, or “map”.

### Characteristics

- Each **key** is a `VARCHAR`.  
- Each **value** is a `VARIANT`.  
- Different values can hold different underlying data types (heterogeneous typing).

Example — constructing an OBJECT:

```sql
SELECT OBJECT_CONSTRUCT(
  'name', 'Jones'::VARIANT,
  'age',  42::VARIANT
);
```

This creates an OBJECT:
```json
{"name": "Jones", "age": 42}
```

---

## ARRAY

An `ARRAY` represents an ordered collection of values, similar to arrays in other languages.

### Characteristics

- Each element in an array is a `VARIANT` value.
- Values can be of **different underlying data types**.
- You can explicitly cast values to `VARIANT` or rely on **implicit casting** in constructors.

Example — constructing an ARRAY:

```sql
SELECT ARRAY_CONSTRUCT('apple', 10, TRUE, NULL);
```

Result:
```json
["apple", 10, true, null]
```

Because all elements are `VARIANT`s, the array can hold mixed types.

---

## Translator guidance (LLM-facing)

- Map SQL Server JSON functions to Snowflake equivalents:
  - `OPENJSON` → `LATERAL FLATTEN(input => <variant>)`
  - `JSON_VALUE` → `<variant>:key`
  - `JSON_QUERY` → `TO_VARIANT(<expr>)`
- Preserve all nested data structures.  
- When creating tables, define `VARIANT` columns for JSON or XML data.  
- When unsure whether a source structure maps to OBJECT or ARRAY, insert a `-- TODO: confirm structure` note.  
- Prefer `PARSE_JSON()` or `OBJECT_CONSTRUCT()` / `ARRAY_CONSTRUCT()` to build structured values explicitly.
```
