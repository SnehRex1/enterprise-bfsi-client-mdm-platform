import csv
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.matching.deterministic import deterministic_match
from src.matching.fuzzy import calculate_fuzzy_scores
from src.matching.models import RecordRef
from src.matching.scoring import score_match


SILVER_PATHS = {
    "CORE": (
        PROJECT_ROOT
        / "data"
        / "dev"
        / "silver"
        / "core"
        / "core_customers.csv"
    ),
    "CRM": (
        PROJECT_ROOT
        / "data"
        / "dev"
        / "silver"
        / "crm"
        / "crm_customers.csv"
    ),
    "KYC": (
        PROJECT_ROOT
        / "data"
        / "dev"
        / "silver"
        / "kyc"
        / "kyc_customers.csv"
    ),
    "WEALTH": (
        PROJECT_ROOT
        / "data"
        / "dev"
        / "silver"
        / "wealth"
        / "wealth_customers.csv"
    ),
}


CANDIDATE_PATH = (
    PROJECT_ROOT
    / "data"
    / "dev"
    / "matching"
    / "candidate_pairs.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "dev"
    / "matching"
)

RESULT_PATH = (
    OUTPUT_DIR
    / "entity_resolution_results.csv"
)

SUMMARY_PATH = (
    OUTPUT_DIR
    / "entity_resolution_summary.json"
)


def load_silver_records():

    records = {}

    for source_system, path in SILVER_PATHS.items():

        with path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                source_id = row["source_id"]

                records[
                    (source_system, source_id)
                ] = row

    return records


def make_record_ref(
    source_system,
    source_id,
):
    return RecordRef(
        source_system=source_system,
        source_id=source_id,
    )


def serialize_result(
    result,
    blocking_keys="",
):
    """
    Convert MatchResult into a CSV-friendly dictionary.
    """

    return {
        "left_source_system": (
            result.left.source_system
        ),

        "left_source_id": (
            result.left.source_id
        ),

        "right_source_system": (
            result.right.source_system
        ),

        "right_source_id": (
            result.right.source_id
        ),

        "blocking_keys": blocking_keys,

        "match_score": result.match_score,

        "decision": result.decision,

        "matching_rule": (
            result.matching_rule or ""
        ),

        "name_score": (
            "" if result.name_score is None
            else result.name_score
        ),

        "address_score": (
            "" if result.address_score is None
            else result.address_score
        ),

        "phone_score": (
            "" if result.phone_score is None
            else result.phone_score
        ),

        "email_score": (
            "" if result.email_score is None
            else result.email_score
        ),

        "dob_score": (
            "" if result.dob_score is None
            else result.dob_score
        ),

        "reason": result.reason or "",
    }


def main():

    print("ENTITY RESOLUTION ENGINE")
    print("=" * 70)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------------
    # Load Silver
    # ---------------------------------------------------------------

    print()
    print("Loading Silver records...")

    silver_records = load_silver_records()

    print(
        f"Silver records loaded: "
        f"{len(silver_records):,}"
    )

    # ---------------------------------------------------------------
    # Prepare result writer
    # ---------------------------------------------------------------

    fieldnames = [
        "left_source_system",
        "left_source_id",
        "right_source_system",
        "right_source_id",
        "blocking_keys",
        "match_score",
        "decision",
        "matching_rule",
        "name_score",
        "address_score",
        "phone_score",
        "email_score",
        "dob_score",
        "reason",
    ]

    # ---------------------------------------------------------------
    # Counters
    # ---------------------------------------------------------------

    total_candidates = 0
    deterministic_matches = 0
    fuzzy_evaluated = 0

    fuzzy_matches = 0
    reviews = 0
    no_matches = 0

    missing_record_pairs = 0

    with (
        CANDIDATE_PATH.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as candidate_file,
        RESULT_PATH.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as result_file,
    ):

        candidate_reader = csv.DictReader(
            candidate_file
        )

        writer = csv.DictWriter(
            result_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for row in candidate_reader:

            total_candidates += 1

            left_ref_tuple = (
                row["left_source_system"],
                row["left_source_id"],
            )

            right_ref_tuple = (
                row["right_source_system"],
                row["right_source_id"],
            )

            left_row = silver_records.get(
                left_ref_tuple
            )

            right_row = silver_records.get(
                right_ref_tuple
            )

            if (
                left_row is None
                or right_row is None
            ):
                missing_record_pairs += 1
                continue

            left_ref = make_record_ref(
                row["left_source_system"],
                row["left_source_id"],
            )

            right_ref = make_record_ref(
                row["right_source_system"],
                row["right_source_id"],
            )

            blocking_keys = row.get(
                "blocking_keys",
                "",
            )

            # -------------------------------------------------------
            # Stage 1: Deterministic matching
            # -------------------------------------------------------

            deterministic_result = (
                deterministic_match(
                    left_ref,
                    right_ref,
                    left_row,
                    right_row,
                )
            )

            if deterministic_result is not None:

                deterministic_matches += 1

                writer.writerow(
                    serialize_result(
                        deterministic_result,
                        blocking_keys,
                    )
                )

                continue

            # -------------------------------------------------------
            # Stage 2: Fuzzy matching
            # -------------------------------------------------------

            fuzzy_evaluated += 1

            scores = calculate_fuzzy_scores(
                left_row,
                right_row,
            )

            fuzzy_result = score_match(
                left_ref,
                right_ref,
                scores,
            )

            if fuzzy_result.decision == "MATCH":
                fuzzy_matches += 1

            elif fuzzy_result.decision == "REVIEW":
                reviews += 1

            else:
                no_matches += 1

            writer.writerow(
                serialize_result(
                    fuzzy_result,
                    blocking_keys,
                )
            )

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------

    summary = {
        "silver_records": len(
            silver_records
        ),

        "candidate_pairs": total_candidates,

        "deterministic_matches": (
            deterministic_matches
        ),

        "fuzzy_evaluated": fuzzy_evaluated,

        "fuzzy_matches": fuzzy_matches,

        "review": reviews,

        "no_match": no_matches,

        "missing_record_pairs": (
            missing_record_pairs
        ),
    }

    with SUMMARY_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summary,
            file,
            indent=2,
        )

    print()
    print("ENTITY RESOLUTION SUMMARY")
    print("-" * 70)

    print(
        f"Candidate pairs:        "
        f"{total_candidates:,}"
    )

    print(
        f"Deterministic matches: "
        f"{deterministic_matches:,}"
    )

    print(
        f"Fuzzy evaluated:       "
        f"{fuzzy_evaluated:,}"
    )

    print(
        f"Fuzzy MATCH:           "
        f"{fuzzy_matches:,}"
    )

    print(
        f"REVIEW:                "
        f"{reviews:,}"
    )

    print(
        f"NO MATCH:              "
        f"{no_matches:,}"
    )

    print(
        f"Missing record pairs:  "
        f"{missing_record_pairs:,}"
    )

    print()
    print(
        f"Results: {RESULT_PATH}"
    )

    print(
        f"Summary: {SUMMARY_PATH}"
    )

    print()
    print("=" * 70)
    print(
        "Entity resolution processing complete."
    )


if __name__ == "__main__":
    main()