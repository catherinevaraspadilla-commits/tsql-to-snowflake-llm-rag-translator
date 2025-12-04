---
topic: commands
page_title: JOIN
section_path: "SQL Command Reference > JOIN"
tags: [join, inner, left-outer, right-outer, full-outer, cross, natural, on, where, directed, cartesian]
url: TODO
version: "2025-10-22"
---

# JOIN

A JOIN operation combines rows from two tables — or other table-like sources, such as views or table functions — to create a new combined row that can be used in the query. For a conceptual explanation of joins, see Working with joins.

## Inputs

object_ref1 and object_ref2 — Each object reference is a table or table-like data source.

## JOIN keyword

Use the JOIN keyword to specify that the tables should be joined. Combine JOIN with other join-related keywords — for example, INNER or OUTER — to specify the type of join.

For brevity, this topic uses o1 and o2 for object_ref1 and object_ref2, respectively.

## Join types and semantics

o1 INNER JOIN o2  
For each row of o1, a row is produced for each row of o2 that matches according to the ON condition subclause. You can also use a comma to specify an inner join. If you use INNER JOIN without the ON clause, or if you use a comma without a WHERE clause, the result is the same as using CROSS JOIN: a Cartesian product; every row of o1 paired with every row of o2.

o1 LEFT OUTER JOIN o2  
The result of the inner join is augmented with a row for each row of o1 that has no matches in o2. The result columns referencing o2 contain NULL.

o1 RIGHT OUTER JOIN o2  
The result of the inner join is augmented with a row for each row of o2 that has no matches in o1. The result columns referencing o1 contain NULL.

o1 FULL OUTER JOIN o2  
Returns all joined rows, plus one row for each unmatched left side row (extended with NULLs on the right), plus one row for each unmatched right side row (extended with NULLs on the left).

o1 CROSS JOIN o2  
For every possible combination of rows from o1 and o2 (that is, a Cartesian product), the joined table contains a row consisting of all columns in o1 followed by all columns in o2. A CROSS JOIN can’t be combined with an ON condition clause. However, you can use a WHERE clause to filter the results.

o1 NATURAL JOIN o2  
A NATURAL JOIN is identical to an explicit JOIN on the common columns of the two tables, except that the common columns are included only once in the output. A natural join assumes that columns with the same name (but in different tables) contain corresponding data. A NATURAL JOIN can be combined with an OUTER JOIN. A NATURAL JOIN can’t be combined with an ON condition clause because the JOIN condition is already implied. However, you can use a WHERE clause to filter the results.

## DIRECTED joins

The DIRECTED keyword specifies a directed join, which enforces the join order of the tables. The first (left) table is scanned before the second (right) table. For example, o1 INNER DIRECTED JOIN o2 scans the o1 table before the o2 table.

Directed joins are useful in the following situations:
- You are migrating workloads into Snowflake that have join order directives.
- You want to improve performance by scanning join tables in a specific order.

## Translator guidance (LLM-facing)

- If source SQL uses a comma join without a WHERE clause, rewrite as CROSS JOIN.  
- Ensure INNER JOIN has an ON predicate; if missing, warn about Cartesian product risk.  
- NATURAL JOIN cannot have an ON clause; if both appear, prefer explicit JOIN ... ON with named columns.  
- For performance-sensitive migrations that specify join order, preserve DIRECTED keyword when present.
