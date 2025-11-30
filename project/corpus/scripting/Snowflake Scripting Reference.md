```md
---
topic: scripting
page_title: Snowflake Scripting Reference
section_path: "Snowflake Scripting > Reference"
tags: ["declare", "if", "case", "for", "while", "repeat", "loop", "break", "continue", "let", "open", "fetch", "close", "await", "cancel", "raise", "return", "exception", "cursor", "snowflake-scripting", "control-flow"]
url: TODO
version: "2025-10-22"
---

# Snowflake Scripting Reference

Snowflake Scripting extends SQL with procedural logic — including **variables, loops, branching, exception handling**, and more.

Below is an overview of core scripting constructs.

---

## Variable declaration

```sql
DECLARE <variable_name> <data_type> [ DEFAULT <expression> ];
```

---

## Block structure

```sql
BEGIN
    -- statements and control flow
END;
```

---

## Branching

```sql
IF <condition> THEN
    <statement>;
[ ELSEIF <condition> THEN
    <statement>; ]
[ ELSE
    <statement>; ]
END IF;

CASE
    WHEN <condition> THEN <statement>;
    ...
END CASE;
```

---

## Looping constructs

### FOR loop (cursor-based)

```sql
FOR <row_variable> IN <cursor_name> DO
    <statement>;
    [ <statement>; ... ]
END FOR [ <label> ];
```

### FOR loop (counter-based)

```sql
FOR <counter_variable> IN [ REVERSE ] <start> TO <end> { DO | LOOP }
    <statement>;
    [ <statement>; ... ]
END { FOR | LOOP } [ <label> ];
```

> A FOR loop repeats a sequence of steps either:
> - A specified number of times (counter-based), or  
> - Once per row in a cursor (cursor-based).

---

### WHILE loop

```sql
WHILE ( <condition> ) { DO | LOOP }
    <statement>;
    [ <statement>; ... ]
END { WHILE | LOOP } [ <label> ];
```

- Repeats **while** the condition evaluates to `TRUE`.
- A `statement` may be:
  - A SQL command (including `CALL`)
  - A control-flow statement (`IF`, `CASE`, `FOR`, etc.)
  - A nested block
- If the condition is `NULL`, it’s treated as `FALSE`.

> Valid only inside a Snowflake Scripting block.

---

### REPEAT loop

```sql
REPEAT
    <statement>;
    [ <statement>; ... ]
UNTIL ( <condition> )
END REPEAT [ <label> ];
```

- Executes **at least once**, checking the condition at the end.  
- Parentheses around the condition are **required**.
- If the condition never becomes `TRUE` and no `BREAK` occurs, the loop runs indefinitely.

---

### LOOP (infinite)

```sql
LOOP
    <statement>;
    [ <statement>; ... ]
END LOOP [ <label> ];
```

- Loops indefinitely until a `BREAK` or `RETURN` occurs.
- Typically combined with `IF` or `CASE` to control exit conditions.

---

### Loop termination

```sql
BREAK;     -- exit current loop
CONTINUE;  -- skip to next iteration
```

---

## Variable assignment

```sql
LET <variable_name> = <expression>;
```

---

## Cursor management

```sql
OPEN <cursor_name>;
FETCH <cursor_name> INTO <variable>;
CLOSE <cursor_name>;
```

---

## Asynchronous child jobs

```sql
AWAIT <child_job_name>;
CANCEL <child_job_name>;
```

---

## No-operation statement

```sql
NULL;
```
> Typically used inside a branch or exception block as a placeholder.

---

## Raising exceptions

```sql
RAISE;                 -- re-throws current exception
RAISE <exception_name> [ USING MESSAGE = '<text>' ];
```

---

## Returning values

```sql
RETURN <expression>;
```

---

## Exception handling

```sql
EXCEPTION
    WHEN <exception_type> THEN
        <statement>;
END;
```

---

## Translator guidance (LLM-facing)

- Map procedural SQL code blocks (e.g., T-SQL or PL/SQL) to Snowflake Scripting equivalents:
  - `BEGIN ... END` blocks → same syntax.
  - `WHILE`, `FOR`, `IF`, `CASE` → direct analogs.
  - `EXIT`, `CONTINUE` → map to `BREAK`, `CONTINUE`.
- Always enclose control structures inside a `BEGIN ... END;` block.
- Parentheses are **mandatory** around loop and condition expressions.
- Mark invalid constructs (e.g., dynamic cursors outside scripting) with `-- TODO: confirm Snowflake syntax`.
- Use `LET` for assignment and `DECLARE` for variable initialization.
- Exception handling always follows the `EXCEPTION WHEN ... THEN` pattern.
```
