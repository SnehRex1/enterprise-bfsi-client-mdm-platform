from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from src.survivorship.clustering import (
    RecordRef,
    UnionFind,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

CONFIG_PATH = (
    PROJECT_ROOT
    / "configs"
    / "survivorship.yaml"
)


def load_config() -> dict[str, Any]:
    """
    Read the survivorship policy from YAML.
    """

    with CONFIG_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return yaml.safe_load(file)


def is_present(value: Any) -> bool:
    """
    Determine whether an attribute actually has a value.

    Treat these as missing:

        None
        NaN
        ""
        "   "
    """

    if value is None:
        return False

    if pd.isna(value):
        return False

    return str(value).strip() != ""


def parse_date(value: Any) -> pd.Timestamp | None:
    """
    Safely convert a value into a timestamp.
    """

    if not is_present(value):
        return None

    parsed = pd.to_datetime(
        value,
        errors="coerce",
    )

    if pd.isna(parsed):
        return None

    return parsed


def load_silver_records() -> pd.DataFrame:
    """
    Load all four DEV Silver datasets.

    All four should already use the canonical Silver schema
    created in Phase 2.
    """

    silver_root = (
        PROJECT_ROOT
        / "data"
        / "dev"
        / "silver"
    )

    systems = [
        "core",
        "crm",
        "kyc",
        "wealth",
    ]

    frames: list[pd.DataFrame] = []

    for system in systems:

        path = (
            silver_root
            / system
            / f"{system}_customers.csv"
        )

        df = pd.read_csv(
            path,
            dtype=str,
        )

        frames.append(df)

    records = pd.concat(
        frames,
        ignore_index=True,
    )

    records["source_system"] = (
        records["source_system"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    records["source_id"] = (
        records["source_id"]
        .astype(str)
        .str.strip()
    )

    return records


def load_match_results() -> pd.DataFrame:
    """
    Load Phase 3 entity-resolution results.
    """

    path = (
        PROJECT_ROOT
        / "data"
        / "dev"
        / "matching"
        / "entity_resolution_results.csv"
    )

    results = pd.read_csv(path)

    return results


def build_clusters(
    records: pd.DataFrame,
    results: pd.DataFrame,
) -> dict:
    """
    Turn pairwise MATCH relationships into entity groups.
    """

    uf = UnionFind()

    # Add EVERY Silver record.
    #
    # Why?
    # A record with no accepted MATCH is still a legitimate
    # standalone master entity.
    for row in records.itertuples(
        index=False
    ):

        uf.add(
            RecordRef(
                source_system=str(
                    row.source_system
                ).upper(),
                source_id=str(
                    row.source_id
                ),
            )
        )

    # Only MATCH is allowed to merge records.
    matches = results[
        results["decision"]
        .astype(str)
        .str.upper()
        .eq("MATCH")
    ]

    for row in matches.itertuples(
        index=False
    ):

        left = RecordRef(
            source_system=str(
                row.left_source_system
            ).upper(),
            source_id=str(
                row.left_source_id
            ),
        )

        right = RecordRef(
            source_system=str(
                row.right_source_system
            ).upper(),
            source_id=str(
                row.right_source_id
            ),
        )

        uf.union(left, right)

    return uf.groups()


def build_confidence(
    matches: pd.DataFrame,
) -> dict[RecordRef, float]:
    """
    For every source record, remember the strongest
    accepted match score associated with that record.
    """

    confidence: dict[
        RecordRef,
        float
    ] = {}

    for row in matches.itertuples(
        index=False
    ):

        score = float(row.match_score)

        left = RecordRef(
            source_system=str(
                row.left_source_system
            ).upper(),
            source_id=str(
                row.left_source_id
            ),
        )

        right = RecordRef(
            source_system=str(
                row.right_source_system
            ).upper(),
            source_id=str(
                row.right_source_id
            ),
        )

        confidence[left] = max(
            confidence.get(left, 0.0),
            score,
        )

        confidence[right] = max(
            confidence.get(right, 0.0),
            score,
        )

    return confidence


def calculate_completeness(
    row: pd.Series,
    attributes: list[str],
) -> int:
    """
    Count how many Golden Record attributes
    are populated in this source record.
    """

    return sum(
        1
        for attribute in attributes
        if is_present(row.get(attribute))
    )


def calculate_verification(
    row: pd.Series,
) -> int:
    """
    Use verification_date as our verification signal.

    We deliberately do not invent a KYC status enumeration,
    because the project's source data has not established
    one universal verified-status vocabulary.
    """

    return int(
        is_present(
            row.get("verification_date")
        )
    )


def build_rank(
    row: pd.Series,
    attributes: list[str],
    authority: dict[str, int],
    confidence: dict[RecordRef, float],
) -> tuple:

    source_system = str(
        row["source_system"]
    ).upper()

    source_id = str(
        row["source_id"]
    )

    ref = RecordRef(
        source_system=source_system,
        source_id=source_id,
    )

    authority_score = authority.get(
        source_system,
        0,
    )

    verification_score = (
        calculate_verification(row)
    )

    verification_date = parse_date(
        row.get("verification_date")
    )

    # Missing dates should be ranked last.
    recency = (
        verification_date
        if verification_date is not None
        else pd.Timestamp("1900-01-01")
    )

    completeness = calculate_completeness(
        row,
        attributes,
    )

    match_confidence = confidence.get(
        ref,
        0.0,
    )

    # Python compares tuples left -> right.
    #
    # Therefore:
    #
    # authority > verification > recency >
    # completeness > confidence
    return (
        authority_score,
        verification_score,
        recency,
        completeness,
        match_confidence,
        source_system,
        source_id,
    )


def choose_winner(
    cluster_rows: pd.DataFrame,
    attribute: str,
    attributes: list[str],
    authority: dict[str, int],
    confidence: dict[RecordRef, float],
) -> pd.Series | None:
    """
    Select the source record that wins one attribute.
    """

    # Step 1:
    # Ignore blank values before comparing sources.
    available = cluster_rows[
        cluster_rows[attribute].apply(is_present)
    ].copy()

    if available.empty:
        return None

    # Step 2:
    # Calculate the ranking one candidate at a time.
    #
    # We deliberately avoid DataFrame.apply() followed by
    # to_dict("records") here. This function runs for every
    # Golden Record attribute of every master client. Repeatedly
    # converting pandas data into Python dictionaries creates a
    # large amount of temporary data and makes the local run
    # unnecessarily slow.
    best_row = None
    best_rank = None

    for _, row in available.iterrows():
        rank = build_rank(
            row,
            attributes,
            authority,
            confidence,
        )

        if best_rank is None or rank > best_rank:
            best_rank = rank
            best_row = row

    # available is non-empty, so best_row is populated.
    return best_row


def build_golden_records(
    records: pd.DataFrame,
    clusters: dict,
    config: dict[str, Any],
    confidence: dict[RecordRef, float],
):
    """
    Build:

        MASTER_CLIENT
        MASTER_CLIENT_ATTRIBUTE
        CLIENT_SOURCE_MAP

    Performance note:
        This function intentionally avoids repeatedly constructing
        pandas DataFrames inside the cluster/attribute loops.
        The DEV dataset has 58k records, so a simple dictionary-based
        lookup is both easier to reason about and much faster locally.
    """

    authority = {
        str(key).upper(): int(value)
        for key, value in config["source_authority"].items()
    }

    attributes = list(config["golden_attributes"])

    master_rows: list[dict[str, Any]] = []
    attribute_rows: list[dict[str, Any]] = []
    source_map_rows: list[dict[str, Any]] = []

    # Convert the Silver dataframe once into a plain Python lookup:
    #
    #     ("CORE", "C00000123") -> {all source attributes...}
    #
    # This avoids repeated pandas MultiIndex lookups for every
    # cluster and every Golden Record attribute.
    record_lookup: dict[tuple[str, str], dict[str, Any]] = {}

    for row in records.to_dict("records"):
        key = (
            str(row["source_system"]).upper(),
            str(row["source_id"]).strip(),
        )

        # Source system + source ID should uniquely identify a record.
        # Keep the first row if a duplicate somehow exists.
        if key not in record_lookup:
            record_lookup[key] = row

    # Pre-calculate the survivorship ranking ONCE per source record.
    #
    # Previously build_rank() was called repeatedly for every
    # attribute of every cluster. That made the local pandas version
    # unnecessarily expensive.
    prepared_records: dict[
        tuple[str, str],
        dict[str, Any],
    ] = {}

    for key, row in record_lookup.items():

        source_system, source_id = key

        # Make a plain dictionary so build_rank() can still work
        # with row["..."] access just like a pandas Series.
        prepared = dict(row)

        prepared["source_system"] = source_system
        prepared["source_id"] = source_id

        prepared["_authority"] = authority.get(
            source_system,
            0,
        )

        prepared["_verified"] = calculate_verification(
            pd.Series(prepared)
        )

        verification_date = parse_date(
            prepared.get("verification_date")
        )

        prepared["_recency"] = (
            verification_date
            if verification_date is not None
            else pd.Timestamp("1900-01-01")
        )

        prepared["_completeness"] = (
            calculate_completeness(
                pd.Series(prepared),
                attributes,
            )
        )

        ref = RecordRef(
            source_system=source_system,
            source_id=source_id,
        )

        prepared["_confidence"] = confidence.get(
            ref,
            0.0,
        )

        # Build the tuple once.
        prepared["_rank"] = (
            prepared["_authority"],
            prepared["_verified"],
            prepared["_recency"],
            prepared["_completeness"],
            prepared["_confidence"],
            source_system,
            source_id,
        )

        prepared_records[key] = prepared

    for master_id, members in clusters.items():

        member_records: list[dict[str, Any]] = []

        for member in members:

            key = (
                member.source_system.upper(),
                member.source_id,
            )

            row = prepared_records.get(key)

            if row is not None:
                member_records.append(row)

                source_map_rows.append(
                    {
                        "master_client_id": master_id,
                        "source_system":
                            member.source_system.upper(),
                        "source_id":
                            member.source_id,
                    }
                )

        if not member_records:
            continue

        # Start with the master identifier.
        master = {
            "master_client_id": master_id
        }

        # Attribute-level survivorship:
        #
        # Each attribute independently chooses the highest-ranked
        # source record that actually contains a value.
        for attribute in attributes:

            best_row: dict[str, Any] | None = None
            best_rank = None

            for candidate in member_records:

                value = candidate.get(attribute)

                # Empty values cannot win survivorship.
                if not is_present(value):
                    continue

                rank = candidate["_rank"]

                if best_rank is None or rank > best_rank:
                    best_rank = rank
                    best_row = candidate

            if best_row is None:

                master[attribute] = ""

                attribute_rows.append(
                    {
                        "master_client_id": master_id,
                        "attribute_name": attribute,
                        "attribute_value": "",
                        "winning_source_system": "",
                        "winning_source_id": "",
                        "survivorship_reason":
                            "no populated candidate",
                    }
                )

                continue

            winning_value = best_row[attribute]
            source_system = best_row["source_system"]
            source_id = best_row["source_id"]

            master[attribute] = winning_value

            attribute_rows.append(
                {
                    "master_client_id": master_id,
                    "attribute_name": attribute,
                    "attribute_value": winning_value,
                    "winning_source_system":
                        source_system,
                    "winning_source_id":
                        source_id,
                    "survivorship_reason": (
                        "source_authority="
                        f"{best_row['_authority']}; "
                        "verification="
                        f"{best_row['_verified']}; "
                        "recency="
                        f"{best_row['_recency'].date()}; "
                        "completeness="
                        f"{best_row['_completeness']}; "
                        "confidence="
                        f"{best_row['_confidence']:.4f}"
                    ),
                }
            )

        master_rows.append(master)

    return (
        pd.DataFrame(master_rows),
        pd.DataFrame(attribute_rows),
        pd.DataFrame(source_map_rows),
    )
