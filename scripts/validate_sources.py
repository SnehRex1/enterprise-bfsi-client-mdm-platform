"""
Phase 1 — Source Validation

Validates either:

    --profile dev
or:
    --profile full

The validator reads the actual CSV files from disk using
csv.DictReader. It does NOT use metadata as the source of
row counts.

Metadata is used only afterward to verify that the generated
metadata agrees with the actual files.
"""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


# ============================================================
# PROFILE PATHS
# ============================================================

def get_profile_paths(profile: str):
    """
    Return the source-system root, ground truth path,
    and metadata path for the selected benchmark.
    """

    if profile == "dev":
        root = Path("data/dev")

    elif profile == "full":
        root = Path("data")

    else:
        raise ValueError(
            f"Unsupported profile: {profile}"
        )

    source_root = (
        root / "source_systems"
    )

    ground_truth_path = (
        root
        / "ground_truth"
        / "ground_truth.csv"
    )

    metadata_path = (
        root
        / "ground_truth"
        / "simulator_run_metadata.json"
    )

    return (
        source_root,
        ground_truth_path,
        metadata_path,
    )


# ============================================================
# SOURCE SCHEMA DEFINITIONS
# ============================================================

SOURCE_DEFINITIONS = {

    "core": {
        "directory": "core",
        "filename": "core_customers.csv",
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
        "directory": "crm",
        "filename": "crm_customers.csv",
        "id_column": "crm_customer_id",
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
        "directory": "kyc",
        "filename": "kyc_customers.csv",
        "id_column": "kyc_id",
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
        "directory": "wealth",
        "filename": "wealth_customers.csv",
        "id_column": "client_id",
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


# ============================================================
# ARGUMENTS
# ============================================================

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Validate the Phase 1 "
            "BFSI MDM benchmark."
        )
    )

    parser.add_argument(
        "--profile",
        choices=["dev", "full"],
        default="full",
        help=(
            "Benchmark to validate. "
            "dev = data/dev, "
            "full = data/"
        ),
    )

    return parser.parse_args()


# ============================================================
# BUILD SOURCE PATHS
# ============================================================

def build_source_definitions(
    source_root: Path,
):

    definitions = {}

    for system, definition in (
        SOURCE_DEFINITIONS.items()
    ):

        current = dict(definition)

        current["path"] = (
            source_root
            / definition["directory"]
            / definition["filename"]
        )

        definitions[system] = current

    return definitions


# ============================================================
# VALIDATE ONE SOURCE FILE
# ============================================================

def validate_source_file(
    system: str,
    definition: dict,
):
    """
    Read the actual CSV from disk and count logical CSV
    records using csv.DictReader.

    This is the authoritative row count.
    """

    path = definition["path"]

    if not path.exists():
        raise FileNotFoundError(
            f"Missing {system} source file:\n"
            f"{path}"
        )

    expected_columns = (
        definition["columns"]
    )

    id_column = (
        definition["id_column"]
    )

    prefix = definition["prefix"]

    row_count = 0

    blank_counts = {
        column: 0
        for column in expected_columns
    }

    with path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(
            file
        )

        # ----------------------------------------------------
        # Schema check
        # ----------------------------------------------------

        if reader.fieldnames != (
            expected_columns
        ):
            raise AssertionError(
                f"{system.upper()}: schema mismatch.\n"
                f"Expected:\n{expected_columns}\n"
                f"Actual:\n{reader.fieldnames}"
            )

        # ----------------------------------------------------
        # Actual CSV-record count
        # ----------------------------------------------------

        for row in reader:

            row_count += 1

            # ------------------------------------------------
            # Source ID integrity
            # ------------------------------------------------

            source_id = (
                row.get(
                    id_column,
                    "",
                )
                or ""
            ).strip()

            expected_id = (
                f"{prefix}"
                f"{row_count:08d}"
            )

            if source_id != expected_id:

                raise AssertionError(
                    f"{system.upper()}: source ID "
                    f"sequence broken at CSV record "
                    f"{row_count}.\n"
                    f"Expected: {expected_id}\n"
                    f"Actual:   {source_id}"
                )

            # ------------------------------------------------
            # Truth leakage
            # ------------------------------------------------

            if "entity_key" in row:

                raise AssertionError(
                    f"{system.upper()}: entity_key "
                    f"leaked into source data."
                )

            if "master_id" in row:

                raise AssertionError(
                    f"{system.upper()}: master_id "
                    f"leaked into source data."
                )

            # ------------------------------------------------
            # Blank-value statistics
            # ------------------------------------------------

            for column in expected_columns:

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


# ============================================================
# VALIDATE GROUND TRUTH
# ============================================================

def validate_ground_truth(
    ground_truth_path: Path,
    expected_source_rows: int,
):
    """
    Validate the actual ground-truth CSV.

    Counts the physical logical CSV records using
    csv.DictReader.

    Also validates:
    - schema
    - source-system values
    - source ID sequence
    - non-empty entity_key
    - reconciliation
    - cross-system coverage
    """

    if not ground_truth_path.exists():
        raise FileNotFoundError(
            f"Missing ground truth:\n"
            f"{ground_truth_path}"
        )

    expected_columns = [
        "source_system",
        "source_id",
        "entity_key",
    ]

    row_count = 0

    source_counters = {
        "CORE": 0,
        "CRM": 0,
        "KYC": 0,
        "WEALTH": 0,
    }

    coverage = defaultdict(int)

    current_entity_key = None
    current_systems = set()

    with ground_truth_path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(
            file
        )

        if reader.fieldnames != (
            expected_columns
        ):
            raise AssertionError(
                "Ground truth schema mismatch.\n"
                f"Expected:\n{expected_columns}\n"
                f"Actual:\n{reader.fieldnames}"
            )

        for row in reader:

            row_count += 1

            system = (
                row["source_system"]
                or ""
            ).strip().upper()

            source_id = (
                row["source_id"]
                or ""
            ).strip()

            entity_key = (
                row["entity_key"]
                or ""
            ).strip()

            # ------------------------------------------------
            # Basic values
            # ------------------------------------------------

            if system not in source_counters:

                raise AssertionError(
                    f"Unknown source system: "
                    f"{system}"
                )

            if not source_id:

                raise AssertionError(
                    f"Blank source_id at "
                    f"ground-truth row "
                    f"{row_count}"
                )

            if not entity_key:

                raise AssertionError(
                    f"Blank entity_key at "
                    f"ground-truth row "
                    f"{row_count}"
                )

            # ------------------------------------------------
            # Source ID sequence
            # ------------------------------------------------

            source_counters[system] += 1

            prefix = {
                "CORE": "C",
                "CRM": "CRM",
                "KYC": "KYC",
                "WEALTH": "W",
            }[system]

            expected_id = (
                f"{prefix}"
                f"{source_counters[system]:08d}"
            )

            if source_id != expected_id:

                raise AssertionError(
                    f"Ground truth source ID "
                    f"sequence broken for "
                    f"{system}.\n"
                    f"Expected: {expected_id}\n"
                    f"Actual:   {source_id}"
                )

            # ------------------------------------------------
            # Cross-system coverage
            # ------------------------------------------------

            if (
                current_entity_key is not None
                and entity_key
                != current_entity_key
            ):

                coverage[
                    len(current_systems)
                ] += 1

                current_systems = set()

            if (
                current_entity_key
                != entity_key
            ):

                current_entity_key = (
                    entity_key
                )

            current_systems.add(
                system
            )

    # Flush last entity
    if current_entity_key is not None:

        coverage[
            len(current_systems)
        ] += 1

    # --------------------------------------------------------
    # Reconciliation
    # --------------------------------------------------------

    if row_count != (
        expected_source_rows
    ):

        raise AssertionError(
            "Ground-truth reconciliation failed.\n"
            f"Actual source rows: "
            f"{expected_source_rows:,}\n"
            f"Actual ground-truth rows: "
            f"{row_count:,}"
        )

    return (
        row_count,
        coverage,
        source_counters,
    )


# ============================================================
# VALIDATE METADATA
# ============================================================

def validate_metadata(
    metadata_path: Path,
    profile: str,
    actual_source_counts: dict,
    actual_ground_truth_rows: int,
):
    """
    Metadata is NOT used to count rows.

    We first count the real CSVs, then compare the
    metadata against those actual values.
    """

    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Missing metadata:\n"
            f"{metadata_path}"
        )

    metadata = json.loads(
        metadata_path.read_text(
            encoding="utf-8"
        )
    )

    # --------------------------------------------------------
    # Profile
    # --------------------------------------------------------

    metadata_profile = metadata.get(
        "profile",
        "full",
    )

    if metadata_profile != profile:

        raise AssertionError(
            "Metadata profile mismatch.\n"
            f"Expected: {profile}\n"
            f"Actual:   {metadata_profile}"
        )

    # --------------------------------------------------------
    # Source counts
    # --------------------------------------------------------

    metadata_counts = (
        metadata.get(
            "source_rows",
            {},
        )
    )

    if metadata_counts != (
        actual_source_counts
    ):

        raise AssertionError(
            "Metadata source counts do not "
            "match actual CSV counts.\n"
            f"Metadata: {metadata_counts}\n"
            f"Actual:   {actual_source_counts}"
        )

    # --------------------------------------------------------
    # Ground truth count
    # --------------------------------------------------------

    actual_source_total = sum(
        actual_source_counts.values()
    )

    if actual_ground_truth_rows != (
        actual_source_total
    ):

        raise AssertionError(
            "Ground truth does not reconcile "
            "with source files."
        )

    # --------------------------------------------------------
    # Hidden entity population
    # --------------------------------------------------------

    individuals = metadata.get(
        "individuals_processed"
    )

    legal_entities = metadata.get(
        "legal_entities_processed"
    )

    hidden_entities = metadata.get(
        "hidden_entities"
    )

    if (
        individuals is not None
        and legal_entities is not None
        and hidden_entities is not None
    ):

        expected_hidden = (
            individuals
            + legal_entities
        )

        if hidden_entities != (
            expected_hidden
        ):

            raise AssertionError(
                "Hidden-entity count mismatch.\n"
                f"Individuals + legal entities = "
                f"{expected_hidden:,}\n"
                f"Metadata hidden entities = "
                f"{hidden_entities:,}"
            )

    # --------------------------------------------------------
    # Messiness presence
    # --------------------------------------------------------

    if metadata.get(
        "phone_conflicts",
        0,
    ) <= 0:

        raise AssertionError(
            "No phone conflicts were recorded."
        )

    if metadata.get(
        "email_conflicts",
        0,
    ) <= 0:

        raise AssertionError(
            "No email conflicts were recorded."
        )

    duplicate_rows = metadata.get(
        "duplicate_rows",
        {},
    )

    if not any(
        value > 0
        for value in duplicate_rows.values()
    ):

        raise AssertionError(
            "No duplicate rows were recorded."
        )

    print(
        "\nSIMULATOR METADATA: PASS"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    args = parse_args()

    profile = args.profile

    (
        source_root,
        ground_truth_path,
        metadata_path,
    ) = get_profile_paths(
        profile
    )

    source_definitions = (
        build_source_definitions(
            source_root
        )
    )

    print("=" * 70)

    print(
        "PHASE 1 SOURCE VALIDATION"
    )

    print("=" * 70)

    print(
        f"Profile: {profile}"
    )

    print(
        f"Source root: {source_root}"
    )

    print(
        f"Ground truth: {ground_truth_path}"
    )

    # ========================================================
    # SOURCE VALIDATION
    # ========================================================

    actual_source_counts = {}

    total_source_rows = 0

    print(
        "\nSOURCE SYSTEMS"
    )

    for system, definition in (
        source_definitions.items()
    ):

        (
            row_count,
            blank_counts,
        ) = validate_source_file(
            system,
            definition,
        )

        actual_source_counts[
            system
        ] = row_count

        total_source_rows += (
            row_count
        )

        print(
            f"\n{system.upper()}"
        )

        print(
            f"Rows: {row_count:,}"
        )

        print(
            "Blank values:"
        )

        for column, count in (
            blank_counts.items()
        ):

            if count > 0:

                print(
                    f"  {column}: "
                    f"{count:,}"
                )

    # ========================================================
    # GROUND TRUTH
    # ========================================================

    print(
        "\nGROUND TRUTH"
    )

    (
        ground_truth_rows,
        coverage,
        ground_truth_counts,
    ) = validate_ground_truth(
        ground_truth_path,
        total_source_rows,
    )

    print(
        f"Rows: {ground_truth_rows:,}"
    )

    print(
        "Reconciliation: PASS"
    )

    # ========================================================
    # SOURCE/GROUND-TRUTH ID COUNT AGREEMENT
    # ========================================================

    normalized_ground_truth_counts = {
        "core":
            ground_truth_counts["CORE"],

        "crm":
            ground_truth_counts["CRM"],

        "kyc":
            ground_truth_counts["KYC"],

        "wealth":
            ground_truth_counts["WEALTH"],
    }

    if (
        normalized_ground_truth_counts
        != actual_source_counts
    ):

        raise AssertionError(
            "Ground-truth source counts do "
            "not match actual source counts.\n"
            f"Source files: "
            f"{actual_source_counts}\n"
            f"Ground truth: "
            f"{normalized_ground_truth_counts}"
        )

    # ========================================================
    # COVERAGE
    # ========================================================

    print(
        "\nCROSS-SYSTEM COVERAGE"
    )

    for count in [1, 2, 3, 4]:

        print(
            f"{count} system(s): "
            f"{coverage[count]:,}"
        )

    total_entities = sum(
        coverage.values()
    )

    print(
        f"\nUnderlying entities observed: "
        f"{total_entities:,}"
    )

    # ========================================================
    # METADATA
    # ========================================================

    validate_metadata(
        metadata_path=metadata_path,
        profile=profile,
        actual_source_counts=(
            actual_source_counts
        ),
        actual_ground_truth_rows=(
            ground_truth_rows
        ),
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        "ALL PHASE 1 VALIDATIONS PASSED."
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()