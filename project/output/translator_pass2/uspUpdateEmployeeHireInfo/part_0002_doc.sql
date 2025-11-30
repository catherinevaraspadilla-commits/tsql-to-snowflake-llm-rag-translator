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
CREATE PROCEDURE [HumanResources].[uspUpdateEmployeeHireInfo]
    @BusinessEntityID [int], 
    @JobTitle [nvarchar](50), 
    @HireDate [datetime], 
    @RateChangeDate [datetime], 
    @Rate [money], 
    @PayFrequency [tinyint], 
    @CurrentFlag [dbo].[Flag] 
WITH EXECUTE AS CALLER
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        UPDATE [HumanResources].[Employee] 
        SET [JobTitle] = @JobTitle 
            ,[HireDate] = @HireDate 
            ,[CurrentFlag] = @CurrentFlag 
        WHERE [BusinessEntityID] = @BusinessEntityID;

        INSERT INTO [HumanResources].[EmployeePayHistory] 
            ([BusinessEntityID]
            ,[RateChangeDate]
            ,[Rate]
            ,[PayFrequency]) 
        VALUES (@BusinessEntityID, @RateChangeDate, @Rate, @PayFrequency);

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        -- Rollback any active or uncommittable transactions before
        -- inserting information in the ErrorLog
        IF @@TRANCOUNT > 0
        BEGIN
            ROLLBACK TRANSACTION;
        END

        EXECUTE [dbo].[uspLogError];
    END CATCH;
END;