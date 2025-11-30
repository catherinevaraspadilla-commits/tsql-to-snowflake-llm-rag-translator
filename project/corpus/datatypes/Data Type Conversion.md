```md
---
topic: datatypes
page_title: Data Type Conversion
section_path: "SQL Data Types > Conversion"
tags: [cast, convert, coercion, implicit-cast, explicit-cast, to_date, to_double, to_number, type-conversion, cast-function, cast-operator]
url: TODO
version: "2025-10-22"
---

# Data type conversion

In Snowflake, many values can be converted between data types.  
For example, an `INTEGER` can be converted to a floating-point type.  
This process is called **casting** (or **type conversion**).

Snowflake supports both **explicit** and **implicit** casting behaviors.

## Explicit casting vs implicit casting

- **Explicit casting**: The user intentionally converts a value from one type to another.  
- **Implicit casting (coercion)**: Snowflake automatically converts a value to a compatible type when required.

## Explicit casting

You can explicitly cast values using:

1. The `CAST()` function  
   ```sql
   SELECT CAST('2022-04-01' AS DATE);
   ```

2. The cast operator `::`  
   ```sql
   SELECT '2022-04-01'::DATE;
   ```

3. A conversion function (e.g., `TO_DATE`, `TO_DOUBLE`, `TO_NUMBER`, etc.)  
   ```sql
   SELECT TO_DATE('2022-04-01');
   ```

All three forms above produce equivalent results.

## Implicit casting (coercion)

Snowflake performs implicit type conversion when a function or operator
requires a compatible type that differs from its argument.

For example, if a function expects a `FLOAT` but receives an `INTEGER`,
Snowflake automatically converts the integer to a float:

```sql
SELECT my_float_function(my_integer_column)
  FROM my_table;
```

This process—called **coercion**—allows expressions to work seamlessly
without explicit conversion when types are compatible.

## Translator guidance (LLM-facing)

- When the source query uses T-SQL `CONVERT()` or `CAST()`, map these to Snowflake’s `CAST()` or `::` operator.  
- Replace dialect-specific conversion functions (e.g., `TRY_CAST`, `PARSE`, `CONVERT(datetime, ...)`) with Snowflake equivalents like `TRY_CAST`, `TO_DATE`, or `TO_TIMESTAMP`.  
- Preserve explicit casts exactly; do **not** remove or infer implicit ones unless Snowflake’s documentation confirms automatic coercion.  
- When unsure about type compatibility, insert a `-- TODO: verify implicit coercion` note.
```
