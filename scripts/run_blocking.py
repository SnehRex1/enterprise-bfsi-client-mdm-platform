import sys
import csv
from pathlib import Path


# ---------------------------------------------------------------------------
# Project root / import setup
# ---------------------------------------------------------------------------
# This file lives at:
#
# project_root/
#     scripts/
#         run_blocking.py
#
# parents[0] = scripts/
# parents[1] = project_root/
#
# Adding the project root to sys.path allows:
#
#     from src.matching.blocking import ...
#
# to work when this script is executed directly.
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.matching.blocking import (
    build_block_indexes,
    generate_candidate_pairs,
)


# ---------------------------------------------------------------------------
# Input / output paths
# ---------------------------------------------------------------------------

DEV_SILVER_ROOT = PROJECT_ROOT / "data" / "dev" / "silver"

OUTPUT_DIR = PROJECT_ROOT / "data" / "dev" / "matching"

SOURCE_FILES = {
    "core": DEV_SILVER_ROOT / "core" / "core_customers.csv",
    "crm": DEV_SILVER_ROOT / "crm" / "crm_customers.csv",
    "kyc": DEV_SILVER_ROOT / "kyc" / "kyc_customers.csv",
    "wealth": DEV_SILVER_ROOT / "wealth" / "wealth_customers.csv",
}


# ---------------------------------------------------------------------------
# CSV reader
# ---------------------------------------------------------------------------

def read_csv(path: Path) -> list[dict[str, str]]:
    """
    Read one CSV file and return its rows as dictionaries.
    """

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        return list(csv.DictReader(file))


# ---------------------------------------------------------------------------
# Load all four Silver sources
# ---------------------------------------------------------------------------

def load_all_rows() -> list[dict[str, str]]:
    """
    Load Core, CRM, KYC and Wealth Silver records
    into one list.
    """

    rows = []

    for source_system, path in SOURCE_FILES.items():

        source_rows = read_csv(path)

        print(
            f"{source_system.upper():<8} "
            f"{len(source_rows):>8,} rows"
        )

        rows.extend(source_rows)

    return rows


# ---------------------------------------------------------------------------
# Main blocking workflow
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Run candidate blocking on the DEV Silver dataset.
    """

    # Create the output directory if it does not exist.
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Load all four Silver sources.
    rows = load_all_rows()

    print()
    print(f"Total Silver records: {len(rows):,}")

    # -----------------------------------------------------------------------
    # Build blocking indexes
    # -----------------------------------------------------------------------

    indexes = build_block_indexes(rows)

    print()
    print("BLOCK STATISTICS")
    print("-" * 60)

    for strategy_name, index in indexes.items():

        # Remove empty keys.
        non_empty_blocks = {
            key: records
            for key, records in index.items()
            if key
        }

        # Determine how many records are in every block.
        block_sizes = [
            len(records)
            for records in non_empty_blocks.values()
        ]

        print(
            f"{strategy_name:<20} "
            f"{len(non_empty_blocks):>8,} blocks"
        )

        if block_sizes:
            print(
                f"{'  max block size':<20} "
                f"{max(block_sizes):>8,}"
            )

    # -----------------------------------------------------------------------
    # Generate candidate pairs
    # -----------------------------------------------------------------------

    candidate_pairs = generate_candidate_pairs(rows)

    print()
    print(
        f"Candidate pairs generated: "
        f"{len(candidate_pairs):,}"
    )

    # -----------------------------------------------------------------------
    # Persist candidate pairs
    # -----------------------------------------------------------------------

    candidate_path = OUTPUT_DIR / "candidate_pairs.csv"

    with candidate_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.writer(file)

        # Header
        writer.writerow(
            [
                "left_source_system",
                "left_source_id",
                "right_source_system",
                "right_source_id",
                "blocking_keys",
            ]
        )

        # Candidate pair rows
        for pair in candidate_pairs:

            writer.writerow(
                [
                    pair.left.source_system,
                    pair.left.source_id,
                    pair.right.source_system,
                    pair.right.source_id,
                    "|".join(sorted(pair.blocking_keys)),
                ]
            )

    print(
        f"Candidate file: {candidate_path}"
    )


# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()