from __future__ import annotations

import itertools
import json
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

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "dev"
    / "matching"
    / "diagnostics"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def pair_key(
    source_system_a: str,
    source_id_a: str,
    source_system_b: str,
    source_id_b: str,
) -> tuple[tuple[str, str], tuple[str, str]]:
    left = (str(source_system_a), str(source_id_a))
    right = (str(source_system_b), str(source_id_b))

    return tuple(sorted([left, right]))  # type: ignore[return-value]


def build_truth_pairs(truth_df: pd.DataFrame) -> set:
    """
    Build all true record-to-record pairs belonging to the same entity_key.
    """

    truth_pairs = set()

    for _, group in truth_df.groupby("entity_key", sort=False):
        refs = [
            (str(row.source_system), str(row.source_id))
            for row in group.itertuples(index=False)
        ]

        for left, right in itertools.combinations(refs, 2):
            truth_pairs.add(tuple(sorted([left, right])))

    return truth_pairs


def result_pair_key(row) -> tuple:
    return pair_key(
        row["left_source_system"],
        row["left_source_id"],
        row["right_source_system"],
        row["right_source_id"],
    )


def main() -> None:
    print("=" * 80)
    print("ENTITY RESOLUTION DIAGNOSTICS")
    print("=" * 80)

    print("\nLoading results...")
    results = pd.read_csv(RESULTS_PATH)

    print("Loading ground truth...")
    truth = pd.read_csv(GROUND_TRUTH_PATH)

    print(f"Result rows:       {len(results):,}")
    print(f"Ground truth rows: {len(truth):,}")

    print("\nBuilding true entity pairs...")
    truth_pairs = build_truth_pairs(truth)

    print(f"True entity pairs: {len(truth_pairs):,}")

    results["pair_key"] = results.apply(result_pair_key, axis=1)

    result_lookup = {
        row["pair_key"]: row
        for _, row in results.iterrows()
    }

    predicted_matches = set(
        results.loc[
            results["decision"].astype(str).str.upper() == "MATCH",
            "pair_key",
        ]
    )

    predicted_reviews = set(
        results.loc[
            results["decision"].astype(str).str.upper() == "REVIEW",
            "pair_key",
        ]
    )

    # ------------------------------------------------------------
    # FALSE POSITIVES
    # ------------------------------------------------------------

    false_positive_pairs = predicted_matches - truth_pairs

    fp_rows = results[
        results["pair_key"].isin(false_positive_pairs)
    ].copy()

    fp_rows = fp_rows.drop(columns=["pair_key"])

    fp_path = OUTPUT_DIR / "false_positives.csv"
    fp_rows.to_csv(fp_path, index=False)

    # ------------------------------------------------------------
    # TRUE MATCHES CURRENTLY IN REVIEW
    # ------------------------------------------------------------

    true_review_pairs = predicted_reviews & truth_pairs

    review_true_rows = results[
        results["pair_key"].isin(true_review_pairs)
    ].copy()

    review_true_rows = review_true_rows.drop(columns=["pair_key"])

    review_path = OUTPUT_DIR / "true_matches_in_review.csv"
    review_true_rows.to_csv(review_path, index=False)

    # ------------------------------------------------------------
    # TRUE PAIRS MISSING FROM CANDIDATE RESULTS
    # ------------------------------------------------------------

    result_pairs = set(result_lookup.keys())

    blocked_miss_pairs = truth_pairs - result_pairs

    blocked_miss_rows = []

    for left, right in blocked_miss_pairs:
        blocked_miss_rows.append(
            {
                "left_source_system": left[0],
                "left_source_id": left[1],
                "right_source_system": right[0],
                "right_source_id": right[1],
            }
        )

    blocked_miss_df = pd.DataFrame(blocked_miss_rows)

    blocked_path = OUTPUT_DIR / "blocked_true_pairs_missed.csv"
    blocked_miss_df.to_csv(blocked_path, index=False)

    # ------------------------------------------------------------
    # TRUE PAIRS THAT REACHED MATCHING BUT WERE NOT MATCHED
    # ------------------------------------------------------------

    reached_truth_pairs = truth_pairs & result_pairs

    downstream_false_negative_pairs = {
        pair
        for pair in reached_truth_pairs
        if pair not in predicted_matches
    }

    downstream_fn_rows = results[
        results["pair_key"].isin(downstream_false_negative_pairs)
    ].copy()

    downstream_fn_rows = downstream_fn_rows.drop(columns=["pair_key"])

    downstream_fn_path = OUTPUT_DIR / "downstream_false_negatives.csv"
    downstream_fn_rows.to_csv(downstream_fn_path, index=False)

    # ------------------------------------------------------------
    # DECISION DISTRIBUTION FOR TRUE PAIRS
    # ------------------------------------------------------------

    true_result_rows = results[
        results["pair_key"].isin(truth_pairs)
    ].copy()

    decision_counts = (
        true_result_rows["decision"]
        .astype(str)
        .str.upper()
        .value_counts()
        .to_dict()
    )

    # ------------------------------------------------------------
    # SCORE STATISTICS
    # ------------------------------------------------------------

    fuzzy_results = results[
        results["matching_rule"].astype(str) == "FUZZY_WEIGHTED"
    ].copy()

    fuzzy_true = fuzzy_results[
        fuzzy_results["pair_key"].isin(truth_pairs)
    ]

    fuzzy_false_positive = fuzzy_results[
        fuzzy_results["pair_key"].isin(false_positive_pairs)
    ]

    fuzzy_downstream_fn = fuzzy_results[
        fuzzy_results["pair_key"].isin(downstream_false_negative_pairs)
    ]

    def score_summary(df: pd.DataFrame) -> dict:
        if df.empty:
            return {}

        return {
            "count": int(len(df)),
            "mean_match_score": float(df["match_score"].mean()),
            "min_match_score": float(df["match_score"].min()),
            "max_match_score": float(df["match_score"].max()),
        }

    summary = {
        "true_entity_pairs": len(truth_pairs),
        "candidate_result_pairs": len(result_pairs),
        "false_positive_count": len(false_positive_pairs),
        "blocked_true_pairs_missed": len(blocked_miss_pairs),
        "downstream_false_negative_count": len(
            downstream_false_negative_pairs
        ),
        "true_pairs_in_review": len(true_review_pairs),
        "decision_distribution_among_true_pairs": decision_counts,
        "fuzzy_true_score_summary": score_summary(fuzzy_true),
        "fuzzy_false_positive_score_summary": score_summary(
            fuzzy_false_positive
        ),
        "fuzzy_downstream_false_negative_score_summary": score_summary(
            fuzzy_downstream_fn
        ),
    }

    summary_path = OUTPUT_DIR / "diagnostic_summary.json"

    with open(summary_path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    # ------------------------------------------------------------
    # PRINT SUMMARY
    # ------------------------------------------------------------

    print("\n" + "=" * 80)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 80)

    print(f"True entity pairs:                {len(truth_pairs):,}")
    print(f"Candidate/result pairs:           {len(result_pairs):,}")
    print(f"False positives:                  {len(false_positive_pairs):,}")
    print(f"Blocked true pairs missed:        {len(blocked_miss_pairs):,}")
    print(
        "Downstream false negatives:       "
        f"{len(downstream_false_negative_pairs):,}"
    )
    print(
        "True pairs currently in REVIEW:  "
        f"{len(true_review_pairs):,}"
    )

    print("\nTrue-pair decisions:")
    for decision, count in sorted(decision_counts.items()):
        print(f"  {decision:<15} {count:>10,}")

    print("\nFuzzy true-pair score summary:")
    print(json.dumps(summary["fuzzy_true_score_summary"], indent=2))

    print("\nFuzzy false-positive score summary:")
    print(
        json.dumps(
            summary["fuzzy_false_positive_score_summary"],
            indent=2,
        )
    )

    print("\nFuzzy downstream-FN score summary:")
    print(
        json.dumps(
            summary[
                "fuzzy_downstream_false_negative_score_summary"
            ],
            indent=2,
        )
    )

    print("\nOutput files:")
    print(f"  {fp_path}")
    print(f"  {review_path}")
    print(f"  {blocked_path}")
    print(f"  {downstream_fn_path}")
    print(f"  {summary_path}")

    print("\nDiagnostics complete.")


if __name__ == "__main__":
    main()