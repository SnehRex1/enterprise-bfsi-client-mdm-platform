from __future__ import annotations

import json
from pathlib import Path


def load_registry(path: Path) -> dict[str, str]:
    """
    Load:

        source_system::source_id -> MASTER_CLIENT_ID

    Example:

        CORE::C000001 -> MC000001
        KYC::K000001  -> MC000001
    """

    if not path.exists():
        return {}

    return json.loads(path.read_text(encoding="utf-8"))


def save_registry(
    path: Path,
    registry: dict[str, str],
) -> None:
    """
    Save the master ID registry to disk.
    """

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(
            registry,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def assign_master_ids(
    clusters: dict,
    registry: dict[str, str],
):
    """
    Assign stable MASTER_CLIENT_ID values.

    Rules:

    1. New cluster:
       create new ID.

    2. Existing cluster with one known ID:
       reuse it.

    3. Cluster contains multiple historical IDs:
       keep one but emit a warning.
       This represents a potential master merge and
       should not be silently hidden.
    """

    existing_numbers = [
        int(value[2:])
        for value in registry.values()
        if value.startswith("MC")
        and value[2:].isdigit()
    ]

    next_number = (
        max(existing_numbers) + 1
        if existing_numbers
        else 1
    )

    cluster_to_master: dict = {}
    updated_registry = dict(registry)
    merge_warnings: list[str] = []

    for root, members in clusters.items():

        # Find IDs previously assigned to any member.
        prior_ids = sorted(
            {
                registry[
                    f"{member.source_system.upper()}::{member.source_id}"
                ]
                for member in members
                if (
                    f"{member.source_system.upper()}::{member.source_id}"
                    in registry
                )
            }
        )

        if not prior_ids:
            # Completely new entity.
            master_id = f"MC{next_number:06d}"
            next_number += 1

        elif len(prior_ids) == 1:
            # Existing entity.
            master_id = prior_ids[0]

        else:
            # Two previously separate masters now became one cluster.
            master_id = prior_ids[0]

            merge_warnings.append(
                f"Potential master merge: "
                f"{prior_ids} -> {master_id}"
            )

        cluster_to_master[root] = master_id

        for member in members:
            key = (
                f"{member.source_system.upper()}::"
                f"{member.source_id}"
            )

            updated_registry[key] = master_id

    return (
        cluster_to_master,
        updated_registry,
        merge_warnings,
    )