-- Person.vStateProvinceCountryRegion (VIEW)
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
-- TODOs:
--   -- TODO: Model unavailable; conservative pass-through. Review manually.
-- ===============================================
-- TODO: Model unavailable; conservative pass-through. Review manually.
CREATE VIEW [Person].[vStateProvinceCountryRegion] 
WITH SCHEMABINDING 
AS 
SELECT 
    sp.[StateProvinceID] 
    ,sp.[StateProvinceCode] 
    ,sp.[IsOnlyStateProvinceFlag] 
    ,sp.[Name] AS [StateProvinceName] 
    ,sp.[TerritoryID] 
    ,cr.[CountryRegionCode] 
    ,cr.[Name] AS [CountryRegionName]
FROM [Person].[StateProvince] sp 
    INNER JOIN [Person].[CountryRegion] cr 
    ON sp.[CountryRegionCode] = cr.[CountryRegionCode];
