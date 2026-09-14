"""
Run Phase 2 standardization for all four source systems.

Usage:

    python scripts\standardize_sources.py --profile dev

    python scripts\standardize_sources.py --profile full
"""

import argparse
import csv
import sys
from pathlib import Path

import yaml


# ------------------------------------------------------------
# Make project root importable when this file is run directly.
# ------------------------------------------------------------

PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from src.standardization.standardize import (
    build_canonical_record,
)


SOURCE_DEFINITIONS = {
    "core": "core_customers.csv",
    "crm": "crm_customers.csv",
    "kyc": "kyc_customers.csv",
    "wealth": "wealth_customers.csv",
}


CANONICAL_COLUMNS = [
    "source_system",
    "source_id",

    "name",
    "normalized_name",

    "dob",
    "normalized_dob",

    "phone",
    "normalized_phone",

    "email",
    "normalized_email",

    "address",
    "normalized_address",

    "tax_id",
    "lei",

    "account_id",
    "branch_id",

    "segment",
    "kyc_status",

    "verification_date",
    "normalized_verification_date",

    "aum",
    "risk_profile",
    "relationship_manager",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run Phase 2 standardization."
        )
    )

    parser.add_argument(
        "--profile",
        choices=[
            "dev",
            "full",
        ],
        default="dev",
    )

    return parser.parse_args()


def get_profile_root(
    profile: str,
) -> Path:

    if profile == "dev":
        return Path(
            "data/dev"
        )

    if profile == "full":
        return Path(
            "data"
        )

    raise ValueError(
        f"Unsupported profile: {profile}"
    )


def load_mapping() -> dict:
    """
    Load canonical field mappings from YAML.
    """

    mapping_path = Path(
        "configs/canonical_mapping.yaml"
    )

    with mapping_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return yaml.safe_load(file)


def standardize_file(
    source_system: str,
    source_path: Path,
    output_path: Path,
    mapping: dict,
) -> int:

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    row_count = 0

    with (
        source_path.open(
            "r",
            newline="",
            encoding="utf-8",
        ) as source_file,

        output_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as output_file,
    ):

        reader = csv.DictReader(
            source_file
        )

        writer = csv.DictWriter(
            output_file,
            fieldnames=CANONICAL_COLUMNS,
        )

        writer.writeheader()

        for row in reader:

            canonical = (
                build_canonical_record(
                    source_system,
                    row,
                    mapping[source_system],
                )
            )

            writer.writerow(
                canonical
            )

            row_count += 1

    return row_count


def main():

    args = parse_args()

    profile_root = (
        get_profile_root(
            args.profile
        )
    )

    input_root = (
        profile_root
        / "contract_validated"
    )

    output_root = (
        profile_root
        / "standardized"
    )

    mapping = load_mapping()

    print("=" * 70)
    print(
        "PHASE 2 STANDARDIZATION"
    )
    print("=" * 70)

    print(
        f"Profile: {args.profile}"
    )

    total_rows = 0

    for (
        source_system,
        filename,
    ) in SOURCE_DEFINITIONS.items():

        source_path = (
            input_root
            / source_system
            / filename
        )

        output_path = (
            output_root
            / source_system
            / filename
        )

        print()
        print("-" * 70)
        print(
            source_system.upper()
        )

        count = standardize_file(
            source_system=source_system,
            source_path=source_path,
            output_path=output_path,
            mapping=mapping,
        )

        total_rows += count

        print(
            f"Input rows: {count:,}"
        )

        print(
            f"Output: {output_path}"
        )

    print()
    print("=" * 70)
    print(
        "STANDARDIZATION SUMMARY"
    )
    print("=" * 70)

    print(
        f"Total processed rows: "
        f"{total_rows:,}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()