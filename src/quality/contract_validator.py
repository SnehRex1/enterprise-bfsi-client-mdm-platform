"""
Generic YAML-driven data-contract validator.

Responsibilities:
    1. Load a YAML contract.
    2. Validate CSV schema.
    3. Validate individual field values.
    4. Write valid rows to a validated output.
    5. Write invalid rows to quarantine.
    6. Record failure reasons.
    7. Produce a machine-readable validation report.

This module intentionally does NOT:
    - normalize names
    - normalize phone numbers
    - normalize emails
    - normalize addresses
    - perform entity matching
    - read ground truth

Those belong to later phases.
"""

import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class ContractValidationError(Exception):
    """
    Raised when the contract definition itself is invalid.

    This is different from a bad source record.

    Example:

        Bad source row
            -> quarantine

        Broken contract YAML
            -> raise ContractValidationError
    """



def load_contract(contract_path: Path) -> dict:
    """
    Load one YAML contract from disk.

    Parameters
    ----------
    contract_path:
        Path to the YAML contract.

    Returns
    -------
    dict
        Parsed contract.

    Raises
    ------
    FileNotFoundError
        If the contract does not exist.

    ContractValidationError
        If the contract structure is invalid.
    """

    # Make sure the contract file actually exists.
    if not contract_path.exists():
        raise FileNotFoundError(
            f"Contract file not found: {contract_path}"
        )

    # Open the YAML file as UTF-8 text.
    with contract_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        # Convert YAML into Python dictionaries/lists.
        contract = yaml.safe_load(file)

    # The top-level YAML object must be a dictionary.
    if not isinstance(contract, dict):
        raise ContractValidationError(
            f"Contract must contain a YAML mapping: {contract_path}"
        )

    # The contract must contain a top-level "contract" section.
    if "contract" not in contract:
        raise ContractValidationError(
            f"Missing top-level 'contract' section: "
            f"{contract_path}"
        )

    contract_body = contract["contract"]

    # The contract body must also be a dictionary.
    if not isinstance(contract_body, dict):
        raise ContractValidationError(
            f"'contract' section must be a mapping: "
            f"{contract_path}"
        )

    # The fields section is mandatory.
    if "fields" not in contract_body:
        raise ContractValidationError(
            f"Missing 'fields' section: {contract_path}"
        )

    return contract


def is_blank(value: Any) -> bool:
    """
    Return True when a value is None or contains only whitespace.

    Examples:
        None       -> True
        ""         -> True
        "   "      -> True
        "John"     -> False
    """

    if value is None:
        return True

    return not str(value).strip()


def validate_type(
    value: str,
    expected_type: str,
) -> str | None:
    """
    Validate the basic datatype of one value.

    Returns:
        None when valid.
        An error message when invalid.
    """

    # Remove surrounding whitespace before checking.
    value = value.strip()

    try:

        # Every textual source field is accepted as a string.
        if expected_type == "string":
            return None

        # Attempt to parse an integer.
        if expected_type == "integer":
            int(value)
            return None

        # Attempt to parse a floating-point number.
        if expected_type == "float":
            float(value)
            return None

        # Support simple boolean representation.
        if expected_type == "boolean":

            normalized = value.lower()

            if normalized not in {
                "true",
                "false",
                "1",
                "0",
            }:
                return (
                    "expected boolean "
                    "(true/false/1/0)"
                )

            return None

        # Unknown types are contract-definition problems,
        # not source-data problems.
        raise ContractValidationError(
            f"Unsupported contract type: "
            f"{expected_type}"
        )

    except ValueError:

        return (
            f"expected {expected_type}, "
            f"received '{value}'"
        )


def validate_semantic_format(
    value: str,
    field_rules: dict,
) -> str | None:
    """
    Validate semantic formats such as dates.

    Important:
        The physical source datatype may still be STRING.

        Example:
            type: string
            semantic_type: date

    That lets us accept multiple raw date representations
    without performing normalization.
    """

    semantic_type = field_rules.get(
        "semantic_type"
    )

    formats = field_rules.get(
        "allowed_formats",
        [],
    )

    # Currently we support semantic date validation.
    if semantic_type == "date":

        # Try each approved date format.
        for date_format in formats:

            try:

                datetime.strptime(
                    value,
                    date_format,
                )

                # The value matched one allowed format.
                return None

            except ValueError:
                # Try the next allowed format.
                continue

        # None of the formats matched.
        return (
            f"value '{value}' does not match "
            f"allowed date formats: {formats}"
        )

    return None


def validate_value(
    value: Any,
    field_name: str,
    field_rules: dict,
) -> list[str]:
    """
    Validate one field value using the YAML rules.

    Multiple validation issues can theoretically exist for one field,
    therefore this returns a list of error messages.
    """

    issues: list[str] = []

    required = field_rules.get(
        "required",
        False,
    )

    nullable = field_rules.get(
        "nullable",
        False,
    )

    # --------------------------------------------------------
    # 1. Blank/null handling
    # --------------------------------------------------------

    if is_blank(value):

        # A blank is only a problem when the field is required
        # AND the field is not nullable.
        if required and not nullable:

            issues.append(
                f"{field_name}: "
                f"required value is blank"
            )

        # If the field is nullable, the blank is legitimate.
        #
        # We stop here because there is nothing meaningful to
        # type-check or pattern-check.
        return issues

    value_str = str(value).strip()

    # --------------------------------------------------------
    # 2. Basic datatype validation
    # --------------------------------------------------------

    expected_type = field_rules.get(
        "type"
    )

    if expected_type:

        type_error = validate_type(
            value_str,
            expected_type,
        )

        if type_error:

            issues.append(
                f"{field_name}: "
                f"{type_error}"
            )

    # --------------------------------------------------------
    # 3. Pattern validation
    # --------------------------------------------------------

    pattern = field_rules.get(
        "pattern"
    )

    if pattern:

        if not re.fullmatch(
            pattern,
            value_str,
        ):

            issues.append(
                f"{field_name}: "
                f"value '{value_str}' "
                f"does not match pattern "
                f"'{pattern}'"
            )

    # --------------------------------------------------------
    # 4. Allowed-value validation
    # --------------------------------------------------------

    allowed_values = field_rules.get(
        "allowed_values"
    )

    # Only validate when the contract actually supplies
    # a non-empty list of allowed values.
    if allowed_values:

        if value_str not in allowed_values:

            issues.append(
                f"{field_name}: "
                f"value '{value_str}' "
                f"is not in allowed values "
                f"{allowed_values}"
            )

    # --------------------------------------------------------
    # 5. Semantic format validation
    # --------------------------------------------------------

    semantic_error = validate_semantic_format(
        value_str,
        field_rules,
    )

    if semantic_error:

        issues.append(
            f"{field_name}: "
            f"{semantic_error}"
        )

    return issues


def validate_headers(
    actual_headers: list[str] | None,
    expected_headers: list[str],
) -> list[str]:
    """
    Compare actual CSV columns to contract columns.

    We care about:
        - missing columns
        - unexpected columns

    We deliberately do NOT require physical column order to match.
    """

    if actual_headers is None:

        return [
            "source file has no CSV header"
        ]

    actual_set = set(
        actual_headers
    )

    expected_set = set(
        expected_headers
    )

    # Columns required by the contract but absent in CSV.
    missing = sorted(
        expected_set - actual_set
    )

    # Columns present in CSV but not declared by contract.
    unexpected = sorted(
        actual_set - expected_set
    )

    issues: list[str] = []

    if missing:

        issues.append(
            "missing columns: "
            + ", ".join(missing)
        )

    if unexpected:

        issues.append(
            "unexpected columns: "
            + ", ".join(unexpected)
        )

    return issues


def validate_source_file(
    source_path: Path,
    contract_path: Path,
    validated_output_path: Path,
    quarantine_output_path: Path,
    report_path: Path,
) -> dict:
    """
    Validate one source CSV using one YAML contract.

    Processing flow:

        source CSV
              ↓
        contract validation
              ↓
        ┌───────────────┐
        │               │
       PASS            FAIL
        │               │
        ↓               ↓
    validated       quarantine
                        +
                  failure_reason

    No invalid record is silently dropped.
    """

    # --------------------------------------------------------
    # Load contract
    # --------------------------------------------------------

    contract = load_contract(
        contract_path
    )

    contract_body = contract[
        "contract"
    ]

    fields = contract_body[
        "fields"
    ]

    # The field names declared in YAML become the expected
    # CSV header set.
    expected_headers = list(
        fields.keys()
    )

    # --------------------------------------------------------
    # Check input source exists
    # --------------------------------------------------------

    if not source_path.exists():

        raise FileNotFoundError(
            f"Source file not found: "
            f"{source_path}"
        )

    # --------------------------------------------------------
    # Create output directories
    # --------------------------------------------------------

    validated_output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    quarantine_output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Counters
    # --------------------------------------------------------

    total_rows = 0
    passed_rows = 0
    quarantined_rows = 0
    issue_count = 0

    schema_issues: list[str] = []

    # --------------------------------------------------------
    # Open source CSV
    # --------------------------------------------------------

    with source_path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as source_file:

        # DictReader turns each CSV row into a dictionary.
        #
        # Example:
        #
        # {
        #   "customer_id": "C00000001",
        #   "full_name": "John Smith",
        #   ...
        # }
        reader = csv.DictReader(
            source_file
        )

        # Validate headers before validating rows.
        schema_issues = validate_headers(
            reader.fieldnames,
            expected_headers,
        )

        # Preserve the actual source header order in the output.
        output_headers = list(
            reader.fieldnames
            or expected_headers
        )

        # ----------------------------------------------------
        # Open validated and quarantine outputs
        # ----------------------------------------------------

        with (
            validated_output_path.open(
                "w",
                newline="",
                encoding="utf-8",
            ) as validated_file,

            quarantine_output_path.open(
                "w",
                newline="",
                encoding="utf-8",
            ) as quarantine_file
        ):

            # Writer for records that pass the contract.
            validated_writer = csv.DictWriter(
                validated_file,
                fieldnames=output_headers,
            )

            # Quarantine gets one additional column.
            quarantine_writer = csv.DictWriter(
                quarantine_file,
                fieldnames=(
                    output_headers
                    + ["failure_reason"]
                ),
                extrasaction="ignore",
            )

            # Write headers.
            validated_writer.writeheader()
            quarantine_writer.writeheader()

            # ------------------------------------------------
            # Validate every logical CSV record
            # ------------------------------------------------

            for row in reader:

                total_rows += 1

                row_issues: list[str] = []

                # ------------------------------------------------
                # Schema problems apply to every row.
                # ------------------------------------------------

                if schema_issues:

                    row_issues.extend(
                        f"schema: {issue}"
                        for issue in schema_issues
                    )

                else:

                    # --------------------------------------------
                    # Validate every contract field.
                    # --------------------------------------------

                    for (
                        field_name,
                        field_rules,
                    ) in fields.items():

                        value = row.get(
                            field_name
                        )

                        field_issues = (
                            validate_value(
                                value,
                                field_name,
                                field_rules,
                            )
                        )

                        row_issues.extend(
                            field_issues
                        )

                # ------------------------------------------------
                # Invalid row → quarantine
                # ------------------------------------------------

                if row_issues:

                    quarantined_rows += 1

                    issue_count += len(
                        row_issues
                    )

                    # Join multiple reasons into one auditable field.
                    row[
                        "failure_reason"
                    ] = " | ".join(
                        row_issues
                    )

                    quarantine_writer.writerow(
                        row
                    )

                # ------------------------------------------------
                # Valid row → validated output
                # ------------------------------------------------

                else:

                    passed_rows += 1

                    validated_writer.writerow(
                        row
                    )

    # --------------------------------------------------------
    # Reconciliation
    # --------------------------------------------------------

    # Every input row must appear in exactly one destination:
    #
    # input = passed + quarantined
    #
    reconciled = (
        total_rows
        ==
        passed_rows
        + quarantined_rows
    )

    if not reconciled:

        raise AssertionError(
            "Contract validation reconciliation "
            "failed: "
            f"input={total_rows}, "
            f"passed={passed_rows}, "
            f"quarantined={quarantined_rows}"
        )

    # --------------------------------------------------------
    # Overall status
    # --------------------------------------------------------

    if (
        not schema_issues
        and quarantined_rows == 0
    ):

        status = "PASS"

    else:

        status = "FAIL_WITH_QUARANTINE"

    # --------------------------------------------------------
    # Machine-readable report
    # --------------------------------------------------------

    report = {

        "source_system": contract_body[
            "source_system"
        ],

        "contract_name": contract_body[
            "name"
        ],

        "contract_version": contract_body[
            "version"
        ],

        "source_file": str(
            source_path
        ),

        "total_rows": total_rows,

        "passed_rows": passed_rows,

        "quarantined_rows": (
            quarantined_rows
        ),

        "issue_count": issue_count,

        "schema_issues": schema_issues,

        "reconciliation": (
            "PASS"
            if reconciled
            else "FAIL"
        ),

        "status": status,

        "validated_output": str(
            validated_output_path
        ),

        "quarantine_output": str(
            quarantine_output_path
        ),
    }

    # Write a JSON report that later orchestration systems can read.
    report_path.write_text(
        json.dumps(
            report,
            indent=2,
        ),
        encoding="utf-8",
    )

    return report