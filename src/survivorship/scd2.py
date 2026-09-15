from __future__ import annotations

from typing import Any


def build_initial_scd2(
    master_clients: list[dict[str, Any]],
    fields: list[str],
    effective_date: str,
) -> list[dict[str, Any]]:
    """
    Build the first SCD2 version.

    Every Golden Record attribute starts as the current version.

    Example:

        MC000001 | phone | 9876543210
        effective_date = 2026-09-15
        expiry_date    = ""
        is_current     = True
    """

    history: list[dict[str, Any]] = []

    for master in master_clients:

        master_id = master["master_client_id"]

        for field in fields:

            history.append(
                {
                    "master_client_id": master_id,
                    "field": field,
                    "value": master.get(field, ""),
                    "effective_date": effective_date,
                    "expiry_date": "",
                    "is_current": True,
                }
            )

    return history


def apply_scd2(
    existing_history: list[dict[str, Any]],
    new_master_clients: list[dict[str, Any]],
    run_date: str,
    fields: list[str],
) -> list[dict[str, Any]]:
    """
    Compare the existing current state with a new Golden Record
    snapshot.

    Rules:

    1. New master/attribute
       -> create a current row.

    2. Existing value unchanged
       -> keep the current row unchanged.

    3. Existing value changed
       -> expire old row and create a new current row.

    Already-expired rows are never modified.
    """

    # ---------------------------------------------------------
    # Find the current version of each:
    #
    #     master_client_id + field
    #
    # Example:
    #
    #     ("MC000001", "phone")
    # ---------------------------------------------------------

    current_rows: dict[
        tuple[str, str],
        dict[str, Any],
    ] = {}

    history: list[dict[str, Any]] = []

    for row in existing_history:

        is_current = row["is_current"] in (
            True,
            "True",
            "true",
            "1",
        )

        key = (
            row["master_client_id"],
            row["field"],
        )

        if is_current:
            current_rows[key] = row
        else:
            # Historical rows are immutable.
            history.append(row)

    # ---------------------------------------------------------
    # Compare the new Golden Record with the current version.
    # ---------------------------------------------------------

    for master in new_master_clients:

        master_id = master["master_client_id"]

        for field in fields:

            key = (
                master_id,
                field,
            )

            new_value = master.get(
                field,
                "",
            )

            existing = current_rows.pop(
                key,
                None,
            )

            # -------------------------------------------------
            # Case 1: brand-new master/attribute
            # -------------------------------------------------

            if existing is None:

                history.append(
                    {
                        "master_client_id": master_id,
                        "field": field,
                        "value": new_value,
                        "effective_date": run_date,
                        "expiry_date": "",
                        "is_current": True,
                    }
                )

            # -------------------------------------------------
            # Case 2: value did not change
            # -------------------------------------------------

            elif existing["value"] == new_value:

                history.append(existing)

            # -------------------------------------------------
            # Case 3: value changed
            # -------------------------------------------------

            else:

                # Close the old version.
                expired = dict(existing)

                expired["expiry_date"] = run_date
                expired["is_current"] = False

                history.append(expired)

                # Open the new version.
                history.append(
                    {
                        "master_client_id": master_id,
                        "field": field,
                        "value": new_value,
                        "effective_date": run_date,
                        "expiry_date": "",
                        "is_current": True,
                    }
                )

    # ---------------------------------------------------------
    # Any current rows left over were not present in the new
    # snapshot.
    #
    # Preserve them rather than silently deleting history.
    # ---------------------------------------------------------

    history.extend(current_rows.values())

    return history