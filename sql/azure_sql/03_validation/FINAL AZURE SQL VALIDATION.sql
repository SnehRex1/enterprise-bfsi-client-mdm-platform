/* ============================================================
    Master clients
   ============================================================ */

SELECT COUNT(*) AS master_client_rows
FROM mdm.master_client;

/* ============================================================
    Source map
   ============================================================ */

SELECT COUNT(*) AS source_map_rows
FROM mdm.client_source_map;

/* ============================================================
    Trusted source records
   ============================================================ */

SELECT COUNT(*) AS client_record_rows
FROM mdm.client_record;

/* ============================================================
    Review
   ============================================================ */

SELECT COUNT(*) AS review_rows
FROM mdm.match_review;

/* ============================================================
    Stewardship
   ============================================================ */

SELECT COUNT(*) AS stewardship_rows
FROM mdm.stewardship_case;

/* ============================================================
    Decision audit
   ============================================================ */

SELECT COUNT(*) AS decision_rows
FROM mdm.stewardship_decision;

/* ============================================================
    Pending review
   ============================================================ */

SELECT COUNT(*) AS pending_reviews
FROM mdm.v_pending_match_review;

/* ============================================================
    Platform health
   ============================================================ */

SELECT *
FROM mdm.platform_health
ORDER BY metric_name;

/* ============================================================
    ER summary
   ============================================================ */

SELECT *
FROM mdm.entity_resolution_summary
ORDER BY decision;