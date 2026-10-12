/* =====================================================================
   PROJECT: Enterprise BFSI Client MDM Platform
   SCRIPT: 05_configure_power_bi_readonly_access.sql
   PHASE: 12 — Power BI read-only serving access

   PURPOSE
     Grants SELECT on the four serving tables imported into the Power BI
     report: platform_health, pipeline_run, entity_resolution_summary, and
     match_review.

   IMPORTANT AUTHENTICATION NOTE
     The original file attempted CREATE USER ... WITH PASSWORD = ''. An empty
     password is not a valid setup and has been removed. This script expects
     the pbi_readonly database principal to be created first through your
     approved authentication method (prefer Microsoft Entra ID where possible).
     Do not commit passwords or secrets to source control.
   ===================================================================== */

IF DATABASE_PRINCIPAL_ID(N'pbi_readonly') IS NULL
BEGIN
    ;THROW 51000,
      'Database principal pbi_readonly does not exist. Create it using an approved authentication method, then rerun this grants script.',
      1;
END;
GO

-- Read-only permissions for the two dashboards; no write grants are given.
GRANT SELECT ON OBJECT::mdm.platform_health
    TO [pbi_readonly];
GRANT SELECT ON OBJECT::mdm.pipeline_run
    TO [pbi_readonly];
GRANT SELECT ON OBJECT::mdm.entity_resolution_summary
    TO [pbi_readonly];
GRANT SELECT ON OBJECT::mdm.match_review
    TO [pbi_readonly];
GO

-- Verify the principal exists. Use permission checks or execute-as tests
-- separately if your environment permits impersonation.
SELECT name, type_desc
FROM sys.database_principals
WHERE name = N'pbi_readonly';
