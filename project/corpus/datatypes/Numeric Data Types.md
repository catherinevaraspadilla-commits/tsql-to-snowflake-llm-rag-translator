```md
---
topic: datatypes
page_title: Numeric Data Types
section_path: "SQL Data Types > Numeric"
tags: [number, decimal, numeric, int, integer, bigint, float, double, real, precision, scale, nan, inf, rounding, fixed-point, floating-point]
url: TODO
version: "2025-10-22"
---

# Numeric data types

This topic describes the numeric data types supported in Snowflake, along with the formats for numeric constants and literals.

---

## Data types for fixed-point numbers

Snowflake supports the following fixed-point numeric types:

### NUMBER

`NUMBER` stores up to **38 digits** of precision, with optional **precision** and **scale** parameters:

- **Precision** — total number of digits allowed.  
- **Scale** — number of digits to the right of the decimal point.

### DECIMAL, DEC, NUMERIC

Synonyms for `NUMBER`.

### INT, INTEGER, BIGINT, SMALLINT, TINYINT, BYTEINT

Synonyms for `NUMBER`, but **without precision and scale specification**.  
All integer data types default to `NUMBER(38, 0)`.

Range:  
`-99999999999999999999999999999999999999` to  
`+99999999999999999999999999999999999999`

These names exist for compatibility and to suggest expected ranges when porting schemas from other systems.

### Example — fixed-point data types in a table

```sql
CREATE OR REPLACE TABLE test_fixed(
  num0 NUMBER,
  num10 NUMBER(10,1),
  dec20 DECIMAL(20,2),
  numeric30 NUMERIC(30,3),
  int1 INT,
  int2 INTEGER);

DESC TABLE test_fixed;
```

---

## Data types for floating-point numbers

Snowflake supports the following floating-point types:

### FLOAT, FLOAT4, FLOAT8

All are treated as **64-bit double-precision** IEEE 754 floating-point numbers.

#### Precision
Approx. **15 digits** of precision.

Range:
- Integers: `-9007199254740991` to `+9007199254740991`
- Floating-point values: `~10^-308` to `~10^+308`
- Extended range (less precise): `~10^-324` to `~10^-308`

For higher precision, use the fixed-point `NUMBER` type.

---

### Special FLOAT values

Snowflake supports the following special values:

- `'NaN'` — Not a number  
- `'inf'` — Infinity  
- `'-inf'` — Negative infinity  

These must be enclosed in single quotes and are case-insensitive.

#### Comparison semantics vs IEEE 754

| Condition | Snowflake | IEEE 754 | Comment |
|------------|------------|----------|----------|
| `'NaN' = 'NaN'` | TRUE | FALSE | Snowflake treats all NaNs as equal. |
| `'NaN' > X` (any FLOAT except NaN) | TRUE | FALSE | `'NaN'` is greater than any other FLOAT, including infinity. |

---

### Rounding errors

Floating-point operations can introduce rounding errors in the least significant digits.

**Key points:**
- Errors can vary between query executions.  
- Larger when operands differ in precision or scale.  
- Can accumulate during aggregations (`SUM`, `AVG`, etc.).  
- Casting to `NUMBER` before aggregating may reduce errors.  
- Affects both SQL and procedural code (e.g., JavaScript, Python UDFs).

**Recommendation:**  
Use approximate equality comparisons instead of strict equality for FLOATs.

---

### DOUBLE, DOUBLE PRECISION, REAL

Synonyms for `FLOAT`.

---

### Example — floating-point data types in a table

```sql
CREATE OR REPLACE TABLE test_float(
  double1 DOUBLE,
  float1 FLOAT,
  dp1 DOUBLE PRECISION,
  real1 REAL);

DESC TABLE test_float;
```

---

## Translator guidance (LLM-facing)

- Map SQL Server types:
  - `DECIMAL(p, s)` → `NUMBER(p, s)`
  - `MONEY` / `SMALLMONEY` → `NUMBER(19,4)`
  - `FLOAT(n)` / `REAL` → `FLOAT`
- Preserve precision and scale when possible; default to `NUMBER(38, 0)` for generic integers.  
- Replace dialect-specific types (`NUMERIC`, `DECIMAL`, etc.) with `NUMBER` while maintaining semantics.  
- Handle `NaN` and infinity explicitly when present; include `-- TODO: check FLOAT special values` if uncertain.  
- For calculations involving FLOATs, prefer Snowflake fixed-point for reproducibility.
```
