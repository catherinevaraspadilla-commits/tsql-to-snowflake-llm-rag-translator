-- HumanResources.uspUpdateEmployeePersonalInfo (PROCEDURE)
-- ===============================================
-- Translation summary (Phase 4)
-- Citations:
--   - Snowflake Scripting Reference > Returning values
--   - Aggregate Functions > General Aggregation
--   - GROUP BY > Usage notes
--   - Aggregate Functions > Translator guidance (LLM-facing)
--   - Snowflake Scripting Reference > Looping constructs > REPEAT loop
--   - Snowflake Scripting Reference > Looping constructs > FOR loop (cursor-based)
--   - Aggregate Functions > Aggregation Utilities
--   - QUALIFY > Examples
-- Applied fixes: (none)
-- TODOs:
--   -- TODO: Model unavailable; conservative pass-through. Review manually.
-- ===============================================
-- TODO: Model unavailable; conservative pass-through. Review manually.
CREATE PROCEDURE [HumanResources].[uspUpdateEmployeePersonalInfo]
    @BusinessEntityID [int], 
    @NationalIDNumber [nvarchar](15), 
    @BirthDate [datetime], 
    @MaritalStatus [nchar](1), 
    @Gender [nchar](1)
WITH EXECUTE AS CALLER
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        UPDATE [HumanResources].[Employee] 
        SET [NationalIDNumber] = @NationalIDNumber 
            ,[BirthDate] = @BirthDate 
            ,[MaritalStatus] = @MaritalStatus 
            ,[Gender] = @Gender 
        WHERE [BusinessEntityID] = @BusinessEntityID;
    END TRY
    BEGIN CATCH
        EXECUTE [dbo].[uspLogError];
    END CATCH;
END;
