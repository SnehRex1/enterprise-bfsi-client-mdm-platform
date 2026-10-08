# Enterprise BFSI Client MDM & Data Governance Platform

BFSI-focused Master Data Management platform for resolving fragmented
client records across simulated Core Banking, CRM, KYC and Wealth systems.


What the project is:

An enterprise BFSI Master Data Management platform that ingests inconsistent
client records from multiple simulated banking systems, determines which
records represent the same real-world client, creates one trusted Golden
Record, preserves provenance and history, and exposes governed master data.


Primary business problem:

    Core Banking
    CRM
    KYC
    Wealth
        ↓
    inconsistent representations
        ↓
    MDM
        ↓
    one trusted client identity

Example:

    Core Banking : C10231  | Rahul Kumar Sharma | 9876543210
    CRM          : CRM8892 | Rahul K Sharma      | +91 98765 43210
    KYC          : KYC4421 | RAHUL KUMAR SHARMA  | 9876543210
    Wealth       : W8821   | Rahul Sharma        | 9876543210

Later the MDM platform should determine all of these belong to one client.


## 3. FROZEN END-TO-END ARCHITECTURE


<img width="1408" height="768" alt="Gemini_Generated_Image_uvmi21uvmi21uvmi (2)" src="https://github.com/user-attachments/assets/1efbe395-6efd-49c6-8c52-b1217f345896" />


    Banking Digital Twin + GLEIF
                ↓
         Source Simulator
                ↓
      Core / CRM / KYC / Wealth
                ↓
      Azure Data Factory
       metadata-driven ingestion
                ↓
             ADLS Gen2
       raw → bronze
                ↓
       Contract Validation
          ↙             ↘
       pass          quarantine
         ↓
    Standardization
         ↓
    Canonical Client Representation
         ↓
    Data Quality
       ↙       ↘
     pass    quarantine
       ↓
     Silver
       ↓
    Candidate Blocking
       ↓
    Deterministic Matching
       ↓
    Fuzzy Matching
       ↓
    Explainable Scoring
       ↓
    MATCH / REVIEW / NO MATCH
       ↓
    Stewardship for REVIEW
       ↓
    Survivorship
       ↓
    Golden Record
     + Provenance
     + Source Map
     + SCD2 History
       ↓
    Delta Gold
       ↓
    Unity Catalog Governance
       ↓
    Azure SQL Serving
       ↓
    FastAPI / Streamlit / Power BI



## 4. FROZEN TECHNOLOGY STACK


Cloud:
    Azure

Orchestration:
    Azure Data Factory

Storage:
    ADLS Gen2

Processing:
    Azure Databricks + PySpark

Table format:
    Delta Lake

Governance:
    Unity Catalog

Database:
    Azure SQL

API:
    FastAPI

UI:
    Streamlit

Analytics:
    Power BI

Security:
    Azure Key Vault + Managed Identity

Infrastructure as Code:
    Terraform

Testing:
    pytest

CI/CD:
    GitHub Actions

Matching:
    Deterministic + fuzzy/explainable entity resolution
    NO ML/LLM matching

Data:
    Banking Digital Twin + GLEIF




## Status

## Phase 0 — Repository and environment setup.

## Architecture

Public BFSI data
→ Source Simulator
→ Core / CRM / KYC / Wealth
→ Data Engineering Pipeline
→ Entity Resolution
→ Golden Record
→ Governance
→ Serving

## Phase 1 — Banking Digital Twin + GLEIF + Source Simulator

Phase 1 establishes the reproducible data foundation for the MDM platform.

The benchmark combines:

- **900,000** synthetic individual customers from the Banking Digital Twin
- **94,422** GB legal entities from a frozen GLEIF Level-1 Golden Copy snapshot
- **994,422** underlying entities in total
- **2,638,899** heterogeneous source records across four simulated banking systems

### Source systems

| Source | Approximate role | Output |
|---|---|---|
| Core Banking | Primary banking/customer record | `core_customers.csv` |
| CRM | Customer relationship record | `crm_customers.csv` |
| KYC | Identity/compliance record | `kyc_customers.csv` |
| Wealth | Investment/wealth relationship record | `wealth_customers.csv` |

The simulator intentionally introduces realistic heterogeneity:

- Different source-specific schemas and field names
- Name representation differences
- Phone and date-format differences
- Address variation
- Missing attributes
- Conflicting values
- Same-source duplicate records
- Legal entities with GLEIF LEIs

### Ground truth

A hidden `entity_key` identifies the underlying entity that produced each source record. It is stored only in:

`data/ground_truth/ground_truth.csv`

The source-system datasets never contain `entity_key`, so the later entity-resolution engine must infer the relationships from the available attributes rather than reading the answer key.

`MASTER_CLIENT_ID` is intentionally not created in Phase 1. It is generated later during Golden Record construction.

### Reproducibility

The simulator uses a fixed random seed of **42** and a frozen GLEIF snapshot. The Phase 1 benchmark is validated before being frozen so later entity-resolution experiments can be compared against the same underlying dataset.

### Validation

The final Phase 1 validation passed for:

- Source schemas
- Source-ID sequencing
- Ground-truth reconciliation
- Cross-system coverage
- Hidden `entity_key` isolation
- Duplicate generation
- Missing-value generation
- Conflict generation
- Simulator metadata consistency

Generated datasets are intentionally excluded from Git. Only the code, configuration, documentation and infrastructure definitions are version controlled.

### Data sources

**Banking Digital Twin**

https://github.com/meetnishant/BankingDigitalTwin

**GLEIF**

https://www.gleif.org/

See `docs/phase1_benchmark.md` for the benchmark definition, source filters, simulator configuration and final statistics.
