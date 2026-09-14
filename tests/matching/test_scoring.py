from src.matching.models import RecordRef
from src.matching.scoring import (
    MATCH_THRESHOLD,
    REVIEW_THRESHOLD,
    calculate_weighted_score,
    make_decision,
    score_match,
)


LEFT_REF = RecordRef(
    source_system="CORE",
    source_id="C001",
)

RIGHT_REF = RecordRef(
    source_system="CRM",
    source_id="CRM001",
)


def test_weighted_score_ignores_missing_fields():

    scores = {
        "name_score": 100.0,
        "address_score": 100.0,
        "phone_score": None,
        "email_score": None,
        "dob_score": None,
    }

    score, count = calculate_weighted_score(
        scores
    )

    assert count == 2
    assert score == 100.0


def test_high_score_is_match():

    decision = make_decision(
        MATCH_THRESHOLD,
        5,
    )

    assert decision == "MATCH"


def test_middle_score_is_review():

    decision = make_decision(
        REVIEW_THRESHOLD,
        5,
    )

    assert decision == "REVIEW"


def test_low_score_is_no_match():

    decision = make_decision(
        50.0,
        5,
    )

    assert decision == "NO MATCH"


def test_too_few_fields_is_no_match():

    decision = make_decision(
        100.0,
        1,
    )

    assert decision == "NO MATCH"


def test_score_match_is_explainable():

    scores = {
        "name_score": 95.0,
        "address_score": 90.0,
        "phone_score": 100.0,
        "email_score": 100.0,
        "dob_score": 100.0,
    }

    result = score_match(
        LEFT_REF,
        RIGHT_REF,
        scores,
    )

    assert result.decision == "MATCH"

    assert (
        result.matching_rule
        == "FUZZY_WEIGHTED"
    )

    assert result.match_score >= 90.0

    assert result.name_score == 95.0
    assert result.address_score == 90.0
    assert result.phone_score == 100.0
    assert result.email_score == 100.0
    assert result.dob_score == 100.0

    assert result.reason is not None
    assert "Fuzzy weighted score" in result.reason