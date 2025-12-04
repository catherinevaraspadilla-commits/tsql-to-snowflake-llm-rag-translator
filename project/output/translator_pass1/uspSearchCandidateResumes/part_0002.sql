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
        LET language = CONVERT(INT, SYSTEM$GET_PARAMETER('LCID'));
    END IF;

    -- FREETEXTTABLE case as inflectional and thesaurus were required
    IF useThesaurus = TRUE AND useInflectional = TRUE THEN
        RETURN (
            SELECT FT_TBL.JobCandidateID, KEY_TBL.RANK
            FROM HumanResources.JobCandidate AS FT_TBL
            INNER JOIN TABLE(FREETEXTTABLE(HumanResources.JobCandidate, '*', searchString, LANGUAGE => language)) AS KEY_TBL
            ON FT_TBL.JobCandidateID = KEY_TBL.KEY
        )::STRING;
    ELSEIF useThesaurus = TRUE THEN
        LET string = 'FORMSOF(THESAURUS, "' || searchString || '")';
        RETURN (
            SELECT FT_TBL.JobCandidateID, KEY_TBL.RANK
            FROM HumanResources.JobCandidate AS FT_TBL
            INNER JOIN TABLE(CONTAINSTABLE(HumanResources.JobCandidate, '*', string, LANGUAGE => language)) AS KEY_TBL
            ON FT_TBL.JobCandidateID = KEY_TBL.KEY
        )::STRING;
    ELSEIF useInflectional = TRUE THEN
        LET string = 'FORMSOF(INFLECTIONAL, "' || searchString || '")';
        RETURN (
            SELECT FT_TBL.JobCandidateID, KEY_TBL.RANK
            FROM HumanResources.JobCandidate AS FT_TBL
            INNER JOIN TABLE(CONTAINSTABLE(HumanResources.JobCandidate, '*', string, LANGUAGE => language)) AS KEY_TBL
            ON FT_TBL.JobCandidateID = KEY_TBL.KEY
        )::STRING;
    ELSE
        -- Base case, plain CONTAINSTABLE
        LET string = '"' || searchString || '"';
        RETURN (
            SELECT FT_TBL.JobCandidateID, KEY_TBL.RANK
            FROM HumanResources.JobCandidate AS FT_TBL
            INNER JOIN TABLE(CONTAINSTABLE(HumanResources.JobCandidate, '*', string, LANGUAGE => language)) AS KEY_TBL
            ON FT_TBL.JobCandidateID = KEY_TBL.KEY
        )::STRING;
    END IF;

END;
$$;