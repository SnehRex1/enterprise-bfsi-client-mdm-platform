/* =====================================================================
   PROJECT: Enterprise BFSI Client MDM Platform
   Metadata-driven ADF ingestion

   PURPOSE
     Creates dbo.adf_ingestion_control, the configuration table that tells
     ADF which source files to copy and where to land them in ADLS.

   RUN WHEN
     Connected to the intended Azure SQL database, before seeding metadata.

   SAFETY
     Idempotent for table creation. It does not alter an existing table.
   ===================================================================== */

-- ============================================================
-- ADF metadata-driven ingestion control table
-- ============================================================

IF OBJECT_ID('dbo.adf_ingestion_control', 'U') IS NULL
BEGIN

    CREATE TABLE dbo.adf_ingestion_control
    (
        -- ----------------------------------------------------
        -- Unique row identifier.
        -- SQL automatically generates 1, 2, 3, ...
        -- ----------------------------------------------------
        control_id INT IDENTITY(1,1) NOT NULL,

        -- ----------------------------------------------------
        -- Logical source-system name.
        -- Examples: CORE, CRM, KYC, WEALTH
        -- ----------------------------------------------------
        source_system VARCHAR(20) NOT NULL,

        -- ----------------------------------------------------
        -- SOURCE LOCATION
        -- Where ADF should read the file from.
        -- ----------------------------------------------------
        source_container VARCHAR(100) NOT NULL,
        source_folder    VARCHAR(255) NOT NULL,
        source_file      VARCHAR(255) NOT NULL,

        -- ----------------------------------------------------
        -- TARGET LOCATION
        -- Where ADF should write the file.
        -- ----------------------------------------------------
        target_container VARCHAR(100) NOT NULL,
        target_folder    VARCHAR(255) NOT NULL,
        target_file      VARCHAR(255) NOT NULL,

        -- ----------------------------------------------------
        -- Current ingestion mode.
        -- We are doing FULL loads
        -- ----------------------------------------------------
        load_type VARCHAR(20) NOT NULL
            CONSTRAINT DF_adf_ingestion_load_type
            DEFAULT ('FULL'),

        -- ----------------------------------------------------
        -- 1 = process this metadata row
        -- 0 = ignore this metadata row
        -- ----------------------------------------------------
        is_active BIT NOT NULL
            CONSTRAINT DF_adf_ingestion_is_active
            DEFAULT (1),

        -- ----------------------------------------------------
        -- Controls deterministic processing order.
        -- ----------------------------------------------------
        load_order INT NOT NULL,

        -- ----------------------------------------------------
        -- Primary key.
        -- Every control row gets a unique control_id.
        -- ----------------------------------------------------
        CONSTRAINT PK_adf_ingestion_control
            PRIMARY KEY (control_id)
    );

END;
GO


-- Verify that the Phase 7 control table exists.
SELECT
    name,
    create_date
FROM sys.tables
WHERE name = 'adf_ingestion_control';
