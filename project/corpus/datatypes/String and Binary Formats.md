```md
---
topic: datatypes
page_title: String and Binary Formats
section_path: "SQL Data Types > Binary"
tags: [binary, hex, to_binary, varchar, encoding, base16, hex-format, case-insensitive]
url: TODO
version: "2025-10-22"
---

# Overview of supported binary formats

Snowflake supports the **hexadecimal (“hex”) binary format** by default.

---

## Hex format (default)

The **hex** format represents binary data using base 16 notation.  
Each byte is represented by **two characters** — digits (`0–9`) and letters (`A–F`).

### Conversion behavior

| From | To | Notes |
|------|----|-------|
| Binary | String | Uses uppercase letters |
| String | Binary | Case-insensitive |

Hex is the **default binary format** used in Snowflake.

---

## Example — binary input and output

Binary data input/output can be misleading because “what you see isn’t necessarily what you get.”

```sql
CREATE OR REPLACE TABLE binary_table (v VARCHAR, b BINARY);

INSERT INTO binary_table (v, b)
  SELECT 'AB', TO_BINARY('AB');

SELECT v, b FROM binary_table;
```

---

## Hexadecimal (“HEX”) format example

To insert binary data encoded as hexadecimal characters:

```sql
CREATE OR REPLACE TABLE demo_binary_hex (b BINARY);
```

If you try to insert a non-hex string into a BINARY column using `TO_BINARY`, the conversion fails:

```sql
INSERT INTO demo_binary_hex (b)
  SELECT TO_BINARY('HELP', 'HEX');  -- ❌ Invalid hex string
```

---

## Translator guidance (LLM-facing)

- Map SQL Server’s `VARBINARY` to Snowflake `BINARY`.  
- When explicit encoding (e.g., `CONVERT(VARBINARY, 'ABC', 2)`) is used, replace with `TO_BINARY('<string>', 'HEX')`.  
- Preserve hex encoding in translations; add `-- TODO: verify hex format` if unclear.  
- Remember: `TO_BINARY()` defaults to HEX format unless specified otherwise.  
- Use `TO_VARCHAR(<binary>, 'HEX')` for output conversion when reversing binary-to-string.
```
