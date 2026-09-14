import re
from collections import defaultdict
from typing import Dict, Iterable, List


def safe_text(value: str | None) -> str:
    """
    Convert None/blank values into an empty string.
    """
    if value is None:
        return ""

    return str(value).strip()


def extract_surname(normalized_name: str | None) -> str:
    """
    Extract the final token from a normalized name.

    Example:
        "RAHUL KUMAR SHARMA"
        -> "SHARMA"
    """
    value = safe_text(normalized_name)

    if not value:
        return ""

    parts = value.split()

    return parts[-1] if parts else ""


def extract_postcode(address: str | None) -> str:
    """
    Extract a UK-style postcode from an address.

    Returns an uppercase compact postcode or an empty string
    when one cannot be found.
    """
    value = safe_text(address).upper()

    if not value:
        return ""

    pattern = r"\b([A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2})\b"

    match = re.search(pattern, value)

    if not match:
        return ""

    return match.group(1).replace(" ", "")


def make_surname_dob_key(row: Dict[str, str]) -> str:
    surname = extract_surname(row.get("normalized_name"))
    dob = safe_text(row.get("normalized_dob"))

    if not surname or not dob:
        return ""

    return f"{surname}|{dob}"


def make_email_key(row: Dict[str, str]) -> str:
    return safe_text(row.get("normalized_email"))


def make_phone_suffix_key(
    row: Dict[str, str],
    suffix_length: int = 7,
) -> str:
    phone = safe_text(row.get("normalized_phone"))

    if not phone:
        return ""

    digits = re.sub(r"\D", "", phone)

    if len(digits) < suffix_length:
        return ""

    return digits[-suffix_length:]


def make_dob_postcode_key(row: Dict[str, str]) -> str:
    dob = safe_text(row.get("normalized_dob"))
    postcode = extract_postcode(row.get("normalized_address"))

    if not dob or not postcode:
        return ""

    return f"{dob}|{postcode}"


BLOCKING_STRATEGIES = {
    "surname_dob": make_surname_dob_key,
    "email": make_email_key,
    "phone_suffix": make_phone_suffix_key,
    "dob_postcode": make_dob_postcode_key,
}


def build_block_indexes(rows: Iterable[Dict[str, str]]) -> dict:
    """
    Build an inverted index for all blocking strategies.

    Returns:
        {
            "surname_dob": {
                "SHARMA|1988-06-12": [row, row, ...]
            },
            "email": {
                "rahul@example.com": [row, row, ...]
            },
            ...
        }
    """
    indexes = {
        strategy_name: defaultdict(list)
        for strategy_name in BLOCKING_STRATEGIES
    }

    for row in rows:
        for strategy_name, key_function in BLOCKING_STRATEGIES.items():

            key = key_function(row)

            if not key:
                continue

            indexes[strategy_name][key].append(row)

    return indexes

from itertools import combinations

from .models import CandidatePair, RecordRef


def generate_candidate_pairs(
    rows: Iterable[dict[str, str]],
) -> list[CandidatePair]:
    """
    Generate candidate record pairs using all blocking strategies.
    """

    rows = list(rows)

    indexes = build_block_indexes(rows)

    pair_map: dict[tuple[tuple[str, str], tuple[str, str]], CandidatePair] = {}

    for strategy_name, index in indexes.items():

        for block_key, block_rows in index.items():

            if len(block_rows) < 2:
                continue

            for left, right in combinations(block_rows, 2):

                left_ref = RecordRef(
                    source_system=left["source_system"],
                    source_id=left["source_id"],
                )

                right_ref = RecordRef(
                    source_system=right["source_system"],
                    source_id=right["source_id"],
                )

                if left_ref == right_ref:
                    continue

                ordered_refs = tuple(
                    sorted([left_ref, right_ref], key=lambda ref: (
                        ref.source_system,
                        ref.source_id,
                    ))
                )

                pair_key = (
                    (ordered_refs[0].source_system,
                     ordered_refs[0].source_id),
                    (ordered_refs[1].source_system,
                     ordered_refs[1].source_id),
                )

                if pair_key not in pair_map:

                    pair_map[pair_key] = CandidatePair(
                        left=ordered_refs[0],
                        right=ordered_refs[1],
                        blocking_keys=[strategy_name],
                    )

                else:

                    if strategy_name not in pair_map[pair_key].blocking_keys:
                        pair_map[pair_key].blocking_keys.append(
                            strategy_name
                        )

    return list(pair_map.values())