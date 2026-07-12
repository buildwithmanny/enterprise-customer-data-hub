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
        "port": int(os.environ["DB_PORT"]),
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
    Verify that Python can connect to PostgreSQL.
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
            "Database connection succeeded, but "
            "PostgreSQL returned no connection details."
        )

    database_name, database_user, version = result

    print("\nPostgreSQL connection successful.")
    print(f"Database: {database_name}")
    print(f"User:     {database_user}")
    print(f"Version:  {version}")


def execute_schema(
    schema_path: Path
) -> None:
    """
    Execute the SQL schema file.
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
            cursor.execute(schema_sql)

        connection.commit()

    print(
        f"\nDatabase schema created from: "
        f"{schema_path}"
    )


def to_decimal(
    value: Any
) -> Decimal | None:
    """
    Convert a value into Decimal for PostgreSQL NUMERIC
    fields. Missing or invalid values become None.
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


def insert_customers(
    connection: Connection,
    customers: list[dict[str, Any]]
) -> None:
    """
    Insert canonical customer profiles and their
    department-specific data.
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
            has_support_record
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
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
                EXCLUDED.has_support_record;
    """

    sales_sql = """
        INSERT INTO customer_sales (
            customer_id,
            total_orders,
            lifetime_value,
            last_purchase
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (customer_id)
        DO UPDATE SET
            total_orders =
                EXCLUDED.total_orders,
            lifetime_value =
                EXCLUDED.lifetime_value,
            last_purchase =
                EXCLUDED.last_purchase;
    """

    finance_sql = """
        INSERT INTO customer_finance (
            customer_id,
            monthly_income,
            credit_score,
            debt,
            risk_status
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (customer_id)
        DO UPDATE SET
            monthly_income =
                EXCLUDED.monthly_income,
            credit_score =
                EXCLUDED.credit_score,
            debt =
                EXCLUDED.debt,
            risk_status =
                EXCLUDED.risk_status;
    """

    support_sql = """
        INSERT INTO customer_support (
            customer_id,
            last_ticket,
            ticket_status,
            customer_sentiment,
            support_priority
        )
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (customer_id)
        DO UPDATE SET
            last_ticket =
                EXCLUDED.last_ticket,
            ticket_status =
                EXCLUDED.ticket_status,
            customer_sentiment =
                EXCLUDED.customer_sentiment,
            support_priority =
                EXCLUDED.support_priority;
    """

    with connection.cursor() as cursor:
        for customer in customers:
            customer_id = customer.get(
                "customer_id"
            )

            name = customer.get("name")

            if not customer_id or not name:
                print(
                    "Skipping customer with missing "
                    f"customer_id or name: {customer}"
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
                    customer.get("status"),
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

            if customer.get(
                "has_sales_record"
            ):
                cursor.execute(
                    sales_sql,
                    (
                        customer_id,
                        to_integer(
                            customer.get(
                                "total_orders"
                            )
                        ),
                        to_decimal(
                            customer.get(
                                "lifetime_value"
                            )
                        ),
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
                    customer.get("debt")
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
                        customer.get(
                            "risk_status"
                        )
                    )
                )

            if customer.get(
                "has_support_record"
            ):
                cursor.execute(
                    support_sql,
                    (
                        customer_id,
                        customer.get(
                            "last_ticket"
                        ),
                        customer.get(
                            "ticket_status"
                        ),
                        customer.get(
                            "customer_sentiment"
                        ),
                        customer.get(
                            "support_priority"
                        )
                    )
                )


def load_customers_to_postgres(
    customers: list[dict[str, Any]]
) -> None:
    """
    Load all canonical profiles into PostgreSQL
    as one transaction.
    """

    with get_database_connection() as connection:
        try:
            insert_customers(
                connection,
                customers
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

    print(
        f"\nLoaded {len(customers)} unified "
        "customer profiles into PostgreSQL."
    )


def run_basic_queries() -> None:
    """
    Run and display basic Day 6 SQL queries.
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
                c.customer_id,
                c.name,
                s.lifetime_value
            FROM customers AS c
            INNER JOIN customer_sales AS s
                ON c.customer_id = s.customer_id
            ORDER BY s.lifetime_value DESC
            LIMIT 5;
        """,
        "Highest financial risk customers": """
            SELECT
                c.customer_id,
                c.name,
                f.credit_score,
                f.debt,
                f.risk_status
            FROM customers AS c
            INNER JOIN customer_finance AS f
                ON c.customer_id = f.customer_id
            WHERE f.risk_status = 'high'
            ORDER BY f.debt DESC NULLS LAST;
        """,
        "Open support tickets": """
            SELECT
                c.customer_id,
                c.name,
                s.last_ticket,
                s.support_priority
            FROM customers AS c
            INNER JOIN customer_support AS s
                ON c.customer_id = s.customer_id
            WHERE s.ticket_status IN (
                'open',
                'pending'
            )
            ORDER BY
                s.support_priority,
                c.customer_id;
        """
    }

    with get_database_connection() as connection:
        with connection.cursor() as cursor:
            for query_name, query in queries.items():
                cursor.execute(query)

                rows = cursor.fetchall()

                print(f"\n{'-' * 60}")
                print(query_name)
                print(f"{'-' * 60}")

                if not rows:
                    print("No rows returned.")
                    continue

                for row in rows:
                    print(row)