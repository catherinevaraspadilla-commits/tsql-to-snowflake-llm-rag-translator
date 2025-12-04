---
topic: scripting
page_title: Functions, Procedures, and Scripting Commands
section_path: "Snowflake Scripting > Functions & Procedures"
tags: [udf, external-function, data-metric-function, dmf, service-function, stored-procedure, create-function, alter-function, drop-function, describe-function, show, create-procedure, alter-procedure, call, execute-immediate]
url: TODO
version: "2025-10-22"
---

# Functions, procedures, and scripting commands

Functions, procedures, and scripting commands enable you to manage user-defined functions (UDFs), external functions, stored procedures, and scripts.

## User-defined function (UDF)

- CREATE FUNCTION
- ALTER FUNCTION
- DESCRIBE FUNCTION
- DROP FUNCTION
- SHOW USER FUNCTIONS

## Data metric function (DMF)

- CREATE DATA METRIC FUNCTION
- ALTER FUNCTION (DMF)
- DESCRIBE FUNCTION (DMF)
- DROP FUNCTION (DMF)
- SHOW DATA METRIC FUNCTIONS

Additionally, you can use **ALTER TABLE** and **ALTER VIEW** to:
- Add or drop a data metric function on a **column**.
- Add or drop a data metric function on the **table** or **view** itself.
- Schedule the data metric function to run.

(For representative examples, see “Use data metric functions to perform data quality checks.”)

## Service function (Snowpark Container Services)

- CREATE FUNCTION (Snowpark Container Services)
- ALTER FUNCTION (Snowpark Container Services)
- DESCRIBE FUNCTION (Snowpark Container Services)
- DROP FUNCTION (Snowpark Container Services)

## External function

- CREATE EXTERNAL FUNCTION
- ALTER FUNCTION
- DESCRIBE FUNCTION
- DROP FUNCTION
- SHOW EXTERNAL FUNCTIONS

## Stored procedure

- CREATE PROCEDURE
- ALTER PROCEDURE
- CALL
- CALL (with anonymous procedure)
- DESCRIBE PROCEDURE
- DROP PROCEDURE
- SHOW PROCEDURES
- SHOW USER PROCEDURES

## Scripting

- EXECUTE IMMEDIATE
- EXECUTE IMMEDIATE FROM

## Translator guidance (LLM-facing)

- Ensure procedures include: RETURNS <type>, LANGUAGE SQL, and AS $$ ... $$ delimiters when translating from T-SQL-like definitions.
- Map PRINT (T-SQL) to RETURN or appropriate alternative; add a “-- TODO” when intent is unclear.
- For UDFs/external functions/DMFs, preserve CREATE/ALTER/DROP/SHOW semantics; do not invent options. If required options are missing, insert a “-- TODO”.
