from src.matching.blocking import (
    extract_postcode,
    extract_surname,
    make_email_key,
    make_phone_suffix_key,
    make_surname_dob_key,
)


def test_extract_surname():
    assert extract_surname("RAHUL KUMAR SHARMA") == "SHARMA"


def test_extract_postcode():
    address = "10 HIGH STREET, LONDON, SW1A 1AA"

    assert extract_postcode(address) == "SW1A1AA"


def test_surname_dob_key():
    row = {
        "normalized_name": "RAHUL KUMAR SHARMA",
        "normalized_dob": "1988-06-12",
    }

    assert make_surname_dob_key(row) == "SHARMA|1988-06-12"


def test_email_key():
    row = {
        "normalized_email": "rahul.sharma@example.com",
    }

    assert make_email_key(row) == "rahul.sharma@example.com"


def test_phone_suffix_key():
    row = {
        "normalized_phone": "919876543210",
    }

    assert make_phone_suffix_key(row, suffix_length=7) == "6543210"