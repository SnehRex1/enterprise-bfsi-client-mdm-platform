/* =====================================================================
   PROJECT: Enterprise BFSI Client MDM Platform
   SCRIPT: 01_validate_serving_row_counts.sql
   PHASE: 9 / 12 — Azure SQL serving validation

   PURPOSE
     Returns table counts, pending-review count, decision distributions, and
     the compact health/ER summary tables. These are live counts, not fixed
     expected values; decision counts can change after stewardship activity.

   RUN AFTER
     Gold-to-SQL publication has completed successfully.
   ===================================================================== */

-- Core serving table row counts.
SELECT N'mdm.master_client' AS table_name, COUNT_BIG(*) AS row_count FROM mdm.master_client;
SELECT N'mdm.client_source_map' AS table_name, COUNT_BIG(*) AS row_count FROM mdm.client_source_map;
SELECT N'mdm.client_record' AS table_name, COUNT_BIG(*) AS row_count FROM mdm.client_record;
SELECT N'mdm.match_review' AS table_name, COUNT_BIG(*) AS row_count FROM mdm.match_review;
SELECT N'mdm.stewardship_case' AS table_name, COUNT_BIG(*) AS row_count FROM mdm.stewardship_case;
SELECT N'mdm.stewardship_decision' AS table_name, COUNT_BIG(*) AS row_count FROM mdm.stewardship_decision;
SELECT N'mdm.pipeline_run' AS table_name, COUNT_BIG(*) AS row_count FROM mdm.pipeline_run;
SELECT N'mdm.platform_health' AS table_name, COUNT_BIG(*) AS row_count FROM mdm.platform_health;
SELECT N'mdm.entity_resolution_summary' AS table_name, COUNT_BIG(*) AS row_count FROM mdm.entity_resolution_summary;

-- The view must exist before running this query.
SELECT COUNT_BIG(*) AS pending_reviews
FROM mdm.v_pending_match_review;

-- Current match-review distribution.
SELECT decision, COUNT_BIG(*) AS row_count
FROM mdm.match_review
GROUP BY decision
ORDER BY decision;

-- Decisions taken on operational stewardship cases.
SELECT decision, COUNT_BIG(*) AS row_count
FROM mdm.stewardship_case
GROUP BY decision
ORDER BY decision;

-- Latest published platform metrics and aggregate ER distribution.
SELECT * FROM mdm.platform_health ORDER BY metric_name;
SELECT * FROM mdm.entity_resolution_summary ORDER BY decision;
