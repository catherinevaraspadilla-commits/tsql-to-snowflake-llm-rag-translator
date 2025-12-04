-- part_0001: preamble/top-level
USE [AdventureWorks2022]
GO

/****** Object:  View [Person].[vStateProvinceCountryRegion]    Script Date: 10/7/2025 6:19:33 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

-- part_0003: EXEC sp_addextendedproperty
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Joins StateProvince table with CountryRegion table.' , @level0type=N'SCHEMA',@level0name=N'Person', @level1type=N'VIEW',@level1name=N'vStateProvinceCountryRegion'
