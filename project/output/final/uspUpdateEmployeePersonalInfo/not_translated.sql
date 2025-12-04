-- part_0001: preamble/top-level
USE [AdventureWorks2022]
GO

/****** Object:  StoredProcedure [HumanResources].[uspUpdateEmployeePersonalInfo]    Script Date: 10/7/2025 6:15:01 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

-- part_0003: EXEC sp_addextendedproperty
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Updates the Employee table with the values specified in the input parameters for the given EmployeeID.' , @level0type=N'SCHEMA',@level0name=N'HumanResources', @level1type=N'PROCEDURE',@level1name=N'uspUpdateEmployeePersonalInfo'

-- part_0004: EXEC sp_addextendedproperty
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Input parameter for the stored procedure uspUpdateEmployeePersonalInfo. Enter a valid BusinessEntityID from the HumanResources.Employee table.' , @level0type=N'SCHEMA',@level0name=N'HumanResources', @level1type=N'PROCEDURE',@level1name=N'uspUpdateEmployeePersonalInfo', @level2type=N'PARAMETER',@level2name=N'@BusinessEntityID'

-- part_0005: EXEC sp_addextendedproperty
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Input parameter for the stored procedure uspUpdateEmployeeHireInfo. Enter a national ID for the employee.' , @level0type=N'SCHEMA',@level0name=N'HumanResources', @level1type=N'PROCEDURE',@level1name=N'uspUpdateEmployeePersonalInfo', @level2type=N'PARAMETER',@level2name=N'@NationalIDNumber'

-- part_0006: EXEC sp_addextendedproperty
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Input parameter for the stored procedure uspUpdateEmployeeHireInfo. Enter a birth date for the employee.' , @level0type=N'SCHEMA',@level0name=N'HumanResources', @level1type=N'PROCEDURE',@level1name=N'uspUpdateEmployeePersonalInfo', @level2type=N'PARAMETER',@level2name=N'@BirthDate'

-- part_0007: EXEC sp_addextendedproperty
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Input parameter for the stored procedure uspUpdateEmployeeHireInfo. Enter a marital status for the employee.' , @level0type=N'SCHEMA',@level0name=N'HumanResources', @level1type=N'PROCEDURE',@level1name=N'uspUpdateEmployeePersonalInfo', @level2type=N'PARAMETER',@level2name=N'@MaritalStatus'

-- part_0008: EXEC sp_addextendedproperty
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Input parameter for the stored procedure uspUpdateEmployeeHireInfo. Enter a gender for the employee.' , @level0type=N'SCHEMA',@level0name=N'HumanResources', @level1type=N'PROCEDURE',@level1name=N'uspUpdateEmployeePersonalInfo', @level2type=N'PARAMETER',@level2name=N'@Gender'
