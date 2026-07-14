from pathlib import Path

from loader import load_csv, load_json
from merger import build_unified_customer_profiles
from validator import (
    validate_crm,
    validate_finance,
    validate_sales,
    validate_support
)


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

DATA_DIRECTORY = PROJECT_ROOT / "data"


def load_project_datasets() -> tuple[
    list[dict],
    list[dict],
    list[dict],
    list[dict]
]:
    """
    Load the actual Day 10 project datasets.
    """

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

    return (
        crm_records,
        sales_records,
        finance_records,
        support_records
    )


def index_customers_by_id(
    customers: list[dict]
) -> dict[str, dict]:
    """
    Index unified customers by customer_id.
    """

    return {
        customer["customer_id"]: customer
        for customer in customers
    }


def test_stale_crm_record_does_not_override_newer_record() -> None:
    """
    Confirm the newest CRM record supplies the final
    contact information.
    """

    (
        crm_records,
        sales_records,
        finance_records,
        support_records
    ) = load_project_datasets()

    result = build_unified_customer_profiles(
        crm_records,
        sales_records,
        finance_records,
        support_records
    )

    customers = index_customers_by_id(
        result["customers"]
    )

    linda = customers["C018"]

    assert linda["email"] == "linda.chen@email.com"

    assert (
        linda["address"]
        == "99 New Harbor Rd, Irvine, CA"
    )


def test_newest_finance_snapshot_wins() -> None:
    """
    Confirm the current Finance record replaces a stale
    financial snapshot.
    """

    (
        crm_records,
        sales_records,
        finance_records,
        support_records
    ) = load_project_datasets()

    result = build_unified_customer_profiles(
        crm_records,
        sales_records,
        finance_records,
        support_records
    )

    customers = index_customers_by_id(
        result["customers"]
    )

    linda = customers["C018"]

    assert linda["credit_score"] == 735
    assert linda["monthly_income"] == 7600
    assert linda["debt"] == 12000
    assert linda["risk_status"] == "low"


def test_newest_support_record_wins() -> None:
    """
    Confirm the most recent Support record supplies the
    final ticket status.
    """

    (
        crm_records,
        sales_records,
        finance_records,
        support_records
    ) = load_project_datasets()

    result = build_unified_customer_profiles(
        crm_records,
        sales_records,
        finance_records,
        support_records
    )

    customers = index_customers_by_id(
        result["customers"]
    )

    linda = customers["C018"]

    assert linda["last_ticket"] == "T1017"
    assert linda["ticket_status"] == "open"
    assert linda["support_priority"] == "high"


def test_typo_email_can_use_controlled_name_fallback() -> None:
    """
    Confirm Support can enrich a CRM customer when the
    CRM email contains a typo but the customer name
    matches the Support email username.
    """

    (
        crm_records,
        sales_records,
        finance_records,
        support_records
    ) = load_project_datasets()

    result = build_unified_customer_profiles(
        crm_records,
        sales_records,
        finance_records,
        support_records
    )

    customers = index_customers_by_id(
        result["customers"]
    )

    marcus = customers["C019"]

    assert (
        marcus["email"]
        == "marcus.reedemail.com"
    )

    assert marcus["has_support_record"] is True
    assert marcus["last_ticket"] == "T1018"
    assert marcus["ticket_status"] == "pending"

    assert marcus["has_finance_record"] is False
    assert marcus["monthly_income"] is None


def test_stale_sales_record_is_aggregated_but_newest_date_wins() -> None:
    """
    Confirm duplicate Sales records are aggregated while
    the newest purchase date is retained.
    """

    (
        crm_records,
        sales_records,
        finance_records,
        support_records
    ) = load_project_datasets()

    result = build_unified_customer_profiles(
        crm_records,
        sales_records,
        finance_records,
        support_records
    )

    customers = index_customers_by_id(
        result["customers"]
    )

    olivia = customers["C020"]

    assert olivia["total_orders"] == 10
    assert olivia["lifetime_value"] == 2750.00
    assert olivia["last_purchase"] == "2026-06-15"

    assert (
        olivia["address"]
        == "700 New Coast Hwy, Laguna Beach, CA"
    )


def test_missing_customer_ids_are_not_promoted() -> None:
    """
    Confirm CRM rows without customer IDs do not become
    canonical customer profiles.
    """

    (
        crm_records,
        sales_records,
        finance_records,
        support_records
    ) = load_project_datasets()

    result = build_unified_customer_profiles(
        crm_records,
        sales_records,
        finance_records,
        support_records
    )

    customer_names = {
        customer["name"]
        for customer in result["customers"]
    }

    assert "Kevin Lee" not in customer_names
    assert "No Identifier" not in customer_names

    missing_id_decisions = [
        decision
        for decision in result[
            "crm_resolution_decisions"
        ]
        if decision.get("reason")
        == "CRM record is missing customer_id"
    ]

    assert len(missing_id_decisions) == 2


def test_messy_data_generates_validation_failures() -> None:
    """
    Confirm the deliberately messy datasets produce
    validation errors rather than silently passing.
    """

    (
        crm_records,
        sales_records,
        finance_records,
        support_records
    ) = load_project_datasets()

    reports = [
        validate_crm(crm_records),
        validate_sales(sales_records),
        validate_finance(finance_records),
        validate_support(support_records)
    ]

    total_errors = sum(
        report["total_errors"]
        for report in reports
    )

    assert total_errors > 0

    crm_issues = {
        error["issue"]
        for error in reports[0]["errors"]
    }

    assert "Invalid email format" in crm_issues
    assert "Missing required value" in crm_issues