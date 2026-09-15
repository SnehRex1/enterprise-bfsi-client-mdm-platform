from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.survivorship.scd2 import (
    apply_scd2,
    build_initial_scd2,
)


GOLD_ROOT = (
    PROJECT_ROOT
    / "data"
    / "dev"
    / "gold"
)

MASTER_CLIENT_PATH = (
    GOLD_ROOT
    / "master_client.csv"
)

HISTORY_PATH = (
    GOLD_ROOT
    / "master_client_history.csv"
)


# These are the Golden Record attributes.
# master_client_id identifies the master itself,
# so it is not an SCD attribute.
GOLDEN_ATTRIBUTES = [
    "name",
    "dob",
    "phone",
    "email",
    "address",
    "tax_id",
    "lei",
    "segment",
    "kyc_status",
    "verification_date",
    "aum",
    "risk_profile",
    "relationship_manager",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build or update Phase 5 SCD Type 2 history."
    )

    parser.add_argument(
        "--run-date",
        default=str(date.today()),
        help=(
            "Date used for SCD2 effective/expiry dates. "
            "Default: today's date."
        ),
    )

    return parser.parse_args()


def main():

    args = parse_args()

    print("=" * 70)
    print("PHASE 5 — SCD TYPE 2")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Load current Golden Record
    # ---------------------------------------------------------

    print("\nLoading Golden Record...")

    master_df = pd.read_csv(
        MASTER_CLIENT_PATH,
        dtype=str,
    )

    # pandas converts empty CSV fields to NaN by default.
    # SCD2 treats missing attributes as empty strings so
    # comparisons remain deterministic.
    master_df = master_df.fillna("")

    print(
        f"Master clients: {len(master_df):,}"
    )

    # Convert DataFrame rows to Python dictionaries because
    # the SCD2 engine works with simple records.
    master_clients = (
        master_df.to_dict("records")
    )

    # ---------------------------------------------------------
    # 2. Initial load OR incremental update
    # ---------------------------------------------------------

    if not HISTORY_PATH.exists():

        print("\nNo existing SCD2 history found.")
        print("Building initial history...")

        history = build_initial_scd2(
            master_clients=master_clients,
            fields=GOLDEN_ATTRIBUTES,
            effective_date=args.run_date,
        )

        print(
            "Initial history created."
        )

    else:

        print("\nExisting SCD2 history found.")
        print("Applying incremental update...")

        history_df = pd.read_csv(
            HISTORY_PATH,
            dtype=str,
        )

        history_df = history_df.fillna("")

        existing_history = (
            history_df.to_dict("records")
        )

        history = apply_scd2(
            existing_history=existing_history,
            new_master_clients=master_clients,
            run_date=args.run_date,
            fields=GOLDEN_ATTRIBUTES,
        )

    # ---------------------------------------------------------
    # 3. Save history
    # ---------------------------------------------------------

    history_df = pd.DataFrame(history)

    history_df.to_csv(
        HISTORY_PATH,
        index=False,
    )

    # ---------------------------------------------------------
    # 4. Validate basic current-state invariant
    # ---------------------------------------------------------

    current_df = history_df[
        history_df["is_current"]
        .astype(str)
        .str.lower()
        .eq("true")
    ]

    current_duplicates = (
        current_df
        .groupby(
            [
                "master_client_id",
                "field",
            ]
        )
        .size()
    )

    duplicate_current_rows = int(
        (current_duplicates > 1).sum()
    )

    print("\nSCD2 SUMMARY")
    print("-" * 70)

    print(
        f"History rows:          {len(history_df):,}"
    )

    print(
        f"Current rows:          {len(current_df):,}"
    )

    print(
        f"Expired rows:          "
        f"{len(history_df) - len(current_df):,}"
    )

    print(
        f"Current duplicates:    "
        f"{duplicate_current_rows:,}"
    )

    print(
        f"Run date:              {args.run_date}"
    )

    print("\nOutput:")

    print(HISTORY_PATH)

    if duplicate_current_rows != 0:
        raise ValueError(
            "SCD2 validation failed: "
            "more than one current version exists "
            "for at least one master/attribute."
        )

    print("\nSCD2 processing complete.")


if __name__ == "__main__":
    main()