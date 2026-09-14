from typing import Optional

from src.matching.models import MatchResult, RecordRef


def normalize(value: object) -> str:
    """
    Convert a value into a comparable normalized string.

    Empty/null values become "".
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


def exact_equal(
    left_row: dict,
    right_row: dict,
    *field_names: str,
) -> bool:
    """
    Return True when a field is present on both records
    and the normalized values are exactly equal.
    """
    left_value = normalize(
        get_field(left_row, *field_names)
    )

    right_value = normalize(
        get_field(right_row, *field_names)
    )

    if not left_value or not right_value:
        return False

    return left_value == right_value


def match_lei_exact(
    left_row: dict,
    right_row: dict,
) -> bool:
    """
    Deterministic rule:
        LEI exact
    """
    return exact_equal(
        left_row,
        right_row,
        "lei",
        "LEI",
    )


def match_tax_id_exact(
    left_row: dict,
    right_row: dict,
) -> bool:
    """
    Deterministic rule:
        Tax ID exact
    """
    return exact_equal(
        left_row,
        right_row,
        "tax_id",
        "taxId",
        "taxID",
    )


def match_phone_dob_exact(
    left_row: dict,
    right_row: dict,
) -> bool:
    """
    Deterministic rule:
        normalized phone + normalized DOB exact
    """
    return (
        exact_equal(
            left_row,
            right_row,
            "normalized_phone",
            "phone",
        )
        and
        exact_equal(
            left_row,
            right_row,
            "normalized_dob",
            "dob",
        )
    )


def match_email_dob_exact(
    left_row: dict,
    right_row: dict,
) -> bool:
    """
    Deterministic rule:
        normalized email + normalized DOB exact
    """
    return (
        exact_equal(
            left_row,
            right_row,
            "normalized_email",
            "email",
        )
        and
        exact_equal(
            left_row,
            right_row,
            "normalized_dob",
            "dob",
        )
    )


def deterministic_match(
    left_ref: RecordRef,
    right_ref: RecordRef,
    left_row: dict,
    right_row: dict,
) -> Optional[MatchResult]:
    """
    Apply deterministic matching rules in priority order.

    Returns:
        MatchResult when a strong deterministic match is found.
        None when the pair needs fuzzy evaluation.
    """

    if match_lei_exact(
        left_row,
        right_row,
    ):
        return MatchResult(
            left=left_ref,
            right=right_ref,
            match_score=100.0,
            decision="MATCH",
            matching_rule="LEI_EXACT",
            reason=(
                "LEI values match exactly."
            ),
        )

    if match_tax_id_exact(
        left_row,
        right_row,
    ):
        return MatchResult(
            left=left_ref,
            right=right_ref,
            match_score=100.0,
            decision="MATCH",
            matching_rule="TAX_ID_EXACT",
            reason=(
                "Tax ID values match exactly."
            ),
        )

    if match_phone_dob_exact(
        left_row,
        right_row,
    ):
        return MatchResult(
            left=left_ref,
            right=right_ref,
            match_score=100.0,
            decision="MATCH",
            matching_rule="PHONE_DOB_EXACT",
            reason=(
                "Normalized phone and DOB "
                "match exactly."
            ),
        )

    if match_email_dob_exact(
        left_row,
        right_row,
    ):
        return MatchResult(
            left=left_ref,
            right=right_ref,
            match_score=100.0,
            decision="MATCH",
            matching_rule="EMAIL_DOB_EXACT",
            reason=(
                "Normalized email and DOB "
                "match exactly."
            ),
        )

    return None