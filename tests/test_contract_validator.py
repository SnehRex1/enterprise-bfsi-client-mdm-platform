"""
Unit tests for the generic Phase 2 contract validator.
"""

import csv
from pathlib import Path

import yaml

from src.quality.contract_validator import (
    validate_source_file,
)


def write_contract(
    path: Path,
):
    """
    Create a tiny test contract.

    We don't use the real Core/CRM/KYC/Wealth contracts
    here because unit tests should isolate the validator
    behavior itself.
    """

    contract = {

        "contract": {

            "name": "test_contract",

            "version": "1.0.0",

            "source_system": "test",

            "source_owner": "Test",

            "primary_key": "id",

            "fields": {

                "id": {
                    "type": "string",
                    "required": True,
                    "nullable": False,
                    "pattern": r"^T[0-9]{3}$",
                },

                "name": {
                    "type": "string",
                    "required": True,
                    "nullable": False,
                },

                "score": {
                    "type": "float",
                    "required": True,
                    "nullable": False,
                },

            },

        }

    }

    # Write the Python dictionary as valid YAML.
    path.write_text(
        yaml.safe_dump(
            contract,
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def write_csv(
    path: Path,
    rows: list[dict],
):
    """
    Write a small CSV file.
    """

    fieldnames = [
        "id",
        "name",
        "score",
    ]

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


def test_valid_rows_pass(
    tmp_path,
):
    """
    Valid records should appear in the validated output.
    """

    contract_path = (
        tmp_path / "contract.yaml"
    )

    source_path = (
        tmp_path / "source.csv"
    )

    validated_path = (
        tmp_path / "validated.csv"
    )

    quarantine_path = (
        tmp_path / "quarantine.csv"
    )

    report_path = (
        tmp_path / "report.json"
    )

    write_contract(
        contract_path
    )

    write_csv(
        source_path,
        [
            {
                "id": "T001",
                "name": "Alice",
                "score": "10.5",
            },
            {
                "id": "T002",
                "name": "Bob",
                "score": "20.0",
            },
        ],
    )

    report = validate_source_file(
        source_path=source_path,
        contract_path=contract_path,
        validated_output_path=(
            validated_path
        ),
        quarantine_output_path=(
            quarantine_path
        ),
        report_path=report_path,
    )

    assert report[
        "total_rows"
    ] == 2

    assert report[
        "passed_rows"
    ] == 2

    assert report[
        "quarantined_rows"
    ] == 0

    assert report[
        "reconciliation"
    ] == "PASS"


def test_invalid_row_goes_to_quarantine(
    tmp_path,
):
    """
    Invalid records must not disappear.

    They must go into quarantine.
    """

    contract_path = (
        tmp_path / "contract.yaml"
    )

    source_path = (
        tmp_path / "source.csv"
    )

    validated_path = (
        tmp_path / "validated.csv"
    )

    quarantine_path = (
        tmp_path / "quarantine.csv"
    )

    report_path = (
        tmp_path / "report.json"
    )

    write_contract(
        contract_path
    )

    write_csv(
        source_path,
        [
            {
                # Invalid:
                # required + non-nullable
                "id": "",

                "name": "Broken",

                # Invalid float
                "score": "NOT_A_NUMBER",
            }
        ],
    )

    report = validate_source_file(
        source_path=source_path,
        contract_path=contract_path,
        validated_output_path=(
            validated_path
        ),
        quarantine_output_path=(
            quarantine_path
        ),
        report_path=report_path,
    )

    assert report[
        "total_rows"
    ] == 1

    assert report[
        "passed_rows"
    ] == 0

    assert report[
        "quarantined_rows"
    ] == 1

    assert report[
        "reconciliation"
    ] == "PASS"

    # Read the quarantine file and make sure
    # the explanation exists.
    quarantine_text = (
        quarantine_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        "failure_reason"
        in quarantine_text
    )

    assert (
        "required value is blank"
        in quarantine_text
    )


def test_reconciliation(
    tmp_path,
):
    """
    Test the critical invariant:

        input = passed + quarantined
    """

    contract_path = (
        tmp_path / "contract.yaml"
    )

    source_path = (
        tmp_path / "source.csv"
    )

    validated_path = (
        tmp_path / "validated.csv"
    )

    quarantine_path = (
        tmp_path / "quarantine.csv"
    )

    report_path = (
        tmp_path / "report.json"
    )

    write_contract(
        contract_path
    )

    write_csv(
        source_path,
        [
            {
                "id": "T001",
                "name": "Good",
                "score": "10",
            },
            {
                "id": "",
                "name": "Bad",
                "score": "20",
            },
        ],
    )

    report = validate_source_file(
        source_path=source_path,
        contract_path=contract_path,
        validated_output_path=(
            validated_path
        ),
        quarantine_output_path=(
            quarantine_path
        ),
        report_path=report_path,
    )

    assert (
        report["total_rows"]
        ==
        report["passed_rows"]
        +
        report["quarantined_rows"]
    )


def test_nullable_field_can_be_blank(
    tmp_path,
):
    """
    A nullable field should NOT cause quarantine.

    This protects one of our most important contract concepts:
        required != non-nullable
    """

    contract = {

        "contract": {

            "name": "nullable_test",

            "version": "1.0.0",

            "source_system": "test",

            "source_owner": "Test",

            "primary_key": "id",

            "fields": {

                "id": {
                    "type": "string",
                    "required": True,
                    "nullable": False,
                },

                "optional_field": {
                    "type": "string",
                    "required": True,
                    "nullable": True,
                },

            },

        }

    }

    contract_path = (
        tmp_path / "contract.yaml"
    )

    source_path = (
        tmp_path / "source.csv"
    )

    validated_path = (
        tmp_path / "validated.csv"
    )

    quarantine_path = (
        tmp_path / "quarantine.csv"
    )

    report_path = (
        tmp_path / "report.json"
    )

    contract_path.write_text(
        yaml.safe_dump(
            contract,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    with source_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "id",
                "optional_field",
            ],
        )

        writer.writeheader()

        writer.writerow(
            {
                "id": "X1",
                "optional_field": "",
            }
        )

    report = validate_source_file(
        source_path=source_path,
        contract_path=contract_path,
        validated_output_path=(
            validated_path
        ),
        quarantine_output_path=(
            quarantine_path
        ),
        report_path=report_path,
    )

    assert (
        report["passed_rows"]
        == 1
    )

    assert (
        report["quarantined_rows"]
        == 0
    )