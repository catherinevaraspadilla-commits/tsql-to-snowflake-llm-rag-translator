---
topic: commands
page_title: QUALIFY
section_path: "SQL Command Reference > QUALIFY"
tags: [qualify, window, row_number, dense_rank, rank, over, partition-by, having, predicate, filter, select-order]
url: TODO
version: "2025-10-22"
---

# QUALIFY

In a SELECT statement, the QUALIFY clause filters the results of window functions.

QUALIFY does with window functions what HAVING does with aggregate functions and GROUP BY clauses.

In the logical execution order, QUALIFY is evaluated after window functions are computed. A typical evaluation order:

1. FROM
2. WHERE
3. GROUP BY
4. HAVING
5. WINDOW (analytic functions)
6. QUALIFY
7. DISTINCT
8. ORDER BY
9. LIMIT

## Syntax

    QUALIFY <predicate>

General shape (variations in order are possible but not shown here):

    SELECT <column_list>
      FROM <data_source>
      [GROUP BY ...]
      [HAVING ...]
      QUALIFY <predicate>
      [ ... ]

## Parameters

column_list — As in the SELECT projection rules.

data_source — A table or table-like source (view, UDTF, etc.).

predicate — Boolean expression evaluated after window functions and aggregates. Can reference window functions and behaves like HAVING (but without the HAVING keyword).

## Usage notes

- QUALIFY requires at least one window function either in the SELECT list or inside the QUALIFY predicate.
- Expressions in the SELECT list (including window functions) may be referenced by column alias in QUALIFY.
- Aggregates and subqueries are allowed inside QUALIFY; aggregate rules mirror those of HAVING.
- QUALIFY is Snowflake-specific (not ANSI); QUALIFY is a reserved word.

## Translator guidance (LLM-facing)

- If the source filters on a window function in WHERE, move that predicate to QUALIFY.
- Prefer aliasing window results (e.g., AS rn) and writing QUALIFY rn = 1 for clarity.
- When translating T-SQL patterns like WHERE ROW_NUMBER() OVER(...) = 1, emit a validator suggestion MOVE_TO_QUALIFY if needed and rewrite with QUALIFY.

## Examples

Create and load a table:

    CREATE TABLE qt (i INTEGER, p CHAR(1), o INTEGER);
    INSERT INTO qt (i, p, o) VALUES
        (1, 'A', 1),
        (2, 'A', 2),
        (3, 'B', 1),
        (4, 'B', 2);

Nesting instead of QUALIFY:

    SELECT *
    FROM (
      SELECT i, p, o,
             ROW_NUMBER() OVER (PARTITION BY p ORDER BY o) AS row_num
      FROM qt
    )
    WHERE row_num = 1;

Using QUALIFY:

    SELECT i, p, o
    FROM qt
    QUALIFY ROW_NUMBER() OVER (PARTITION BY p ORDER BY o) = 1;

Referencing a SELECT alias from QUALIFY:

    SELECT i, p, o, ROW_NUMBER() OVER (PARTITION BY p ORDER BY o) AS row_num
    FROM qt
    QUALIFY row_num = 1;

With aggregates and a subquery in the predicate:

    SELECT c2, SUM(c3) OVER (PARTITION BY c2) AS r
    FROM t1
    WHERE c3 < 4
    GROUP BY c2, c3
    HAVING SUM(c1) > 3
    QUALIFY r IN (
      SELECT MIN(c1)
      FROM test
      GROUP BY c2
      HAVING MIN(c1) > 3
    );
