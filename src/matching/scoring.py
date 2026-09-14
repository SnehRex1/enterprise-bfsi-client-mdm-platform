from typing import Optional

from src.matching.models import MatchResult, RecordRef


DEFAULT_WEIGHTS = {
    "name_score": 0.30,
    "address_score": 0.20,
    "phone_score": 0.20,
    "email_score": 0.15,
    "dob_score": 0.15,
}

MIN_COMPARABLE_FIELDS = 2

MATCH_THRESHOLD = 85.0
REVIEW_THRESHOLD = 70.0


def calculate_weighted_score(
    scores: dict[str, Optional[float]],
    weights: Optional[dict[str, float]] = None,
) -> tuple[float, int]:
    """
    Calculate a weighted average using only available fields.

    Missing fields are excluded from the denominator rather than treated
    as zero-quality evidence.

    Returns:
        (score, comparable_field_count)
    """

    if weights is None:
        weights = DEFAULT_WEIGHTS

    weighted_total = 0.0
    available_weight = 0.0
    comparable_fields = 0

    for field, weight in weights.items():

        value = scores.get(field)

        if value is None:
            continue

        weighted_total += value * weight
        available_weight += weight
        comparable_fields += 1

    if comparable_fields == 0:
        return 0.0, 0

    score = (
        weighted_total / available_weight
    )

    return round(score, 4), comparable_fields


def make_decision(
    score: float,
    comparable_fields: int,
) -> str:
    """
    Convert score into the frozen decision bands.
    """

    if comparable_fields < MIN_COMPARABLE_FIELDS:
        return "NO MATCH"

    if score >= MATCH_THRESHOLD:
        return "MATCH"

    if score >= REVIEW_THRESHOLD:
        return "REVIEW"

    return "NO MATCH"


def build_reason(
    scores: dict[str, Optional[float]],
    score: float,
    decision: str,
    comparable_fields: int,
) -> str:
    """
    Build a human-readable explanation for the decision.
    """

    available = []

    for field, value in scores.items():

        if value is not None:

            available.append(
                f"{field}={value:.1f}"
            )

    evidence = ", ".join(available)

    return (
        f"Fuzzy weighted score={score:.2f}; "
        f"decision={decision}; "
        f"comparable_fields={comparable_fields}; "
        f"evidence=[{evidence}]"
    )


def score_match(
    left_ref: RecordRef,
    right_ref: RecordRef,
    scores: dict[str, Optional[float]],
    weights: Optional[dict[str, float]] = None,
) -> MatchResult:
    """
    Build the final explainable fuzzy MatchResult.
    """

    score, comparable_fields = calculate_weighted_score(
        scores,
        weights=weights,
    )

    decision = make_decision(
        score,
        comparable_fields,
    )

    reason = build_reason(
        scores,
        score,
        decision,
        comparable_fields,
    )

    return MatchResult(
        left=left_ref,
        right=right_ref,
        match_score=score,
        decision=decision,
        matching_rule="FUZZY_WEIGHTED",
        name_score=scores.get("name_score"),
        address_score=scores.get("address_score"),
        phone_score=scores.get("phone_score"),
        email_score=scores.get("email_score"),
        dob_score=scores.get("dob_score"),
        reason=reason,
    )