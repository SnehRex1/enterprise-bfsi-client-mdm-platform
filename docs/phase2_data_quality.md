# Phase 2 — Contracts, Standardization and Data Quality

## Objective

Phase 2 transforms validated raw source-system records into a consistent canonical representation and applies data-quality controls before the data enters the Silver layer.

The phase covers:

1. Source data contracts
2. Contract validation
3. Standardization
4. Canonical client representation
5. Data-quality validation
6. DQ quarantine
7. Reconciliation

---

## 1. Source Contracts

The four simulated source systems are:

- Core Banking
- CRM
- KYC
- Wealth

Each source has a YAML contract under:

```text
configs/contracts/