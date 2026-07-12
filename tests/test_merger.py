from merger import (
    build_unified_customer_profiles,
    detect_source_duplicates
)


def test_duplicate_detection() -> None:
    """
    Confirm duplicate identifiers are detected
    independently within each source.
    """

    crm_records = [
        {
            "customer_id": "C001",
            "email": "john@example.com"
        },
        {
            "customer_id": "C001",
            "email": "john.updated@example.com"
        }
    ]

    sales_records = [
        {
            "customer_number": "C001"
        },
        {
            "customer_number": "C001"
        }
    ]

    finance_records = [
        {
            "user_id": "C001"
        }
    ]

    support_records = [
        {
            "email": "john@example.com"
        },
        {
            "email": "john@example.com"
        }
    ]

    duplicate_results = detect_source_duplicates(
        crm_records,
        sales_records,
        finance_records,
        support_records
    )

    crm_duplicate_fields = {
        duplicate["field"]
        for duplicate in duplicate_results["crm"]
    }

    assert "customer_id" in crm_duplicate_fields

    assert len(
        duplicate_results["sales"]
    ) == 1

    assert (
        duplicate_results["sales"][0]["value"]
        == "c001"
    )

    assert (
        duplicate_results["sales"][0]["occurrences"]
        == 2
    )

    assert len(
        duplicate_results["finance"]
    ) == 0

    assert len(
        duplicate_results["support"]
    ) == 1


def test_merge_logic_uses_business_rules() -> None:
    """
    Confirm the unified profile applies the documented
    source priorities and duplicate-resolution rules.
    """

    crm_records = [
        {
            "customer_id": "C001",
            "name": "John Smith",
            "email": "john.smith@email.com",
            "phone": "949-555-0101",
            "address": "123 Old Street",
            "status": "active",
            "last_updated": "2026-05-01"
        },
        {
            "customer_id": "C001",
            "name": "John Smith",
            "email": "john.smith@email.com",
            "phone": "949-555-0101",
            "address": "456 New Street",
            "status": "active",
            "last_updated": "2026-06-01"
        }
    ]

    sales_records = [
        {
            "customer_number": "C001",
            "total_orders": "2",
            "lifetime_value": "100.00",
            "last_purchase": "2026-05-01",
            "sales_region": "West"
        },
        {
            "customer_number": "C001",
            "total_orders": "3",
            "lifetime_value": "150.00",
            "last_purchase": "2026-06-01",
            "sales_region": "West"
        }
    ]

    finance_records = [
        {
            "user_id": "C001",
            "credit_score": 745,
            "monthly_income": 7200,
            "debt": 15000,
            "risk_status": "low",
            "last_updated": "2026-06-01"
        }
    ]

    support_records = [
        {
            "email": "john.smith@email.com",
            "last_ticket": "T1001",
            "ticket_status": "resolved",
            "customer_sentiment": "positive",
            "support_priority": "low",
            "last_updated": "2026-05-15"
        },
        {
            "email": "john.smith@email.com",
            "last_ticket": "T1002",
            "ticket_status": "open",
            "customer_sentiment": "neutral",
            "support_priority": "high",
            "last_updated": "2026-06-10"
        }
    ]

    result = build_unified_customer_profiles(
        crm_records,
        sales_records,
        finance_records,
        support_records
    )

    customers = result["customers"]

    assert len(customers) == 1

    customer = customers[0]

    # CRM is authoritative for identity.
    assert customer["customer_id"] == "C001"
    assert customer["name"] == "John Smith"

    # Newest CRM record supplies the address.
    assert customer["address"] == "456 New Street"

    # Finance supplies financial information.
    assert customer["monthly_income"] == 7200
    assert customer["credit_score"] == 745
    assert customer["debt"] == 15000

    # Duplicate Sales records are aggregated.
    assert customer["total_orders"] == 5
    assert customer["lifetime_value"] == 250.00
    assert customer["last_purchase"] == "2026-06-01"

    # Newest Support record wins.
    assert customer["last_ticket"] == "T1002"
    assert customer["ticket_status"] == "open"
    assert customer["support_priority"] == "high"

    assert customer["has_sales_record"] is True
    assert customer["has_finance_record"] is True
    assert customer["has_support_record"] is True


def test_customer_is_retained_when_sources_are_missing() -> None:
    """
    Confirm a valid CRM customer remains in the unified
    output when Sales, Finance, and Support data are absent.
    """

    crm_records = [
        {
            "customer_id": "C002",
            "name": "Sarah Johnson",
            "email": "sarah.johnson@email.com",
            "phone": "714-555-0102",
            "address": "456 Oak Avenue",
            "status": "active",
            "last_updated": "2026-06-03"
        }
    ]

    result = build_unified_customer_profiles(
        crm_records=crm_records,
        sales_records=[],
        finance_records=[],
        support_records=[]
    )

    customers = result["customers"]

    assert len(customers) == 1

    customer = customers[0]

    assert customer["customer_id"] == "C002"
    assert customer["name"] == "Sarah Johnson"

    assert customer["monthly_income"] is None
    assert customer["credit_score"] is None
    assert customer["total_orders"] is None
    assert customer["last_ticket"] is None

    assert customer["has_sales_record"] is False
    assert customer["has_finance_record"] is False
    assert customer["has_support_record"] is False


def test_customer_missing_crm_id_requires_review() -> None:
    """
    Confirm a CRM record without a customer ID is not
    silently promoted into the canonical customer table.
    """

    crm_records = [
        {
            "customer_id": "",
            "name": "Kevin Lee",
            "email": "kevin.lee@email.com",
            "phone": "626-555-0111",
            "address": "100 Valley Boulevard",
            "status": "active",
            "last_updated": "2026-06-10"
        }
    ]

    result = build_unified_customer_profiles(
        crm_records=crm_records,
        sales_records=[],
        finance_records=[],
        support_records=[]
    )

    assert len(
        result["customers"]
    ) == 0

    decisions = result[
        "crm_resolution_decisions"
    ]

    assert len(decisions) == 1

    assert (
        decisions[0]["reason"]
        == "CRM record is missing customer_id"
    )


def test_merge_summary_counts_source_coverage() -> None:
    """
    Confirm summary metrics correctly count which
    department records enriched the customer profiles.
    """

    crm_records = [
        {
            "customer_id": "C001",
            "name": "John Smith",
            "email": "john.smith@email.com",
            "phone": "949-555-0101",
            "address": "123 Main Street",
            "status": "active",
            "last_updated": "2026-06-01"
        },
        {
            "customer_id": "C002",
            "name": "Sarah Johnson",
            "email": "sarah.johnson@email.com",
            "phone": "714-555-0102",
            "address": "456 Oak Avenue",
            "status": "active",
            "last_updated": "2026-06-03"
        }
    ]

    sales_records = [
        {
            "customer_number": "C001",
            "total_orders": "4",
            "lifetime_value": "500.00",
            "last_purchase": "2026-06-01",
            "sales_region": "West"
        }
    ]

    finance_records = [
        {
            "user_id": "C001",
            "credit_score": 700,
            "monthly_income": 6500,
            "debt": 10000,
            "risk_status": "low",
            "last_updated": "2026-06-01"
        }
    ]

    support_records = []

    result = build_unified_customer_profiles(
        crm_records,
        sales_records,
        finance_records,
        support_records
    )

    summary = result["summary"]

    assert summary["raw_crm_records"] == 2
    assert summary["unified_customers"] == 2
    assert summary["customers_with_sales"] == 1
    assert summary["customers_with_finance"] == 1
    assert summary["customers_with_support"] == 0