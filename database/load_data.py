import sys
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

SRC_DIRECTORY = PROJECT_ROOT / "src"

if str(SRC_DIRECTORY) not in sys.path:
    sys.path.insert(
        0,
        str(SRC_DIRECTORY)
    )


from loader import load_csv, load_json
from merger import build_unified_customer_profiles
from postgres_loader import (
    execute_schema,
    load_customers_to_postgres,
    run_basic_queries,
    test_database_connection,
    verify_schema_objects
)


DATA_DIRECTORY = (
    PROJECT_ROOT / "data"
)

SCHEMA_PATH = (
    PROJECT_ROOT
    / "database"
    / "schema.sql"
)


def main() -> None:
    """
    Build the canonical customer profiles, create the
    PostgreSQL schema, load the data, verify database
    objects, and run basic SQL queries.
    """

    try:
        test_database_connection()

        print("\nLoading source datasets...")

        crm_records = load_csv(
            DATA_DIRECTORY / "crm.csv"
        )

        sales_records = load_csv(
            DATA_DIRECTORY / "sales.csv"
        )

        finance_records = load_json(
            DATA_DIRECTORY / "finance.json"
        )

        support_records = load_csv(
            DATA_DIRECTORY / "support.csv"
        )

        print(
            f"CRM records:     "
            f"{len(crm_records)}"
        )

        print(
            f"Sales records:   "
            f"{len(sales_records)}"
        )

        print(
            f"Finance records: "
            f"{len(finance_records)}"
        )

        print(
            f"Support records: "
            f"{len(support_records)}"
        )

        unified_result = (
            build_unified_customer_profiles(
                crm_records,
                sales_records,
                finance_records,
                support_records
            )
        )

        customers = unified_result[
            "customers"
        ]

        print(
            f"\nCanonical customer profiles: "
            f"{len(customers)}"
        )

        execute_schema(
            SCHEMA_PATH
        )

        load_customers_to_postgres(
            customers
        )

        verify_schema_objects()

        run_basic_queries()

        print(f"\n{'=' * 60}")
        print(
            "Day 11 PostgreSQL schema improvements "
            "completed successfully."
        )
        print(f"{'=' * 60}")

    except Exception as error:
        print(
            f"\nDay 11 database workflow failed: "
            f"{error}"
        )

        raise


if __name__ == "__main__":
    main()