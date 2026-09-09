"""
Build the individual customer population from Banking Digital Twin.

Only the customer/party domain is generated.
The full Banking Digital Twin simulation is NOT executed.

Usage:

    python scripts/build_base_individuals.py --customers 10000
    python scripts/build_base_individuals.py --customers 900000
"""

import argparse
import csv
import importlib.util
import tempfile
from pathlib import Path


REPO_PATH = Path(
    "data/external/banking_digital_twin/"
    "BankingDigitalTwin/generate.py"
)

OUTPUT_PATH = Path(
    "data/external/banking_digital_twin/"
    "base_individuals.csv"
)


DEFAULT_CUSTOMERS = 900_000
DEFAULT_EMPLOYERS = 10_000


def load_generator():
    """Load Banking Digital Twin's generate.py as a module."""

    if not REPO_PATH.exists():
        raise FileNotFoundError(
            f"Banking Digital Twin generator not found:\n"
            f"{REPO_PATH}\n\n"
            "Clone the repository first."
        )

    spec = importlib.util.spec_from_file_location(
        "banking_digital_twin_generate",
        REPO_PATH,
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Unable to load {REPO_PATH}"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(module)

    return module


def build_current_address_index(
    address_file: Path,
) -> dict[str, dict]:
    """
    Read customer_address.csv and retain the current
    address for each customer.
    """

    current_addresses = {}

    with address_file.open(
        newline="",
        encoding="utf-8",
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            if row["is_current"] == "TRUE":

                current_addresses[
                    row["customer_id"]
                ] = row

    return current_addresses


def build_base_population(
    customer_count: int,
    employer_count: int,
) -> int:

    bdt = load_generator()

    # Override the generator configuration before invoking
    # the specific functions we need.
    bdt.NUM_CUSTOMERS = customer_count
    bdt.NUM_EMPLOYERS = employer_count

    with tempfile.TemporaryDirectory() as scratch:

        bdt.OUTPUT_DIR = scratch

        print(
            f"Generating {customer_count:,} customers..."
        )

        employers = (
            bdt.generate_employers()
        )

        bdt.generate_customers(
            employers
        )

        scratch_path = Path(scratch)

        customer_file = (
            scratch_path
            / "customer.csv"
        )

        address_file = (
            scratch_path
            / "customer_address.csv"
        )

        if not customer_file.exists():
            raise FileNotFoundError(
                "Banking Digital Twin did not "
                "produce customer.csv"
            )

        if not address_file.exists():
            raise FileNotFoundError(
                "Banking Digital Twin did not "
                "produce customer_address.csv"
            )

        print(
            "Building current-address index..."
        )

        addresses = (
            build_current_address_index(
                address_file
            )
        )

        OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with (
            customer_file.open(
                newline="",
                encoding="utf-8",
            ) as input_file,
            OUTPUT_PATH.open(
                "w",
                newline="",
                encoding="utf-8",
            ) as output_file,
        ):

            reader = csv.DictReader(
                input_file
            )

            fieldnames = [
                "bdt_customer_id",
                "first_name",
                "last_name",
                "dob",
                "phone",
                "email",
                "address_line",
                "city",
                "region",
                "postcode",
            ]

            writer = csv.DictWriter(
                output_file,
                fieldnames=fieldnames,
            )

            writer.writeheader()

            count = 0

            for row in reader:

                customer_id = row[
                    "customer_id"
                ]

                address = addresses.get(
                    customer_id,
                    {},
                )

                writer.writerow(
                    {
                        "bdt_customer_id":
                            customer_id,

                        "first_name":
                            row["first_name"],

                        "last_name":
                            row["last_name"],

                        "dob":
                            row["date_of_birth"],

                        "phone":
                            row["phone"],

                        "email":
                            row["email"],

                        "address_line":
                            address.get(
                                "line_1",
                                "",
                            ),

                        "city":
                            address.get(
                                "city",
                                "",
                            ),

                        "region":
                            address.get(
                                "region",
                                row.get(
                                    "region",
                                    "",
                                ),
                            ),

                        "postcode":
                            address.get(
                                "postcode",
                                row.get(
                                    "postcode",
                                    "",
                                ),
                            ),
                    }
                )

                count += 1

                if count % 100_000 == 0:
                    print(
                        f"  Extracted "
                        f"{count:,} customers..."
                    )

    print(
        f"\nSaved {count:,} individuals to:"
    )

    print(
        OUTPUT_PATH
    )

    return count


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--customers",
        type=int,
        default=DEFAULT_CUSTOMERS,
        help="Number of customers to generate.",
    )

    parser.add_argument(
        "--employers",
        type=int,
        default=DEFAULT_EMPLOYERS,
        help="Number of employers for the generator.",
    )

    return parser.parse_args()


def main():

    args = parse_args()

    build_base_population(
        customer_count=args.customers,
        employer_count=args.employers,
    )


if __name__ == "__main__":
    main()