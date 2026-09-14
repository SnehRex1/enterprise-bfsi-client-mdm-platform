from src.matching.fuzzy import (
    calculate_fuzzy_scores,
    dob_similarity,
    email_similarity,
    phone_similarity,
    text_similarity,
)


def test_name_similarity_is_high_for_small_variations():
    score = text_similarity(
        "RAHUL KUMAR SHARMA",
        "RAHUL K SHARMA",
    )

    assert score is not None
    assert score >= 80


def test_exact_email_is_100():
    score = email_similarity(
        "rahul@example.com",
        "rahul@example.com",
    )

    assert score == 100.0


def test_exact_phone_is_100():
    score = phone_similarity(
        "9876543210",
        "9876543210",
    )

    assert score == 100.0


def test_exact_dob_is_100():
    score = dob_similarity(
        "1988-06-12",
        "1988-06-12",
    )

    assert score == 100.0


def test_different_dob_is_zero():
    score = dob_similarity(
        "1988-06-12",
        "1989-06-12",
    )

    assert score == 0.0


def test_missing_values_return_none():
    assert (
        text_similarity(
            "",
            "rahul sharma",
        )
        is None
    )

    assert (
        email_similarity(
            "",
            "rahul@example.com",
        )
        is None
    )

    assert (
        phone_similarity(
            "",
            "9876543210",
        )
        is None
    )


def test_all_fuzzy_scores_are_returned():

    left = {
        "normalized_name": "RAHUL KUMAR SHARMA",
        "normalized_address": "10 HIGH STREET LONDON SW1A1AA",
        "normalized_phone": "9876543210",
        "normalized_email": "rahul@example.com",
        "normalized_dob": "1988-06-12",
    }

    right = {
        "normalized_name": "RAHUL K SHARMA",
        "normalized_address": "HIGH STREET LONDON SW1A1AA",
        "normalized_phone": "9876543210",
        "normalized_email": "rahul@example.com",
        "normalized_dob": "1988-06-12",
    }

    scores = calculate_fuzzy_scores(
        left,
        right,
    )

    assert set(scores.keys()) == {
        "name_score",
        "address_score",
        "phone_score",
        "email_score",
        "dob_score",
    }

    assert scores["name_score"] is not None
    assert scores["address_score"] is not None
    assert scores["phone_score"] == 100.0
    assert scores["email_score"] == 100.0
    assert scores["dob_score"] == 100.0