from src.standardization.normalizers import (
    normalize_address,
    normalize_date,
    normalize_email,
    normalize_name,
    normalize_phone,
)


def test_normalize_name():
    assert (
        normalize_name(
            " Rahul K.  Sharma "
        )
        == "RAHUL K SHARMA"
    )


def test_normalize_phone():
    assert (
        normalize_phone(
            "+44 7123-456789"
        )
        == "447123456789"
    )


def test_normalize_email():
    assert (
        normalize_email(
            " Rahul@Example.COM "
        )
        == "rahul@example.com"
    )


def test_normalize_address():
    assert (
        normalize_address(
            "10 High Street, London"
        )
        == "10 HIGH STREET LONDON"
    )


def test_normalize_date():
    assert (
        normalize_date(
            "12/03/1984"
        )
        == "1984-03-12"
    )


def test_blank_values():
    assert normalize_name("") == ""
    assert normalize_phone("") == ""
    assert normalize_email("") == ""
    assert normalize_address("") == ""
    assert normalize_date("") == ""


def test_none_values():
    assert normalize_name(None) == ""
    assert normalize_phone(None) == ""
    assert normalize_email(None) == ""
    assert normalize_address(None) == ""
    assert normalize_date(None) == ""