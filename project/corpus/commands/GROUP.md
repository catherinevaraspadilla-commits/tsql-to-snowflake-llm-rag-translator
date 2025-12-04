---
topic: commands
page_title: GROUP BY
section_path: "SQL Command Reference > GROUP BY"
tags: [group-by, aggregates, having, cube, grouping-sets, rollup, grouping-columns, positional-index]
url: TODO
version: "2025-10-22"
---

# GROUP BY

Groups rows with the same group-by-item expressions and computes aggregate functions for each resulting group.

A GROUP BY expression can be:
- A column name.
- A number referencing a position in the SELECT list.
- A general expression.

## Syntax (core)

    SELECT <select_list>
    FROM <table_or_source>
    [WHERE <predicate>]
    GROUP BY <group_item> [, <group_item>, ...]
    [HAVING <aggregate_predicate>]
    [ORDER BY <expr> [ASC|DESC]]
    [LIMIT <n>]

Where a `<group_item>` is:
- A column reference (e.g., city)
- A positional index (e.g., 1 for the first projected column)
- An expression (e.g., DATE_TRUNC('month', ts))

## Usage notes

- Aggregates (e.g., COUNT, SUM, MIN, MAX, AVG) are typically used with GROUP BY.
- Positional indexes refer to items in the SELECT list (1-based). Use with care for readability.
- Columns in the SELECT list must be either:
  - Grouped (appear in GROUP BY), or
  - Aggregated, or
  - Functionally dependent when supported by the engine rules.
- HAVING filters **after** grouping and can only reference grouped columns, aggregates, or expressions derived from them.

## Extensions

### GROUP BY CUBE
`GROUP BY CUBE` is similar to `GROUP BY ROLLUP` but also adds all “cross-tabulation” rows. A CUBE with N elements corresponds to `2^N` grouping sets.

High level:
- Produces all rollup totals plus every combination of dimensions.
- Useful for multi-dimensional summaries.

### GROUP BY GROUPING SETS
Computes multiple group-by lists in a single query. Each grouping set is an independent grouping of dimension columns.

Equivalences:
- `GROUP BY GROUPING SETS (a)` ≈ `GROUP BY a`
- `GROUP BY GROUPING SETS (a, b)` ≈ `(GROUP BY a) UNION ALL (GROUP BY b)`

### GROUP BY ROLLUP
Produces hierarchical subtotals in addition to grouped rows. Think of it as multiple result levels where each subsequent level aggregates the previous one (e.g., city → state → all).

## Examples: CUBE (sales)

Start by creating and loading a table with information about sales from a chain store that has branches in different cities and states/territories.

    -- Create some tables and insert some rows.
    CREATE TABLE products (product_ID INTEGER, wholesale_price REAL);
    INSERT INTO products (product_ID, wholesale_price) VALUES 
        (1, 1.00),
        (2, 2.00);

    CREATE TABLE sales (product_ID INTEGER, retail_price REAL, 
        quantity INTEGER, city VARCHAR, state VARCHAR);
    INSERT INTO sales (product_id, retail_price, quantity, city, state) VALUES 
        (1, 2.00,  1, 'SF', 'CA'),
        (1, 2.00,  2, 'SJ', 'CA'),
        (2, 5.00,  4, 'SF', 'CA'),
        (2, 5.00,  8, 'SJ', 'CA'),
        (2, 5.00, 16, 'Miami', 'FL'),
        (2, 5.00, 32, 'Orlando', 'FL'),
        (2, 5.00, 64, 'SJ', 'PR');

Run a cube query that shows profit by city, state, and total across all states. The example below shows a query that has three “levels”:
- Each city.
- Each state.
- All revenue combined.

Use `ORDER BY state, city NULLS LAST` to keep each state’s rollup directly after its cities and to place the grand total at the end.

    -- Example shape (illustrative):
    -- SELECT state, city, SUM((s.retail_price - p.wholesale_price) * s.quantity) AS profit
    -- FROM products AS p JOIN sales AS s ON s.product_ID = p.product_ID
    -- GROUP BY CUBE (state, city)
    -- ORDER BY state, city NULLS LAST;

## Examples: GROUPING SETS (nurses)

These examples use a table of information about nurses with two categories of licenses.

    CREATE OR REPLACE TABLE nurses (
      ID INTEGER,
      full_name VARCHAR,
      medical_license VARCHAR,   -- LVN, RN, etc.
      radio_license VARCHAR      -- Technician, General, Amateur Extra
    );

    INSERT INTO nurses
        (ID, full_name, medical_license, radio_license)
      VALUES
        (201, 'Thomas Leonard Vicente', 'LVN', 'Technician'),
        (202, 'Tamara Lolita VanZant', 'LVN', 'Technician'),
        (341, 'Georgeann Linda Vente', 'LVN', 'General'),
        (471, 'Andrea Renee Nouveau', 'RN', 'Amateur Extra');

Use `GROUP BY GROUPING SETS` to compute multiple independent aggregations in a single pass:

    SELECT COUNT(*), medical_license, radio_license
      FROM nurses
      GROUP BY GROUPING SETS (medical_license, radio_license);

Output (illustrative):

    +----------+-----------------+---------------+
    | COUNT(*) | MEDICAL_LICENSE | RADIO_LICENSE |
    |----------+-----------------+---------------|
    |        3 | LVN             | NULL          |
    |        1 | RN              | NULL          |
    |        2 | NULL            | Technician    |
    |        1 | NULL            | General       |
    |        1 | NULL            | Amateur Extra |
    +----------+-----------------+---------------+

Interpretation:
- Rows with NULL in RADIO_LICENSE count by `medical_license` only.
- Rows with NULL in MEDICAL_LICENSE count by `radio_license` only.

## Examples: ROLLUP (sales)

`ROLLUP` produces hierarchical subtotals (e.g., city → state → grand total).

    SELECT state, city,
           SUM((s.retail_price - p.wholesale_price) * s.quantity) AS profit 
    FROM products AS p
    JOIN sales AS s
      ON s.product_ID = p.product_ID
    GROUP BY ROLLUP (state, city)
    ORDER BY state, city NULLS LAST;

Illustrative output:

    +-------+---------+--------+
    | STATE | CITY    | PROFIT |
    |-------+---------+--------|
    | CA    | SF      |     13 |
    | CA    | SJ      |     26 |
    | CA    | NULL    |     39 |
    | FL    | Miami   |     48 |
    | FL    | Orlando |     96 |
    | FL    | NULL    |    144 |
    | PR    | SJ      |    192 |
    | PR    | NULL    |    192 |
    | NULL  | NULL    |    375 |
    +-------+---------+--------+

## Translator guidance (LLM-facing)

- Preserve GROUP BY semantics; avoid inventing columns or grouping keys.
- When source uses positional references (e.g., `GROUP BY 1, 2`), maintain them only if unambiguous; prefer explicit column names when clarity matters.
- For T-SQL migrations that simulate `GROUPING SETS` with `UNION ALL`, prefer Snowflake’s `GROUP BY GROUPING SETS` directly.
- For hierarchical summaries, translate T-SQL multi-step rollups to a single `GROUP BY ROLLUP`.
- Keep `ORDER BY` consistent with expected subtotal layout; consider `NULLS LAST` for rollups.
