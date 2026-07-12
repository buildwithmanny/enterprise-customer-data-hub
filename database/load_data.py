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
    test_database_connection
)


DATA_DIRECTORY = PROJECT_ROOT / "data"
SCHEMA_PATH = (
    PROJECT_ROOT
    / "database"
    / "schema.sql"
)


def main() -> None:
    """
    Build the canonical profiles and load them into
    PostgreSQL.
    """

    try:
        test_database_connection()

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

        execute_schema(
            SCHEMA_PATH
        )

        load_customers_to_postgres(
            customers
        )

        run_basic_queries()

        print(f"\n{'=' * 60}")
        print(
            "Day 6 PostgreSQL load completed "
            "successfully."
        )
        print(f"{'=' * 60}")

    except Exception as error:
        print(
            f"\nDay 6 database load failed: "
            f"{error}"
        )

        raise


if __name__ == "__main__":
    main()