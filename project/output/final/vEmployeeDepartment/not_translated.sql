-- part_0001: preamble/top-level
USE [AdventureWorks2022]
GO

/****** Object:  View [HumanResources].[vEmployeeDepartment]    Script Date: 10/7/2025 6:17:54 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

-- part_0003: EXEC sp_addextendedproperty
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Returns employee name, title, and current department.' , @level0type=N'SCHEMA',@level0name=N'HumanResources', @level1type=N'VIEW',@level1name=N'vEmployeeDepartment'
