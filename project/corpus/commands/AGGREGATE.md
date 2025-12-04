---
topic: commands
page_title: Aggregate
section_path: "SQL Functions > Aggregate Functions"
tags: [aggregate, count, sum, avg, min, max, stddev, variance, percentile, listagg, approx, hll, grouping, regression]
url: TODO
version: "2025-10-22"
---

# Aggregate functions

Aggregate functions operate on values across rows to perform calculations such as sum, average, counts, min/max, standard deviation, percentiles/medians, and estimation.  
An aggregate function consumes zero, one, or more input rows and produces a **single** output value.  
(In contrast, **scalar** functions produce one output per input row.)

## Usage

- Typically used with `GROUP BY`, or over the entire result set if no grouping is specified.  
- `DISTINCT` is supported by many aggregates (e.g., `COUNT(DISTINCT col)`), with different performance trade-offs.  
- Some families below include helper functions that are **not** aggregates (noted explicitly).

## General Aggregation

- `ANY_VALUE`
- `AVG`
- `CORR`
- `COUNT`, `COUNT_IF`
- `COVAR_POP`, `COVAR_SAMP`
- `LISTAGG`
- `MAX`, `MAX_BY`
- `MEDIAN`
- `MIN`, `MIN_BY`
- `MODE`
- `PERCENTILE_CONT`  (different syntax than most aggregates)
- `PERCENTILE_DISC`  (different syntax than most aggregates)
- `STDDEV`, `STDDEV_SAMP`  (aliases)
- `STDDEV_POP`
- `SUM`
- `VAR_POP`
- `VAR_SAMP`
- `VARIANCE_POP`  (alias for `VAR_POP`)
- `VARIANCE`, `VARIANCE_SAMP`  (aliases for `VAR_SAMP`)

## Bitwise Aggregation

- `BITAND_AGG`
- `BITOR_AGG`
- `BITXOR_AGG`

## Boolean Aggregation

- `BOOLAND_AGG`
- `BOOLOR_AGG`
- `BOOLXOR_AGG`

## Hash

- `HASH_AGG`

## Semi-structured Data Aggregation

- `ARRAY_AGG`
- `OBJECT_AGG`

## Linear Regression (regr_*)

- `REGR_AVGX`, `REGR_AVGY`, `REGR_COUNT`, `REGR_INTERCEPT`, `REGR_R2`, `REGR_SLOPE`, `REGR_SXX`, `REGR_SXY`, `REGR_SYY`

## Statistics and Probability

- `KURTOSIS`, `SKEW`

## Counting Distinct Values

- `ARRAY_UNION_AGG`, `ARRAY_UNIQUE_AGG`
- `BITMAP_BIT_POSITION`, `BITMAP_BUCKET_NUMBER`, `BITMAP_COUNT`, `BITMAP_CONSTRUCT_AGG`, `BITMAP_OR_AGG`

## Cardinality Estimation (HyperLogLog family)

- `APPROX_COUNT_DISTINCT`  (alias: `HLL`)
- `DATASKETCHES_HLL`, `DATASKETCHES_HLL_ACCUMULATE`, `DATASKETCHES_HLL_COMBINE`
- `DATASKETCHES_HLL_ESTIMATE`  — not an aggregate; consumes scalar sketches from ACCUMULATE/COMBINE.
- `HLL`, `HLL_ACCUMULATE`, `HLL_COMBINE`
- `HLL_ESTIMATE`  — not an aggregate; consumes scalar sketches from ACCUMULATE/COMBINE.
- `HLL_EXPORT`, `HLL_IMPORT`

## Similarity Estimation (MinHash family)

- `APPROXIMATE_JACCARD_INDEX`  (alias: `APPROXIMATE_SIMILARITY`)
- `APPROXIMATE_SIMILARITY`
- `MINHASH`, `MINHASH_COMBINE`

## Frequency Estimation (Space-Saving)

- `APPROX_TOP_K`, `APPROX_TOP_K_ACCUMULATE`, `APPROX_TOP_K_COMBINE`
- `APPROX_TOP_K_ESTIMATE` — not an aggregate; consumes scalar state from ACCUMULATE/COMBINE.

## Percentile Estimation (t-Digest family)

- `APPROX_PERCENTILE`, `APPROX_PERCENTILE_ACCUMULATE`, `APPROX_PERCENTILE_COMBINE`
- `APPROX_PERCENTILE_ESTIMATE` — not an aggregate; consumes scalar digest from ACCUMULATE/COMBINE.

## Aggregation Utilities

- `GROUPING` — not an aggregate; indicates the aggregation level of a row (with `GROUP BY`/`ROLLUP`/`CUBE`/`GROUPING SETS`).
- `GROUPING_ID` — alias for `GROUPING`.

## AI Functions (aggregate variants)

- `AI_AGG`
- `AI_SUMMARIZE_AGG`

## Examples (illustrative)

Count and sum by group:

    SELECT dept, COUNT(*) AS n, SUM(salary) AS payroll
    FROM employees
    GROUP BY dept;

Distinct count vs approximate:

    SELECT COUNT(DISTINCT user_id) AS exact_uv,
           APPROX_COUNT_DISTINCT(user_id) AS approx_uv
    FROM events;

Concatenate values per group:

    SELECT dept, LISTAGG(employee_name, ', ') WITHIN GROUP (ORDER BY employee_name) AS names
    FROM employees
    GROUP BY dept;

Median and percentiles:

    SELECT MEDIAN(latency_ms) AS p50,
           PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95
    FROM request_metrics;

t-Digest workflow (sketch accumulate → estimate):

    -- Build or combine digests by group
    SELECT region,
           APPROX_PERCENTILE_ACCUMULATE(latency_ms) AS digest
    FROM request_metrics
    GROUP BY region;

    -- Later, estimate from stored digest
    -- SELECT APPROX_PERCENTILE_ESTIMATE(digest, 0.99) AS p99 FROM stored_digests;

## Translator guidance (LLM-facing)

- Preserve aggregate semantics; if the source uses dialect-specific forms, map to Snowflake equivalents (`COUNT_IF`, `LISTAGG`, `PERCENTILE_CONT`, etc.).  
- Prefer `APPROX_COUNT_DISTINCT` for large distinct counts when performance matters; keep exact `COUNT(DISTINCT ...)` when correctness is required.  
- Do not invent `WITHIN GROUP` orderings for `LISTAGG`/percentiles; if absent in the source and required for Snowflake, add a `-- TODO:` note.  
- For sketch-based families (HLL, t-Digest, TOP-K), ensure ACCUMULATE/COMBINE/ESTIMATE functions are used in the correct phases; mark `-- TODO:` when state objects are missing or unclear.
