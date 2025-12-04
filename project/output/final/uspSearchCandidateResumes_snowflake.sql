-- dbo.uspSearchCandidateResumes (PROCEDURE)
CREATE OR REPLACE PROCEDURE dbo.uspSearchCandidateResumes(
    searchString STRING,   
    useInflectional BOOLEAN DEFAULT FALSE,
    useThesaurus BOOLEAN DEFAULT FALSE,
    language INT DEFAULT 0
)
RETURNS STRING
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
BEGIN
    DECLARE string STRING;

    -- Setting the language to the default instance LCID if needed
    IF language IS NULL OR language = 0 THEN
        LET language = TRY_CAST(SYSTEM$GET_PARAMETER('LCID') AS INT); -- TODO: Verify if SYSTEM$GET_PARAMETER('LCID') returns a valid INT
    END IF;

    -- FREETEXTTABLE case as inflectional and thesaurus were required
    IF useThesaurus = TRUE AND useInflectional = TRUE THEN
        RETURN (
            SELECT OBJECT_CONSTRUCT(FT_TBL.JobCandidateID, KEY_TBL.RANK)::STRING
            FROM HumanResources.JobCandidate AS FT_TBL
            INNER JOIN TABLE(FREETEXTTABLE(HumanResources.JobCandidate, '*', searchString, LANGUAGE => language)) AS KEY_TBL
            ON FT_TBL.JobCandidateID = KEY_TBL.KEY
        );
    ELSEIF useThesaurus = TRUE THEN
        LET string = 'FORMSOF(THESAURUS, "' || searchString || '")';
        RETURN (
            SELECT OBJECT_CONSTRUCT(FT_TBL.JobCandidateID, KEY_TBL.RANK)::STRING
            FROM HumanResources.JobCandidate AS FT_TBL
            INNER JOIN TABLE(CONTAINSTABLE(HumanResources.JobCandidate, '*', string, LANGUAGE => language)) AS KEY_TBL
            ON FT_TBL.JobCandidateID = KEY_TBL.KEY
        );
    ELSEIF useInflectional = TRUE THEN
        LET string = 'FORMSOF(INFLECTIONAL, "' || searchString || '")';
        RETURN (
            SELECT OBJECT_CONSTRUCT(FT_TBL.JobCandidateID, KEY_TBL.RANK)::STRING
            FROM HumanResources.JobCandidate AS FT_TBL
            INNER JOIN TABLE(CONTAINSTABLE(HumanResources.JobCandidate, '*', string, LANGUAGE => language)) AS KEY_TBL
            ON FT_TBL.JobCandidateID = KEY_TBL.KEY
        );
    ELSE
        -- Base case, plain CONTAINSTABLE
        LET string = '"' || searchString || '"';
        RETURN (
            SELECT OBJECT_CONSTRUCT(FT_TBL.JobCandidateID, KEY_TBL.RANK)::STRING
            FROM HumanResources.JobCandidate AS FT_TBL
            INNER JOIN TABLE(CONTAINSTABLE(HumanResources.JobCandidate, '*', string, LANGUAGE => language)) AS KEY_TBL
            ON FT_TBL.JobCandidateID = KEY_TBL.KEY
        );
    END IF;

END;
$$;
