import re
from datetime import datetime
from typing import Any


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

PHONE_PATTERN = re.compile(
    r"^\d{3}-\d{3}-\d{4}$"
)


def is_missing(value: Any) -> bool:
    """
    Return True when a value is None, an empty string,
    or a string containing only spaces.
    """

    return value is None or (
        isinstance(value, str) and value.strip() == ""
    )


def is_valid_iso_date(value: Any) -> bool:
    """
    Validate dates in YYYY-MM-DD format.
    """

    if not isinstance(value, str):
        return False

    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def is_valid_email(value: Any) -> bool:
    """
    Validate a basic email format.
    """

    if not isinstance(value, str):
        return False

    return EMAIL_PATTERN.fullmatch(value.strip()) is not None


def is_valid_phone(value: Any) -> bool:
    """
    Validate phone numbers formatted as ###-###-####.
    """

    if not isinstance(value, str):
        return False

    return PHONE_PATTERN.fullmatch(value.strip()) is not None


def add_error(
    errors: list[dict[str, Any]],
    row_number: int,
    record_id: str,
    field: str,
    issue: str,
    value: Any
) -> None:
    """
    Add one validation error to the error list.
    """

    errors.append(
        {
            "row": row_number,
            "record_id": record_id,
            "field": field,
            "issue": issue,
            "value": value
        }
    )


def build_validation_report(
    dataset_name: str,
    records: list[dict[str, Any]],
    errors: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Build a summary report for one dataset.
    """

    invalid_rows = {
        error["row"]
        for error in errors
    }

    return {
        "dataset": dataset_name,
        "total_records": len(records),
        "valid_records": len(records) - len(invalid_rows),
        "invalid_records": len(invalid_rows),
        "total_errors": len(errors),
        "errors": errors
    }


def validate_crm(
    records: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Validate CRM records independently.
    """

    required_fields = [
        "customer_id",
        "name",
        "email",
        "phone",
        "address",
        "status",
        "last_updated"
    ]

    valid_statuses = {"active", "inactive"}
    errors: list[dict[str, Any]] = []

    for row_number, record in enumerate(records, start=2):
        record_id = record.get("customer_id") or "missing"

        for field in required_fields:
            if is_missing(record.get(field)):
                add_error(
                    errors,
                    row_number,
                    record_id,
                    field,
                    "Missing required value",
                    record.get(field)
                )

        email = record.get("email")
        if not is_missing(email) and not is_valid_email(email):
            add_error(
                errors,
                row_number,
                record_id,
                "email",
                "Invalid email format",
                email
            )

        phone = record.get("phone")
        if not is_missing(phone) and not is_valid_phone(phone):
            add_error(
                errors,
                row_number,
                record_id,
                "phone",
                "Invalid phone format; expected ###-###-####",
                phone
            )

        status = record.get("status")
        if (
            not is_missing(status)
            and status not in valid_statuses
        ):
            add_error(
                errors,
                row_number,
                record_id,
                "status",
                "Invalid status",
                status
            )

        last_updated = record.get("last_updated")
        if (
            not is_missing(last_updated)
            and not is_valid_iso_date(last_updated)
        ):
            add_error(
                errors,
                row_number,
                record_id,
                "last_updated",
                "Invalid date format; expected YYYY-MM-DD",
                last_updated
            )

    return build_validation_report("crm", records, errors)


def validate_sales(
    records: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Validate sales records independently.
    """

    required_fields = [
        "customer_number",
        "total_orders",
        "lifetime_value",
        "last_purchase",
        "sales_region"
    ]

    errors: list[dict[str, Any]] = []

    for row_number, record in enumerate(records, start=2):
        record_id = record.get("customer_number") or "missing"

        for field in required_fields:
            if is_missing(record.get(field)):
                add_error(
                    errors,
                    row_number,
                    record_id,
                    field,
                    "Missing required value",
                    record.get(field)
                )

        total_orders = record.get("total_orders")
        if not is_missing(total_orders):
            try:
                parsed_orders = int(total_orders)

                if parsed_orders < 0:
                    raise ValueError

            except (TypeError, ValueError):
                add_error(
                    errors,
                    row_number,
                    record_id,
                    "total_orders",
                    "Must be a non-negative integer",
                    total_orders
                )

        lifetime_value = record.get("lifetime_value")
        if not is_missing(lifetime_value):
            try:
                parsed_value = float(lifetime_value)

                if parsed_value < 0:
                    raise ValueError

            except (TypeError, ValueError):
                add_error(
                    errors,
                    row_number,
                    record_id,
                    "lifetime_value",
                    "Must be a non-negative number",
                    lifetime_value
                )

        last_purchase = record.get("last_purchase")
        if (
            not is_missing(last_purchase)
            and not is_valid_iso_date(last_purchase)
        ):
            add_error(
                errors,
                row_number,
                record_id,
                "last_purchase",
                "Invalid date format; expected YYYY-MM-DD",
                last_purchase
            )

    return build_validation_report("sales", records, errors)


def validate_finance(
    records: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Validate finance records independently.
    """

    required_fields = [
        "user_id",
        "credit_score",
        "monthly_income",
        "debt",
        "risk_status",
        "last_updated"
    ]

    valid_risk_statuses = {
        "low",
        "medium",
        "high",
        "unknown"
    }

    errors: list[dict[str, Any]] = []

    for row_number, record in enumerate(records, start=1):
        record_id = record.get("user_id") or "missing"

        for field in required_fields:
            if is_missing(record.get(field)):
                add_error(
                    errors,
                    row_number,
                    record_id,
                    field,
                    "Missing required value",
                    record.get(field)
                )

        credit_score = record.get("credit_score")
        if not is_missing(credit_score):
            if (
                not isinstance(credit_score, int)
                or isinstance(credit_score, bool)
                or not 300 <= credit_score <= 850
            ):
                add_error(
                    errors,
                    row_number,
                    record_id,
                    "credit_score",
                    "Must be an integer between 300 and 850",
                    credit_score
                )

        monthly_income = record.get("monthly_income")
        if not is_missing(monthly_income):
            if (
                not isinstance(monthly_income, (int, float))
                or isinstance(monthly_income, bool)
                or monthly_income < 0
            ):
                add_error(
                    errors,
                    row_number,
                    record_id,
                    "monthly_income",
                    "Must be a non-negative number",
                    monthly_income
                )

        debt = record.get("debt")
        if not is_missing(debt):
            if (
                not isinstance(debt, (int, float))
                or isinstance(debt, bool)
                or debt < 0
            ):
                add_error(
                    errors,
                    row_number,
                    record_id,
                    "debt",
                    "Must be a non-negative number",
                    debt
                )

        risk_status = record.get("risk_status")
        if (
            not is_missing(risk_status)
            and risk_status not in valid_risk_statuses
        ):
            add_error(
                errors,
                row_number,
                record_id,
                "risk_status",
                "Invalid risk status",
                risk_status
            )

        last_updated = record.get("last_updated")
        if (
            not is_missing(last_updated)
            and not is_valid_iso_date(last_updated)
        ):
            add_error(
                errors,
                row_number,
                record_id,
                "last_updated",
                "Invalid date format; expected YYYY-MM-DD",
                last_updated
            )

    return build_validation_report("finance", records, errors)


def validate_support(
    records: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Validate support records independently.
    """

    required_fields = [
        "email",
        "last_ticket",
        "ticket_status",
        "customer_sentiment",
        "support_priority",
        "last_updated"
    ]

    valid_ticket_statuses = {
        "open",
        "pending",
        "resolved",
        "closed"
    }

    valid_sentiments = {
        "positive",
        "neutral",
        "negative"
    }

    valid_priorities = {
        "low",
        "medium",
        "high"
    }

    errors: list[dict[str, Any]] = []

    for row_number, record in enumerate(records, start=2):
        record_id = (
            record.get("email")
            or record.get("last_ticket")
            or "missing"
        )

        for field in required_fields:
            if is_missing(record.get(field)):
                add_error(
                    errors,
                    row_number,
                    record_id,
                    field,
                    "Missing required value",
                    record.get(field)
                )

        email = record.get("email")
        if not is_missing(email) and not is_valid_email(email):
            add_error(
                errors,
                row_number,
                record_id,
                "email",
                "Invalid email format",
                email
            )

        ticket_status = record.get("ticket_status")
        if (
            not is_missing(ticket_status)
            and ticket_status not in valid_ticket_statuses
        ):
            add_error(
                errors,
                row_number,
                record_id,
                "ticket_status",
                "Invalid ticket status",
                ticket_status
            )

        sentiment = record.get("customer_sentiment")
        if (
            not is_missing(sentiment)
            and sentiment not in valid_sentiments
        ):
            add_error(
                errors,
                row_number,
                record_id,
                "customer_sentiment",
                "Invalid customer sentiment",
                sentiment
            )

        priority = record.get("support_priority")
        if (
            not is_missing(priority)
            and priority not in valid_priorities
        ):
            add_error(
                errors,
                row_number,
                record_id,
                "support_priority",
                "Invalid support priority",
                priority
            )

        last_updated = record.get("last_updated")
        if (
            not is_missing(last_updated)
            and not is_valid_iso_date(last_updated)
        ):
            add_error(
                errors,
                row_number,
                record_id,
                "last_updated",
                "Invalid date format; expected YYYY-MM-DD",
                last_updated
            )

    return build_validation_report("support", records, errors)