-- Person.vStateProvinceCountryRegion (VIEW)
CREATE OR REPLACE VIEW Person.vStateProvinceCountryRegion COPY GRANTS
AS
SELECT 
    sp.StateProvinceID,
    sp.StateProvinceCode,
    sp.IsOnlyStateProvinceFlag,
    sp.Name AS StateProvinceName,
    sp.TerritoryID,
    cr.CountryRegionCode,
    cr.Name AS CountryRegionName
FROM Person.StateProvince sp
    INNER JOIN Person.CountryRegion cr 
    ON sp.CountryRegionCode = cr.CountryRegionCode;
