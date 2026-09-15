# Phase 5 — Survivorship, Golden Record, Provenance & SCD2

## Objective

Phase 5 converts accepted entity-resolution MATCH relationships into MDM master entities and produces a trusted Golden Record for each master entity.

The flow is:

MATCHED SOURCE RECORDS
→ ENTITY CLUSTERING
→ MASTER_CLIENT_ID
→ ATTRIBUTE-LEVEL SURVIVORSHIP
→ GOLDEN RECORD
→ ATTRIBUTE-LEVEL PROVENANCE
→ CLIENT_SOURCE_MAP
→ SCD TYPE 2 HISTORY

## Input

Phase 5 consumes:

- Canonical Silver records from Phase 2
- Entity-resolution results from Phase 3
- The survivorship policy defined in `configs/survivorship.yaml`

Only records with:

    decision = MATCH

are automatically merged into clusters.

REVIEW records are intentionally excluded from automatic clustering and remain candidates for future stewardship.

NO MATCH records are not merged.

## Entity Clustering

Pairwise MATCH results are converted into connected components using Union-Find.

Every Silver record is initially added as its own cluster.

Accepted MATCH edges then merge connected records.

This means:

    A ↔ B = MATCH
    B ↔ C = MATCH

produces one master entity even when A and C were not directly matched.

Singleton Silver records remain valid master entities.

## Stable MASTER_CLIENT_ID

Master identifiers use the format:

    MC000001
    MC000002
    ...

A registry maps:

    SOURCE_SYSTEM::SOURCE_ID
        →
    MASTER_CLIENT_ID

This preserves master identity across subsequent processing runs.

Potential cases where previously separate master IDs become one cluster are surfaced as merge warnings instead of being silently hidden.

## Survivorship Policy

The initial project policy uses the following source authority:

    KYC   = 4
    CORE  = 3
    CRM   = 2
    WEALTH = 1

Higher authority has higher priority.

The survivorship ranking dimensions are:

1. Source authority
2. Verification
3. Recency
4. Completeness
5. Match confidence

Verification is based on the presence of `verification_date`.

The implementation does not invent a universal KYC-status enumeration because the source data has not established one.

## Attribute-Level Survivorship

The Golden Record is built independently for each attribute.

The system does not simply select one winning source row.

For example:

    name  → KYC
    phone → KYC
    email → CORE
    segment → CRM

can all originate from different source records belonging to the same master entity.

This preserves the strongest available value for each individual Golden Record attribute.

## Golden Record Attributes

The Phase 5 Golden Record contains:

- name
- dob
- phone
- email
- address
- tax_id
- lei
- segment
- kyc_status
- verification_date
- aum
- risk_profile
- relationship_manager

## Provenance

`MASTER_CLIENT_ATTRIBUTE` records:

- MASTER_CLIENT_ID
- attribute name
- attribute value
- winning source system
- winning source ID
- survivorship reason

This provides attribute-level lineage explaining where each Golden Record value came from and why it won.

## CLIENT_SOURCE_MAP

`CLIENT_SOURCE_MAP` maps every source record to its master:

    MASTER_CLIENT_ID
    SOURCE_SYSTEM
    SOURCE_ID

This preserves the relationship between source-system records and the enterprise master entity.

## SCD Type 2

`MASTER_CLIENT_HISTORY` stores attribute history.

Each master/attribute combination contains:

- effective_date
- expiry_date
- is_current

For an initial load, every Golden Record attribute receives a current version.

When an attribute changes in a later run:

1. The existing current version is expired.
2. A new version is created.
3. The new version becomes current.

Unchanged attributes remain unchanged.

## DEV Validation Results

The validated DEV Phase 5 run produced:

| Metric | Result |
|---|---:|
| Silver records | 58,370 |
| Accepted MATCH edges | 54,027 |
| Master clients | 22,407 |
| CLIENT_SOURCE_MAP rows | 58,370 |
| Provenance rows | 291,291 |
| Attributes per master | 13 |
| SCD2 history rows | 291,291 |
| Current SCD2 rows | 291,291 |
| Expired SCD2 rows | 0 |
| Duplicate current SCD2 versions | 0 |

## Integrity Checks

Validated successfully:

- Every MASTER_CLIENT_ID is unique.
- Every source-system/source-ID mapping is unique.
- Every master contains the expected 13 Golden Record attributes.
- Initial SCD2 history contains one current version per master/attribute.
- No duplicate current SCD2 versions exist.
- Full automated test suite passes.

## Test Results

Final test suite:

    47 passed

RapidFuzz dependency was corrected to:

    rapidfuzz==3.14.6

and the dependency file was successfully installed and verified.

## Important Design Boundary

Phase 5 is currently validated against the DEV dataset.

The logic will later be productionized in Azure Databricks using PySpark.

The DEV implementation is intentionally kept straightforward so that the business logic can be validated before cloud productionization.