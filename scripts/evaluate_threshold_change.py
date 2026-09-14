from __future__ import annotations

import itertools
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RESULTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "dev"
    / "matching"
    / "entity_resolution_results.csv"
)

GROUND_TRUTH_PATH = (
    PROJECT_ROOT
    / "data"
    / "dev"
    / "ground_truth"
    / "ground_truth.csv"
)


def build_truth_pairs(truth_df: pd.DataFrame) -> set:
    truth_pairs = set()

    for _, group in truth_df.groupby("entity_key", sort=False):
        refs = [
            (str(row.source_system), str(row.source_id))
            for row in group.itertuples(index=False)
        ]

        for left, right in itertools.combinations(refs, 2):
            truth_pairs.add(tuple(sorted([left, right])))

    return truth_pairs


def make_pair_key(row) -> tuple:
    left = (
        str(row["left_source_system"]),
        str(row["left_source_id"]),
    )

    right = (
        str(row["right_source_system"]),
        str(row["right_source_id"]),
    )

    return tuple(sorted([left, right]))


def evaluate_threshold(
    results: pd.DataFrame,
    truth_pairs: set,
    threshold: float,
) -> dict:

    working = results.copy()

    working["pair_key"] = working.apply(make_pair_key, axis=1)

    # Deterministic matches remain MATCH.
    working["predicted_match"] = (
        working["matching_rule"].astype(str) != "FUZZY_WEIGHTED"
    )

    # Re-evaluate fuzzy decisions using only a different MATCH threshold.
    fuzzy_mask = (
        working["matching_rule"].astype(str) == "FUZZY_WEIGHTED"
    )

    working.loc[fuzzy_mask, "predicted_match"] = (
        pd.to_numeric(
            working.loc[fuzzy_mask, "match_score"],
            errors="coerce",
        )
        >= threshold
    )

    predicted_matches = set(
        working.loc[
            working["predicted_match"],
            "pair_key",
        ]
    )

    true_positives = len(predicted_matches & truth_pairs)
    false_positives = len(predicted_matches - truth_pairs)
    false_negatives = len(truth_pairs - predicted_matches)

    precision = (
        true_positives / (true_positives + false_positives)
        if true_positives + false_positives
        else 0.0
    )

    recall = (
        true_positives / (true_positives + false_negatives)
        if true_positives + false_negatives
        else 0.0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "threshold": threshold,
        "TP": true_positives,
        "FP": false_positives,
        "FN": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def main() -> None:
    print("=" * 80)
    print("MATCH THRESHOLD EXPERIMENT")
    print("=" * 80)

    print("\nLoading entity-resolution results...")
    results = pd.read_csv(RESULTS_PATH)

    print("Loading ground truth...")
    truth = pd.read_csv(GROUND_TRUTH_PATH)

    truth_pairs = build_truth_pairs(truth)

    print(f"True entity pairs: {len(truth_pairs):,}")
    print(f"Result rows:       {len(results):,}")

    thresholds = [90, 89, 88, 87, 86, 85]

    rows = []

    for threshold in thresholds:
        rows.append(
            evaluate_threshold(
                results,
                truth_pairs,
                threshold,
            )
        )

    output = pd.DataFrame(rows)

    print("\n")
    print(
        output.to_string(
            index=False,
            formatters={
                "precision": "{:.4%}".format,
                "recall": "{:.4%}".format,
                "f1": "{:.4%}".format,
            },
        )
    )


if __name__ == "__main__":
    main()