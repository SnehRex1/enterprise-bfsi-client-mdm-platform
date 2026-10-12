/* =====================================================================
   PROJECT: Enterprise BFSI Client MDM Platform
   SCRIPT: 04_validate_stewardship_decisions.sql
   PHASE: 10 / 11 — stewardship API and audit verification

   PURPOSE
     Checks selected known test case IDs in stewardship_decision and
     stewardship_case after approval/rejection actions.

   NOTE
     The case IDs below came from the uploaded test script. If the test data
     is reseeded or IDs change, replace them with the current test case IDs.
     Empty results are not a SQL error; they mean those IDs were not found.
   ===================================================================== */

SELECT
    case_id,
    decision,
    steward_id,
    decision_reason,
    decision_timestamp
FROM mdm.stewardship_decision
WHERE case_id IN (
    'e754fbc0de2a33fbc483ef76e456fca3b4d92454e785ea36315beaff85427bbb',
    '954f9a48f9425fa5c8639b873cdb200ba28bfb4a855313527addc84b3b51b04',
    '33e068d27d9160d8b37fce68323c3f6d66e3eed45d17d303e4ffd6e1187a28be',
    '5e936045594ac4c8e0b0ff027ce392280f19ad1fedd811852eb0ac5376205797'
)
ORDER BY decision_timestamp;


SELECT
    case_id,
    status,
    decision,
    steward_id,
    decision_timestamp
FROM mdm.stewardship_case
WHERE case_id IN (
    '9fe5c2edf74135be2ae6e1e2615538845d7b1330b44255a143daab735031d347',
    '6d52974ab55763d33151dee2ecc9f23d9dcac4ae2a9fd7970fc9d52716af896b'
);



SELECT
    case_id,
    status,
    decision,
    steward_id,
    decision_reason,
    decision_timestamp
FROM mdm.stewardship_case
WHERE case_id IN (
    '70820d0d3fbceeebe86025074e0e2ea09c75414c2a5d78274bdd8b31580c99d5',
    '72f729cb05b5baf8f273655eea1b19fe9192a35cdf2d0622a399733b5cc81055'
)
ORDER BY decision_timestamp DESC;
