from src.matching.deterministic import (
    deterministic_match,
    match_email_dob_exact,
    match_lei_exact,
    match_phone_dob_exact,
    match_tax_id_exact,
)
from src.matching.models import RecordRef


LEFT_REF = RecordRef(
    source_system="CORE",
    source_id="C001",
)

RIGHT_REF = RecordRef(
    source_system="CRM",
    source_id="CRM001",
)


def test_lei_exact():
    left = {
        "lei": "549300ABC123"
    }

    right = {
        "lei": "549300ABC123"
    }

    assert match_lei_exact(left, right)


def test_tax_id_exact():
    left = {
        "tax_id": "GB123456789"
    }

    right = {
        "tax_id": "GB123456789"
    }

    assert match_tax_id_exact(left, right)


def test_phone_dob_exact():
    left = {
        "normalized_phone": "9876543210",
        "normalized_dob": "1988-06-12",
    }

    right = {
        "normalized_phone": "9876543210",
        "normalized_dob": "1988-06-12",
    }

    assert match_phone_dob_exact(left, right)


def test_email_dob_exact():
    left = {
        "normalized_email": "rahul@example.com",
        "normalized_dob": "1988-06-12",
    }

    right = {
        "normalized_email": "rahul@example.com",
        "normalized_dob": "1988-06-12",
    }

    assert match_email_dob_exact(left, right)


def test_phone_dob_requires_both_fields():
    left = {
        "normalized_phone": "9876543210",
        "normalized_dob": "",
    }

    right = {
        "normalized_phone": "9876543210",
        "normalized_dob": "1988-06-12",
    }

    assert not match_phone_dob_exact(left, right)


def test_deterministic_match_returns_explainable_result():
    left = {
        "normalized_phone": "9876543210",
        "normalized_dob": "1988-06-12",
    }

    right = {
        "normalized_phone": "9876543210",
        "normalized_dob": "1988-06-12",
    }

    result = deterministic_match(
        LEFT_REF,
        RIGHT_REF,
        left,
        right,
    )

    assert result is not None
    assert result.decision == "MATCH"
    assert result.matching_rule == "PHONE_DOB_EXACT"
    assert result.match_score == 100.0


def test_no_deterministic_match_returns_none():
    left = {
        "normalized_phone": "1111111111",
        "normalized_dob": "1988-06-12",
        "normalized_email": "a@example.com",
    }

    right = {
        "normalized_phone": "2222222222",
        "normalized_dob": "1990-01-01",
        "normalized_email": "b@example.com",
    }

    result = deterministic_match(
        LEFT_REF,
        RIGHT_REF,
        left,
        right,
    )

    assert result is None