-- HumanResources.vEmployeeDepartment (VIEW)
-- ===============================================
-- Translation summary (Phase 4)
-- Citations:
--   - GROUP BY > Usage notes
--   - Aggregate Functions > General Aggregation
--   - SELECT > Notes
--   - Query Operators > Notes
--   - Aggregate Functions > Aggregation Utilities
--   - Aggregate Functions > Translator guidance (LLM-facing)
--   - QUALIFY > Examples
--   - Aggregate Functions > Examples (illustrative)
-- Applied fixes: (none)
-- TODOs: (none)
-- ===============================================
CREATE OR REPLACE VIEW HumanResources.vEmployeeDepartment [COPY GRANTS]
AS
SELECT 
    e.BusinessEntityID,
    p.Title,
    p.FirstName,
    p.MiddleName,
    p.LastName,
    p.Suffix,
    e.JobTitle,
    d.Name AS Department,
    d.GroupName,
    edh.StartDate
FROM HumanResources.Employee e
    INNER JOIN Person.Person p
        ON p.BusinessEntityID = e.BusinessEntityID
    INNER JOIN HumanResources.EmployeeDepartmentHistory edh
        ON e.BusinessEntityID = edh.BusinessEntityID
    INNER JOIN HumanResources.Department d
        ON edh.DepartmentID = d.DepartmentID
WHERE edh.EndDate IS NULL;
