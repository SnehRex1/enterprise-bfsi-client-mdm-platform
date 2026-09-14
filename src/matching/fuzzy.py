from typing import Optional

from rapidfuzz import fuzz


def normalize(value: object) -> str:
    """
    Normalize a value for fuzzy comparison.

    None / empty values become "".
    """
    if value is None:
        return ""

    return str(value).strip().lower()


def get_field(row: dict, *field_names: str) -> str:
    """
    Return the first available value from the supplied field names.
    """
    for field_name in field_names:
        if field_name in row:
            value = row[field_name]

            if value is not None:
                return str(value).strip()

    return ""


def text_similarity(
    left_value: str,
    right_value: str,
) -> Optional[float]:
    """
    Fuzzy similarity for names and addresses.

    Returns None when either field is missing.
    Otherwise returns 0-100.
    """
    left = normalize(left_value)
    right = normalize(right_value)

    if not left or not right:
        return None

    return float(
        fuzz.token_set_ratio(left, right)
    )


def email_similarity(
    left_value: str,
    right_value: str,
) -> Optional[float]:
    """
    Similarity for email addresses.

    Exact normalized email = 100.
    Otherwise use character-level similarity.
    """
    left = normalize(left_value)
    right = normalize(right_value)

    if not left or not right:
        return None

    if left == right:
        return 100.0

    return float(
        fuzz.ratio(left, right)
    )


def phone_similarity(
    left_value: str,
    right_value: str,
) -> Optional[float]:
    """
    Similarity for normalized phone values.

    Exact values receive 100.

    For non-identical numbers we use digit-level similarity.
    """
    left = normalize(left_value)
    right = normalize(right_value)

    if not left or not right:
        return None

    if left == right:
        return 100.0

    return float(
        fuzz.ratio(left, right)
    )


def dob_similarity(
    left_value: str,
    right_value: str,
) -> Optional[float]:
    """
    DOB is not treated as ordinary fuzzy text.

    Exact normalized DOB = 100.
    Different DOB = 0.
    Missing DOB = None.
    """
    left = normalize(left_value)
    right = normalize(right_value)

    if not left or not right:
        return None

    if left == right:
        return 100.0

    return 0.0


def calculate_fuzzy_scores(
    left_row: dict,
    right_row: dict,
) -> dict[str, Optional[float]]:
    """
    Calculate all required field-level fuzzy scores.
    """

    left_name = get_field(
        left_row,
        "normalized_name",
        "name",
    )

    right_name = get_field(
        right_row,
        "normalized_name",
        "name",
    )

    left_address = get_field(
        left_row,
        "normalized_address",
        "address",
    )

    right_address = get_field(
        right_row,
        "normalized_address",
        "address",
    )

    left_phone = get_field(
        left_row,
        "normalized_phone",
        "phone",
    )

    right_phone = get_field(
        right_row,
        "normalized_phone",
        "phone",
    )

    left_email = get_field(
        left_row,
        "normalized_email",
        "email",
    )

    right_email = get_field(
        right_row,
        "normalized_email",
        "email",
    )

    left_dob = get_field(
        left_row,
        "normalized_dob",
        "dob",
    )

    right_dob = get_field(
        right_row,
        "normalized_dob",
        "dob",
    )

    return {
        "name_score": text_similarity(
            left_name,
            right_name,
        ),
        "address_score": text_similarity(
            left_address,
            right_address,
        ),
        "phone_score": phone_similarity(
            left_phone,
            right_phone,
        ),
        "email_score": email_similarity(
            left_email,
            right_email,
        ),
        "dob_score": dob_similarity(
            left_dob,
            right_dob,
        ),
    }