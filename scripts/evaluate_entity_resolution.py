import csv
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


GROUND_TRUTH_PATH = (
    PROJECT_ROOT
    / "data"
    / "dev"
    / "ground_truth"
    / "ground_truth.csv"
)

RESULT_PATH = (
    PROJECT_ROOT
    / "data"
    / "dev"
    / "matching"
    / "entity_resolution_results.csv"
)


def make_record_ref(
    source_system,
    source_id,
):
    return (
        source_system.strip().upper(),
        source_id.strip(),
    )


def make_pair_key(
    left,
    right,
):
    return tuple(
        sorted(
            [left, right],
            key=lambda record: (
                record[0],
                record[1],
            ),
        )
    )


def build_true_pairs():

    entity_records = defaultdict(list)

    with GROUND_TRUTH_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            entity_key = row[
                "entity_key"
            ].strip()

            record_ref = make_record_ref(
                row["source_system"],
                row["source_id"],
            )

            entity_records[
                entity_key
            ].append(record_ref)

    true_pairs = set()

    for records in entity_records.values():

        if len(records) < 2:
            continue

        for left, right in combinations(
            records,
            2,
        ):

            true_pairs.add(
                make_pair_key(
                    left,
                    right,
                )
            )

    return true_pairs


def load_predicted_matches():

    predicted_matches = set()
    review_pairs = set()

    total_rows = 0

    with RESULT_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            total_rows += 1

            left = make_record_ref(
                row["left_source_system"],
                row["left_source_id"],
            )

            right = make_record_ref(
                row["right_source_system"],
                row["right_source_id"],
            )

            pair = make_pair_key(
                left,
                right,
            )

            decision = row[
                "decision"
            ].strip().upper()

            if decision == "MATCH":
                predicted_matches.add(pair)

            elif decision == "REVIEW":
                review_pairs.add(pair)

    return (
        predicted_matches,
        review_pairs,
        total_rows,
    )


def calculate_metrics(
    true_pairs,
    predicted_matches,
):

    true_positive = len(
        true_pairs
        & predicted_matches
    )

    false_positive = len(
        predicted_matches
        - true_pairs
    )

    false_negative = len(
        true_pairs
        - predicted_matches
    )

    precision = (
        true_positive
        / (
            true_positive
            + false_positive
        )
        if (
            true_positive
            + false_positive
        )
        else 0.0
    )

    recall = (
        true_positive
        / (
            true_positive
            + false_negative
        )
        if (
            true_positive
            + false_negative
        )
        else 0.0
    )

    f1 = (
        2
        * precision
        * recall
        / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def source_pair_type(pair):

    left_source = pair[0][0]
    right_source = pair[1][0]

    return "-".join(
        sorted(
            [
                left_source,
                right_source,
            ]
        )
    )


def main():

    print(
        "ENTITY RESOLUTION EVALUATION"
    )

    print("=" * 70)

    true_pairs = build_true_pairs()

    (
        predicted_matches,
        review_pairs,
        total_result_rows,
    ) = load_predicted_matches()

    print(
        f"True entity pairs: "
        f"{len(true_pairs):,}"
    )

    print(
        f"Result rows: "
        f"{total_result_rows:,}"
    )

    print(
        f"Predicted MATCH pairs: "
        f"{len(predicted_matches):,}"
    )

    print(
        f"REVIEW pairs: "
        f"{len(review_pairs):,}"
    )

    print()

    metrics = calculate_metrics(
        true_pairs,
        predicted_matches,
    )

    print("OVERALL METRICS")
    print("-" * 70)

    print(
        f"True positives:  "
        f"{metrics['true_positive']:,}"
    )

    print(
        f"False positives: "
        f"{metrics['false_positive']:,}"
    )

    print(
        f"False negatives: "
        f"{metrics['false_negative']:,}"
    )

    print(
        f"Precision: "
        f"{metrics['precision'] * 100:.4f}%"
    )

    print(
        f"Recall:    "
        f"{metrics['recall'] * 100:.4f}%"
    )

    print(
        f"F1:        "
        f"{metrics['f1'] * 100:.4f}%"
    )

    # ---------------------------------------------------------------
    # Source-pair recall
    # ---------------------------------------------------------------

    grouped_true = defaultdict(set)

    for pair in true_pairs:

        grouped_true[
            source_pair_type(pair)
        ].add(pair)

    print()
    print(
        "RECALL BY SOURCE COMBINATION"
    )
    print("-" * 70)

    for pair_type in sorted(
        grouped_true
    ):

        pairs = grouped_true[
            pair_type
        ]

        captured = (
            pairs
            & predicted_matches
        )

        recall = (
            len(captured)
            / len(pairs)
            if pairs
            else 0.0
        )

        print(
            f"{pair_type:<15} "
            f"captured={len(captured):>8,} "
            f"total={len(pairs):>8,} "
            f"recall={recall * 100:>8.4f}%"
        )

    print()
    print("=" * 70)
    print(
        "Entity resolution evaluation complete."
    )


if __name__ == "__main__":
    main()