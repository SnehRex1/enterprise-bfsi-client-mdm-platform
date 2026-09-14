"""
Data Quality checks for standardized MDM records.

These checks operate AFTER standardization.

They do NOT:
    - perform entity matching
    - use ground truth
    - create master IDs
    - perform survivorship
"""

from datetime import date, datetime
from typing import Any


MAX_PLAUSIBLE_AGE = 110


def check_completeness(
    row: dict[str, Any],
) -> list[str]:
    """
    Check mandatory canonical attributes.
    """

    issues = []

    if not str(
        row.get(
            "normalized_name",
            "",
        )
    ).strip():

        issues.append(
            "completeness: normalized_name is blank"
        )

    return issues


def check_validity(
    row: dict[str, Any],
) -> list[str]:
    """
    Check basic validity of standardized values.
    """

    issues = []

    phone = str(
        row.get(
            "normalized_phone",
            "",
        )
    ).strip()

    if phone:

        if not phone.isdigit():

            issues.append(
                "validity: normalized_phone contains non-digits"
            )

        elif len(phone) < 7:

            issues.append(
                "validity: normalized_phone is too short"
            )

    email = str(
        row.get(
            "normalized_email",
            "",
        )
    ).strip()

    if email:

        if (
            "@" not in email
            or "." not in email.split(
                "@"
            )[-1]
        ):

            issues.append(
                "validity: normalized_email is invalid"
            )

    return issues


def check_consistency(
    row: dict[str, Any],
) -> list[str]:
    """
    Check whether standardized values make
    semantic sense.
    """

    issues = []

    dob = str(
        row.get(
            "normalized_dob",
            "",
        )
    ).strip()

    if dob:

        try:

            dob_date = datetime.strptime(
                dob,
                "%Y-%m-%d",
            ).date()

        except ValueError:

            issues.append(
                "consistency: normalized_dob is not a valid calendar date"
            )

            return issues

        today = date.today()

        if dob_date > today:

            issues.append(
                f"consistency: normalized_dob '{dob}' is in the future"
            )

        else:

            age = (
                today - dob_date
            ).days / 365.25

            if age > MAX_PLAUSIBLE_AGE:

                issues.append(
                    "consistency: normalized_dob "
                    f"implies age > {MAX_PLAUSIBLE_AGE}"
                )

    # If raw phone exists but normalized phone is blank,
    # normalization did not behave as expected.
    raw_phone = str(
        row.get(
            "phone",
            "",
        )
    ).strip()

    if (
        raw_phone
        and not str(
            row.get(
                "normalized_phone",
                "",
            )
        ).strip()
    ):

        issues.append(
            "consistency: phone normalization failed"
        )

    # Same concept for DOB.
    raw_dob = str(
        row.get(
            "dob",
            "",
        )
    ).strip()

    if (
        raw_dob
        and not str(
            row.get(
                "normalized_dob",
                "",
            )
        ).strip()
    ):

        issues.append(
            "consistency: dob normalization failed"
        )

    return issues


def check_referential_integrity(
    row: dict[str, Any],
) -> list[str]:
    """
    Ensure every canonical record remains traceable
    to its source.
    """

    issues = []

    if not str(
        row.get(
            "source_system",
            "",
        )
    ).strip():

        issues.append(
            "referential_integrity: source_system is missing"
        )

    if not str(
        row.get(
            "source_id",
            "",
        )
    ).strip():

        issues.append(
            "referential_integrity: source_id is missing"
        )

    return issues


def run_all_checks(
    row: dict[str, Any],
) -> list[str]:
    """
    Execute all enforced row-level DQ checks.
    """

    issues: list[str] = []

    issues.extend(
        check_completeness(row)
    )

    issues.extend(
        check_validity(row)
    )

    issues.extend(
        check_consistency(row)
    )

    issues.extend(
        check_referential_integrity(row)
    )

    return issues