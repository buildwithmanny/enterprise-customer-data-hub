from datetime import datetime
from typing import Any


SOURCE_PRIORITIES = {
    "name": ["crm"],
    "email": ["crm", "support"],
    "phone": ["crm"],
    "address": ["crm"],
    "status": ["crm"],
    "monthly_income": ["finance"],
    "credit_score": ["finance"],
    "debt": ["finance"],
    "risk_status": ["finance"],
    "total_orders": ["sales"],
    "lifetime_value": ["sales"],
    "last_purchase": ["sales"],
    "last_ticket": ["support"],
    "ticket_status": ["support"],
    "customer_sentiment": ["support"],
    "support_priority": ["support"]
}


def normalize_text(value: Any) -> str:
    """
    Normalize text for comparison and empty-value checks.
    """

    if value is None:
        return ""

    return str(value).strip()


def is_missing(value: Any) -> bool:
    """
    Return True when a value is None or blank.
    """

    return (
        value is None
        or (
            isinstance(value, str)
            and value.strip() == ""
        )
    )


def parse_date(value: Any) -> datetime | None:
    """
    Parse supported date formats.

    Invalid or missing dates return None.
    """

    if is_missing(value):
        return None

    supported_formats = [
        "%Y-%m-%d",
        "%m/%d/%Y"
    ]

    for date_format in supported_formats:
        try:
            return datetime.strptime(
                str(value).strip(),
                date_format
            )
        except ValueError:
            continue

    return None


def choose_newest_record(
    records: list[dict[str, Any]],
    date_field: str = "last_updated"
) -> dict[str, Any] | None:
    """
    Select the record with the newest valid date.

    When no valid dates exist, select the final record
    so the process remains deterministic.
    """

    if not records:
        return None

    dated_records = []

    for record in records:
        parsed_date = parse_date(
            record.get(date_field)
        )

        if parsed_date is not None:
            dated_records.append(
                (
                    parsed_date,
                    record
                )
            )

    if dated_records:
        dated_records.sort(
            key=lambda item: item[0],
            reverse=True
        )

        return dated_records[0][1]

    return records[-1]


def resolve_crm_duplicate_group(
    records: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Resolve multiple CRM records representing the same
    customer.

    Rules:
    - Use CRM as the authoritative source.
    - Prefer the newest CRM record.
    - Fill missing values from older CRM records.
    - Preserve the newest address.
    """

    newest_record = choose_newest_record(
        records,
        "last_updated"
    )

    if newest_record is None:
        return {}

    resolved_record = newest_record.copy()

    fields_to_preserve = [
        "customer_id",
        "name",
        "email",
        "phone",
        "address",
        "status"
    ]

    for field in fields_to_preserve:
        if is_missing(resolved_record.get(field)):
            for record in records:
                candidate_value = record.get(field)

                if not is_missing(candidate_value):
                    resolved_record[field] = (
                        candidate_value
                    )
                    break

    return resolved_record


def resolve_crm_records(
    crm_records: list[dict[str, Any]]
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]]
]:
    """
    Resolve CRM duplicates by customer ID.

    Records without a customer ID are retained separately
    and flagged for manual review.
    """

    grouped_records: dict[
        str,
        list[dict[str, Any]]
    ] = {}

    records_missing_id = []

    for position, record in enumerate(
        crm_records,
        start=1
    ):
        customer_id = normalize_text(
            record.get("customer_id")
        ).lower()

        if not customer_id:
            records_missing_id.append(
                {
                    "source_position": position,
                    "reason": (
                        "CRM record is missing customer_id"
                    ),
                    "record": record
                }
            )
            continue

        grouped_records.setdefault(
            customer_id,
            []
        ).append(record)

    resolved_records = []
    duplicate_decisions = []

    for customer_id, records in grouped_records.items():
        resolved_record = (
            resolve_crm_duplicate_group(records)
        )

        resolved_records.append(
            resolved_record
        )

        if len(records) > 1:
            duplicate_decisions.append(
                {
                    "customer_id": customer_id,
                    "records_reviewed": len(records),
                    "rule_applied": (
                        "Prefer newest CRM record and "
                        "fill missing values from older "
                        "CRM records"
                    ),
                    "selected_last_updated": (
                        resolved_record.get(
                            "last_updated"
                        )
                    ),
                    "selected_address": (
                        resolved_record.get(
                            "address"
                        )
                    )
                }
            )

    decision_log = (
        duplicate_decisions
        + records_missing_id
    )

    return resolved_records, decision_log


def choose_preferred_value(
    field_name: str,
    source_records: dict[
        str,
        dict[str, Any] | None
    ]
) -> tuple[Any, str | None]:
    """
    Select a value based on the source-priority rules.

    Returns:
    - selected value
    - source that supplied the value
    """

    source_priority = SOURCE_PRIORITIES.get(
        field_name,
        []
    )

    for source_name in source_priority:
        source_record = source_records.get(
            source_name
        )

        if source_record is None:
            continue

        value = source_record.get(field_name)

        if not is_missing(value):
            return value, source_name

    return None, None


def resolve_customer_attributes(
    crm_record: dict[str, Any] | None,
    sales_record: dict[str, Any] | None,
    finance_record: dict[str, Any] | None,
    support_record: dict[str, Any] | None
) -> tuple[
    dict[str, Any],
    dict[str, str | None]
]:
    """
    Resolve customer fields across source systems.

    Core rules:
    - Prefer CRM name.
    - Prefer Finance income and credit information.
    - Prefer Sales transactional metrics.
    - Prefer Support service information.
    - Prefer the newest CRM address after CRM duplicates
      have already been resolved.
    """

    source_records = {
        "crm": crm_record,
        "sales": sales_record,
        "finance": finance_record,
        "support": support_record
    }

    fields_to_resolve = [
        "name",
        "email",
        "phone",
        "address",
        "status",
        "monthly_income",
        "credit_score",
        "debt",
        "risk_status",
        "total_orders",
        "lifetime_value",
        "last_purchase",
        "last_ticket",
        "ticket_status",
        "customer_sentiment",
        "support_priority"
    ]

    resolved_customer = {}
    field_lineage = {}

    for field_name in fields_to_resolve:
        value, source_name = choose_preferred_value(
            field_name,
            source_records
        )

        resolved_customer[field_name] = value
        field_lineage[field_name] = source_name

    customer_id = None

    if crm_record is not None:
        customer_id = crm_record.get(
            "customer_id"
        )

    elif sales_record is not None:
        customer_id = sales_record.get(
            "customer_number"
        )

    elif finance_record is not None:
        customer_id = finance_record.get(
            "user_id"
        )

    resolved_customer["customer_id"] = customer_id
    field_lineage["customer_id"] = (
        "crm"
        if crm_record is not None
        else (
            "sales"
            if sales_record is not None
            else (
                "finance"
                if finance_record is not None
                else None
            )
        )
    )

    return resolved_customer, field_lineage


def describe_business_rules() -> list[dict[str, str]]:
    """
    Return the project business rules in a
    stakeholder-readable format.
    """

    return [
        {
            "rule": "Customer name authority",
            "decision": (
                "Use CRM name when available."
            ),
            "reason": (
                "CRM is treated as the primary system "
                "of customer identity."
            )
        },
        {
            "rule": "Financial information authority",
            "decision": (
                "Use Finance for monthly income, debt, "
                "credit score, and risk status."
            ),
            "reason": (
                "Finance owns the financial profile."
            )
        },
        {
            "rule": "Customer address",
            "decision": (
                "Use the address from the newest valid "
                "CRM record."
            ),
            "reason": (
                "CRM owns contact information, and the "
                "newest timestamp is treated as the most "
                "current version."
            )
        },
        {
            "rule": "Duplicate CRM records",
            "decision": (
                "Collapse records sharing the same "
                "customer_id into one canonical record."
            ),
            "reason": (
                "A customer ID should represent one "
                "trusted customer."
            )
        },
        {
            "rule": "Missing CRM customer ID",
            "decision": (
                "Do not automatically merge the record."
            ),
            "reason": (
                "The record lacks a sufficiently reliable "
                "primary identifier and requires review."
            )
        },
        {
            "rule": "Ambiguous matches",
            "decision": (
                "Do not silently choose among multiple "
                "candidate records."
            ),
            "reason": (
                "Ambiguity should be visible rather than "
                "converted into a potentially incorrect "
                "customer profile."
            )
        },
        {
            "rule": "Missing source record",
            "decision": (
                "Retain the customer and leave fields from "
                "the missing source as null."
            ),
            "reason": (
                "Absence of one department's data should "
                "not delete a valid customer from another "
                "system."
            )
        }
    ]