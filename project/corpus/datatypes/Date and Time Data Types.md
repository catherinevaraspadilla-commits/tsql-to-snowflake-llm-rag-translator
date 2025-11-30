```md
---
topic: datatypes
page_title: Date and Time Data Types
section_path: "SQL Data Types > Date and Time"
tags: [date, time, datetime, timestamp, timestamp_ltz, timestamp_ntz, timestamp_tz, timezone, format, precision, utc, mapping]
url: TODO
version: "2025-10-22"
---

# Date & time data types

Snowflake supports data types for managing dates, times, and timestamps (combined date + time).  
It also supports flexible formats for string constants representing these values.

## Supported data types

- `DATE`
- `DATETIME`
- `TIME`
- `TIMESTAMP_LTZ`, `TIMESTAMP_NTZ`, `TIMESTAMP_TZ`

---

### DATE

Snowflake supports a single `DATE` data type for storing dates (without time elements).  
`DATE` accepts common forms such as `YYYY-MM-DD`, `DD-MON-YYYY`, and others.

All accepted `TIMESTAMP` values are valid inputs for dates, but time information is truncated.

---

### DATETIME

`DATETIME` is synonymous with `TIMESTAMP_NTZ`.

---

### TIME

`TIME` stores wall-clock time in `HH:MI:SS` format.  
Supports optional precision for fractional seconds (e.g., `TIME(3)`).

- Precision range: `0` (seconds) to `9` (nanoseconds).  
- Default precision: `9`.  
- Valid range: `00:00:00` to `23:59:59.999999999`.  
- Operations on `TIME` ignore time zones.

Example:

```sql
CREATE TABLE t (t1 TIME(3));
INSERT INTO t VALUES ('12:30:15.123');
```

---

### TIMESTAMP variations

Snowflake supports three timestamp variations:

#### TIMESTAMP_LTZ (Local Time Zone)

- Internally stores UTC values with specified precision.
- Operations occur in the session’s time zone (`TIMEZONE` parameter).
- Synonyms:
  - `TIMESTAMPLTZ`
  - `TIMESTAMP WITH LOCAL TIME ZONE`

#### TIMESTAMP_NTZ (No Time Zone)

- Stores “wall-clock” time with precision, ignoring time zones.
- Displays UTC indicator (`Z`) if the output format includes a time zone.
- Default mapping for `TIMESTAMP`.
- Synonyms:
  - `TIMESTAMPNTZ`
  - `TIMESTAMP WITHOUT TIME ZONE`
  - `DATETIME`

#### TIMESTAMP_TZ (With Time Zone)

- Stores UTC value **plus** a time zone offset.
- If no time zone is provided, the session’s offset is used.
- Comparisons occur in UTC.
- Synonyms:
  - `TIMESTAMPTZ`
  - `TIMESTAMP WITH TIME ZONE`

Example — equivalent UTC comparison:

```sql
SELECT '2024-01-01 10:00:00 -05:00'::TIMESTAMP_TZ
     = '2024-01-01 15:00:00 +00:00'::TIMESTAMP_TZ;  -- TRUE
```

---

### TIMESTAMP alias

`TIMESTAMP` is a user-specified alias bound to one of the `TIMESTAMP_*` variations.  
It’s not stored in tables; operations use the underlying type set by:

```sql
ALTER SESSION SET TIMESTAMP_TYPE_MAPPING = TIMESTAMP_NTZ;
```

The default mapping is `TIMESTAMP_NTZ`.

Precision for fractional seconds can range from 0–9 (default 9).

---

## Examples

```sql
ALTER SESSION SET TIMESTAMP_TYPE_MAPPING = TIMESTAMP_NTZ;

CREATE OR REPLACE TABLE ts_test(ts TIMESTAMP);

DESC TABLE ts_test;
```

---

## Date and time formats

All these types accept most non-ambiguous date/time formats.  
Below are common format elements recognized by Snowflake.

| Format Element | Description |
|----------------|--------------|
| `YYYY` | Four-digit year |
| `YY` | Two-digit year, controlled by `TWO_DIGIT_CENTURY_START` |
| `MM` | Two-digit month (01–12) |
| `MON` | Month name (full or abbreviated) |
| `MMMM` | Full month name |
| `DD` | Two-digit day of month (01–31) |
| `DY` | Abbreviated day of week |
| `HH24` | Hour (00–23), no AM/PM |
| `HH12` | Hour (01–12), use with AM/PM |
| `AM`, `PM` | Ante/post meridiem indicators |
| `MI` | Minute (00–59) |
| `SS` | Second (00–59) |
| `FF[0-9]` | Fractional seconds precision (0–9) |
| `TZH:TZM`, `TZHTZM`, `TZH` | Time zone hour/minute offset (+/- from UTC) |
| `UUUU` | ISO year, negative for BCE years |

---

## Translator guidance (LLM-facing)

- Map T-SQL `DATETIME`, `SMALLDATETIME`, or `DATETIME2` to `TIMESTAMP_NTZ` by default.  
- For timezone-aware constructs, use `TIMESTAMP_TZ`.  
- Avoid assuming implicit conversion between TIMESTAMP variants; add `-- TODO: confirm TIMESTAMP type` if unclear.  
- Retain explicit
