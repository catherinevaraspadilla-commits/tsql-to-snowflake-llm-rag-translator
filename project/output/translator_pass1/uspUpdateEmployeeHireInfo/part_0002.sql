CREATE OR REPLACE PROCEDURE HumanResources.uspUpdateEmployeeHireInfo(
    BusinessEntityID INT, 
    JobTitle STRING, 
    HireDate TIMESTAMP, 
    RateChangeDate TIMESTAMP, 
    Rate NUMERIC(19,4), 
    PayFrequency TINYINT, 
    CurrentFlag BOOLEAN
)
RETURNS STRING
LANGUAGE SQL
EXECUTE AS CALLER
$$
BEGIN
    -- Declare a variable to track errors
    DECLARE error_occurred BOOLEAN DEFAULT FALSE;

    -- Start a transaction
    BEGIN TRANSACTION;

    -- Try block
    BEGIN
        -- Update the Employee table
        UPDATE HumanResources.Employee
        SET JobTitle = JobTitle,
            HireDate = HireDate,
            CurrentFlag = CurrentFlag
        WHERE BusinessEntityID = BusinessEntityID;

        -- Insert into EmployeePayHistory table
        INSERT INTO HumanResources.EmployeePayHistory (
            BusinessEntityID,
            RateChangeDate,
            Rate,
            PayFrequency
        )
        VALUES (
            BusinessEntityID,
            RateChangeDate,
            Rate,
            PayFrequency
        );

        -- Commit the transaction
        COMMIT;
    EXCEPTION
        -- Catch block
        WHEN OTHERS THEN
            -- Rollback the transaction if an error occurs
            ROLLBACK;
            -- Set the error flag
            LET error_occurred = TRUE;
    END;

    -- If an error occurred, log it
    IF error_occurred THEN
        CALL dbo.uspLogError();
    END IF;

    -- Return success message
    RETURN 'OK'::STRING;
END;
$$;