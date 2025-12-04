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
--   -- TODO: Replace 'dbo.uspLogError' with the appropriate Snowflake error logging procedure if available
-- ===============================================
CREATE OR REPLACE PROCEDURE HumanResources.uspUpdateEmployeePersonalInfo(
    BusinessEntityID INT, 
    NationalIDNumber STRING, 
    BirthDate TIMESTAMP, 
    MaritalStatus STRING, 
    Gender STRING
)
RETURNS STRING
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
BEGIN
    -- Declare a variable to capture errors
    DECLARE error_message STRING;

    BEGIN
        -- Attempt to update the Employee table
        UPDATE HumanResources.Employee
        SET NationalIDNumber = NationalIDNumber,
            BirthDate = BirthDate,
            MaritalStatus = MaritalStatus,
            Gender = Gender
        WHERE BusinessEntityID = BusinessEntityID;
    EXCEPTION
        -- Catch any errors and log them
        WHEN OTHERS THEN
            -- TODO: Replace 'dbo.uspLogError' with the appropriate Snowflake error logging procedure if available
            -- Ensure the error logging procedure exists and is correctly referenced
            CALL dbo.uspLogError();
            RETURN 'Error occurred while updating employee personal info'::STRING;
    END;

    -- Return success message
    RETURN 'OK'::STRING;
END;
$$;