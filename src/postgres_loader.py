import os
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv
from psycopg import Connection


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)


VALID_CUSTOMER_STATUSES = {
    "active",
    "inactive"
}

VALID_RISK_STATUSES = {
    "low",
    "medium",
    "high",
    "unknown"
}

VALID_TICKET_STATUSES = {
    "open",
    "pending",
    "resolved",
    "closed"
}

VALID_SENTIMENTS = {
    "positive",
    "neutral",
    "negative"
}

VALID_SUPPORT_PRIORITIES = {
    "low",
    "medium",
    "high"
}


def get_database_config() -> dict[str, Any]:
    """
    Read PostgreSQL connection settings from .env.
    """

    required_variables = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD"
    ]

    missing_variables = [
        variable
        for variable in required_variables
        if not os.getenv(variable)
    ]

    if missing_variables:
        missing_text = ", ".join(
            missing_variables
        )

        raise ValueError(
            "Missing required database environment "
            f"variables: {missing_text}"
        )

    return {
        "host": os.environ["DB_HOST"],
        "port": int(
            os.environ["DB_PORT"]
        ),
        "dbname": os.environ["DB_NAME"],
        "user": os.environ["DB_USER"],
        "password": os.environ["DB_PASSWORD"]
    }


def get_database_connection() -> Connection:
    """
    Open and return a PostgreSQL connection.
    """

    config = get_database_config()

    return psycopg.connect(
        **config
    )


def test_database_connection() -> None:
    """
    Verify Python can connect to PostgreSQL.
    """

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    current_database(),
                    current_user,
                    version();
                """
            )

            result = cursor.fetchone()

    if result is None:
        raise RuntimeError(
            "PostgreSQL returned no connection "
            "information."
        )

    database_name, database_user, version = (
        result
    )

    print("\nPostgreSQL connection successful.")
    print(f"Database: {database_name}")
    print(f"User:     {database_user}")
    print(f"Version:  {version}")


def execute_schema(
    schema_path: Path
) -> None:
    """
    Execute the complete PostgreSQL schema file.
    """

    if not schema_path.exists():
        raise FileNotFoundError(
            f"Schema file not found: {schema_path}"
        )

    schema_sql = schema_path.read_text(
        encoding="utf-8"
    )

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                schema_sql
            )

        connection.commit()

    print(
        f"\nDatabase schema created from: "
        f"{schema_path}"
    )


def to_decimal(
    value: Any
) -> Decimal | None:
    """
    Convert a value into Decimal.

    Missing or invalid values become None.
    """

    if value is None or value == "":
        return None

    try:
        return Decimal(
            str(value)
        )

    except (
        InvalidOperation,
        TypeError,
        ValueError
    ):
        return None


def to_integer(
    value: Any
) -> int | None:
    """
    Convert a value into an integer.
    """

    if value is None or value == "":
        return None

    try:
        return int(value)

    except (
        TypeError,
        ValueError
    ):
        return None


def normalize_allowed_value(
    value: Any,
    allowed_values: set[str]
) -> str | None:
    """
    Normalize a string and retain it only when it is
    permitted by the database business rules.
    """

    if value is None:
        return None

    normalized_value = str(
        value
    ).strip().lower()

    if normalized_value in allowed_values:
        return normalized_value

    return None


def insert_customers(
    connection: Connection,
    customers: list[dict[str, Any]]
) -> int:
    """
    Insert canonical customers and their related
    departmental records.

    Returns the number of customer rows processed.
    """

    customer_sql = """
        INSERT INTO customers (
            customer_id,
            name,
            email,
            phone,
            address,
            customer_status,
            has_sales_record,
            has_finance_record,
            has_support_record,
            updated_at
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (customer_id)
        DO UPDATE SET
            name = EXCLUDED.name,
            email = EXCLUDED.email,
            phone = EXCLUDED.phone,
            address = EXCLUDED.address,
            customer_status =
                EXCLUDED.customer_status,
            has_sales_record =
                EXCLUDED.has_sales_record,
            has_finance_record =
                EXCLUDED.has_finance_record,
            has_support_record =
                EXCLUDED.has_support_record,
            updated_at =
                CURRENT_TIMESTAMP;
    """

    sales_sql = """
        INSERT INTO customer_sales (
            customer_id,
            total_orders,
            lifetime_value,
            last_purchase,
            updated_at
        )
        VALUES (
            %s, %s, %s, %s,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (customer_id)
        DO UPDATE SET
            total_orders =
                EXCLUDED.total_orders,
            lifetime_value =
                EXCLUDED.lifetime_value,
            last_purchase =
                EXCLUDED.last_purchase,
            updated_at =
                CURRENT_TIMESTAMP;
    """

    finance_sql = """
        INSERT INTO customer_finance (
            customer_id,
            monthly_income,
            credit_score,
            debt,
            risk_status,
            updated_at
        )
        VALUES (
            %s, %s, %s, %s, %s,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (customer_id)
        DO UPDATE SET
            monthly_income =
                EXCLUDED.monthly_income,
            credit_score =
                EXCLUDED.credit_score,
            debt =
                EXCLUDED.debt,
            risk_status =
                EXCLUDED.risk_status,
            updated_at =
                CURRENT_TIMESTAMP;
    """

    support_sql = """
        INSERT INTO customer_support (
            customer_id,
            last_ticket,
            ticket_status,
            customer_sentiment,
            support_priority,
            updated_at
        )
        VALUES (
            %s, %s, %s, %s, %s,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (customer_id)
        DO UPDATE SET
            last_ticket =
                EXCLUDED.last_ticket,
            ticket_status =
                EXCLUDED.ticket_status,
            customer_sentiment =
                EXCLUDED.customer_sentiment,
            support_priority =
                EXCLUDED.support_priority,
            updated_at =
                CURRENT_TIMESTAMP;
    """

    processed_customers = 0

    with connection.cursor() as cursor:
        for customer in customers:
            customer_id = customer.get(
                "customer_id"
            )

            name = customer.get(
                "name"
            )

            customer_status = (
                normalize_allowed_value(
                    customer.get("status"),
                    VALID_CUSTOMER_STATUSES
                )
            )

            if (
                not customer_id
                or not name
                or customer_status is None
            ):
                print(
                    "Skipping customer with missing or "
                    "invalid identity information: "
                    f"{customer}"
                )

                continue

            cursor.execute(
                customer_sql,
                (
                    customer_id,
                    name,
                    customer.get("email"),
                    customer.get("phone"),
                    customer.get("address"),
                    customer_status,
                    customer.get(
                        "has_sales_record",
                        False
                    ),
                    customer.get(
                        "has_finance_record",
                        False
                    ),
                    customer.get(
                        "has_support_record",
                        False
                    )
                )
            )

            processed_customers += 1

            if customer.get(
                "has_sales_record"
            ):
                total_orders = to_integer(
                    customer.get(
                        "total_orders"
                    )
                )

                lifetime_value = to_decimal(
                    customer.get(
                        "lifetime_value"
                    )
                )

                if (
                    total_orders is not None
                    and total_orders < 0
                ):
                    total_orders = None

                if (
                    lifetime_value is not None
                    and lifetime_value < 0
                ):
                    lifetime_value = None

                cursor.execute(
                    sales_sql,
                    (
                        customer_id,
                        total_orders,
                        lifetime_value,
                        customer.get(
                            "last_purchase"
                        )
                    )
                )

            if customer.get(
                "has_finance_record"
            ):
                credit_score = to_integer(
                    customer.get(
                        "credit_score"
                    )
                )

                monthly_income = to_decimal(
                    customer.get(
                        "monthly_income"
                    )
                )

                debt = to_decimal(
                    customer.get(
                        "debt"
                    )
                )

                risk_status = (
                    normalize_allowed_value(
                        customer.get(
                            "risk_status"
                        ),
                        VALID_RISK_STATUSES
                    )
                )

                if (
                    credit_score is not None
                    and not 300 <= credit_score <= 850
                ):
                    credit_score = None

                if (
                    monthly_income is not None
                    and monthly_income < 0
                ):
                    monthly_income = None

                if (
                    debt is not None
                    and debt < 0
                ):
                    debt = None

                cursor.execute(
                    finance_sql,
                    (
                        customer_id,
                        monthly_income,
                        credit_score,
                        debt,
                        risk_status
                    )
                )

            if customer.get(
                "has_support_record"
            ):
                ticket_status = (
                    normalize_allowed_value(
                        customer.get(
                            "ticket_status"
                        ),
                        VALID_TICKET_STATUSES
                    )
                )

                sentiment = (
                    normalize_allowed_value(
                        customer.get(
                            "customer_sentiment"
                        ),
                        VALID_SENTIMENTS
                    )
                )

                support_priority = (
                    normalize_allowed_value(
                        customer.get(
                            "support_priority"
                        ),
                        VALID_SUPPORT_PRIORITIES
                    )
                )

                cursor.execute(
                    support_sql,
                    (
                        customer_id,
                        customer.get(
                            "last_ticket"
                        ),
                        ticket_status,
                        sentiment,
                        support_priority
                    )
                )

    return processed_customers


def load_customers_to_postgres(
    customers: list[dict[str, Any]]
) -> None:
    """
    Load canonical profiles into PostgreSQL as one
    transaction.
    """

    with get_database_connection() as connection:
        try:
            processed_customers = insert_customers(
                connection,
                customers
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

    print(
        f"\nLoaded {processed_customers} unified "
        "customer profiles into PostgreSQL."
    )


def verify_schema_objects() -> None:
    """
    Display tables, relationships, constraints, indexes,
    and views created by the Day 11 schema.
    """

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
                """
            )

            tables = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    tc.table_name,
                    tc.constraint_name,
                    tc.constraint_type
                FROM information_schema.table_constraints
                    AS tc
                WHERE tc.table_schema = 'public'
                ORDER BY
                    tc.table_name,
                    tc.constraint_type,
                    tc.constraint_name;
                """
            )

            constraints = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    tablename,
                    indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY
                    tablename,
                    indexname;
                """
            )

            indexes = cursor.fetchall()

            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.views
                WHERE table_schema = 'public'
                ORDER BY table_name;
                """
            )

            views = cursor.fetchall()

    print(f"\n{'=' * 60}")
    print("DAY 11 SCHEMA VERIFICATION")
    print(f"{'=' * 60}")

    print("\nTables:")

    for table in tables:
        print(f"- {table[0]}")

    print("\nConstraints:")

    for constraint in constraints:
        print(
            f"- Table: {constraint[0]} | "
            f"Name: {constraint[1]} | "
            f"Type: {constraint[2]}"
        )

    print("\nIndexes:")

    for index in indexes:
        print(
            f"- Table: {index[0]} | "
            f"Index: {index[1]}"
        )

    print("\nViews:")

    for view in views:
        print(f"- {view[0]}")


def run_basic_queries() -> None:
    """
    Run and display basic SQL queries.
    """

    queries = {
        "Customer count": """
            SELECT COUNT(*)
            FROM customers;
        """,

        "Customers with complete source coverage": """
            SELECT
                customer_id,
                name
            FROM customers
            WHERE
                has_sales_record = TRUE
                AND has_finance_record = TRUE
                AND has_support_record = TRUE
            ORDER BY customer_id;
        """,

        "Highest lifetime value customers": """
            SELECT
                customer_id,
                name,
                lifetime_value
            FROM customer_360
            WHERE lifetime_value IS NOT NULL
            ORDER BY lifetime_value DESC
            LIMIT 5;
        """,

        "Highest financial risk customers": """
            SELECT
                customer_id,
                name,
                credit_score,
                debt,
                risk_status
            FROM customer_360
            WHERE risk_status = 'high'
            ORDER BY debt DESC NULLS LAST;
        """,

        "Open support tickets": """
            SELECT
                customer_id,
                name,
                last_ticket,
                support_priority
            FROM customer_360
            WHERE ticket_status IN (
                'open',
                'pending'
            )
            ORDER BY
                support_priority,
                customer_id;
        """,

        "Customer 360 sample": """
            SELECT
                customer_id,
                name,
                credit_score,
                lifetime_value,
                ticket_status
            FROM customer_360
            ORDER BY customer_id
            LIMIT 10;
        """
    }

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            for query_name, query in queries.items():
                cursor.execute(
                    query
                )

                rows = cursor.fetchall()

                print(f"\n{'-' * 60}")
                print(query_name)
                print(f"{'-' * 60}")

                if not rows:
                    print(
                        "No rows returned."
                    )
                    continue

                for row in rows:
                    print(row)