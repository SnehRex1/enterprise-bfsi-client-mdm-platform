/* =====================================================================
   PROJECT: Enterprise BFSI Client MDM Platform
   SCRIPT: 04_configure_adf_serving_identity_permissions.sql
   PHASE: 9 — ADF Gold-to-Azure-SQL serving

   PURPOSE
     Reproduces the development permissions used by ADF to publish serving
     data and refresh/report on pipeline health.

   SECURITY WARNING
     db_datareader + db_datawriter apply broadly across this database.
     ALTER permissions are powerful and may be needed by a FULL-refresh pattern
     that truncates/recreates data, but they are not least-privilege grants.
     Keep this script scoped to the development identity/database. Review and
     narrow permissions before production use.

   PRECONDITION
     Serving tables under schema mdm must already exist.
   ===================================================================== */

-- Create the database principal only when it does not already exist.
IF DATABASE_PRINCIPAL_ID(N'adf-bfsi-mdm-dev') IS NULL
BEGIN
    CREATE USER [adf-bfsi-mdm-dev] FROM EXTERNAL PROVIDER;
END;
GO

ALTER USER [adf-bfsi-mdm-dev] WITH DEFAULT_SCHEMA = [mdm];
GO

-- The role-membership checks make this section safe to rerun.
IF NOT EXISTS
(
    SELECT 1
    FROM sys.database_role_members AS drm
    JOIN sys.database_principals AS role_principal
        ON role_principal.principal_id = drm.role_principal_id
    JOIN sys.database_principals AS member_principal
        ON member_principal.principal_id = drm.member_principal_id
    WHERE role_principal.name = N'db_datareader'
      AND member_principal.name = N'adf-bfsi-mdm-dev'
)
    ALTER ROLE db_datareader ADD MEMBER [adf-bfsi-mdm-dev];
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.database_role_members AS drm
    JOIN sys.database_principals AS role_principal
        ON role_principal.principal_id = drm.role_principal_id
    JOIN sys.database_principals AS member_principal
        ON member_principal.principal_id = drm.member_principal_id
    WHERE role_principal.name = N'db_datawriter'
      AND member_principal.name = N'adf-bfsi-mdm-dev'
)
    ALTER ROLE db_datawriter ADD MEMBER [adf-bfsi-mdm-dev];
GO

-- Object-level ALTER permissions retained from the existing dev setup.
-- They are not equivalent to ordinary INSERT/UPDATE permission; see warning above.
GRANT ALTER ON OBJECT::mdm.master_client TO [adf-bfsi-mdm-dev];
GRANT ALTER ON OBJECT::mdm.client_source_map TO [adf-bfsi-mdm-dev];
GRANT ALTER ON OBJECT::mdm.match_review TO [adf-bfsi-mdm-dev];
GRANT ALTER ON OBJECT::mdm.client_record TO [adf-bfsi-mdm-dev];
GRANT ALTER ON OBJECT::mdm.stewardship_case TO [adf-bfsi-mdm-dev];
GRANT ALTER ON OBJECT::mdm.stewardship_decision TO [adf-bfsi-mdm-dev];

-- Explicit grants retained for pipeline/monitoring tables.
GRANT SELECT, INSERT, ALTER ON OBJECT::mdm.pipeline_run
    TO [adf-bfsi-mdm-dev];
GRANT SELECT, INSERT, ALTER ON OBJECT::mdm.platform_health
    TO [adf-bfsi-mdm-dev];
GRANT SELECT, INSERT, ALTER ON OBJECT::mdm.entity_resolution_summary
    TO [adf-bfsi-mdm-dev];
GO

-- Verify principal and role memberships.
SELECT name, type_desc, default_schema_name
FROM sys.database_principals
WHERE name = N'adf-bfsi-mdm-dev';

SELECT
    role_principal.name AS role_name,
    member_principal.name AS member_name
FROM sys.database_role_members AS drm
JOIN sys.database_principals AS role_principal
    ON role_principal.principal_id = drm.role_principal_id
JOIN sys.database_principals AS member_principal
    ON member_principal.principal_id = drm.member_principal_id
WHERE member_principal.name = N'adf-bfsi-mdm-dev'
ORDER BY role_principal.name;
