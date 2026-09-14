# Phase 2 — Data Contracts

## Purpose

Phase 2 defines formal data contracts for the four simulated BFSI
source systems created in Phase 1.

The contracts provide a machine-readable agreement describing the
expected structure and validation rules for each source.

## Source Systems

- Core Banking
- CRM
- KYC
- Wealth Management

## Contract Files

- `configs/contracts/core.yaml`
- `configs/contracts/crm.yaml`
- `configs/contracts/kyc.yaml`
- `configs/contracts/wealth.yaml`

## Contract Definition

Each contract defines:

- source system
- source owner
- contract version
- primary key
- expected fields
- data types
- required fields
- nullability
- structural patterns
- semantic date formats
- allowed values where verified

## Required vs Nullable

`required` describes whether a column must exist.

`nullable` describes whether an individual record may contain a
blank value.

For example:

```yaml
dob:
  required: true
  nullable: true