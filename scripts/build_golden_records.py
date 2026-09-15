from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd

# Allow imports from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.survivorship.engine import (
    build_clusters,
    build_confidence,
    build_golden_records,
    load_config,
    load_match_results,
    load_silver_records,
)

from src.survivorship.master_id import (
    assign_master_ids,
    load_registry,
    save_registry,
)


def main() -> None:

    print("=" * 70)
    print("PHASE 5 — SURVIVORSHIP + GOLDEN RECORD")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Load inputs
    # --------------------------------------------------------

    print("\nLoading Silver records...")

    records = load_silver_records()

    print(
        f"Silver records: {len(records):,}"
    )

    print("\nLoading entity-resolution results...")

    results = load_match_results()

    print(
        f"Match result rows: {len(results):,}"
    )

    # --------------------------------------------------------
    # 2. Keep only accepted MATCH relationships
    # --------------------------------------------------------

    matches = results[
        results["decision"]
        .astype(str)
        .str.upper()
        .eq("MATCH")
    ].copy()

    print(
        f"Accepted MATCH edges: {len(matches):,}"
    )

    # REVIEW and NO MATCH are intentionally excluded.

    # --------------------------------------------------------
    # 3. Build entity clusters
    # --------------------------------------------------------

    print("\nBuilding entity clusters...")

    raw_clusters = build_clusters(
        records,
        matches,
    )

    print(
        f"Clusters created: {len(raw_clusters):,}"
    )

    # --------------------------------------------------------
    # 4. Stable master IDs
    # --------------------------------------------------------

    gold_root = (
        PROJECT_ROOT
        / "data"
        / "dev"
        / "gold"
    )

    registry_path = (
        gold_root
        / "master_id_registry.json"
    )

    registry = load_registry(
        registry_path
    )

    # Convert Union-Find root keys into a stable
    # temporary structure keyed by root.
    #
    # We assign IDs using the actual clusters.
    cluster_to_master = {}
    updated_registry = dict(registry)
    warnings = []

    # Import here to avoid exposing registry internals
    # to the core engine.
    from src.survivorship.master_id import (
        assign_master_ids,
    )

    cluster_to_master, updated_registry, warnings = (
        assign_master_ids(
            raw_clusters,
            registry,
        )
    )

    # Re-key clusters by their MASTER_CLIENT_ID.
    master_clusters = {
        cluster_to_master[root]: members
        for root, members in raw_clusters.items()
    }

    save_registry(
        registry_path,
        updated_registry,
    )

    print(
        f"Master clients: {len(master_clusters):,}"
    )

    if warnings:
        print("\nMASTER MERGE WARNINGS:")

        for warning in warnings:
            print(
                f"  WARNING: {warning}"
            )

    # --------------------------------------------------------
    # 5. Build confidence for survivorship ranking
    # --------------------------------------------------------

    confidence = build_confidence(
        matches
    )

    # --------------------------------------------------------
    # 6. Build Golden Record
    # --------------------------------------------------------

    print("\nRunning survivorship...")

    config = load_config()

    (
        master_client,
        master_client_attribute,
        client_source_map,
    ) = build_golden_records(
        records,
        master_clusters,
        config,
        confidence,
    )

    # --------------------------------------------------------
    # 7. Write outputs
    # --------------------------------------------------------

    gold_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    master_client.to_csv(
        gold_root / "master_client.csv",
        index=False,
    )

    master_client_attribute.to_csv(
        gold_root / "master_client_attribute.csv",
        index=False,
    )

    client_source_map.to_csv(
        gold_root / "client_source_map.csv",
        index=False,
    )

    # Small run summary.
    summary = pd.DataFrame(
        [
            {
                "run_date": str(date.today()),
                "silver_records":
                    len(records),
                "match_edges":
                    len(matches),
                "master_clients":
                    len(master_client),
                "source_map_rows":
                    len(client_source_map),
                "attribute_provenance_rows":
                    len(master_client_attribute),
            }
        ]
    )

    summary.to_csv(
        gold_root / "survivorship_summary.csv",
        index=False,
    )

    # --------------------------------------------------------
    # 8. Print final summary
    # --------------------------------------------------------

    print("\nPHASE 5 SUMMARY")
    print("-" * 70)

    print(
        f"Silver records:       {len(records):,}"
    )

    print(
        f"MATCH edges:          {len(matches):,}"
    )

    print(
        f"Master clients:       {len(master_client):,}"
    )

    print(
        f"Source-map rows:      {len(client_source_map):,}"
    )

    print(
        f"Provenance rows:      "
        f"{len(master_client_attribute):,}"
    )

    print("\nOutputs:")

    print(
        gold_root
        / "master_client.csv"
    )

    print(
        gold_root
        / "master_client_attribute.csv"
    )

    print(
        gold_root
        / "client_source_map.csv"
    )

    print(
        gold_root
        / "survivorship_summary.csv"
    )


if __name__ == "__main__":
    main()