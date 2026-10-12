/* =====================================================================
   PROJECT: Enterprise BFSI Client MDM Platform
   SCRIPT: 03_grant_adf_ingestion_control_read.sql
   PHASE: 7 — ADF managed-identity access

   PURPOSE
     Creates/maps the ADF managed identity database user if needed and grants
     read-only access to the ingestion-control table.

   PRECONDITIONS
     - Run in the target Azure SQL database.
     - The Azure Data Factory managed identity must exist and be resolvable
       by Microsoft Entra ID under the name below.
     - dbo.adf_ingestion_control must already exist.
   ===================================================================== */

IF DATABASE_PRINCIPAL_ID(N'adf-bfsi-mdm-dev') IS NULL
BEGIN
    CREATE USER [adf-bfsi-mdm-dev] FROM EXTERNAL PROVIDER;
END;
GO

-- ADF reads configuration metadata; it does not need to edit the control rows.
GRANT SELECT
ON OBJECT::dbo.adf_ingestion_control
TO [adf-bfsi-mdm-dev];
GO

-- Confirm the database principal exists.
SELECT name, type_desc
FROM sys.database_principals
WHERE name = N'adf-bfsi-mdm-dev';

-- Confirm the explicit object permission.
SELECT
    principal.name AS principal_name,
    permission.permission_name,
    permission.state_desc
FROM sys.database_permissions AS permission
JOIN sys.database_principals AS principal
    ON permission.grantee_principal_id = principal.principal_id
WHERE principal.name = N'adf-bfsi-mdm-dev'
  AND permission.major_id = OBJECT_ID(N'dbo.adf_ingestion_control');
