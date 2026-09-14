"""
Run data-contract validation for all four source systems.

Usage:

    python scripts\validate_contracts.py --profile dev

    python scripts\validate_contracts.py --profile full
"""

import argparse
import sys
from pathlib import Path

# ------------------------------------------------------------
# Make the project root importable.
#
# __file__ points to:
#     project_root/scripts/validate_contracts.py
#
# .parent gives:
#     project_root/scripts
#
# .parent.parent gives:
#     project_root
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.quality.contract_validator import (
    validate_source_file,
)

# ------------------------------------------------------------
# Mapping between source-system names and their files/contracts.
# ------------------------------------------------------------

SOURCE_DEFINITIONS = {

    "core": {
        "filename": "core_customers.csv",
        "contract": "core.yaml",
    },

    "crm": {
        "filename": "crm_customers.csv",
        "contract": "crm.yaml",
    },

    "kyc": {
        "filename": "kyc_customers.csv",
        "contract": "kyc.yaml",
    },

    "wealth": {
        "filename": "wealth_customers.csv",
        "contract": "wealth.yaml",
    },
}


def parse_args():
    """
    Parse command-line arguments.

    Default profile is DEV because DEV is our normal
    development environment.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Run Phase 2 data-contract validation."
        )
    )

    parser.add_argument(
        "--profile",
        choices=[
            "dev",
            "full",
        ],
        default="dev",
        help=(
            "Benchmark profile to validate. "
            "Default: dev"
        ),
    )

    return parser.parse_args()


def get_profile_root(
    profile: str,
) -> Path:
    """
    Resolve the root directory for the selected benchmark.

    DEV:
        data/dev/

    FULL:
        data/
    """

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


def main():

    args = parse_args()

    # --------------------------------------------------------
    # Determine profile-specific paths.
    # --------------------------------------------------------

    profile_root = get_profile_root(
        args.profile
    )

    source_root = (
        profile_root
        / "source_systems"
    )

    contract_root = Path(
        "configs/contracts"
    )

    # This folder stores machine-readable reports.
    validation_root = (
        profile_root
        / "contract_validation"
    )

    # This folder contains records that passed the contract.
    validated_root = (
        profile_root
        / "contract_validated"
    )

    # Invalid records go here.
    quarantine_root = (
        profile_root
        / "quarantine"
        / "contract_validation"
    )

    print("=" * 70)
    print(
        "PHASE 2 DATA CONTRACT VALIDATION"
    )
    print("=" * 70)

    print(
        f"Profile: {args.profile}"
    )

    print(
        f"Source root: {source_root}"
    )

    print(
        f"Contract root: {contract_root}"
    )

    # --------------------------------------------------------
    # Overall counters.
    # --------------------------------------------------------

    total_input = 0
    total_passed = 0
    total_quarantined = 0

    # --------------------------------------------------------
    # Validate each source system.
    # --------------------------------------------------------

    for (
        system,
        definition,
    ) in SOURCE_DEFINITIONS.items():

        # Example:
        #
        # data/dev/source_systems/core/core_customers.csv
        source_path = (
            source_root
            / system
            / definition["filename"]
        )

        # Example:
        #
        # configs/contracts/core.yaml
        contract_path = (
            contract_root
            / definition["contract"]
        )

        # Example:
        #
        # data/dev/contract_validated/core/core_customers.csv
        validated_output_path = (
            validated_root
            / system
            / definition["filename"]
        )

        # Example:
        #
        # data/dev/quarantine/contract_validation/core/
        #     core_customers_quarantine.csv
        quarantine_output_path = (
            quarantine_root
            / system
            / definition[
                "filename"
            ].replace(
                ".csv",
                "_quarantine.csv",
            )
        )

        # Example:
        #
        # data/dev/contract_validation/core/
        #     validation_report.json
        report_path = (
            validation_root
            / system
            / "validation_report.json"
        )

        print()
        print("-" * 70)
        print(
            system.upper()
        )

        # ----------------------------------------------------
        # Run generic validation.
        # ----------------------------------------------------

        report = validate_source_file(
            source_path=source_path,
            contract_path=contract_path,
            validated_output_path=(
                validated_output_path
            ),
            quarantine_output_path=(
                quarantine_output_path
            ),
            report_path=report_path,
        )

        # ----------------------------------------------------
        # Add this source's results to overall totals.
        # ----------------------------------------------------

        total_input += report[
            "total_rows"
        ]

        total_passed += report[
            "passed_rows"
        ]

        total_quarantined += report[
            "quarantined_rows"
        ]

        print(
            f"Input rows: "
            f"{report['total_rows']:,}"
        )

        print(
            f"Passed rows: "
            f"{report['passed_rows']:,}"
        )

        print(
            f"Quarantined rows: "
            f"{report['quarantined_rows']:,}"
        )

        print(
            f"Status: "
            f"{report['status']}"
        )

    # --------------------------------------------------------
    # Overall summary.
    # --------------------------------------------------------

    print()
    print("=" * 70)

    print(
        "CONTRACT VALIDATION SUMMARY"
    )

    print("=" * 70)

    print(
        f"Input rows: "
        f"{total_input:,}"
    )

    print(
        f"Passed rows: "
        f"{total_passed:,}"
    )

    print(
        f"Quarantined rows: "
        f"{total_quarantined:,}"
    )

    # --------------------------------------------------------
    # Critical reconciliation invariant.
    # --------------------------------------------------------

    # Nothing may disappear.
    #
    # input = passed + quarantined
    #
    if total_input != (
        total_passed
        + total_quarantined
    ):

        raise AssertionError(
            "Input/pass/quarantine "
            "reconciliation failed."
        )

    print(
        "Reconciliation: PASS"
    )

    # --------------------------------------------------------
    # Final status.
    # --------------------------------------------------------

    if total_quarantined == 0:

        print(
            "ALL DATA CONTRACT "
            "VALIDATIONS PASSED."
        )

    else:

        print(
            "CONTRACT VALIDATION "
            "COMPLETED WITH "
            "QUARANTINED ROWS."
        )

    print("=" * 70)


if __name__ == "__main__":
    main()