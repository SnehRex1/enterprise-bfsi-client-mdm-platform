"""
Convert one contract-validated source row into the
Canonical Client Representation.

This module:
    - maps source-specific columns
    - preserves raw canonical values
    - creates normalized values

It does NOT:
    - match entities
    - use ground truth
    - create master IDs
    - perform survivorship
"""

from typing import Any

from src.standardization.normalizers import (
    normalize_address,
    normalize_date,
    normalize_email,
    normalize_name,
    normalize_phone,
)


def build_canonical_record(
    source_system: str,
    row: dict[str, Any],
    mapping: dict[str, Any],
) -> dict[str, Any]:
    """
    Build one canonical record from one source row.
    """

    source_system = source_system.lower()

    if source_system == "core":
        source_id = row.get(
            "customer_id",
            "",
        )

    elif source_system == "crm":
        source_id = row.get(
            "crm_customer_id",
            "",
        )

    elif source_system == "kyc":
        source_id = row.get(
            "kyc_id",
            "",
        )

    elif source_system == "wealth":
        source_id = row.get(
            "client_id",
            "",
        )

    else:
        raise ValueError(
            f"Unsupported source system: {source_system}"
        )

    raw_name = row.get(
        mapping.get("canonical_name")
        or "",
        "",
    )

    raw_dob = row.get(
        mapping.get("canonical_dob")
        or "",
        "",
    )

    raw_phone = row.get(
        mapping.get("canonical_phone")
        or "",
        "",
    )

    raw_email = row.get(
        mapping.get("canonical_email")
        or "",
        "",
    )

    raw_address = row.get(
        mapping.get("canonical_address")
        or "",
        "",
    )

    canonical = {
        "source_system": source_system.upper(),
        "source_id": source_id,

        "name": raw_name,
        "normalized_name": normalize_name(
            raw_name
        ),

        "dob": raw_dob,
        "normalized_dob": normalize_date(
            raw_dob
        ),

        "phone": raw_phone,
        "normalized_phone": normalize_phone(
            raw_phone
        ),

        "email": raw_email,
        "normalized_email": normalize_email(
            raw_email
        ),

        "address": raw_address,
        "normalized_address": normalize_address(
            raw_address
        ),

        "tax_id": row.get(
            "tax_id",
            "",
        ),

        "lei": row.get(
            "LEI",
            "",
        ),

        "account_id": row.get(
            "account_id",
            "",
        ),

        "branch_id": row.get(
            "branch_id",
            "",
        ),

        "segment": row.get(
            "segment",
            "",
        ),

        "kyc_status": row.get(
            "kyc_status",
            "",
        ),

        "verification_date": row.get(
            "verification_date",
            "",
        ),

        "normalized_verification_date": normalize_date(
            row.get(
                "verification_date",
                "",
            )
        ),

        "aum": row.get(
            "aum",
            "",
        ),

        "risk_profile": row.get(
            "risk_profile",
            "",
        ),

        "relationship_manager": row.get(
            "relationship_manager",
            "",
        ),
    }

    return canonical