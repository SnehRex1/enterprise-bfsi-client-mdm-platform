# Enterprise BFSI Client MDM & Data Governance Platform

A reproducible, Azure-based Master Data Management (MDM) reference implementation for resolving fragmented customer records across simulated Core Banking, CRM, KYC, and Wealth systems. The platform standardizes and validates multi-source data, evaluates identity relationships using deterministic and fuzzy matching, creates governed Golden Records, preserves source provenance and an SCD Type 2 history model, and serves the published data through Azure SQL, FastAPI, Streamlit, and Power BI.

> **Scope note:** This is a portfolio/reference implementation using synthetic customer data and simulated source systems. It is not a production banking service and does not contain real customer records. The architecture is frozen at V4; this README documents the implemented system and its verified results without implying that every production-hardening feature is complete.

[![GitHub Actions](https://github.com/SnehRex1/enterprise-bfsi-client-mdm-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/SnehRex1/enterprise-bfsi-client-mdm-platform/actions)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![Cloud](https://img.shields.io/badge/Cloud-Microsoft%20Azure-0078D4)](https://azure.microsoft.com/)
[![Tests](https://img.shields.io/badge/Tests-pytest-informational)](https://docs.pytest.org/)

---

## Table of Contents

- [Business Problem](#business-problem)
- [Architecture](#architecture)
- [Key Results](#key-results)
- [Technology Stack](#technology-stack)
- [End-to-End Data Flow](#end-to-end-data-flow)
- [Data Foundation and Benchmark](#data-foundation-and-benchmark)
- [Data Contracts, Standardization and Quality](#data-contracts-standardization-and-quality)
- [Entity Resolution](#entity-resolution)
- [Stewardship](#stewardship)
- [Survivorship and Golden Records](#survivorship-and-golden-records)
- [Provenance and SCD Type 2 History](#provenance-and-scd-type-2-history)
- [Unity Catalog Governance and Security](#unity-catalog-governance-and-security)
- [Azure SQL Serving Model](#azure-sql-serving-model)
- [FastAPI](#fastapi)
- [Streamlit Application](#streamlit-application)
- [Power BI Dashboards](#power-bi-dashboards)
- [Testing and GitHub Actions](#testing-and-github-actions)
- [Repository Structure](#repository-structure)
- [Local Setup and Running Applications](#local-setup-and-running-applications)
- [Documentation and Evidence](#documentation-and-evidence)
- [Known Limitations and Honest Reporting](#known-limitations-and-honest-reporting)
- [Security and Cost Considerations](#security-and-cost-considerations)
- [Future Acceptance Checklist](#future-acceptance-checklist)

---

## Business Problem

A banking customer may be represented differently in the organization’s operational systems. Core Banking may hold a legal name, CRM may use a shortened name, KYC may hold the compliance name, and Wealth may contain an abbreviated relationship record. Phone numbers, emails, addresses, and dates may also differ in formatting or be missing.

For example:

| System | Example source ID | Example name | Example phone |
|---|---|---|---|
| Core Banking | `C10231` | Rahul Kumar Sharma | `9876543210` |
| CRM | `CRM8892` | Rahul K Sharma | `+91 98765 43210` |
| KYC | `KYC4421` | RAHUL KUMAR SHARMA | `9876543210` |
| Wealth | `W8821` | Rahul Sharma | `9876543210` |

These are illustrative examples. An MDM platform must decide whether records represent the same real-world entity, determine which values should be trusted when sources disagree, and retain traceability to the evidence behind the resulting master record.

The platform separates four different concerns:

1. **Standardization:** make comparable representations of source attributes without erasing the original values.
2. **Entity resolution:** score plausible record pairs and distinguish MATCH, REVIEW, and NO_MATCH outcomes.
3. **Survivorship:** choose a winning value for each Golden Record attribute using an explicit authority and completeness policy.
4. **Governance and serving:** preserve provenance and history, control access to sensitive fields, and expose mastered results through stable interfaces.

---

## Architecture

The system uses Azure Data Factory for metadata-driven ingestion and Gold-to-SQL transfer; Azure Databricks and PySpark for scalable MDM processing; Unity Catalog for governance; Azure SQL as the serving database; and FastAPI, Streamlit, and Power BI for consumption.

![Enterprise BFSI Client MDM & Data Governance Platform architecture](architecture/Enterprise%20BFSI%20Client%20MDM%20Platform%20-%20Architecture%20Diagram.png)

**Download/view the [architecture diagram](architecture/Enterprise%20BFSI%20Client%20MDM%20Platform%20-%20Architecture%20Diagram.png).**

### Architecture at a glance

```text
Banking Digital Twin + GLEIF Golden Copy
                  |
                  v
          Source Simulator
                  |
                  v
       Core / CRM / KYC / Wealth
                  |
                  v
        ADLS Gen2 source/ -> Azure Data Factory
                                  |
                                  v
                            ADLS Gen2 raw/
                                  |
                                  v
                    Databricks + PySpark / Delta Lake
                      Bronze -> Contracts -> Standardization
                                  -> Data Quality / Silver
                                  -> Candidate Blocking
                                  -> Deterministic + Fuzzy Matching
                                  -> MATCH / REVIEW / NO_MATCH
                                  -> Stewardship decisions
                                  -> Accepted identity graph
                                  -> Survivorship / Golden Records
                                  -> Provenance / SCD2 / Gold certification
                                  |
                      Unity Catalog governance (cross-cutting)
                                  |
                                  v
                        ADF Gold-to-SQL pipeline
                                  |
                                  v
                              Azure SQL
                           /      |       \
                          v       v        v
                      FastAPI  Power BI  other approved SQL consumers
                          |
                          v
                       Streamlit
```

Streamlit communicates with FastAPI and does not connect directly to Azure SQL. Power BI imports a bounded serving model rather than the full candidate-pair population. Unity Catalog applies to governed Databricks data and is not a sequential transformation stage.

### Main architectural boundaries

- **Ingestion boundary:** ADF transfers source files using configuration stored in Azure SQL. The ADF copy pipeline is metadata-driven; it does not standardize the CSV contents.
- **Processing boundary:** Databricks performs record validation, standardization, DQ checks, candidate generation, matching, stewardship integration, clustering, survivorship, and publication.
- **Governance boundary:** Unity Catalog provides catalog/schema/table access controls, group-based permissions, PII tags, masking functions, Catalog Explorer lineage and pipeline audit evidence.
- **Serving boundary:** ADF copies curated Gold and supporting operational tables into Azure SQL.
- **Application boundary:** FastAPI implements serving endpoints and decision persistence; Streamlit calls the API; Power BI consumes a small SQL import model.
- **Engineering boundary:** Terraform, pytest and GitHub Actions support infrastructure definition, regression checks and CI. The current workflow is CI, not an Azure deployment pipeline.

---

## Key Results

The FULL benchmark was processed through the recorded cloud run. The counts below are from the verified project checkpoint.

### FULL benchmark and data quality

| Metric | Verified result |
|---|---:|
| Banking Digital Twin individuals | 900,000 |
| Qualifying GLEIF entities | 94,422 |
| Underlying entities | 994,422 |
| Source records | 2,638,899 |
| Contract-valid records | 2,638,894 |
| Contract-quarantined records | 5 |
| DQ-quarantined records | 25 |
| Trusted Silver records | 2,638,869 |

Reconciliation:

```text
2,638,899 source records
= 5 contract quarantines
+ 25 data-quality quarantines
+ 2,638,869 trusted Silver records
```

### FULL entity resolution and mastering

| Metric | Verified result |
|---|---:|
| Candidate pairs | 138,074,372 |
| MATCH candidates | 2,249,077 |
| REVIEW candidates | 159,560 |
| NO_MATCH candidates | 135,665,735 |
| Accepted identity edges at recorded checkpoint | 2,249,078 |
| Master clients / Golden Records | 1,080,592 |
| Source-map rows | 2,638,869 |
| Golden Record attributes | 13 |
| Attribute-level provenance/survivorship rows | 14,047,696 |
| Initial SCD2 history rows | 14,047,696 |
| Gold publication status | `SUCCESS` |
| Gold validation status | `ALL_GOLD_VALIDATIONS_PASSED` |

The accepted-edge count includes 2,249,077 automatic MATCH edges plus one persisted approval in the recorded serving checkpoint. At that checkpoint there were two persisted stewardship decisions total: one approval and one rejection. These are point-in-time evidence counts, not a claim that all REVIEW cases were manually processed.

### Full cloud candidate-pair decision distribution

| Decision | Count | Share of candidate pairs |
|---|---:|---:|
| MATCH | 2,249,077 | 1.6289% |
| REVIEW | 159,560 | 0.1156% |
| NO_MATCH | 135,665,735 | 98.2556% |
| **Total** | **138,074,372** | **100%** |

Percentages are calculated from the FULL candidate-pair denominator. They are not Precision, Recall, or F1 metrics.

### Validation and application checkpoint

- Nine ADF serving Copy activities completed successfully in the recorded Gold-to-SQL run.
- The Azure SQL serving checkpoint contains nine tables with reconciled row counts.
- The Power BI import model contains four SQL tables: `mdm.platform_health` (9 rows), `mdm.pipeline_run` (1), `mdm.match_review` (159,560), and `mdm.entity_resolution_summary` (3).
- The local API regression tests passed: 8 API tests; full pytest suite: 55 tests.
- GitHub Actions CI passed for the recorded Phase 13 evidence commit `c31a558`.

These are recorded results from the project's verification runs, not a claim of continuous production availability.

---

## Technology Stack

| Area | Technology | Responsibility |
|---|---|---|
| Cloud | Microsoft Azure | Managed cloud environment |
| Object storage | Azure Data Lake Storage Gen2 | Source, raw, quarantine and Delta data |
| Ingestion/orchestration | Azure Data Factory | Metadata-driven source-to-raw copies and Gold-to-SQL publishing |
| Processing | Azure Databricks + PySpark | Distributed data processing and MDM algorithms |
| Table format | Delta Lake | Structured, versioned data tables |
| Governance | Unity Catalog | Permissions, metadata, PII classification/masking, lineage |
| Serving database | Azure SQL Database | Relational serving model |
| API | FastAPI | REST endpoints and stewardship decision workflow |
| UI | Streamlit | Client search, Golden Record and match review |
| BI | Power BI | Operational health and entity-resolution analytics |
| Identity and secrets | Microsoft Entra ID, managed identities, Azure Key Vault | Authentication and secure configuration |
| IaC | Terraform | Infrastructure definition |
| Local tests | pytest | Unit and API regression tests |
| CI | GitHub Actions | Compile and test on push/PR |
| Matching | Deterministic rules + fuzzy/explainable scoring | Entity-resolution decisions |
| Reference data | Banking Digital Twin + GLEIF | Synthetic benchmark foundation |

The matching engine does not use an ML or LLM model. Kafka, Event Hubs, Kubernetes, Airflow, Snowflake, AWS, a fifth source system and a third Power BI dashboard are outside the frozen project scope.

---

## End-to-End Data Flow

### 1. Source generation and benchmark isolation

The benchmark combines 900,000 synthetic individuals from the Banking Digital Twin with 94,422 eligible UK legal entities from a frozen GLEIF Level 1 Golden Copy snapshot. The GLEIF filter is country `GB`, entity status `ACTIVE`, and registration status `ISSUED`.

The simulator projects underlying entities into four heterogeneous source schemas. The hidden `entity_key` is stored in the separate ground-truth file and never appears in source-system files or becomes a matching feature. Later, MDM creates its own `MASTER_CLIENT_ID`.

The fixed seed is `42`. The Phase 1 benchmark is frozen; small changes should be tested against DEV rather than casually regenerating FULL.

### 2. Metadata-driven Azure Data Factory ingestion

The ingestion pipeline is `pl_bfsi_mdm_ingest`. Its control metadata is in `dbo.adf_ingestion_control`.

The table defines the source system, source and target containers/folders/files, load type, active flag and load order. ADF looks up active rows, iterates over the configured systems and copies files from `source/` to `raw/`. Four configured sources are handled by the same parameterized pattern.

This design keeps ingestion configuration separate from customer data and makes it easier to add or change ingestion metadata without implementing four unrelated pipelines. The copy operation transfers the files; parsing and transformations take place downstream in Databricks.

### 3. Bronze ingestion

Notebook: `notebooks/databricks/MDM_DATAPLATFORM/01_bronze` (notebook artifacts are organized in the subfolders under the Databricks workspace path).

Bronze reads the four CSV inputs with explicit source schemas and writes Delta tables. It adds metadata such as batch ID, ingestion timestamp and record hash while preserving the source data needed for later investigation. Multiline-aware CSV parsing is important because quoted fields may contain embedded newlines: physical line counts are not the same as logical CSV record counts.

### 4. Contract validation

Four YAML contracts live in `configs/contracts/`:

- `core.yaml`
- `crm.yaml`
- `kyc.yaml`
- `wealth.yaml`

Contracts express expected fields, data types, required columns, row-level nullability, patterns, semantic dates and enumerations only where verified. Contract failures go to quarantine with a failure reason; rows are not silently dropped.

The FULL cloud run recorded 5 contract-quarantined records and 2,638,894 contract-valid records.

### 5. Standardization and canonical representation

Source-specific fields are mapped to common concepts. For example, Core `full_name`, CRM `customer_name`, KYC `legal_name` and Wealth `client_name` map to canonical `name`.

The implementation keeps raw and normalized forms of comparable attributes such as name, DOB, phone, email and address. Source system and source ID remain available for record identity and provenance. Missing values remain missing rather than being invented during standardization.

### 6. Data quality and trusted Silver

DQ checks assess normalized names and identifiers, phone/email/DOB validity, future dates, unrealistic ages, and raw-versus-normalized consistency. DQ is distinct from contract validation: a field can have the correct type and still contain a semantically invalid value.

In the FULL run, DQ quarantined 25 records for normalized-email validation. The resulting trusted population was 2,638,869 records.

### 7. Candidate blocking

Comparing every pair among millions of records would be computationally impractical. Blocking creates plausible candidate pairs from shared keys, such as DOB plus postal code, surname plus DOB, normalized email and phone-based keys.

The FULL implementation uses a compact, key-first approach to reduce shuffle and spill. The final full-value phone blocking configuration generated 138,074,372 candidate pairs from trusted Silver. Blocking is a candidate-generation step, not a decision that the records match.

### 8. Deterministic matching

The implemented exact rules include:

- `lei_exact`
- `tax_id_exact`
- `phone_dob_exact`
- `email_dob_exact`

The FULL cloud run recorded the following rule counts:

| Rule | Count |
|---|---:|
| `phone_dob_exact` | 1,961,486 |
| `email_dob_exact` | 70,298 |
| `tax_id_exact` | 14,567 |
| `lei_exact` | 1,431 |
| **Total recorded rule counts** | **2,047,782** |

These are execution counts, not a full-ground-truth accuracy score.

### 9. Fuzzy matching and explainable scoring

The FULL cloud configuration computes similarity for name, phone, address, email and DOB using Spark-native Levenshtein-based logic. The local DEV reference implementation uses RapidFuzz. The two implementations should not be assumed to have identical behavior without a direct comparative evaluation.

The documented FULL cloud weights are:

| Attribute | Weight |
|---|---:|
| Name | 35% |
| Phone | 25% |
| Address | 20% |
| Email | 10% |
| DOB | 10% |

The matching result retains attribute-level scores, aggregate score, matching rule, decision and an explanation/reason. The documented decision thresholds are:

- `MATCH`: score >= 85
- `REVIEW`: 70 <= score < 85
- `NO_MATCH`: score < 70

The local DEV benchmark previously measured precision 99.9926%, recall 97.4423%, F1 98.7010%, and blocking recall 99.4769% for the validated DEV configuration. **These are DEV metrics, not FULL cloud metrics.** A FULL precision/recall/F1 claim would require a full evaluation against hidden ground truth using the specific FULL matching configuration.

### 10. Human stewardship

REVIEW cases are not automatically merged. A steward examines both source records, the score, matching rule, field-level evidence and explanation, then submits an approval or rejection through the application.

The case records retain state, decision, steward ID, reason and timestamp. The API's transaction checks for an existing decision and returns HTTP 409 for a duplicate decision. An approval or rejection updates the case to `RESOLVED` and inserts a decision-audit row.

At the recorded Azure SQL checkpoint, 159,560 review cases existed and two decisions were persisted: one `APPROVE_MATCH` and one `REJECT_MATCH`. This implies 159,558 unresolved cases at that checkpoint; it does not mean that every review case was handled manually.

### 11. Clustering and master identity

The mastering stage builds an accepted identity graph from automatic MATCH edges and explicit `APPROVE_MATCH` stewardship decisions. REJECT_MATCH, unresolved REVIEW and NO_MATCH edges are excluded.

Connected components group records transitively: if A is accepted as matching B and B matches C, all three may belong to the same cluster even without a direct A-C edge. The FULL cloud implementation used iterative distributed label propagation and converged in five iterations for the recorded graph.

The master registry maps `SOURCE_SYSTEM::SOURCE_ID` to `MASTER_CLIENT_ID`. The initial FULL run produced 1,080,592 master identities from 2,638,869 trusted source records. Registry reuse logic exists, but cross-run master-ID stability has not yet been empirically demonstrated by the initial FULL run.

### 12. Attribute-level survivorship

A master record is not created by selecting one entire source row. Each Golden Record attribute is selected independently according to the project policy.

Source authority is:

| Source | Authority score |
|---|---:|
| KYC | 4 |
| Core | 3 |
| CRM | 2 |
| Wealth | 1 |

The documented ranking dimensions are source authority, verification, recency, completeness, match confidence and deterministic tie-breakers. Verification is inferred from the presence of `verification_date`; a missing recency value uses the configured fallback date `1900-01-01`.

The 13 Golden Record attributes are:

`name`, `dob`, `phone`, `email`, `address`, `tax_id`, `lei`, `segment`, `kyc_status`, `verification_date`, `aum`, `risk_profile`, and `relationship_manager`.

The authority policy is specific to this project; it is not presented as a universal banking standard.

### 13. Provenance, source map and SCD Type 2

The mastering outputs include:

- `MASTER_CLIENT`: current Golden Record values.
- `CLIENT_SOURCE_MAP`: mapping from source system/ID to the master.
- `MASTER_CLIENT_ATTRIBUTE`: winning value, winning source and survivorship reason for each master attribute.
- `SURVIVORSHIP_AUDIT`: attribute-level selection audit.
- `MASTER_CLIENT_HISTORY`: SCD Type 2 attribute history.

The FULL outputs contain 1,080,592 masters, 2,638,869 source mappings and 14,047,696 attribute-level provenance/survivorship rows. The audit/history grain is 13 attributes per master:

`1,080,592 × 13 = 14,047,696`.

SCD2 stores effective date, expiry date and current-row state. The initial FULL load produced 14,047,696 current rows and zero expired rows, as expected for an initial load. The later-run expiration logic exists, but a subsequent changed-value run has not been verified as empirical evidence of expiry behavior.

### 14. Gold certification and publication

The `08_gold_publish` stage validates the certified Gold boundary. Checks include master-ID uniqueness, source-map uniqueness and coverage, provenance completeness, current-history consistency and reference integrity.

The recorded FULL publication audit reports `SUCCESS` and `ALL_GOLD_VALIDATIONS_PASSED`. The audit is stored in the Databricks pipeline run audit table.

### 15. Unity Catalog governance

The implemented Databricks catalog is `bfsi_mdm_dev`, organized into schemas including `bronze`, `silver`, `gold`, `mdm`, `quarantine` and `audit`.

Governance evidence covers catalog/schema/table permissions, RBAC groups (`mdm_engineers`, `mdm_stewards`, `mdm_analysts`, `mdm_pii_access`), PII tags/classification, masking functions for email/phone/tax ID, Catalog Explorer lineage and pipeline audit.

Masked columns return reduced values for users without the authorized PII group. The serving ADF managed identity has explicit access to read original governed values for the approved Gold-to-SQL transfer.

Catalog Explorer lineage for the Gold master table was verified. Direct SQL queries against Databricks `system.access` lineage/audit tables were permission-limited and are not claimed as verified.

### 16. Azure SQL serving

ADF pipeline `pl_bfsi_mdm_gold_to_sql` transfers curated Gold and supporting operational data into the `mdm` schema. The recorded run had nine successful serving Copy activities.

| Azure SQL table/view | Role | Recorded rows |
|---|---|---:|
| `mdm.master_client` | Current Golden Records | 1,080,592 |
| `mdm.client_source_map` | Source-to-master mapping | 2,638,869 |
| `mdm.client_record` | Canonical trusted source records | 2,638,869 |
| `mdm.match_review` | REVIEW candidate evidence | 159,560 |
| `mdm.stewardship_case` | Review status and decision state | 159,560 |
| `mdm.stewardship_decision` | Persisted stewardship decisions | 2 |
| `mdm.pipeline_run` | Latest publication metadata | 1 |
| `mdm.platform_health` | Health and quality metrics | 9 |
| `mdm.entity_resolution_summary` | MATCH/REVIEW/NO_MATCH aggregates | 3 |

The view `mdm.v_pending_match_review` exposes unresolved review cases. The SQL model is intended for low-latency application lookup and compact reporting, not for repeating distributed matching.

### 17. FastAPI

Application location: `apps/api/`

- `main.py`: endpoint definitions and decision workflow.
- `db.py`: SQLAlchemy/pyodbc connection configuration with `DefaultAzureCredential`.
- `schemas.py`: request and response schemas.

The API does not perform entity resolution, fuzzy matching, clustering, survivorship or Golden Record generation. Those happen upstream in Databricks.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Database connectivity check using `SELECT 1` |
| GET | `/clients/search?q=...` | Bounded master search |
| GET | `/clients/{master_client_id}` | Retrieve complete Golden Record |
| GET | `/clients/{master_client_id}/sources` | Retrieve mapped source records |
| GET | `/matches/pending?limit=...` | Bounded pending-review queue |
| GET | `/matches/{case_id}` | Review evidence, case state and source records |
| POST | `/matches/{case_id}/approve` | Persist an approval |
| POST | `/matches/{case_id}/reject` | Persist a rejection |

Search result limits and request schemas are validated. Duplicate stewardship decisions return HTTP 409. The decision transaction updates `mdm.stewardship_case` and inserts `mdm.stewardship_decision` atomically.

Interactive API documentation is served at `/docs` when the local API is running.

### 18. Streamlit application

Application location: `apps/streamlit/app.py`

Streamlit communicates with FastAPI using HTTP requests. It has three screens:

1. **Client Search:** search mastered clients by ID, name prefix, email or phone.
2. **Golden Record:** inspect a master and its mapped trusted source records.
3. **Match Review:** inspect match score, rule, explanation, individual scores and both records; submit a steward decision with a reason.

The UI does not connect directly to SQL and does not independently run matching or mastering.

### 19. Power BI dashboards

The Power BI report has two intended pages:

- **Platform Health:** source, contract, quarantine, Silver and master counts; accepted identity edges; candidate-pair volume; latest publication/validation status.
- **Entity Resolution:** candidate-pair and decision counts, rates, decision distribution, average score by decision and a Top 50 review worklist.

The imported model contains four tables: `mdm.platform_health`, `mdm.pipeline_run`, `mdm.match_review`, and `mdm.entity_resolution_summary`. Relationships connect `pipeline_run[run_id]` to the related run-level tables. The report uses the maximum candidate-pair total from the three-row summary rather than summing a repeated total three times.

A temporary `TEMP - Validation` page was used to verify imported row counts. It is validation evidence, not a third dashboard. The editable `.pbix` is intentionally ignored by Git because it can contain imported data; the public repository contains the PDF export and screenshots.

---

## Data Foundation and Benchmark

### FULL benchmark

| Population | Count |
|---|---:|
| Banking Digital Twin individuals | 900,000 |
| GLEIF legal entities | 94,422 |
| **Underlying entities** | **994,422** |

The simulator generates these source records:

| Source | Rows |
|---|---:|
| Core Banking | 964,240 |
| CRM | 660,223 |
| KYC | 811,892 |
| Wealth | 202,544 |
| **Total** | **2,638,899** |

The ground-truth file contains 2,638,899 source-to-entity mappings—one mapping for every logical source record.

### Coverage across source systems

| Systems containing an entity | Entities |
|---|---:|
| 1 system | 72,720 |
| 2 systems | 348,465 |
| 3 systems | 475,828 |
| 4 systems | 97,409 |
| **Total** | **994,422** |

### Controlled messiness and benchmark integrity

The synthetic source data includes name/middle-name variation, phone and date formatting variation, address differences, missing attributes, conflicting values and same-source duplicates.

Recorded FULL simulator statistics include:

- Seed: `42`
- Middle names added: `269,177`
- Phone conflicts: `91,743`
- Email conflicts: `40,115`
- Zero-source fallbacks: `2,813`
- Duplicate rows: Core `19,071`, CRM `13,046`, KYC `15,998`, Wealth `4,014`

A blank is not automatically a data-quality error. For example, DOB is not applicable to legal entities and LEI is not applicable to individuals. DQ rules must account for entity type and semantics.

### DEV benchmark

DEV is a smaller 22,000-entity/58,370-record workbench for local development and quick testing. Its source rows were:

| Source | DEV rows |
|---|---:|
| Core | 21,258 |
| CRM | 14,552 |
| KYC | 18,048 |
| Wealth | 4,512 |
| **Total** | **58,370** |

Use DEV for iterations and FULL for acceptance-scale checks. Do not confuse DEV matching metrics with FULL results, and do not regenerate the frozen FULL benchmark for small code changes.

### Data sources

- [Banking Digital Twin](https://github.com/meetnishant/BankingDigitalTwin)
- [GLEIF](https://www.gleif.org/)

See [docs/phase1_benchmark.md](docs/phase1_benchmark.md) for the complete benchmark manifest, source filters, schemas, hash metadata, simulator settings, coverage and freeze policy.

---

## Testing and GitHub Actions

The repository contains tests for configuration/setup, source contracts, standardization, DQ, matching (blocking, deterministic, fuzzy and scoring), survivorship/SCD2 and API behavior.

### Recorded Phase 13 results

```text
python -m pytest tests/test_api.py -q
8 passed

python -m pytest -q
55 passed

python -m compileall -q apps src tests
passed
```

The local TestClient emitted a Starlette deprecation warning related to its HTTP client integration. The suite still passed. The API regression tests mock database operations; they do not require submitting real approvals or rejections to a live SQL database.

### CI workflow

Workflow: `.github/workflows/ci.yml`

It runs on pushes to `main`, pull requests targeting `main`, and manual workflow dispatch. The Ubuntu runner sets up Python 3.11, installs dependencies and ODBC build requirements, compiles the Python code and runs pytest. The job has read-only repository content permissions and does not connect to Azure.

[View GitHub Actions runs](https://github.com/SnehRex1/enterprise-bfsi-client-mdm-platform/actions)

**CI status:** The recorded latest evidence checkpoint `c31a558` had a successful run. A documentation update triggers another run, so check Actions after the README commit.

---

## Repository Structure

The structure below highlights the important tracked project areas. Generated datasets are excluded from Git and therefore do not appear in this tree.

```text
enterprise-bfsi-client-mdm-platform/
├── .github/
│   └── workflows/
│       └── ci.yml
├── architecture/
│   └── Enterprise BFSI Client MDM Platform - Architecture Diagram.png
├── application_pdfs/
│   ├── FastAPI/
│   │   └── BFSI_Client_MDM_API_FastAPI.pdf
│   └── Streamlit/
│       ├── BFSI_Client_MDM_Streamlit_Client_Search.pdf
│       ├── BFSI_Client_MDM_Streamlit_Golden_Record.pdf
│       └── BFSI_Client_MDM_Streamlit_Match_Review.pdf
├── apps/
│   ├── api/
│   │   ├── db.py
│   │   ├── main.py
│   │   └── schemas.py
│   └── streamlit/
│       └── app.py
├── configs/
│   ├── contracts/
│   ├── canonical_mapping.yaml
│   ├── survivorship.yaml
│   ├── config.yaml
│   └── simulator.yaml
├── docs/
│   ├── DATA_DICTIONARY.md
│   ├── PHASE3_ENTITY_RESOLUTION.md
│   ├── PHASE5_SURVIVORSHIP_GOLDEN_RECORD.md
│   ├── architecture.md
│   ├── data-model.md
│   ├── data_contracts.md
│   ├── entity-resolution.md
│   ├── governance.md
│   ├── phase1_benchmark.md
│   └── phase2_data_quality.md
├── notebooks/
│   └── databricks/
│       └── MDM_DATAPLATFORM/
│           ├── 01_bronze/
│           ├── 02_silver/
│           ├── 03_mdm/
│           ├── 04_gold/
│           └── 05_governance/
├── reports/
│   └── powerbi/
│       └── enterprise_bfsi_mdm_powerbi.pdf
├── screenshots/
│   ├── 01_Azure_Infrastructure_and_Storage/
│   ├── 02_Azure_Data_Factory/
│   ├── 03_Databricks_Data_Processing_and_MDM/
│   ├── 04_Unity_Catalog_Governance/
│   ├── 05_Azure_SQL_Serving/
│   ├── 06_Power_BI_Dashboards/
│   ├── 07_Validation_and_Operations/
│   └── 08_CI_and_Acceptance/
├── scripts/
├── sql/
│   └── azure_sql/
│       ├── 01_adf_ingestion/
│       ├── 02_serving/
│       └── 03_validation/
├── src/
│   ├── matching/
│   ├── quality/
│   ├── standardization/
│   ├── survivorship/
│   └── utils/
├── terraform/
├── tests/
│   ├── matching/
│   ├── survivorship/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_contract_validator.py
│   ├── test_dq_checks.py
│   ├── test_setup.py
│   └── test_standardization.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

## Local Setup and Running Applications

### Prerequisites

- Git
- Python 3.11 (the CI version)
- ODBC Driver 18 for SQL Server for a database-backed API session
- Azure CLI and an Azure identity authorized to access the target Azure SQL database for live serving
- Microsoft Azure resources already provisioned and configured for the cloud-backed path

The pytest API suite mocks database operations, so running tests does not require live Azure access.

### 1. Clone the repository

```powershell
git clone https://github.com/SnehRex1/enterprise-bfsi-client-mdm-platform.git
cd enterprise-bfsi-client-mdm-platform
```

### 2. Create the Python virtual environment

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation under your local execution policy, use the environment's Python executable directly or follow your organization's policy instead of weakening system-wide security settings.

### 3. Run tests

```powershell
python -m compileall -q apps src tests
python -m pytest tests/test_api.py -q
python -m pytest -q
```

### 4. Configure Azure SQL access for FastAPI

The database connection uses `DefaultAzureCredential` with Microsoft Entra authentication and requires the correct Azure SQL permissions. Set the target server and database for your environment. Do not put credentials in source control.

```powershell
$env:MDM_SQL_SERVER = "<your-server>.database.windows.net"
$env:MDM_SQL_DATABASE = "<your-database>"
az login
```

Then start the API:

```powershell
python -m uvicorn apps.api.main:app --reload
```

Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the interactive API documentation. The API's `/health` endpoint checks the live database with `SELECT 1`; therefore a healthy response requires working Azure SQL connectivity and permissions.

### 5. Start Streamlit

Open a separate terminal with the same Python environment activated and configure the API URL:

```powershell
$env:MDM_API_URL = "http://127.0.0.1:8000"
python -m streamlit run apps/streamlit/app.py
```

Open the local URL shown by Streamlit. The API must already be running for database-backed application actions.

### 6. Power BI

The repository contains a PDF export for review. The editable `enterprise_bfsi_mdm_powerbi.pbix` is intentionally excluded from Git because it can contain imported data. To edit or refresh the report, use the locally retained PBIX and the appropriate authorized SQL connection.

---

## Documentation and Evidence

### Application walkthrough PDFs

- [FastAPI endpoint walkthrough](application_pdfs/FastAPI/BFSI_Client_MDM_API_FastAPI.pdf)
- [Streamlit — Client Search](application_pdfs/Streamlit/BFSI_Client_MDM_Streamlit_Client_Search.pdf)
- [Streamlit — Golden Record](application_pdfs/Streamlit/BFSI_Client_MDM_Streamlit_Golden_Record.pdf)
- [Streamlit — Match Review](application_pdfs/Streamlit/BFSI_Client_MDM_Streamlit_Match_Review.pdf)
- [Power BI report PDF](reports/powerbi/enterprise_bfsi_mdm_powerbi.pdf)

### Selected visual evidence

#### Azure infrastructure and storage

![Azure resource group and provisioned MDM resources](screenshots/01_Azure_Infrastructure_and_Storage/01_Azure_Resource_Group_Provisioned_MDM_Resources.png)

#### Azure Data Factory ingestion

![ADF metadata-driven source ingestion success](screenshots/02_Azure_Data_Factory/11_ADF_Metadata_Driven_Source_Ingestion_Success.png)

#### Databricks MDM processing

![Databricks entity resolution decisions and matching rules](screenshots/03_Databricks_Data_Processing_and_MDM/18_Databricks_Entity_Resolution_Decisions_and_Matching_Rules.png)

#### Unity Catalog governance

![Unity Catalog MDM catalog and schemas](screenshots/04_Unity_Catalog_Governance/13_Unity_Catalog_MDM_Catalog_and_Schemas.png)

#### Azure SQL serving

![Azure SQL final serving validation](screenshots/05_Azure_SQL_Serving/Azure_SQL_Final_Serving_Validation.png)

#### Power BI — Platform Health

![Power BI Platform Health dashboard](screenshots/06_Power_BI_Dashboards/26_Power_BI_Platform_Health_Dashboard.png)

#### Power BI — Entity Resolution

![Power BI Entity Resolution dashboard](screenshots/06_Power_BI_Dashboards/27_Power_BI_Entity_Resolution_Dashboard.png)

#### Gold publication and validation

![Pipeline run audit and Gold validation status](screenshots/07_Validation_and_Operations/24_Pipeline_Run_Audit_and_Gold_Validation_Status.png)

#### Phase 13 regression tests

![API and full test suite passed](screenshots/08_CI_and_Acceptance/01_API_and_Full_Test_Suite_Passed.png)

#### Phase 13 GitHub Actions

![GitHub Actions CI passed](screenshots/08_CI_and_Acceptance/02_GitHub_Actions_CI_Passed.png)

The repository also contains supporting screenshots for storage, managed identities, ADF linked services, notebook organization, contract/DQ validation, stewardship, survivorship, provenance/SCD2, Gold publication, SQL validation and Power BI row-count verification.

### Technical documentation

- [Phase 1 benchmark manifest](docs/phase1_benchmark.md)
- [Phase 2 data quality](docs/phase2_data_quality.md)
- [Phase 3 entity resolution](docs/PHASE3_ENTITY_RESOLUTION.md)
- [Phase 5 survivorship, Golden Record and SCD2](docs/PHASE5_SURVIVORSHIP_GOLDEN_RECORD.md)
- [Data contracts](docs/data_contracts.md)
- [Data model](docs/data-model.md)
- [Data dictionary](docs/DATA_DICTIONARY.md)
- [Entity resolution](docs/entity-resolution.md)
- [Governance](docs/governance.md)
- [Architecture notes](docs/architecture.md)

---

## Known Limitations and Honest Reporting

- **Synthetic data:** The customer data is synthetic. The system is not connected to actual bank client records.
- **FULL accuracy metrics:** The available precision/recall/F1 figures belong to the local DEV benchmark. Do not present them as FULL cloud metrics without a full hidden-ground-truth evaluation of the FULL matching configuration.
- **Stewardship volume:** 159,560 REVIEW cases were recorded, but only two persisted decisions were evidenced in the recorded Azure SQL checkpoint. The queue size is not a count of manually reviewed cases.
- **SCD2:** The initial FULL load has 14,047,696 current history rows and zero expired rows. The existence of incremental change-handling logic does not by itself prove a later changed-value expiration run.
- **Stable IDs across runs:** The registry-reuse logic exists, but cross-run master-ID stability has not been empirically demonstrated by the initial FULL run.
- **Unity Catalog platform audit:** Catalog Explorer lineage and pipeline audit are verified to the recorded scope. Direct queries against `system.access` lineage/audit tables are not claimed as verified because access was permission-limited.
- **Deployment:** GitHub Actions currently performs compilation and tests. It does not deploy services to Azure.
- **Final report artifact:** The published PDF and screenshots document the two intended dashboards. The editable PBIX remains local/ignored and may contain imported data.
- **Production hardening:** Authentication, secrets, resource sizing, operational monitoring, release control, network restrictions and data-protection obligations would need a separate production readiness review before any real customer-data use.

---

## Security and Cost Considerations

- Do not commit `.env`, passwords, access tokens, service-principal secrets, SQL connection credentials or private source datasets.
- Use managed identities and Microsoft Entra authentication where configured, with only the permissions needed for each service.
- Keep the editable Power BI `.pbix` out of the public repository unless its contents have been explicitly reviewed and approved for publication.
- Review screenshots and PDFs for sensitive values before publication.
- Use DEV for routine iterations and reserve FULL processing for planned acceptance/scale checks.
- Shut down or terminate compute when it is no longer required, following the project's cost-control process.
- Do not run `terraform destroy` or delete Azure resources until required evidence/results have been backed up and the cleanup scope has been explicitly reviewed.

---

## Future Acceptance Checklist

The architecture and most implementation phases are complete to the verified scope. The remaining project-polish tasks tracked in the Phase 13 handoff are:

- Verify the resolved case ID in Streamlit displays the same `RESOLVED` status returned by a fresh API GET.
- Reopen the saved local Power BI PBIX and confirm only Platform Health and Entity Resolution are intended visible pages; ensure the published PDF corresponds to the final report.
- Create/finish the concise demo runbook using existing evidence.
- Complete the final security, repository hygiene and Azure cost review.
- Confirm the latest README commit triggers a successful GitHub Actions run.

These items are acceptance/packaging checks and do not imply that the verified FULL data-processing run needs to be regenerated.

---

## Acknowledgements

- [Banking Digital Twin](https://github.com/meetnishant/BankingDigitalTwin) — synthetic individual/customer foundation.
- [GLEIF](https://www.gleif.org/) — legal-entity reference data.

---

**Project:** Enterprise BFSI Client MDM & Data Governance Platform  
**Architecture:** Frozen V4  
**Primary path:** Azure Data Factory → ADLS Gen2 → Databricks/PySpark + Delta Lake → Unity Catalog governance → Azure SQL → FastAPI / Streamlit / Power BI  
**Matching:** Deterministic rules + fuzzy/explainable scoring; no ML/LLM matching  
**Evaluation:** Hidden ground truth is reserved for benchmark evaluation and is not used as a matching input  
