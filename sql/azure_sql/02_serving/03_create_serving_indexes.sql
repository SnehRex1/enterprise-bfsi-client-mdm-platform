/* =====================================================================
   PROJECT: Enterprise BFSI Client MDM Platform
   SCRIPT: 03_create_serving_indexes.sql
   PHASE: 9.20 — Azure SQL serving indexes

   PURPOSE
     Adds indexes that support Golden Record lookup, source mapping, trusted
     record lookup, match review, stewardship, and pipeline-run queries.

   RUN WHEN
     After the mdm tables exist. For the initial load, it is often preferable
     to bulk-load serving data before building indexes.

   SAFETY
     Each index is created only when an index with that name does not already
     exist on the target table. Existing indexes are not rebuilt or changed.
     Unique indexes will fail if the target key values are not unique.
   ===================================================================== */

-- 1. GOLDEN RECORD -------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'mdm.master_client') AND name = N'IX_master_client_id')
    CREATE UNIQUE CLUSTERED INDEX IX_master_client_id
        ON mdm.master_client(master_client_id);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'mdm.master_client') AND name = N'IX_master_client_name')
    CREATE INDEX IX_master_client_name ON mdm.master_client(name);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'mdm.master_client') AND name = N'IX_master_client_email')
    CREATE INDEX IX_master_client_email ON mdm.master_client(email);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'mdm.master_client') AND name = N'IX_master_client_phone')
    CREATE INDEX IX_master_client_phone ON mdm.master_client(phone);

-- 2. SOURCE MAPPING ------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'mdm.client_source_map') AND name = N'IX_client_source_map_source')
    CREATE UNIQUE CLUSTERED INDEX IX_client_source_map_source
        ON mdm.client_source_map(source_system, source_id);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'mdm.client_source_map') AND name = N'IX_client_source_map_master')
    CREATE INDEX IX_client_source_map_master
        ON mdm.client_source_map(master_client_id);

-- 3. TRUSTED SOURCE RECORDS ---------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'mdm.client_record') AND name = N'IX_client_record_key')
    CREATE UNIQUE CLUSTERED INDEX IX_client_record_key
        ON mdm.client_record(record_key);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'mdm.client_record') AND name = N'IX_client_record_source')
    CREATE INDEX IX_client_record_source
        ON mdm.client_record(source_system, source_id);

-- 4. MATCH REVIEW --------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'mdm.match_review') AND name = N'IX_match_review_case')
    CREATE UNIQUE CLUSTERED INDEX IX_match_review_case
        ON mdm.match_review(case_id);

-- 5. STEWARDSHIP ---------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'mdm.stewardship_case') AND name = N'IX_stewardship_case_case')
    CREATE UNIQUE CLUSTERED INDEX IX_stewardship_case_case
        ON mdm.stewardship_case(case_id);

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'mdm.stewardship_case') AND name = N'IX_stewardship_case_decision')
    CREATE INDEX IX_stewardship_case_decision
        ON mdm.stewardship_case(decision);

-- 6. PIPELINE RUN --------------------------------------------------------
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID(N'mdm.pipeline_run') AND name = N'IX_pipeline_run')
    CREATE UNIQUE CLUSTERED INDEX IX_pipeline_run
        ON mdm.pipeline_run(run_id);
GO

-- Verify indexes currently defined on mdm tables.
SELECT
    schema_info.name AS schema_name,
    table_info.name AS table_name,
    index_info.name AS index_name,
    index_info.type_desc,
    index_info.is_unique,
    index_info.is_primary_key
FROM sys.indexes AS index_info
JOIN sys.tables AS table_info
    ON index_info.object_id = table_info.object_id
JOIN sys.schemas AS schema_info
    ON table_info.schema_id = schema_info.schema_id
WHERE schema_info.name = N'mdm'
  AND index_info.index_id > 0
ORDER BY table_info.name, index_info.name;
