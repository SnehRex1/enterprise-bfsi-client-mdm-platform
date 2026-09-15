import pandas as pd

from src.survivorship.scd2 import (
    apply_scd2,
    build_initial_scd2,
)


FIELDS = [
    "name",
    "phone",
]


def test_scd2_end_to_end_change():

    # --------------------------------------------------------
    # First Golden Record snapshot.
    # --------------------------------------------------------

    run_one = [
        {
            "master_client_id": "MC000001",
            "name": "CONNOR SMITH",
            "phone": "1111111111",
        }
    ]

    initial = build_initial_scd2(
        master_clients=run_one,
        fields=FIELDS,
        effective_date="2026-09-15",
    )

    # --------------------------------------------------------
    # Second snapshot.
    #
    # Name stays the same.
    # Phone changes.
    # --------------------------------------------------------

    run_two = [
        {
            "master_client_id": "MC000001",
            "name": "CONNOR SMITH",
            "phone": "2222222222",
        }
    ]

    updated = apply_scd2(
        existing_history=initial,
        new_master_clients=run_two,
        run_date="2026-10-01",
        fields=FIELDS,
    )

    history_df = pd.DataFrame(updated)

    phone_history = history_df[
        history_df["field"] == "phone"
    ]

    # We should now have two phone versions.
    assert len(phone_history) == 2

    # Old version should be expired.
    old_version = phone_history[
        phone_history["value"] == "1111111111"
    ].iloc[0]

    assert bool(old_version["is_current"]) is False
    assert old_version["expiry_date"] == "2026-10-01"

    # New version should be current.
    new_version = phone_history[
        phone_history["value"] == "2222222222"
    ].iloc[0]

    assert bool(new_version["is_current"]) is True
    assert new_version["effective_date"] == "2026-10-01"
    
    
    
def test_scd2_does_not_create_version_when_nothing_changes():

    first = [
        {
            "master_client_id": "MC000001",
            "name": "CONNOR SMITH",
            "phone": "1111111111",
        }
    ]

    initial = build_initial_scd2(
        first,
        FIELDS,
        "2026-09-15",
    )

    second = [
        {
            "master_client_id": "MC000001",
            "name": "CONNOR SMITH",
            "phone": "1111111111",
        }
    ]

    updated = apply_scd2(
        initial,
        second,
        "2026-10-01",
        FIELDS,
    )

    assert len(updated) == 2

    assert all(
        row["is_current"]
        for row in updated
    )