/* =====================================================================
   PROJECT: Enterprise BFSI Client MDM Platform
   SCRIPT: 02_seed_adf_ingestion_control.sql
   PHASE: 7 — metadata-driven ADF ingestion

   PURPOSE
     Registers the CORE, CRM, KYC, and WEALTH source-to-raw file copies.

   EXPECTED PATH MAPPING
     source/core/core_customers.csv   -> raw/core/core_customers.csv
     source/crm/crm_customers.csv     -> raw/crm/crm_customers.csv
     source/kyc/kyc_customers.csv     -> raw/kyc/kyc_customers.csv
     source/wealth/wealth_customers.csv -> raw/wealth/wealth_customers.csv

   SAFETY
     The insert only adds missing source_system + source_file combinations.
     Existing configuration rows are not overwritten. Review existing rows
     manually if any paths or load_order values need to change.
   ===================================================================== */

INSERT INTO dbo.adf_ingestion_control
(
    source_system,
    source_container,
    source_folder,
    source_file,
    target_container,
    target_folder,
    target_file,
    load_type,
    is_active,
    load_order
)
SELECT
    src.source_system,
    src.source_container,
    src.source_folder,
    src.source_file,
    src.target_container,
    src.target_folder,
    src.target_file,
    src.load_type,
    src.is_active,
    src.load_order
FROM
(
    VALUES
        ('CORE',   'source', 'core',   'core_customers.csv',   'raw', 'core',   'core_customers.csv',   'FULL', 1, 1),
        ('CRM',    'source', 'crm',    'crm_customers.csv',    'raw', 'crm',    'crm_customers.csv',    'FULL', 1, 2),
        ('KYC',    'source', 'kyc',    'kyc_customers.csv',    'raw', 'kyc',    'kyc_customers.csv',    'FULL', 1, 3),
        ('WEALTH', 'source', 'wealth', 'wealth_customers.csv', 'raw', 'wealth', 'wealth_customers.csv', 'FULL', 1, 4)
) AS src
(
    source_system, source_container, source_folder, source_file,
    target_container, target_folder, target_file, load_type, is_active, load_order
)
WHERE NOT EXISTS
(
    SELECT 1
    FROM dbo.adf_ingestion_control AS existing
    WHERE existing.source_system = src.source_system
      AND existing.source_file = src.source_file
);
GO

-- Validate active metadata. Expected: four active rows in load_order 1–4.
SELECT
    control_id,
    source_system,
    source_container,
    source_folder,
    source_file,
    target_container,
    target_folder,
    target_file,
    load_type,
    is_active,
    load_order
FROM dbo.adf_ingestion_control
WHERE is_active = 1
ORDER BY load_order;
