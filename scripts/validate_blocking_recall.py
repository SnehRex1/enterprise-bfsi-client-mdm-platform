import csv
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path


# ---------------------------------------------------------------------------
# Project root / import setup
# ---------------------------------------------------------------------------
# This script lives at:
#
# project_root/
#     scripts/
#         validate_blocking_recall.py
#
# parents[1] = project root
#
# We add the project root so the script behaves consistently when executed
# directly from PowerShell.
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

GROUND_TRUTH_PATH = (
    PROJECT_ROOT
    / "data"
    / "dev"
    / "ground_truth"
    / "ground_truth.csv"
)

CANDIDATE_PATH = (
    PROJECT_ROOT
    / "data"
    / "dev"
    / "matching"
    / "candidate_pairs.csv"
)


# ---------------------------------------------------------------------------
# Helper: create a canonical representation of a source record
# ---------------------------------------------------------------------------

def make_record_ref(
    source_system: str,
    source_id: str,
) -> tuple[str, str]:
    """
    Represent a source record as a stable tuple.

    Example:

        ("CORE", "C00000001")
    """

    return (
        source_system.strip().upper(),
        source_id.strip(),
    )


# ---------------------------------------------------------------------------
# Helper: normalize a pair so A-B and B-A are treated as the same pair
# ---------------------------------------------------------------------------

def make_pair_key(
    left: tuple[str, str],
    right: tuple[str, str],
) -> tuple[
    tuple[str, str],
    tuple[str, str],
]:
    """
    Return a canonical ordering for a pair.

    This means:

        A-B

    and:

        B-A

    become the same key.
    """

    return tuple(
        sorted(
            [left, right],
            key=lambda record: (
                record[0],
                record[1],
            ),
        )
    )


# ---------------------------------------------------------------------------
# Read ground truth
# ---------------------------------------------------------------------------

def load_ground_truth() -> list[dict[str, str]]:
    """
    Load the DEV ground-truth mapping.
    """

    with GROUND_TRUTH_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        return list(csv.DictReader(file))


# ---------------------------------------------------------------------------
# Build the true entity pairs from ground truth
# ---------------------------------------------------------------------------

def build_true_pairs(
    ground_truth_rows: list[dict[str, str]],
) -> set:
    """
    Build every pair of source records that belongs to the same hidden entity.

    Important:
        entity_key is used here ONLY for evaluation.

    It is never passed into the matching engine.
    """

    # entity_key -> list of source records
    entity_records = defaultdict(list)

    for row in ground_truth_rows:

        entity_key = row["entity_key"].strip()

        record_ref = make_record_ref(
            row["source_system"],
            row["source_id"],
        )

        entity_records[entity_key].append(record_ref)

    true_pairs = set()

    for records in entity_records.values():

        # An entity with only one source record has no pair to compare.
        if len(records) < 2:
            continue

        # combinations(records, 2) creates every unique pair.
        for left, right in combinations(records, 2):

            true_pairs.add(
                make_pair_key(left, right)
            )

    return true_pairs


# ---------------------------------------------------------------------------
# Read candidate pairs produced by blocking
# ---------------------------------------------------------------------------

def load_candidate_pairs() -> set:
    """
    Load candidate pairs produced by the blocking engine.
    """

    candidate_pairs = set()

    with CANDIDATE_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            left = make_record_ref(
                row["left_source_system"],
                row["left_source_id"],
            )

            right = make_record_ref(
                row["right_source_system"],
                row["right_source_id"],
            )

            candidate_pairs.add(
                make_pair_key(left, right)
            )

    return candidate_pairs


# ---------------------------------------------------------------------------
# Calculate recall
# ---------------------------------------------------------------------------

def calculate_recall(
    true_pairs: set,
    candidate_pairs: set,
) -> tuple[float, set]:
    """
    Calculate blocking recall.

    Recall =
        true pairs captured by blocking
        --------------------------------
        total true pairs
    """

    if not true_pairs:
        return 1.0, set()

    captured_pairs = true_pairs & candidate_pairs

    missed_pairs = true_pairs - candidate_pairs

    recall = (
        len(captured_pairs)
        / len(true_pairs)
    )

    return recall, missed_pairs


# ---------------------------------------------------------------------------
# Source-pair classification
# ---------------------------------------------------------------------------

def source_pair_type(
    pair: tuple[
        tuple[str, str],
        tuple[str, str],
    ]
) -> str:

    left_source = pair[0][0]
    right_source = pair[1][0]

    if left_source == right_source:
        return f"{left_source}-{right_source}"

    return "-".join(
        sorted(
            [left_source, right_source]
        )
    )


# ---------------------------------------------------------------------------
# Recall by source combination
# ---------------------------------------------------------------------------

def calculate_recall_by_source(
    true_pairs: set,
    candidate_pairs: set,
) -> dict[str, tuple[int, int, float]]:

    grouped_true = defaultdict(set)

    for pair in true_pairs:

        grouped_true[
            source_pair_type(pair)
        ].add(pair)

    results = {}

    for pair_type, pairs in grouped_true.items():

        captured = pairs & candidate_pairs

        total = len(pairs)

        recall = (
            len(captured) / total
            if total
            else 1.0
        )

        results[pair_type] = (
            total,
            len(captured),
            recall,
        )

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:

    print("BLOCKING RECALL VALIDATION")
    print("=" * 70)

    # Load evaluation truth.
    ground_truth_rows = load_ground_truth()

    print(
        f"Ground-truth mappings loaded: "
        f"{len(ground_truth_rows):,}"
    )

    # Build true pairs.
    true_pairs = build_true_pairs(
        ground_truth_rows
    )

    print(
        f"True entity pairs: "
        f"{len(true_pairs):,}"
    )

    # Load candidate pairs generated by blocking.
    candidate_pairs = load_candidate_pairs()

    print(
        f"Candidate pairs loaded: "
        f"{len(candidate_pairs):,}"
    )

    # Calculate recall.
    recall, missed_pairs = calculate_recall(
        true_pairs,
        candidate_pairs,
    )

    print()
    print("OVERALL BLOCKING RECALL")
    print("-" * 70)

    print(
        f"Captured true pairs: "
        f"{len(true_pairs) - len(missed_pairs):,}"
    )

    print(
        f"Missed true pairs:   "
        f"{len(missed_pairs):,}"
    )

    print(
        f"Blocking recall:     "
        f"{recall * 100:.4f}%"
    )

    # -----------------------------------------------------------------------
    # Recall by source combination
    # -----------------------------------------------------------------------

    print()
    print("RECALL BY SOURCE COMBINATION")
    print("-" * 70)

    source_results = calculate_recall_by_source(
        true_pairs,
        candidate_pairs,
    )

    for pair_type in sorted(source_results):

        total, captured, pair_recall = source_results[
            pair_type
        ]

        print(
            f"{pair_type:<15} "
            f"captured={captured:>8,} "
            f"total={total:>8,} "
            f"recall={pair_recall * 100:>8.4f}%"
        )

    # -----------------------------------------------------------------------
    # Show missed examples
    # -----------------------------------------------------------------------

    if missed_pairs:

        print()
        print("EXAMPLE MISSED TRUE PAIRS")
        print("-" * 70)

        for pair in list(missed_pairs)[:10]:

            print(
                f"{pair[0][0]}:{pair[0][1]}"
                f" <-> "
                f"{pair[1][0]}:{pair[1][1]}"
            )

    else:

        print()
        print("SUCCESS: no true entity pairs were missed by blocking.")

    print()
    print("=" * 70)
    print("Blocking recall validation complete.")


if __name__ == "__main__":
    main()