"""
Phase 1 - Prepare the final GLEIF snapshot.

Input:
    data/external/gleif/golden_copy/*.zip

The ZIP is expected to contain the GLEIF Level-1 Golden Copy CSV.

We stream the CSV directly from the ZIP instead of extracting the
entire file or loading millions of rows into memory.

Filters:
    Country = GB
    Entity Status = ACTIVE
    Registration Status = ISSUED

Output:
    data/external/gleif/gleif_entities.csv
    data/external/gleif/snapshot_metadata.json
"""

import argparse
import csv
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path


GOLDEN_COPY_DIR = Path(
    "data/external/gleif/golden_copy"
)

OUTPUT_PATH = Path(
    "data/external/gleif/gleif_entities.csv"
)

METADATA_PATH = Path(
    "data/external/gleif/snapshot_metadata.json"
)

DEFAULT_TARGET = 100_000
DEFAULT_COUNTRY = "GB"


OUTPUT_COLUMNS = [
    "lei",
    "legal_name",
    "address_line",
    "city",
    "region",
    "postal_code",
    "country",
    "entity_status",
    "registration_status",
]


INPUT_COLUMNS = {
    "lei": "LEI",
    "legal_name": "Entity.LegalName",
    "address_line": "Entity.LegalAddress.FirstAddressLine",
    "city": "Entity.LegalAddress.City",
    "region": "Entity.LegalAddress.Region",
    "postal_code": "Entity.LegalAddress.PostalCode",
    "country": "Entity.LegalAddress.Country",
    "entity_status": "Entity.EntityStatus",
    "registration_status": "Registration.RegistrationStatus",
}


def find_zip_file() -> Path:
    """Find the Golden Copy ZIP in the expected directory."""

    zip_files = sorted(
        GOLDEN_COPY_DIR.glob("*.zip")
    )

    if not zip_files:
        raise FileNotFoundError(
            "No GLEIF ZIP file found in:\n"
            f"{GOLDEN_COPY_DIR}"
        )

    if len(zip_files) > 1:
        raise RuntimeError(
            "More than one GLEIF ZIP exists.\n"
            "Keep only the snapshot we intend to use, "
            "or modify the script to explicitly select one."
        )

    return zip_files[0]


def sha256_file(
    path: Path,
) -> str:
    """Calculate SHA-256 for a local file."""

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as file:

        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):

            digest.update(chunk)

    return digest.hexdigest()


def build_address(
    row: dict[str, str],
) -> str:
    """
    Build a simple address string from the registered legal address.

    We intentionally use only the primary address line plus location
    fields needed for our simulated KYC population.
    """

    parts = [
        row.get(
            "Entity.LegalAddress.FirstAddressLine",
            "",
        ),
        row.get(
            "Entity.LegalAddress.City",
            "",
        ),
        row.get(
            "Entity.LegalAddress.Region",
            "",
        ),
        row.get(
            "Entity.LegalAddress.PostalCode",
            "",
        ),
    ]

    return ", ".join(
        part.strip()
        for part in parts
        if part and part.strip()
    )


def prepare_snapshot(
    target_count: int,
    country: str,
) -> int:

    zip_path = find_zip_file()

    print(
        f"Using Golden Copy ZIP:\n"
        f"  {zip_path}"
    )

    print(
        "\nOpening CSV directly from ZIP..."
    )

    seen_leis: set[str] = set()

    rows_written = 0

    temporary_output = OUTPUT_PATH.with_suffix(
        ".csv.tmp"
    )

    if temporary_output.exists():
        temporary_output.unlink()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with zipfile.ZipFile(
        zip_path,
        "r",
    ) as archive:

        csv_members = [
            name
            for name in archive.namelist()
            if name.lower().endswith(".csv")
        ]

        if len(csv_members) != 1:
            raise RuntimeError(
                "Expected exactly one CSV inside "
                f"the Golden Copy ZIP, found "
                f"{len(csv_members)}."
            )

        csv_member = csv_members[0]

        print(
            f"CSV member:\n"
            f"  {csv_member}"
        )

        with archive.open(
            csv_member,
            "r",
        ) as raw_file:

            import io

            text_file = io.TextIOWrapper(
                raw_file,
                encoding="utf-8-sig",
                newline="",
            )

            reader = csv.DictReader(
                text_file
            )

            if not reader.fieldnames:
                raise RuntimeError(
                    "GLEIF CSV has no header."
                )

            missing_columns = [
                column
                for column in INPUT_COLUMNS.values()
                if column not in reader.fieldnames
            ]

            if missing_columns:

                raise RuntimeError(
                    "GLEIF CSV is missing required "
                    f"columns:\n{missing_columns}"
                )

            with temporary_output.open(
                "w",
                newline="",
                encoding="utf-8",
            ) as output_file:

                writer = csv.DictWriter(
                    output_file,
                    fieldnames=OUTPUT_COLUMNS,
                )

                writer.writeheader()

                for row in reader:

                    row_country = (
                        row.get(
                            "Entity.LegalAddress.Country",
                            "",
                        )
                        or ""
                    ).strip().upper()

                    if row_country != country:
                        continue

                    entity_status = (
                        row.get(
                            "Entity.EntityStatus",
                            "",
                        )
                        or ""
                    ).strip().upper()

                    if entity_status != "ACTIVE":
                        continue

                    registration_status = (
                        row.get(
                            "Registration.RegistrationStatus",
                            "",
                        )
                        or ""
                    ).strip().upper()

                    if registration_status != "ISSUED":
                        continue

                    lei = (
                        row.get(
                            "LEI",
                            "",
                        )
                        or ""
                    ).strip().upper()

                    if not lei:
                        continue

                    if lei in seen_leis:
                        continue

                    legal_name = (
                        row.get(
                            "Entity.LegalName",
                            "",
                        )
                        or ""
                    ).strip()

                    if not legal_name:
                        continue

                    writer.writerow(
                        {
                            "lei": lei,

                            "legal_name":
                                legal_name,

                            "address_line":
                                build_address(
                                    row
                                ),

                            "city":
                                (
                                    row.get(
                                        "Entity.LegalAddress.City",
                                        "",
                                    )
                                    or ""
                                ).strip(),

                            "region":
                                (
                                    row.get(
                                        "Entity.LegalAddress.Region",
                                        "",
                                    )
                                    or ""
                                ).strip(),

                            "postal_code":
                                (
                                    row.get(
                                        "Entity.LegalAddress.PostalCode",
                                        "",
                                    )
                                    or ""
                                ).strip(),

                            "country":
                                row_country,

                            "entity_status":
                                entity_status,

                            "registration_status":
                                registration_status,
                        }
                    )

                    seen_leis.add(lei)

                    rows_written += 1

                    if (
                        rows_written % 10_000
                        == 0
                    ):

                        print(
                            f"Selected "
                            f"{rows_written:,}/"
                            f"{target_count:,} "
                            f"entities..."
                        )

                    if rows_written >= target_count:
                        break

    if rows_written < target_count:

        temporary_output.unlink(
            missing_ok=True
        )

        raise RuntimeError(
            f"Only found {rows_written:,} "
            f"matching entities, but "
            f"{target_count:,} were requested."
        )

    temporary_output.replace(
        OUTPUT_PATH
    )

    return rows_written


def write_metadata(
    zip_path: Path,
    country: str,
    record_count: int,
):

    metadata = {
        "source": "GLEIF",
        "source_type": "Level 1 Golden Copy",
        "source_file": zip_path.name,
        "source_zip_sha256":
            sha256_file(zip_path),
        "filter": {
            "country": country,
            "entity_status": "ACTIVE",
            "registration_status": "ISSUED",
        },
        "records": record_count,
        "output_file":
            OUTPUT_PATH.name,
        "output_sha256":
            sha256_file(
                OUTPUT_PATH
            ),
        "prepared_at_utc":
            datetime.now(
                timezone.utc
            ).isoformat(),
    }

    METADATA_PATH.write_text(
        json.dumps(
            metadata,
            indent=2,
        ),
        encoding="utf-8",
    )


def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--target",
        type=int,
        default=DEFAULT_TARGET,
        help="Number of GLEIF entities to extract.",
    )

    parser.add_argument(
        "--country",
        default=DEFAULT_COUNTRY,
        help="Two-letter ISO country code.",
    )

    return parser.parse_args()


def main():

    args = parse_args()

    zip_path = find_zip_file()

    count = prepare_snapshot(
        target_count=args.target,
        country=args.country.upper(),
    )

    write_metadata(
        zip_path=zip_path,
        country=args.country.upper(),
        record_count=count,
    )

    print(
        "\nGLEIF snapshot prepared successfully."
    )

    print(
        f"Records: {count:,}"
    )

    print(
        f"Output:  {OUTPUT_PATH}"
    )

    print(
        f"Metadata: {METADATA_PATH}"
    )


if __name__ == "__main__":
    main()