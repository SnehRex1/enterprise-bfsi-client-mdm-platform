import csv
import sys
from collections import Counter
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

CANDIDATE_PATH = (
    PROJECT_ROOT
    / "data"
    / "dev"
    / "matching"
    / "candidate_pairs.csv"
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


def make_record_ref(source_system, source_id):
    """Create a normalized record reference."""
    return (
        source_system.strip().upper(),
        source_id.strip(),
    )


def make_pair_key(left, right):
    """
    Create an order-independent pair key.

    This ensures A <-> B and B <-> A are treated as the same pair.
    """
    return tuple(
        sorted(
            [left, right],
            key=lambda record: (record[0], record[1]),
        )
    )


def load_ground_truth():
    """Load ground-truth mappings used only for evaluation."""
    with GROUND_TRUTH_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        return list(csv.DictReader(file))


def build_true_pairs(ground_truth_rows):
    """
    Build all true record-level pairs belonging to the same hidden entity.

    entity_key is used only for evaluation.
    It is never passed into the blocking engine.
    """
    entity_records = {}

    for row in ground_truth_rows:
        entity_key = row["entity_key"].strip()

        record_ref = make_record_ref(
            row["source_system"],
            row["source_id"],
        )

        entity_records.setdefault(
            entity_key,
            [],
        ).append(record_ref)

    true_pairs = set()

    for records in entity_records.values():

        if len(records) < 2:
            continue

        for left, right in combinations(records, 2):
            true_pairs.add(
                make_pair_key(left, right)
            )

    return true_pairs


def load_candidate_pairs():
    """Load candidate pairs produced by the blocking engine."""
    candidate_pairs = set()

    with CANDIDATE_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            left = make_record_ref(
                row["left_source_system"],
                row["left_source_id"],
            )

            right = make_record_ref(
                row["right_source_system"],
                row["right_source_id"],
            )

            candidate_pairs.add(
                make_pair_key(left, right)
            )

    return candidate_pairs


def load_silver_records():
    """
    Load all DEV Silver records into a single lookup dictionary.

    Key:
        (source_system, source_id)
    """
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


def normalize(value):
    """Basic lowercase/trim normalization for diagnostic comparison."""
    if value is None:
        return ""

    return str(value).strip().lower()


def get_field(row, *possible_names):
    """
    Return the first available field from the supplied names.

    This makes the diagnostic resilient to minor naming differences.
    """
    for name in possible_names:

        if name in row:

            value = row[name]

            if value is not None:
                return value.strip()

    return ""


def compare_field(left_row, right_row, *field_names):
    """
    Compare the same field across two records.

    Returns:
        EXACT
        MISSING
        DIFFERENT
    """
    left_value = normalize(
        get_field(
            left_row,
            *field_names,
        )
    )

    right_value = normalize(
        get_field(
            right_row,
            *field_names,
        )
    )

    if not left_value or not right_value:
        return "MISSING"

    if left_value == right_value:
        return "EXACT"

    return "DIFFERENT"


def extract_surname(name):
    """
    Derive surname from normalized full name.

    Example:
        'john michael smith' -> 'smith'
    """
    value = normalize(name)

    if not value:
        return ""

    parts = value.split()

    if not parts:
        return ""

    return parts[-1]


def extract_postcode(address):
    """
    Derive a simple UK-style postcode token from a normalized address.

    This intentionally mirrors the general idea used by blocking:
    look for an address token containing both letters and digits.

    This is diagnostic logic, not a new matching rule.
    """
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


def compare_derived_value(left_value, right_value):
    """
    Compare values derived from name/address.

    Returns:
        EXACT
        MISSING
        DIFFERENT
    """
    left_value = normalize(left_value)
    right_value = normalize(right_value)

    if not left_value or not right_value:
        return "MISSING"

    if left_value == right_value:
        return "EXACT"

    return "DIFFERENT"


def main():

    print("BLOCKING MISS DIAGNOSTIC")
    print("=" * 70)

    # ---------------------------------------------------------------
    # 1. Load evaluation data
    # ---------------------------------------------------------------

    ground_truth_rows = load_ground_truth()

    true_pairs = build_true_pairs(
        ground_truth_rows
    )

    candidate_pairs = load_candidate_pairs()

    missed_pairs = (
        true_pairs - candidate_pairs
    )

    print(
        f"True entity pairs:     {len(true_pairs):,}"
    )

    print(
        f"Candidate pairs:       {len(candidate_pairs):,}"
    )

    print(
        f"Missed true pairs:     {len(missed_pairs):,}"
    )

    print()

    # ---------------------------------------------------------------
    # 2. Load Silver records
    # ---------------------------------------------------------------

    print("Loading Silver records...")

    silver_records = load_silver_records()

    print(
        f"Silver records loaded: {len(silver_records):,}"
    )

    print()

    # ---------------------------------------------------------------
    # 3. Diagnose the missed pairs
    # ---------------------------------------------------------------

    field_statistics = Counter()
    source_statistics = Counter()

    missing_record_count = 0

    for left_ref, right_ref in sorted(
        missed_pairs
    ):

        left_row = silver_records.get(
            left_ref
        )

        right_row = silver_records.get(
            right_ref
        )

        if left_row is None or right_row is None:

            missing_record_count += 1

            continue

        source_pair = (
            f"{left_ref[0]}-{right_ref[0]}"
        )

        source_statistics[
            source_pair
        ] += 1

        # -----------------------------------------------------------
        # Directly stored normalized fields
        # -----------------------------------------------------------

        dob_result = compare_field(
            left_row,
            right_row,
            "normalized_dob",
            "dob",
            "date_of_birth",
        )

        email_result = compare_field(
            left_row,
            right_row,
            "normalized_email",
            "email",
        )

        phone_result = compare_field(
            left_row,
            right_row,
            "normalized_phone",
            "phone",
        )

        # -----------------------------------------------------------
        # Derived surname
        # -----------------------------------------------------------

        left_name = get_field(
            left_row,
            "normalized_name",
            "name",
        )

        right_name = get_field(
            right_row,
            "normalized_name",
            "name",
        )

        left_surname = extract_surname(
            left_name
        )

        right_surname = extract_surname(
            right_name
        )

        surname_result = compare_derived_value(
            left_surname,
            right_surname,
        )

        # -----------------------------------------------------------
        # Derived postal code
        # -----------------------------------------------------------

        left_address = get_field(
            left_row,
            "normalized_address",
            "address",
        )

        right_address = get_field(
            right_row,
            "normalized_address",
            "address",
        )

        left_postcode = extract_postcode(
            left_address
        )

        right_postcode = extract_postcode(
            right_address
        )

        postal_result = compare_derived_value(
            left_postcode,
            right_postcode,
        )

        comparisons = {
            "dob": dob_result,
            "email": email_result,
            "phone": phone_result,
            "surname": surname_result,
            "postal_code": postal_result,
        }

        for field, result in comparisons.items():

            field_statistics[
                f"{field}:{result}"
            ] += 1

    # ---------------------------------------------------------------
    # 4. Source-pair statistics
    # ---------------------------------------------------------------

    print("MISSED PAIRS BY SOURCE COMBINATION")
    print("-" * 70)

    for source_pair, count in sorted(
        source_statistics.items()
    ):

        print(
            f"{source_pair:<15} {count:>6,}"
        )

    print()

    # ---------------------------------------------------------------
    # 5. Field statistics
    # ---------------------------------------------------------------

    print(
        "FIELD COMPARISON FOR MISSED TRUE PAIRS"
    )

    print("-" * 70)

    fields = [
        "dob",
        "email",
        "phone",
        "surname",
        "postal_code",
    ]

    for field in fields:

        exact = field_statistics[
            f"{field}:EXACT"
        ]

        missing = field_statistics[
            f"{field}:MISSING"
        ]

        different = field_statistics[
            f"{field}:DIFFERENT"
        ]

        print(
            f"{field:<15} "
            f"exact={exact:>5,} "
            f"missing={missing:>5,} "
            f"different={different:>5,}"
        )

    print()

    print(
        f"Missed pairs with missing Silver record: "
        f"{missing_record_count:,}"
    )

    print()

    # ---------------------------------------------------------------
    # 6. Show examples
    # ---------------------------------------------------------------

    print("SAMPLE MISSED PAIRS")
    print("-" * 70)

    for left_ref, right_ref in sorted(
        missed_pairs
    )[:20]:

        left_row = silver_records.get(
            left_ref
        )

        right_row = silver_records.get(
            right_ref
        )

        print(
            f"{left_ref[0]}:{left_ref[1]}"
            f" <-> "
            f"{right_ref[0]}:{right_ref[1]}"
        )

        if left_row and right_row:

            left_dob = get_field(
                left_row,
                "normalized_dob",
                "dob",
                "date_of_birth",
            )

            right_dob = get_field(
                right_row,
                "normalized_dob",
                "dob",
                "date_of_birth",
            )

            left_email = get_field(
                left_row,
                "normalized_email",
                "email",
            )

            right_email = get_field(
                right_row,
                "normalized_email",
                "email",
            )

            left_phone = get_field(
                left_row,
                "normalized_phone",
                "phone",
            )

            right_phone = get_field(
                right_row,
                "normalized_phone",
                "phone",
            )

            left_name = get_field(
                left_row,
                "normalized_name",
                "name",
            )

            right_name = get_field(
                right_row,
                "normalized_name",
                "name",
            )

            left_surname = extract_surname(
                left_name
            )

            right_surname = extract_surname(
                right_name
            )

            left_address = get_field(
                left_row,
                "normalized_address",
                "address",
            )

            right_address = get_field(
                right_row,
                "normalized_address",
                "address",
            )

            left_postcode = extract_postcode(
                left_address
            )

            right_postcode = extract_postcode(
                right_address
            )

            print(
                f"    {'DOB':<8} "
                f"{left_dob!r} "
                f"<-> "
                f"{right_dob!r}"
            )

            print(
                f"    {'EMAIL':<8} "
                f"{left_email!r} "
                f"<-> "
                f"{right_email!r}"
            )

            print(
                f"    {'PHONE':<8} "
                f"{left_phone!r} "
                f"<-> "
                f"{right_phone!r}"
            )

            print(
                f"    {'NAME':<8} "
                f"{left_name!r} "
                f"<-> "
                f"{right_name!r}"
            )

            print(
                f"    {'SURNAME':<8} "
                f"{left_surname!r} "
                f"<-> "
                f"{right_surname!r}"
            )

            print(
                f"    {'POSTAL':<8} "
                f"{left_postcode!r} "
                f"<-> "
                f"{right_postcode!r}"
            )

            print(
                f"    {'ADDRESS':<8} "
                f"{left_address!r} "
                f"<-> "
                f"{right_address!r}"
            )

        print()

    print("=" * 70)
    print("Blocking miss diagnostic complete.")


if __name__ == "__main__":
    main()