"""
Run Data Quality checks for standardized source records.

Usage:

    python scripts\run_dq.py --profile dev

    python scripts\run_dq.py --profile full
"""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from src.quality.dq_checks import (
    run_all_checks,
)


SOURCE_DEFINITIONS = {
    "core": "core_customers.csv",
    "crm": "crm_customers.csv",
    "kyc": "kyc_customers.csv",
    "wealth": "wealth_customers.csv",
}


def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Run Phase 2 Data Quality checks."
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


def process_source(
    source_system: str,
    input_path: Path,
    silver_path: Path,
    quarantine_path: Path,
    report_path: Path,
) -> dict:

    silver_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    quarantine_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    total_rows = 0
    passed_rows = 0
    quarantined_rows = 0

    issue_counts = Counter()

    # Used only to measure duplicate IDs.
    # Duplicates are NOT automatically quarantined.
    source_id_counts = Counter()

    with (
        input_path.open(
            "r",
            newline="",
            encoding="utf-8",
        ) as input_file,

        silver_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as silver_file,

        quarantine_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as quarantine_file,
    ):

        reader = csv.DictReader(
            input_file
        )

        headers = list(
            reader.fieldnames or []
        )

        silver_writer = csv.DictWriter(
            silver_file,
            fieldnames=headers,
        )

        quarantine_writer = csv.DictWriter(
            quarantine_file,
            fieldnames=(
                headers
                + ["failure_reason"]
            ),
            extrasaction="ignore",
        )

        silver_writer.writeheader()
        quarantine_writer.writeheader()

        for row in reader:

            total_rows += 1

            source_id = str(
                row.get(
                    "source_id",
                    "",
                )
            ).strip()

            source_id_counts[
                source_id
            ] += 1

            issues = run_all_checks(
                row
            )

            if issues:

                quarantined_rows += 1

                for issue in issues:
                    issue_counts[
                        issue
                    ] += 1

                row[
                    "failure_reason"
                ] = " | ".join(
                    issues
                )

                quarantine_writer.writerow(
                    row
                )

            else:

                passed_rows += 1

                silver_writer.writerow(
                    row
                )

    duplicate_source_ids = {
        source_id: count
        for source_id, count
        in source_id_counts.items()
        if source_id
        and count > 1
    }

    reconciled = (
        total_rows
        == passed_rows
        + quarantined_rows
    )

    if not reconciled:

        raise AssertionError(
            "DQ reconciliation failed: "
            f"input={total_rows}, "
            f"passed={passed_rows}, "
            f"quarantined={quarantined_rows}"
        )

    report = {
        "source_system": source_system,
        "input_rows": total_rows,
        "passed_rows": passed_rows,
        "quarantined_rows": quarantined_rows,

        "reconciliation": (
            "PASS"
            if reconciled
            else "FAIL"
        ),

        "issue_counts": dict(
            issue_counts
        ),

        # Metric only.
        # Duplicates are not automatically failed.
        "duplicate_source_ids": len(
            duplicate_source_ids
        ),
    }

    report_path.write_text(
        json.dumps(
            report,
            indent=2,
        ),
        encoding="utf-8",
    )

    return report


def main():

    args = parse_args()

    profile_root = (
        get_profile_root(
            args.profile
        )
    )

    standardized_root = (
        profile_root
        / "standardized"
    )

    silver_root = (
        profile_root
        / "silver"
    )

    quarantine_root = (
        profile_root
        / "quarantine"
        / "dq"
    )

    report_root = (
        profile_root
        / "dq"
    )

    print("=" * 70)
    print(
        "PHASE 2 DATA QUALITY"
    )
    print("=" * 70)

    print(
        f"Profile: {args.profile}"
    )

    total_input = 0
    total_passed = 0
    total_quarantined = 0

    for (
        source_system,
        filename,
    ) in SOURCE_DEFINITIONS.items():

        input_path = (
            standardized_root
            / source_system
            / filename
        )

        silver_path = (
            silver_root
            / source_system
            / filename
        )

        quarantine_path = (
            quarantine_root
            / source_system
            / filename
        )

        report_path = (
            report_root
            / source_system
            / "dq_report.json"
        )

        print()
        print("-" * 70)
        print(
            source_system.upper()
        )

        report = process_source(
            source_system=source_system,
            input_path=input_path,
            silver_path=silver_path,
            quarantine_path=quarantine_path,
            report_path=report_path,
        )

        total_input += report[
            "input_rows"
        ]

        total_passed += report[
            "passed_rows"
        ]

        total_quarantined += report[
            "quarantined_rows"
        ]

        print(
            f"Input rows: "
            f"{report['input_rows']:,}"
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
            "Duplicate source_id values "
            "(metric only): "
            f"{report['duplicate_source_ids']:,}"
        )

        print(
            "Reconciliation: "
            f"{report['reconciliation']}"
        )

        if report[
            "issue_counts"
        ]:

            print("DQ issues:")

            for (
                issue,
                count,
            ) in report[
                "issue_counts"
            ].items():

                print(
                    f"  {issue}: "
                    f"{count:,}"
                )

    print()
    print("=" * 70)
    print(
        "PHASE 2 DQ SUMMARY"
    )
    print("=" * 70)

    print(
        f"Input rows: "
        f"{total_input:,}"
    )

    print(
        f"Silver rows: "
        f"{total_passed:,}"
    )

    print(
        f"DQ-quarantined rows: "
        f"{total_quarantined:,}"
    )

    if total_input != (
        total_passed
        + total_quarantined
    ):

        raise AssertionError(
            "Overall DQ reconciliation failed."
        )

    print(
        "Reconciliation: PASS"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()