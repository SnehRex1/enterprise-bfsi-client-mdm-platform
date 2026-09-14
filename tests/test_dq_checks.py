from src.quality.dq_checks import (
    check_completeness,
    check_consistency,
    check_referential_integrity,
    check_validity,
    run_all_checks,
)


def test_complete_record_has_no_completeness_issue():

    row = {
        "normalized_name": "RAHUL SHARMA",
        "source_id": "C00000001",
    }

    assert (
        check_completeness(row)
        == []
    )


def test_blank_name_is_detected():

    row = {
        "normalized_name": "",
        "source_id": "C00000001",
    }

    issues = check_completeness(
        row
    )

    assert (
        "completeness: normalized_name is blank"
        in issues
    )


def test_invalid_phone_is_detected():

    row = {
        "normalized_phone": "ABC123",
    }

    issues = check_validity(
        row
    )

    assert (
        "validity: normalized_phone contains non-digits"
        in issues
    )


def test_invalid_email_is_detected():

    row = {
        "normalized_email": "not-an-email",
    }

    issues = check_validity(
        row
    )

    assert (
        "validity: normalized_email is invalid"
        in issues
    )


def test_future_dob_is_detected():

    row = {
        "normalized_dob": "2090-01-01",
    }

    issues = check_consistency(
        row
    )

    assert any(
        "in the future" in issue
        for issue in issues
    )


def test_implausible_age_is_detected():

    row = {
        "normalized_dob": "1850-01-01",
    }

    issues = check_consistency(
        row
    )

    assert any(
        "age > 110" in issue
        for issue in issues
    )


def test_missing_source_reference_is_detected():

    row = {
        "source_system": "CORE",
        "source_id": "",
    }

    issues = check_referential_integrity(
        row
    )

    assert (
        "referential_integrity: source_id is missing"
        in issues
    )


def test_good_record_passes_all_checks():

    row = {
        "source_system": "CORE",
        "source_id": "C00000001",
        "normalized_name": "RAHUL SHARMA",
        "normalized_phone": "447123456789",
        "normalized_email": "rahul@example.com",
        "normalized_dob": "1984-03-12",
        "phone": "447123456789",
        "dob": "1984-03-12",
    }

    assert run_all_checks(
        row
    ) == []