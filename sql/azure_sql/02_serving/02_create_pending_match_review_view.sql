/* =====================================================================
   PROJECT: Enterprise BFSI Client MDM Platform
   SCRIPT: 02_create_pending_match_review_view.sql
   PHASE: 9 — SQL serving / stewardship application

   PURPOSE
     Exposes review cases with no recorded decision, joining the candidate
     review row to its operational stewardship case.

   NOTE
     A row is considered pending when decision is NULL or blank. Review the
     predicate before changing status/decision conventions in the API.
   ===================================================================== */

CREATE OR ALTER VIEW mdm.v_pending_match_review
AS
SELECT
    review.case_id,
    review.record_key_a,
    review.record_key_b,
    review.name_score,
    review.address_score,
    review.phone_score,
    review.email_score,
    review.dob_score,
    review.match_score,
    review.matching_rule,
    review.match_reason,
    stewardship.status,
    stewardship.steward_id,
    stewardship.decision,
    stewardship.decision_reason,
    stewardship.decision_timestamp,
    stewardship.created_at
FROM mdm.match_review AS review
LEFT JOIN mdm.stewardship_case AS stewardship
    ON review.case_id = stewardship.case_id
WHERE stewardship.decision IS NULL
   OR LTRIM(RTRIM(stewardship.decision)) = '';
GO

-- Quick view smoke test. The number changes as cases are resolved.
SELECT COUNT(*) AS pending_reviews
FROM mdm.v_pending_match_review;
