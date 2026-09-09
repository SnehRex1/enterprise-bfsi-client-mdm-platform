# Enterprise BFSI Client MDM & Data Governance Platform

BFSI-focused Master Data Management platform for resolving fragmented
client records across simulated Core Banking, CRM, KYC and Wealth systems.

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
