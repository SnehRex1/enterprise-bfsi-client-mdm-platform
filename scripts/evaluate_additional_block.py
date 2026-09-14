import csv
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


GROUND_TRUTH_PATH = (
    PROJECT_ROOT
    / "data"
    / "dev"
    / "ground_truth"
    / "ground_truth.csv"
)

SILVER_PATHS = {
    "CORE": (
        PROJECT_ROOT
        / "data"
        / "dev"
        / "silver"
        / "core"
        / "core_customers.csv"
    ),
    "CRM": (
        PROJECT_ROOT
        / "data"
        / "dev"
        / "silver"
        / "crm"
        / "crm_customers.csv"
    ),
    "KYC": (
        PROJECT_ROOT
        / "data"
        / "dev"
        / "silver"
        / "kyc"
        / "kyc_customers.csv"
    ),
    "WEALTH": (
        PROJECT_ROOT
        / "data"
        / "dev"
        / "silver"
        / "wealth"
        / "wealth_customers.csv"
    ),
}


def normalize(value):
    if value is None:
        return ""

    return str(value).strip().lower()


def get_field(row, *names):
    for name in names:
        if name in row:
            value = row[name]

            if value is not None:
                return value.strip()

    return ""


def extract_surname(name):
    value = normalize(name)

    if not value:
        return ""

    parts = value.split()

    if not parts:
        return ""

    return parts[-1]


def extract_postcode(address):
    value = normalize(address)

    if not value:
        return ""

    parts = value.split()

    for part in reversed(parts):

        cleaned = (
            part
            .replace(",", "")
            .replace(".", "")
        )

        has_digit = any(
            character.isdigit()
            for character in cleaned
        )

        has_alpha = any(
            character.isalpha()
            for character in cleaned
        )

        if has_digit and has_alpha:
            return cleaned

    return ""


def make_record_ref(source_system, source_id):
    return (
        source_system.strip().upper(),
        source_id.strip(),
    )


def make_pair_key(left, right):
    return tuple(
        sorted(
            [left, right],
            key=lambda record: (record[0], record[1]),
        )
    )


def load_ground_truth():
    with GROUND_TRUTH_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        return list(
            csv.DictReader(file)
        )


def build_true_pairs(rows):

    entity_records = defaultdict(list)

    for row in rows:

        entity_key = row["entity_key"].strip()

        record_ref = make_record_ref(
            row["source_system"],
            row["source_id"],
        )

        entity_records[
            entity_key
        ].append(record_ref)

    true_pairs = set()

    for records in entity_records.values():

        if len(records) < 2:
            continue

        for left, right in combinations(
            records,
            2,
        ):

            true_pairs.add(
                make_pair_key(left, right)
            )

    return true_pairs


def load_silver():

    records = {}

    for source_system, path in SILVER_PATHS.items():

        with path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                source_id = row["source_id"]

                records[
                    (source_system, source_id)
                ] = row

    return records


def build_surname_postcode_pairs(
    silver_records
):

    index = defaultdict(list)

    for record_ref, row in silver_records.items():

        surname = extract_surname(
            get_field(
                row,
                "normalized_name",
                "name",
            )
        )

        postcode = extract_postcode(
            get_field(
                row,
                "normalized_address",
                "address",
            )
        )

        if not surname or not postcode:
            continue

        key = (
            surname,
            postcode,
        )

        index[key].append(
            record_ref
        )

    candidate_pairs = set()

    block_count = 0
    max_block_size = 0

    for records in index.values():

        block_size = len(records)

        block_count += 1

        max_block_size = max(
            max_block_size,
            block_size,
        )

        if block_size < 2:
            continue

        for left, right in combinations(
            records,
            2,
        ):

            candidate_pairs.add(
                make_pair_key(left, right)
            )

    return (
        candidate_pairs,
        block_count,
        max_block_size,
    )


def main():

    print("ADDITIONAL BLOCKING STRATEGY EVALUATION")
    print("=" * 70)

    print()
    print(
        "Testing candidate blocking key:"
    )
    print(
        "surname + postal_code"
    )

    print()

    ground_truth = load_ground_truth()

    true_pairs = build_true_pairs(
        ground_truth
    )

    print(
        f"True entity pairs: "
        f"{len(true_pairs):,}"
    )

    silver_records = load_silver()

    print(
        f"Silver records: "
        f"{len(silver_records):,}"
    )

    print()

    (
        candidate_pairs,
        block_count,
        max_block_size,
    ) = build_surname_postcode_pairs(
        silver_records
    )

    print("BLOCK STATISTICS")
    print("-" * 70)

    print(
        f"surname_postcode blocks: "
        f"{block_count:,}"
    )

    print(
        f"max block size: "
        f"{max_block_size:,}"
    )

    print(
        f"new candidate pairs: "
        f"{len(candidate_pairs):,}"
    )

    print()

    captured_true_pairs = (
        true_pairs & candidate_pairs
    )

    print("TRUE-PAIR COVERAGE")
    print("-" * 70)

    print(
        f"True pairs captured by new key: "
        f"{len(captured_true_pairs):,}"
    )

    recall = (
        len(captured_true_pairs)
        / len(true_pairs)
        if true_pairs
        else 1.0
    )

    print(
        f"Recall of surname+postal key: "
        f"{recall * 100:.4f}%"
    )

    print()

    print("=" * 70)

    print(
        "Additional blocking strategy evaluation complete."
    )


if __name__ == "__main__":
    main()