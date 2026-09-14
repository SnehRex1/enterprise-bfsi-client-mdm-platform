"""
Reusable normalization functions for the MDM pipeline.

Important boundary:

These functions standardize representation.

They do NOT:
    - perform entity matching
    - decide whether two records are the same entity
    - create master IDs
    - perform survivorship
    - use ground truth
"""

import re
import unicodedata
from datetime import datetime
from typing import Any


# Phase 2 contract validation already accepts
# these raw date representations.
SUPPORTED_DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
]


def _is_blank(value: Any) -> bool:
    """
    Return True when the value is None or only whitespace.
    """

    if value is None:
        return True

    return not str(value).strip()


def normalize_name(value: Any) -> str:
    """
    Standardize name representation.

    Example:
        "  Rahul K.  Sharma "
        -> "RAHUL K SHARMA"

    We do NOT:
        - remove middle names
        - guess aliases
        - reorder names
        - perform fuzzy matching
    """

    if _is_blank(value):
        return ""

    text = str(value).strip()

    # Normalize Unicode representation.
    text = unicodedata.normalize(
        "NFKC",
        text,
    )

    # Use one consistent case.
    text = text.upper()

    # Replace punctuation with spaces.
    text = re.sub(
        r"[^\w\s]",
        " ",
        text,
    )

    # Collapse repeated spaces.
    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text


def normalize_phone(value: Any) -> str:
    """
    Standardize phone representation by keeping digits only.

    Example:
        "+44 7123-456789"
        -> "447123456789"

    Important:
        We deliberately do NOT assume country codes,
        remove prefixes, or decide whether two phone
        numbers represent the same person.

        That belongs to later entity-resolution logic.
    """

    if _is_blank(value):
        return ""

    text = str(value).strip()

    return re.sub(
        r"\D",
        "",
        text,
    )


def normalize_email(value: Any) -> str:
    """
    Standardize email representation.

    Example:
        " Rahul@Example.COM "
        -> "rahul@example.com"
    """

    if _is_blank(value):
        return ""

    return str(value).strip().lower()


def normalize_address(value: Any) -> str:
    """
    Light-touch address normalization.

    Example:
        " 10 High Street, London "
        -> "10 HIGH STREET LONDON"

    We intentionally do not try to parse:
        street/city/state/postcode

    That would be a much larger problem than needed here.
    """

    if _is_blank(value):
        return ""

    text = str(value).strip()

    text = unicodedata.normalize(
        "NFKC",
        text,
    )

    text = text.upper()

    text = re.sub(
        r"[^\w\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text


def normalize_date(value: Any) -> str:
    """
    Convert supported source date formats into YYYY-MM-DD.

    Examples:

        1984-03-12
            -> 1984-03-12

        12/03/1984
            -> 1984-03-12

        12-03-1984
            -> 1984-03-12

    Blank input remains blank.

    Contract validation should normally catch invalid
    dates before they reach this function.
    """

    if _is_blank(value):
        return ""

    text = str(value).strip()

    for date_format in SUPPORTED_DATE_FORMATS:

        try:
            parsed = datetime.strptime(
                text,
                date_format,
            )

            return parsed.strftime(
                "%Y-%m-%d"
            )

        except ValueError:
            continue

    # This should normally never happen after contract
    # validation. Returning blank gives DQ a chance to
    # detect the inconsistency rather than silently crashing
    # the whole pipeline.
    return ""