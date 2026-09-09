# Phase 1 Benchmark Manifest

## Status

Phase 1 data foundation and source simulation are complete.

## Benchmark population

| Population | Count |
|---|---:|
| Banking Digital Twin individuals | 900,000 |
| GLEIF legal entities | 94,422 |
| **Total underlying entities** | **994,422** |

The benchmark intentionally uses the naturally available 94,422 qualifying GLEIF entities rather than padding the population to an arbitrary round number.

## Source data

### Banking Digital Twin

Used as the synthetic banking/customer foundation.

Generated population:
- 900,000 individuals

Extracted artifact:

`data/external/banking_digital_twin/base_individuals.csv`

### GLEIF

Used as the legal-entity reference population.

Golden Copy snapshot:

`20260909-1600-gleif-goldencopy-lei2-golden-copy.csv.zip`

Selection criteria:

- Country = `GB`
- Entity status = `ACTIVE`
- Registration status = `ISSUED`

Selected entities:
- 94,422

Prepared artifact:

`data/external/gleif/gleif_entities.csv`

Metadata:

`data/external/gleif/snapshot_metadata.json`

Recorded source ZIP SHA-256:

`27859bf727abbf0aec8f95a24d668f39a252d617171db77ea8b7adcc04368195`

Recorded output SHA-256:

`b799408d75857ada03c68419da52ca8a6c4bb851a5bb169314fed46dc2f56894`

## Simulator configuration

Random seed:

`42`

### Source appearance rates

| Source | Appearance rate |
|---|---:|
| Core | 95% |
| CRM | 65% |
| KYC | 80% |
| Wealth | 20% |

### Messiness configuration

| Mechanism | Rate |
|---|---:|
| Middle-name generation | 30% |
| General missingness | 4% |
| CRM missing DOB | 8% |
| Wealth missing email | 15% |
| Conflict rate | 5% |
| Duplicate rate | 2% |

## Final source-system benchmark

| Source | Rows |
|---|---:|
| Core | 964,240 |
| CRM | 660,223 |
| KYC | 811,892 |
| Wealth | 202,544 |
| **Total** | **2,638,899** |

The ground-truth file contains exactly 2,638,899 mappings, matching the total source-row count.

## Source schemas

### Core

`customer_id, full_name, dob, phone, email, address, account_id, branch_id`

### CRM

`crm_customer_id, customer_name, date_of_birth, mobile, email_address, residential_address, segment`

### KYC

`kyc_id, legal_name, dob, tax_id, phone, address, kyc_status, verification_date, LEI`

### Wealth

`client_id, client_name, dob, phone, email, address, aum, risk_profile, relationship_manager`

## Ground truth

Artifact:

`data/ground_truth/ground_truth.csv`

Schema:

`source_system, source_id, entity_key`

`entity_key` is the simulator's hidden truth identifier.

It is not exposed in any source-system file.

`MASTER_CLIENT_ID` does not exist at Phase 1; it will be created later during Golden Record construction.

## Final simulator statistics

These values are from the final simulator run:

- Individuals processed: 900,000
- Legal entities processed: 94,422
- Hidden entities: 994,422
- Middle names generated: 269,177
- Phone conflicts: 91,743
- Email conflicts: 40,115
- Zero-source fallbacks: 2,813

### Duplicate rows

| Source | Duplicate rows |
|---|---:|
| Core | 19,071 |
| CRM | 13,046 |
| KYC | 15,998 |
| Wealth | 4,014 |

### Entities by source-system coverage

| Number of source systems | Entities |
|---|---:|
| 1 | 72,720 |
| 2 | 348,465 |
| 3 | 475,828 |
| 4 | 97,409 |
| **Total** | **994,422** |

## Validation status

The final validator completed successfully.

Checks passed:

- Source schemas
- Source ID sequencing
- Ground-truth reconciliation
- Cross-system coverage
- `entity_key` leakage check
- `master_id` leakage check
- Simulator metadata consistency
- Presence of missing values
- Presence of conflicts
- Presence of duplicates

Final validation result:

`ALL PHASE 1 VALIDATIONS PASSED.`

## Reproducibility

A smoke-test run was executed twice with the same seed and limits, and the SHA-256 hashes of all five generated files matched between runs.

Final benchmark file hashes should be recorded separately after the final repository verification if desired.

## Freeze policy

Once the Phase 1 commit is pushed, the following become frozen for the benchmark:

- Seed
- BDT input population
- GLEIF snapshot
- Source schemas
- Appearance rates
- Messiness rates
- Simulator logic
- Ground truth

Any change to these creates a new benchmark version rather than modifying the existing benchmark.

## Phase 1 output tree

```text
data/
├── external/
│   ├── banking_digital_twin/
│   │   ├── BankingDigitalTwin/
│   │   └── base_individuals.csv
│   └── gleif/
│       ├── golden_copy/
│       │   └── 20260909-1600-gleif-goldencopy-lei2-golden-copy.csv.zip
│       ├── gleif_entities.csv
│       └── snapshot_metadata.json
├── source_systems/
│   ├── core/
│   │   └── core_customers.csv
│   ├── crm/
│   │   └── crm_customers.csv
│   ├── kyc/
│   │   └── kyc_customers.csv
│   └── wealth/
│       └── wealth_customers.csv
└── ground_truth/
    ├── ground_truth.csv
    └── simulator_run_metadata.json
```
