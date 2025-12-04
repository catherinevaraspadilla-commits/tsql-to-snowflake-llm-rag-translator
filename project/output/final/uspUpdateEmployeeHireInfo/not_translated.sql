-- part_0001: preamble/top-level
USE [AdventureWorks2022]
GO

/****** Object:  StoredProcedure [HumanResources].[uspUpdateEmployeeHireInfo]    Script Date: 10/7/2025 6:14:44 AM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

-- part_0003: EXEC sp_addextendedproperty
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Updates the Employee table and inserts a new row in the EmployeePayHistory table with the values specified in the input parameters.' , @level0type=N'SCHEMA',@level0name=N'HumanResources', @level1type=N'PROCEDURE',@level1name=N'uspUpdateEmployeeHireInfo'

-- part_0004: EXEC sp_addextendedproperty
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Input parameter for the stored procedure uspUpdateEmployeeHireInfo. Enter a valid BusinessEntityID from the Employee table.' , @level0type=N'SCHEMA',@level0name=N'HumanResources', @level1type=N'PROCEDURE',@level1name=N'uspUpdateEmployeeHireInfo', @level2type=N'PARAMETER',@level2name=N'@BusinessEntityID'

-- part_0005: EXEC sp_addextendedproperty
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Input parameter for the stored procedure uspUpdateEmployeeHireInfo. Enter a title for the employee.' , @level0type=N'SCHEMA',@level0name=N'HumanResources', @level1type=N'PROCEDURE',@level1name=N'uspUpdateEmployeeHireInfo', @level2type=N'PARAMETER',@level2name=N'@JobTitle'

-- part_0006: EXEC sp_addextendedproperty
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Input parameter for the stored procedure uspUpdateEmployeeHireInfo. Enter a hire date for the employee.' , @level0type=N'SCHEMA',@level0name=N'HumanResources', @level1type=N'PROCEDURE',@level1name=N'uspUpdateEmployeeHireInfo', @level2type=N'PARAMETER',@level2name=N'@HireDate'

-- part_0007: EXEC sp_addextendedproperty
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Input parameter for the stored procedure uspUpdateEmployeeHireInfo. Enter the date the rate changed for the employee.' , @level0type=N'SCHEMA',@level0name=N'HumanResources', @level1type=N'PROCEDURE',@level1name=N'uspUpdateEmployeeHireInfo', @level2type=N'PARAMETER',@level2name=N'@RateChangeDate'

-- part_0008: EXEC sp_addextendedproperty
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Input parameter for the stored procedure uspUpdateEmployeeHireInfo. Enter the new rate for the employee.' , @level0type=N'SCHEMA',@level0name=N'HumanResources', @level1type=N'PROCEDURE',@level1name=N'uspUpdateEmployeeHireInfo', @level2type=N'PARAMETER',@level2name=N'@Rate'

-- part_0009: EXEC sp_addextendedproperty
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Input parameter for the stored procedure uspUpdateEmployeeHireInfo. Enter the pay frequency for the employee.' , @level0type=N'SCHEMA',@level0name=N'HumanResources', @level1type=N'PROCEDURE',@level1name=N'uspUpdateEmployeeHireInfo', @level2type=N'PARAMETER',@level2name=N'@PayFrequency'

-- part_0010: EXEC sp_addextendedproperty
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'Input parameter for the stored procedure uspUpdateEmployeeHireInfo. Enter the current flag for the employee.' , @level0type=N'SCHEMA',@level0name=N'HumanResources', @level1type=N'PROCEDURE',@level1name=N'uspUpdateEmployeeHireInfo', @level2type=N'PARAMETER',@level2name=N'@CurrentFlag'
