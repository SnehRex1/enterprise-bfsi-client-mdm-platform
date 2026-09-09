"""
Phase 1 validation.

Validates:
1. Expected source schemas
2. Source record counts
3. Sequential source IDs
4. Ground-truth reconciliation
5. entity_key isolation
6. Cross-system coverage
7. Missing values
8. Simulator statistics
"""

import csv
import json
from collections import defaultdict
from pathlib import Path


SOURCE_FILES = {
    "core": {
        "path": Path(
            "data/source_systems/"
            "core/core_customers.csv"
        ),
        "id_column": "customer_id",
        "prefix": "C",
        "columns": [
            "customer_id",
            "full_name",
            "dob",
            "phone",
            "email",
            "address",
            "account_id",
            "branch_id",
        ],
    },

    "crm": {
        "path": Path(
            "data/source_systems/"
            "crm/crm_customers.csv"
        ),
        "id_column":
            "crm_customer_id",
        "prefix": "CRM",
        "columns": [
            "crm_customer_id",
            "customer_name",
            "date_of_birth",
            "mobile",
            "email_address",
            "residential_address",
            "segment",
        ],
    },

    "kyc": {
        "path": Path(
            "data/source_systems/"
            "kyc/kyc_customers.csv"
        ),
        "id_column":
            "kyc_id",
        "prefix": "KYC",
        "columns": [
            "kyc_id",
            "legal_name",
            "dob",
            "tax_id",
            "phone",
            "address",
            "kyc_status",
            "verification_date",
            "LEI",
        ],
    },

    "wealth": {
        "path": Path(
            "data/source_systems/"
            "wealth/wealth_customers.csv"
        ),
        "id_column":
            "client_id",
        "prefix": "W",
        "columns": [
            "client_id",
            "client_name",
            "dob",
            "phone",
            "email",
            "address",
            "aum",
            "risk_profile",
            "relationship_manager",
        ],
    },
}


GROUND_TRUTH = Path(
    "data/ground_truth/"
    "ground_truth.csv"
)

SIMULATOR_METADATA = Path(
    "data/ground_truth/"
    "simulator_run_metadata.json"
)


def validate_source_schema(
    name,
    config,
):
    path = config["path"]

    if not path.exists():
        raise FileNotFoundError(
            f"Missing source file: {path}"
        )

    row_count = 0
    blank_counts = {
        column: 0
        for column in config["columns"]
    }

    expected_prefix = config[
        "prefix"
    ]

    expected_id_number = 0

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(
            file
        )

        if reader.fieldnames != (
            config["columns"]
        ):
            raise AssertionError(
                f"{name}: schema mismatch.\n"
                f"Expected:\n{config['columns']}\n"
                f"Actual:\n{reader.fieldnames}"
            )

        for row in reader:

            row_count += 1

            source_id = row[
                config["id_column"]
            ]

            expected_id_number += 1

            expected_id = (
                f"{expected_prefix}"
                f"{expected_id_number:08d}"
            )

            if source_id != expected_id:

                raise AssertionError(
                    f"{name}: source ID sequence "
                    f"broken at row "
                    f"{row_count}.\n"
                    f"Expected: {expected_id}\n"
                    f"Actual:   {source_id}"
                )

            if (
                "entity_key"
                in row
            ):
                raise AssertionError(
                    f"{name}: entity_key leaked "
                    f"into source data."
                )

            if (
                "master_id"
                in row
            ):
                raise AssertionError(
                    f"{name}: master_id leaked "
                    f"into source data."
                )

            for column in (
                config["columns"]
            ):

                value = (
                    row.get(
                        column,
                        "",
                    )
                    or ""
                )

                if not value.strip():
                    blank_counts[
                        column
                    ] += 1

    return (
        row_count,
        blank_counts,
    )


def validate_ground_truth(
    expected_source_rows,
):
    if not GROUND_TRUTH.exists():
        raise FileNotFoundError(
            f"Missing {GROUND_TRUTH}"
        )

    row_count = 0

    expected_ids = {
        "CORE": 0,
        "CRM": 0,
        "KYC": 0,
        "WEALTH": 0,
    }

    current_entity = None
    current_systems = set()

    coverage = defaultdict(int)

    with GROUND_TRUTH.open(
        newline="",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(
            file
        )

        expected_columns = [
            "source_system",
            "source_id",
            "entity_key",
        ]

        if reader.fieldnames != (
            expected_columns
        ):
            raise AssertionError(
                "Ground-truth schema mismatch."
            )

        for row in reader:

            row_count += 1

            system = (
                row["source_system"]
                .strip()
                .upper()
            )

            source_id = (
                row["source_id"]
                .strip()
            )

            entity_key = (
                row["entity_key"]
                .strip()
            )

            if system not in (
                expected_ids
            ):
                raise AssertionError(
                    f"Unknown source system: "
                    f"{system}"
                )

            if not source_id:
                raise AssertionError(
                    "Blank source_id in "
                    "ground truth."
                )

            if not entity_key:
                raise AssertionError(
                    "Blank entity_key in "
                    "ground truth."
                )

            expected_ids[
                system
            ] += 1

            prefix = {
                "CORE": "C",
                "CRM": "CRM",
                "KYC": "KYC",
                "WEALTH": "W",
            }[system]

            expected_source_id = (
                f"{prefix}"
                f"{expected_ids[system]:08d}"
            )

            if (
                source_id
                != expected_source_id
            ):
                raise AssertionError(
                    f"Ground truth source ID "
                    f"sequence broken for "
                    f"{system}.\n"
                    f"Expected: "
                    f"{expected_source_id}\n"
                    f"Actual: "
                    f"{source_id}"
                )

            # Ground truth is generated one entity
            # at a time, so this stays O(1) memory.
            if (
                current_entity is not None
                and entity_key
                != current_entity
            ):

                coverage[
                    len(
                        current_systems
                    )
                ] += 1

                current_systems = set()

            if (
                current_entity
                != entity_key
            ):
                current_entity = (
                    entity_key
                )

            current_systems.add(
                system
            )

    if current_entity is not None:

        coverage[
            len(
                current_systems
            )
        ] += 1

    if row_count != (
        expected_source_rows
    ):
        raise AssertionError(
            "Ground-truth reconciliation "
            "failed.\n"
            f"Source rows: "
            f"{expected_source_rows:,}\n"
            f"Ground truth: "
            f"{row_count:,}"
        )

    return row_count, coverage


def validate_metadata(
    source_counts,
):

    if not SIMULATOR_METADATA.exists():
        raise FileNotFoundError(
            f"Missing metadata: "
            f"{SIMULATOR_METADATA}"
        )

    metadata = json.loads(
        SIMULATOR_METADATA.read_text(
            encoding="utf-8"
        )
    )

    if metadata[
        "source_rows"
    ] != source_counts:

        raise AssertionError(
            "Simulator metadata source "
            "counts do not match "
            "actual source counts."
        )

    if (
        metadata["phone_conflicts"]
        <= 0
    ):

        raise AssertionError(
            "No phone conflicts were "
            "generated."
        )

    if (
        metadata["email_conflicts"]
        <= 0
    ):

        raise AssertionError(
            "No email conflicts were "
            "generated."
        )

    if not any(
        value > 0
        for value in (
            metadata[
                "missing_values"
            ].values()
        )
    ):

        raise AssertionError(
            "No missing values were "
            "generated."
        )

    if not any(
        value > 0
        for value in (
            metadata[
                "duplicate_rows"
            ].values()
        )
    ):

        raise AssertionError(
            "No duplicate rows were "
            "generated."
        )


def main():

    print("=" * 70)

    print(
        "PHASE 1 SOURCE VALIDATION"
    )

    print("=" * 70)

    source_counts = {}
    total_source_rows = 0

    print(
        "\nSOURCE SYSTEMS"
    )

    for name, config in (
        SOURCE_FILES.items()
    ):

        (
            row_count,
            blank_counts,
        ) = validate_source_schema(
            name,
            config,
        )

        source_counts[name] = (
            row_count
        )

        total_source_rows += (
            row_count
        )

        print(
            f"\n{name.upper()}"
        )

        print(
            f"Rows: "
            f"{row_count:,}"
        )

        print(
            "Blank values:"
        )

        for column, count in (
            blank_counts.items()
        ):

            if count:
                print(
                    f"  {column}: "
                    f"{count:,}"
                )

    print(
        "\nGROUND TRUTH"
    )

    (
        ground_truth_rows,
        coverage,
    ) = validate_ground_truth(
        total_source_rows
    )

    print(
        f"Rows: "
        f"{ground_truth_rows:,}"
    )

    print(
        "Reconciliation: PASS"
    )

    print(
        "\nCROSS-SYSTEM COVERAGE"
    )

    for count in (
        [1, 2, 3, 4]
    ):

        print(
            f"{count} system(s): "
            f"{coverage[count]:,}"
        )

    validate_metadata(
        source_counts
    )

    print(
        "\nSIMULATOR METADATA: PASS"
    )

    print(
        "\nALL PHASE 1 VALIDATIONS PASSED."
    )


if __name__ == "__main__":
    main()