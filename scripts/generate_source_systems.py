"""
Phase 1 — Banking MDM Source-System Simulator

Inputs:
    data/external/banking_digital_twin/base_individuals.csv
    data/external/gleif/gleif_entities.csv

Outputs:
    data/source_systems/core/core_customers.csv
    data/source_systems/crm/crm_customers.csv
    data/source_systems/kyc/kyc_customers.csv
    data/source_systems/wealth/wealth_customers.csv

Ground truth:
    data/ground_truth/ground_truth.csv

IMPORTANT:
    entity_key exists only inside the simulator and ground truth.
    It must NEVER appear in source-system files.
"""

import argparse
import csv
import json
import random
import string
from datetime import date, timedelta
from pathlib import Path

import yaml
from faker import Faker


# ============================================================
# CONFIGURATION
# ============================================================

CONFIG_PATH = Path(
    "configs/simulator.yaml"
)

CONFIG = yaml.safe_load(
    CONFIG_PATH.read_text(
        encoding="utf-8"
    )
)

SEED = CONFIG["simulation"]["seed"]

random.seed(SEED)
Faker.seed(SEED)

fake = Faker("en_GB")


# ============================================================
# INPUTS
# ============================================================

INDIVIDUALS_PATH = Path(
    "data/external/banking_digital_twin/"
    "base_individuals.csv"
)

GLEIF_PATH = Path(
    "data/external/gleif/"
    "gleif_entities.csv"
)


# ============================================================
# OUTPUTS
# ============================================================

SOURCE_DIR = Path(
    "data/source_systems"
)

GROUND_TRUTH_PATH = Path(
    "data/ground_truth/"
    "ground_truth.csv"
)

METADATA_PATH = Path(
    "data/ground_truth/"
    "simulator_run_metadata.json"
)


# ============================================================
# SIMULATION PARAMETERS
# ============================================================

APPEARANCE_RATES = CONFIG[
    "system_appearance_rates"
]

MIDDLE_NAME_RATE = CONFIG[
    "messiness"
]["middle_name_rate"]

MISSING_RATE = CONFIG[
    "messiness"
]["general_missing_rate"]

CRM_MISSING_DOB_RATE = CONFIG[
    "messiness"
]["crm_missing_dob_rate"]

WEALTH_MISSING_EMAIL_RATE = CONFIG[
    "messiness"
]["wealth_missing_email_rate"]

CONFLICT_RATE = CONFIG[
    "messiness"
]["conflict_rate"]

DUPLICATE_RATE = CONFIG[
    "messiness"
]["duplicate_rate"]


# ============================================================
# STATISTICS
# ============================================================

STATS = {
    "individuals_processed": 0,
    "legal_entities_processed": 0,

    "hidden_entities": 0,

    "entities_with_zero_sources_before_fallback": 0,

    "middle_names_added": 0,

    "phone_conflicts": 0,
    "email_conflicts": 0,

    "missing_values": {
        "core": 0,
        "crm": 0,
        "kyc": 0,
        "wealth": 0,
    },

    "duplicate_rows": {
        "core": 0,
        "crm": 0,
        "kyc": 0,
        "wealth": 0,
    },

    "source_rows": {
        "core": 0,
        "crm": 0,
        "kyc": 0,
        "wealth": 0,
    },

    "entities_with_source_count": {
        "1": 0,
        "2": 0,
        "3": 0,
        "4": 0,
    },
}


# ============================================================
# SOURCE SCHEMAS
# ============================================================

SYSTEMS = {
    "core": {
        "prefix": "C",

        "filename":
            "core/core_customers.csv",

        "fields": [
            "customer_id",
            "full_name",
            "dob",
            "phone",
            "email",
            "address",
            "account_id",
            "branch_id",
        ],
    },

    "crm": {
        "prefix": "CRM",

        "filename":
            "crm/crm_customers.csv",

        "fields": [
            "crm_customer_id",
            "customer_name",
            "date_of_birth",
            "mobile",
            "email_address",
            "residential_address",
            "segment",
        ],
    },

    "kyc": {
        "prefix": "KYC",

        "filename":
            "kyc/kyc_customers.csv",

        "fields": [
            "kyc_id",
            "legal_name",
            "dob",
            "tax_id",
            "phone",
            "address",
            "kyc_status",
            "verification_date",
            "LEI",
        ],
    },

    "wealth": {
        "prefix": "W",

        "filename":
            "wealth/wealth_customers.csv",

        "fields": [
            "client_id",
            "client_name",
            "dob",
            "phone",
            "email",
            "address",
            "aum",
            "risk_profile",
            "relationship_manager",
        ],
    },
}


# ============================================================
# HIDDEN ENTITY HELPERS
# ============================================================

def make_entity_key(
    entity_sequence: int,
) -> str:
    """
    Hidden simulator truth identifier.

    NEVER write this into a source-system file.
    """

    return f"E{entity_sequence:07d}"


def make_synthetic_tax_id(
    entity_sequence: int,
) -> str:
    """
    Synthetic tax identifier.

    This is NOT a real tax identifier.
    """

    return (
        f"QQ{entity_sequence:07d}A"
    )


def make_synthetic_phone() -> str:
    """
    Generate a synthetic UK-style mobile number.
    """

    return (
        "07"
        + "".join(
            random.choices(
                string.digits,
                k=9,
            )
        )
    )


def make_account_id(
    sequence: int,
) -> str:

    return (
        f"ACC{sequence:09d}"
    )


def make_branch_id(
    sequence: int,
) -> str:

    branch_number = (
        ((sequence - 1) % 500)
        + 1
    )

    return (
        f"BR{branch_number:03d}"
    )


def make_verification_date() -> str:

    start = date(
        2023,
        1,
        1,
    )

    end = date(
        2026,
        12,
        31,
    )

    days = (
        end - start
    ).days

    return (
        start
        + timedelta(
            days=random.randint(
                0,
                days,
            )
        )
    ).isoformat()


# ============================================================
# BUILD INTERNAL ENTITY REPRESENTATIONS
# ============================================================

def build_individual_entity(
    row: dict,
    entity_sequence: int,
) -> dict:
    """
    Convert one Banking Digital Twin row into
    the simulator's common internal representation.
    """

    middle = None

    if (
        random.random()
        < MIDDLE_NAME_RATE
    ):
        middle = fake.first_name()
        STATS["middle_names_added"] += 1

    return {
        "kind": "individual",

        "first":
            row["first_name"],

        "middle":
            middle,

        "last":
            row["last_name"],

        "full_name_override":
            None,

        "dob":
            row["dob"],

        "phone":
            row["phone"],

        "email":
            row["email"],

        "address_line":
            row["address_line"],

        "city":
            row["city"],

        "region":
            row["region"],

        "postcode":
            row["postcode"],

        "lei":
            "",

        "tax_id":
            make_synthetic_tax_id(
                entity_sequence
            ),
    }


def build_legal_entity(
    row: dict,
    entity_sequence: int,
) -> dict:
    """
    Convert one GLEIF row into the simulator's
    common internal representation.
    """

    return {
        "kind": "entity",

        "first":
            None,

        "middle":
            None,

        "last":
            None,

        "full_name_override":
            row["legal_name"],

        "dob":
            "",

        "phone":
            make_synthetic_phone(),

        "email":
            build_entity_email(
                row["legal_name"]
            ),

        "address_line":
            row.get(
                "address_line",
                "",
            ),

        "city":
            row.get(
                "city",
                "",
            ),

        "region":
            row.get(
                "region",
                "",
            ),

        "postcode":
            row.get(
                "postal_code",
                "",
            ),

        "lei":
            row.get(
                "lei",
                "",
            ),

        "tax_id":
            make_synthetic_tax_id(
                entity_sequence
            ),
    }


def build_entity_email(
    legal_name: str,
) -> str:

    cleaned = (
        legal_name
        .lower()
        .replace(
            " ",
            ".",
        )
    )

    cleaned = (
        cleaned
        .replace(
            ",",
            "",
        )
        .replace(
            "&",
            "and",
        )
    )

    return (
        cleaned[:30]
        + "@example.com"
    )


# ============================================================
# ATTRIBUTE TRANSFORMATIONS
# ============================================================

def true_name(
    record: dict,
) -> str:

    if (
        record["kind"]
        == "entity"
    ):
        return (
            record[
                "full_name_override"
            ]
        )

    parts = [
        record["first"],
        record["middle"],
        record["last"],
    ]

    return " ".join(
        part
        for part in parts
        if part
    )


def corporate_short_name(
    name: str,
) -> str:

    replacements = [
        (
            " PUBLIC LIMITED COMPANY",
            " PLC",
        ),
        (
            " LIMITED",
            " LTD",
        ),
        (
            " CORPORATION",
            " CORP",
        ),
        (
            " INCORPORATED",
            " INC",
        ),
    ]

    result = name

    for old, new in replacements:

        result = (
            result.replace(
                old,
                new,
            )
        )

    return result


def messy_name(
    record: dict,
    system: str,
) -> str:

    name = true_name(
        record
    )

    # Legal entities
    if (
        record["kind"]
        == "entity"
    ):

        if system == "crm":
            return corporate_short_name(
                name
            )

        if system == "kyc":
            return name.upper()

        if system == "wealth":
            return corporate_short_name(
                name
            )

        return name

    # Individuals
    first = record["first"]
    middle = record["middle"]
    last = record["last"]

    if (
        system == "crm"
        and middle
    ):
        return (
            f"{first} "
            f"{middle[0]}. "
            f"{last}"
        )

    if system == "kyc":
        return name.upper()

    if system == "wealth":
        return (
            f"{first} {last}"
        )

    return name


def formatted_phone(
    phone: str,
    system: str,
) -> str:

    if not phone:
        return ""

    digits = "".join(
        char
        for char in phone
        if char.isdigit()
    )

    if len(digits) < 10:
        return phone

    local = digits[-10:]

    if system == "crm":
        return (
            f"+44 "
            f"{local[:4]} "
            f"{local[4:]}"
        )

    if system == "wealth":
        return (
            f"+44-{local}"
        )

    return phone


def maybe_conflicting_phone(
    phone: str,
) -> str:

    if not phone:
        return ""

    if (
        random.random()
        < CONFLICT_RATE
    ):

        STATS[
            "phone_conflicts"
        ] += 1

        return make_synthetic_phone()

    return phone


def maybe_conflicting_email(
    email: str,
) -> str:

    if not email:
        return ""

    if (
        random.random()
        < CONFLICT_RATE
    ):

        STATS[
            "email_conflicts"
        ] += 1

        return email.replace(
            "@example.com",
            "@oldmail.com",
        )

    return email


def maybe_blank(
    value: str,
    system: str,
) -> str:

    if not value:
        return ""

    if (
        random.random()
        < MISSING_RATE
    ):

        STATS[
            "missing_values"
        ][system] += 1

        return ""

    return value


def format_dob(
    dob: str,
    system: str,
) -> str:

    if not dob:
        return ""

    parts = dob.split("-")

    if len(parts) != 3:
        return dob

    year, month, day = parts

    if system == "crm":
        return (
            f"{day}/{month}/{year}"
        )

    if system == "wealth":
        return (
            f"{day}-{month}-{year}"
        )

    return dob


def full_address(
    record: dict,
) -> str:

    parts = [
        record["address_line"],
        record["city"],
        record["region"],
        record["postcode"],
    ]

    return ", ".join(
        part
        for part in parts
        if part and part.strip()
    )


def crm_address(
    record: dict,
) -> str:

    parts = [
        record["city"],
        record["region"],
        record["postcode"],
    ]

    return ", ".join(
        part
        for part in parts
        if part and part.strip()
    )


def wealth_address(
    record: dict,
) -> str:

    parts = [
        record["address_line"],
        record["city"],
    ]

    return ", ".join(
        part
        for part in parts
        if part and part.strip()
    )


# ============================================================
# SOURCE-SPECIFIC BUSINESS ATTRIBUTES
# ============================================================

def choose_segment(
    record: dict,
) -> str:

    if (
        record["kind"]
        == "entity"
    ):

        return random.choice(
            [
                "Corporate",
                "Institutional",
                "SME",
            ]
        )

    return random.choice(
        [
            "Retail",
            "Premier",
            "Affluent",
        ]
    )


def choose_risk_profile() -> str:

    return random.choice(
        [
            "Conservative",
            "Balanced",
            "Growth",
            "Aggressive",
        ]
    )


# ============================================================
# SOURCE ROW BUILDERS
# ============================================================

def build_core_row(
    record: dict,
    source_id: str,
    entity_sequence: int,
) -> dict:

    phone = maybe_conflicting_phone(
        record["phone"]
    )

    email = maybe_blank(
        record["email"],
        "core",
    )

    return {
        "customer_id":
            source_id,

        "full_name":
            messy_name(
                record,
                "core",
            ),

        "dob":
            maybe_blank(
                format_dob(
                    record["dob"],
                    "core",
                ),
                "core",
            ),

        "phone":
            formatted_phone(
                phone,
                "core",
            ),

        "email":
            email,

        "address":
            full_address(
                record
            ),

        "account_id":
            make_account_id(
                entity_sequence
            ),

        "branch_id":
            make_branch_id(
                entity_sequence
            ),
    }


def build_crm_row(
    record: dict,
    source_id: str,
    entity_sequence: int,
) -> dict:

    dob = format_dob(
        record["dob"],
        "crm",
    )

    if (
        dob
        and random.random()
        < CRM_MISSING_DOB_RATE
    ):
        STATS[
            "missing_values"
        ]["crm"] += 1

        dob = ""

    phone = maybe_conflicting_phone(
        record["phone"]
    )

    email = maybe_conflicting_email(
        maybe_blank(
            record["email"],
            "crm",
        )
    )

    return {
        "crm_customer_id":
            source_id,

        "customer_name":
            messy_name(
                record,
                "crm",
            ),

        "date_of_birth":
            dob,

        "mobile":
            formatted_phone(
                phone,
                "crm",
            ),

        "email_address":
            email,

        "residential_address":
            crm_address(
                record
            ),

        "segment":
            choose_segment(
                record
            ),
    }


def build_kyc_row(
    record: dict,
    source_id: str,
    entity_sequence: int,
) -> dict:

    # KYC is deliberately authoritative for
    # identity attributes in our simulation.
    return {
        "kyc_id":
            source_id,

        "legal_name":
            messy_name(
                record,
                "kyc",
            ),

        "dob":
            format_dob(
                record["dob"],
                "kyc",
            ),

        "tax_id":
            record["tax_id"],

        "phone":
            formatted_phone(
                record["phone"],
                "kyc",
            ),

        "address":
            full_address(
                record
            ).upper(),

        "kyc_status":
            random.choice(
                [
                    "VERIFIED",
                    "VERIFIED",
                    "PENDING",
                    "EXPIRED",
                ]
            ),

        "verification_date":
            make_verification_date(),

        "LEI":
            record["lei"],
    }


def build_wealth_row(
    record: dict,
    source_id: str,
    entity_sequence: int,
) -> dict:

    email = record["email"]

    if (
        email
        and random.random()
        < WEALTH_MISSING_EMAIL_RATE
    ):

        STATS[
            "missing_values"
        ]["wealth"] += 1

        email = ""

    elif email:

        email = maybe_conflicting_email(
            email
        )

    phone = maybe_conflicting_phone(
        record["phone"]
    )

    return {
        "client_id":
            source_id,

        "client_name":
            messy_name(
                record,
                "wealth",
            ),

        "dob":
            format_dob(
                record["dob"],
                "wealth",
            ),

        "phone":
            formatted_phone(
                phone,
                "wealth",
            ),

        "email":
            email,

        "address":
            wealth_address(
                record
            ),

        "aum":
            round(
                random.uniform(
                    50_000,
                    5_000_000,
                ),
                2,
            ),

        "risk_profile":
            choose_risk_profile(),

        "relationship_manager":
            fake.name(),
    }


# ============================================================
# SOURCE ID
# ============================================================

def make_source_id(
    system: str,
    sequence: int,
) -> str:

    return (
        f"{SYSTEMS[system]['prefix']}"
        f"{sequence:08d}"
    )


# ============================================================
# SOURCE APPEARANCE
# ============================================================

def selected_systems() -> list[str]:
    """
    Decide which source systems receive this entity.

    We use the configured probabilities.

    If none are selected, we force one system so that
    every underlying entity appears in at least one
    source system. This prevents "invisible" entities
    from disappearing from the benchmark entirely.
    """

    selected = []

    for system in SYSTEMS:

        if (
            random.random()
            <= APPEARANCE_RATES[system]
        ):
            selected.append(system)

    if not selected:

        STATS[
            "entities_with_zero_sources_before_fallback"
        ] += 1

        selected.append(
            random.choice(
                list(SYSTEMS.keys())
            )
        )

    return selected


# ============================================================
# EMIT ONE ENTITY
# ============================================================

def emit_entity(
    record: dict,
    entity_key: str,
    entity_sequence: int,
    writers: dict,
    counters: dict,
    ground_truth_writer,
):

    builders = {
        "core":
            build_core_row,

        "crm":
            build_crm_row,

        "kyc":
            build_kyc_row,

        "wealth":
            build_wealth_row,
    }

    systems_for_entity = (
        selected_systems()
    )

    STATS[
        "entities_with_source_count"
    ][
        str(
            len(
                systems_for_entity
            )
        )
    ] += 1

    for system in systems_for_entity:

        counters[system] += 1

        source_id = make_source_id(
            system,
            counters[system],
        )

        row = builders[system](
            record,
            source_id,
            entity_sequence,
        )

        writers[
            system
        ].writerow(row)

        STATS[
            "source_rows"
        ][system] += 1

        ground_truth_writer.writerow(
            {
                "source_system":
                    system.upper(),

                "source_id":
                    source_id,

                "entity_key":
                    entity_key,
            }
        )

        # ----------------------------------------------------
        # Controlled same-source duplicate
        # ----------------------------------------------------

        if (
            random.random()
            < DUPLICATE_RATE
        ):

            counters[system] += 1

            duplicate_id = make_source_id(
                system,
                counters[system],
            )

            duplicate_row = builders[
                system
            ](
                record,
                duplicate_id,
                entity_sequence,
            )

            writers[
                system
            ].writerow(
                duplicate_row
            )

            STATS[
                "source_rows"
            ][system] += 1

            STATS[
                "duplicate_rows"
            ][system] += 1

            ground_truth_writer.writerow(
                {
                    "source_system":
                        system.upper(),

                    "source_id":
                        duplicate_id,

                    "entity_key":
                        entity_key,
                }
            )


# ============================================================
# OUTPUT WRITERS
# ============================================================

def open_source_writers():

    handles = {}
    writers = {}

    for system, config in (
        SYSTEMS.items()
    ):

        output_path = (
            SOURCE_DIR
            / config["filename"]
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        handle = output_path.open(
            "w",
            newline="",
            encoding="utf-8",
        )

        writer = csv.DictWriter(
            handle,
            fieldnames=config[
                "fields"
            ],
        )

        writer.writeheader()

        handles[system] = handle
        writers[system] = writer

    return handles, writers


# ============================================================
# STREAM INDIVIDUALS
# ============================================================

def stream_individuals(
    writers,
    counters,
    ground_truth_writer,
    maximum=None,
    starting_sequence=0,
):

    count = 0
    entity_sequence = (
        starting_sequence
    )

    with INDIVIDUALS_PATH.open(
        newline="",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            if (
                maximum is not None
                and count >= maximum
            ):
                break

            entity_sequence += 1
            count += 1

            entity_key = (
                make_entity_key(
                    entity_sequence
                )
            )

            record = (
                build_individual_entity(
                    row,
                    entity_sequence,
                )
            )

            emit_entity(
                record=record,
                entity_key=entity_key,
                entity_sequence=entity_sequence,
                writers=writers,
                counters=counters,
                ground_truth_writer=(
                    ground_truth_writer
                ),
            )

            STATS[
                "individuals_processed"
            ] += 1

            STATS[
                "hidden_entities"
            ] += 1

            if (
                count % 100_000
                == 0
            ):

                print(
                    f"Processed "
                    f"{count:,} "
                    f"individual entities..."
                )

    return (
        count,
        entity_sequence,
    )


# ============================================================
# STREAM LEGAL ENTITIES
# ============================================================

def stream_legal_entities(
    writers,
    counters,
    ground_truth_writer,
    maximum=None,
    starting_sequence=0,
):

    count = 0
    entity_sequence = (
        starting_sequence
    )

    with GLEIF_PATH.open(
        newline="",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            if (
                maximum is not None
                and count >= maximum
            ):
                break

            entity_sequence += 1
            count += 1

            entity_key = (
                make_entity_key(
                    entity_sequence
                )
            )

            record = (
                build_legal_entity(
                    row,
                    entity_sequence,
                )
            )

            emit_entity(
                record=record,
                entity_key=entity_key,
                entity_sequence=entity_sequence,
                writers=writers,
                counters=counters,
                ground_truth_writer=(
                    ground_truth_writer
                ),
            )

            STATS[
                "legal_entities_processed"
            ] += 1

            STATS[
                "hidden_entities"
            ] += 1

            if (
                count % 10_000
                == 0
            ):

                print(
                    f"Processed "
                    f"{count:,} "
                    f"legal entities..."
                )

    return (
        count,
        entity_sequence,
    )


# ============================================================
# MAIN
# ============================================================

def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--individual-limit",
        type=int,
        default=None,
        help=(
            "Optional limit for smoke testing."
        ),
    )

    parser.add_argument(
        "--gleif-limit",
        type=int,
        default=None,
        help=(
            "Optional limit for smoke testing."
        ),
    )

    return parser.parse_args()


def main():

    args = parse_args()

    if not INDIVIDUALS_PATH.exists():
        raise FileNotFoundError(
            f"Missing input:\n"
            f"{INDIVIDUALS_PATH}"
        )

    if not GLEIF_PATH.exists():
        raise FileNotFoundError(
            f"Missing input:\n"
            f"{GLEIF_PATH}"
        )

    SOURCE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    GROUND_TRUTH_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    handles, writers = (
        open_source_writers()
    )

    ground_truth_handle = (
        GROUND_TRUTH_PATH.open(
            "w",
            newline="",
            encoding="utf-8",
        )
    )

    ground_truth_writer = (
        csv.DictWriter(
            ground_truth_handle,
            fieldnames=[
                "source_system",
                "source_id",
                "entity_key",
            ],
        )
    )

    ground_truth_writer.writeheader()

    counters = {
        system: 0
        for system in SYSTEMS
    }

    try:

        individual_count, sequence = (
            stream_individuals(
                writers=writers,
                counters=counters,
                ground_truth_writer=(
                    ground_truth_writer
                ),
                maximum=(
                    args.individual_limit
                ),
                starting_sequence=0,
            )
        )

        legal_entity_count, sequence = (
            stream_legal_entities(
                writers=writers,
                counters=counters,
                ground_truth_writer=(
                    ground_truth_writer
                ),
                maximum=(
                    args.gleif_limit
                ),
                starting_sequence=sequence,
            )
        )

    finally:

        for handle in (
            handles.values()
        ):
            handle.close()

        ground_truth_handle.close()

    # ========================================================
    # Write simulator metadata
    # ========================================================

    metadata = {
        "seed": SEED,

        "individuals_processed":
            individual_count,

        "legal_entities_processed":
            legal_entity_count,

        "hidden_entities":
            STATS["hidden_entities"],

        "source_rows":
            STATS["source_rows"],

        "duplicate_rows":
            STATS["duplicate_rows"],

        "middle_names_added":
            STATS["middle_names_added"],

        "phone_conflicts":
            STATS["phone_conflicts"],

        "email_conflicts":
            STATS["email_conflicts"],

        "missing_values":
            STATS["missing_values"],

        "entities_with_source_count":
            STATS[
                "entities_with_source_count"
            ],

        "zero_source_fallbacks":
            STATS[
                "entities_with_zero_sources_before_fallback"
            ],

        "appearance_rates":
            APPEARANCE_RATES,

        "messiness": CONFIG[
            "messiness"
        ],
    }

    METADATA_PATH.write_text(
        json.dumps(
            metadata,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "SOURCE SIMULATION COMPLETE"
    )

    print(
        "=" * 70
    )

    print(
        f"Individuals: "
        f"{individual_count:,}"
    )

    print(
        f"Legal entities: "
        f"{legal_entity_count:,}"
    )

    print(
        f"Hidden entities: "
        f"{STATS['hidden_entities']:,}"
    )

    print(
        "\nSource rows:"
    )

    for system in SYSTEMS:

        print(
            f"  {system.upper():8s}: "
            f"{STATS['source_rows'][system]:,}"
        )

    print(
        "\nGround truth rows:"
    )

    print(
        f"  {sum(STATS['source_rows'].values()):,}"
    )

    print(
        "\nMetadata:"
    )

    print(
        f"  {METADATA_PATH}"
    )


if __name__ == "__main__":
    main()