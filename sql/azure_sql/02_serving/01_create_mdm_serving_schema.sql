/* =====================================================================
   PROJECT: Enterprise BFSI Client MDM Platform
   SCRIPT: 01_create_mdm_serving_schema.sql
   PHASE: 9 — Azure SQL serving layer

   PURPOSE
     Creates the mdm schema and serving tables for golden clients, source
     mappings, trusted source records, match review, stewardship decisions,
     pipeline runs, platform health, and entity-resolution summaries.

   IMPORTANT
     This is a create-if-missing bootstrap, not a migration script. If an
     object already exists, this script will not update its columns or types.
     Review schema changes as explicit migrations instead of dropping tables.
   ===================================================================== */

/* ============================================================
   PHASE 9 — BFSI MDM SERVING SCHEMA
   Azure SQL serving representation of Databricks mastered data
   ============================================================ */


/* ------------------------------------------------------------
   1. Create the mdm schema
   ------------------------------------------------------------ */

IF NOT EXISTS
(
    SELECT 1
    FROM sys.schemas
    WHERE name = 'mdm'
)
BEGIN
    EXEC('CREATE SCHEMA mdm');
END;
GO


/* ------------------------------------------------------------
   2. GOLDEN RECORD
   One row = one MASTER_CLIENT_ID
   ------------------------------------------------------------ */

IF OBJECT_ID('mdm.master_client', 'U') IS NULL
BEGIN

    CREATE TABLE mdm.master_client
    (
        master_client_id      VARCHAR(20)      NOT NULL,
        name                  NVARCHAR(300)    NULL,
        dob                   DATE             NULL,
        phone                 VARCHAR(50)      NULL,
        email                 NVARCHAR(320)    NULL,
        address               NVARCHAR(1000)   NULL,
        tax_id                VARCHAR(100)     NULL,
        lei                   CHAR(20)         NULL,
        segment               VARCHAR(100)     NULL,
        kyc_status            VARCHAR(100)     NULL,
        verification_date     DATE             NULL,
        aum                   DECIMAL(18,2)    NULL,
        risk_profile          VARCHAR(100)     NULL,
        relationship_manager  NVARCHAR(200)    NULL
    );

END;
GO

/* ------------------------------------------------------------
   3. CLIENT SOURCE MAP
   One row = one source record -> one master
   ------------------------------------------------------------ */

IF OBJECT_ID('mdm.client_source_map', 'U') IS NULL
BEGIN

    CREATE TABLE mdm.client_source_map
    (
        master_client_id VARCHAR(20)  NOT NULL,
        source_system    VARCHAR(50)  NOT NULL,
        source_id        VARCHAR(100) NOT NULL
    );

END;
GO

/* ------------------------------------------------------------
   4. TRUSTED CLIENT SOURCE RECORD
   Used by the stewardship UI to inspect source records.
   ------------------------------------------------------------ */

IF OBJECT_ID('mdm.client_record', 'U') IS NULL
BEGIN

    CREATE TABLE mdm.client_record
    (
        record_key                    VARCHAR(160)    NOT NULL,

        source_system                 VARCHAR(50)     NOT NULL,
        source_id                     VARCHAR(100)    NOT NULL,

        name                          NVARCHAR(300)   NULL,
        normalized_name               NVARCHAR(300)   NULL,

        dob                           DATE            NULL,
        normalized_dob                DATE            NULL,

        phone                         VARCHAR(50)     NULL,
        normalized_phone              VARCHAR(50)     NULL,

        email                         NVARCHAR(320)   NULL,
        normalized_email              NVARCHAR(320)   NULL,

        address                       NVARCHAR(1000)  NULL,
        normalized_address            NVARCHAR(1000)  NULL,

        tax_id                        VARCHAR(100)    NULL,
        lei                           CHAR(20)        NULL,

        account_id                    VARCHAR(100)    NULL,
        branch_id                     VARCHAR(100)    NULL,

        segment                       VARCHAR(100)    NULL,
        kyc_status                    VARCHAR(100)    NULL,

        verification_date             DATE            NULL,
        normalized_verification_date  DATE            NULL,

        aum                           DECIMAL(18,2)   NULL,

        risk_profile                  VARCHAR(100)    NULL,
        relationship_manager          NVARCHAR(200)   NULL
    );

END;
GO

/* ------------------------------------------------------------
   5. REVIEW WORKLIST
   Only REVIEW records are served to the application.
   We do NOT copy 138M candidate rows.
   ------------------------------------------------------------ */

IF OBJECT_ID('mdm.match_review', 'U') IS NULL
BEGIN

    CREATE TABLE mdm.match_review
    (
        case_id        VARCHAR(64)     NOT NULL,

        record_key_a   VARCHAR(160)    NOT NULL,
        record_key_b   VARCHAR(160)    NOT NULL,

        name_score     DECIMAL(9,4)    NULL,
        address_score  DECIMAL(9,4)    NULL,
        phone_score    DECIMAL(9,4)    NULL,
        email_score    DECIMAL(9,4)    NULL,
        dob_score      DECIMAL(9,4)    NULL,

        match_score    DECIMAL(9,4)    NULL,

        matching_rule  VARCHAR(100)    NULL,
        match_reason   NVARCHAR(1000)  NULL,
        decision       VARCHAR(30)     NOT NULL
    );

END;
GO

/* ------------------------------------------------------------
   6. STEWARDSHIP CASE
   Operational review record.
   ------------------------------------------------------------ */

IF OBJECT_ID('mdm.stewardship_case', 'U') IS NULL
BEGIN

    CREATE TABLE mdm.stewardship_case
    (
        case_id             VARCHAR(64)     NOT NULL,

        record_key_a        VARCHAR(160)    NOT NULL,
        record_key_b        VARCHAR(160)    NOT NULL,

        match_score         DECIMAL(9,4)    NULL,
        matching_rule       VARCHAR(100)    NULL,

        status               VARCHAR(50)    NULL,
        steward_id           VARCHAR(200)   NULL,

        decision             VARCHAR(50)    NULL,
        decision_reason     NVARCHAR(1000) NULL,
        decision_timestamp  DATETIME2(3)    NULL,

        created_at          DATETIME2(3)    NULL
    );

END;
GO

/* ------------------------------------------------------------
   7. STEWARDSHIP DECISION AUDIT
   Every application decision becomes an explicit event.
   ------------------------------------------------------------ */


IF OBJECT_ID('mdm.stewardship_decision', 'U') IS NULL
BEGIN

    CREATE TABLE mdm.stewardship_decision
    (
        decision_id        BIGINT IDENTITY(1,1) NOT NULL,
        case_id            VARCHAR(64)          NOT NULL,
        decision           VARCHAR(50)          NOT NULL,
        decision_reason    NVARCHAR(1000)       NULL,
        steward_id         VARCHAR(200)         NULL,
        decision_timestamp DATETIME2(3)         NOT NULL
            DEFAULT SYSUTCDATETIME()
    );

END;
GO

/* ------------------------------------------------------------
   8. PIPELINE RUN
   Latest Gold publication metadata.
   ------------------------------------------------------------ */

IF OBJECT_ID('mdm.pipeline_run', 'U') IS NULL
BEGIN

    CREATE TABLE mdm.pipeline_run
    (
        run_id                    VARCHAR(64)    NOT NULL,

        master_client_rows        BIGINT         NULL,
        source_map_rows           BIGINT         NULL,
        provenance_rows           BIGINT         NULL,
        survivorship_audit_rows   BIGINT         NULL,

        history_rows              BIGINT         NULL,
        current_history_rows      BIGINT         NULL,

        status                    VARCHAR(50)    NULL,
        validation_status         VARCHAR(200)   NULL,

        published_at              DATETIME2(3)   NULL
    );

END;
GO

/* ------------------------------------------------------------
   9. PLATFORM HEALTH
   Small serving table for Power BI.
   ------------------------------------------------------------ */

IF OBJECT_ID('mdm.platform_health', 'U') IS NULL
BEGIN

    CREATE TABLE mdm.platform_health
    (
        run_id        VARCHAR(64)     NOT NULL,
        metric_name   VARCHAR(100)    NOT NULL,
        metric_value  BIGINT          NULL,
        metric_text   NVARCHAR(200)   NULL,
        captured_at   DATETIME2(3)    NOT NULL
            DEFAULT SYSUTCDATETIME()
    );

END;
GO

/* ------------------------------------------------------------
   10. ENTITY RESOLUTION SUMMARY
   Only aggregated ER information goes to SQL.
   ------------------------------------------------------------ */

IF OBJECT_ID('mdm.entity_resolution_summary', 'U') IS NULL
BEGIN

    CREATE TABLE mdm.entity_resolution_summary
    (
        run_id             VARCHAR(64)    NOT NULL,
        decision            VARCHAR(30)    NOT NULL,

        record_count        BIGINT         NOT NULL,
        decision_pct        DECIMAL(9,4)   NULL,
        avg_match_score     DECIMAL(9,4)   NULL,

        candidate_pairs     BIGINT         NOT NULL,

        captured_at         DATETIME2(3)   NOT NULL
            DEFAULT SYSUTCDATETIME()
    );

END;
GO
