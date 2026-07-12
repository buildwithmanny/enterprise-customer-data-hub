from collections import defaultdict
from typing import Any

from business_rules import (
    choose_newest_record,
    describe_business_rules,
    normalize_text,
    resolve_crm_records,
    resolve_customer_attributes
)


def normalize_email(value: Any) -> str:
    """
    Normalize an email address for matching.
    """

    return normalize_text(value).lower()


def normalize_name(value: Any) -> str:
    """
    Normalize a customer name for matching.
    """

    normalized_name = normalize_text(
        value
    ).lower()

    return " ".join(
        normalized_name.split()
    )


def find_duplicate_values(
    records: list[dict[str, Any]],
    field_name: str
) -> list[dict[str, Any]]:
    """
    Find duplicate non-empty values within one dataset.
    """

    value_locations: dict[
        str,
        list[int]
    ] = defaultdict(list)

    for index, record in enumerate(
        records,
        start=1
    ):
        normalized_value = normalize_text(
            record.get(field_name)
        ).lower()

        if normalized_value:
            value_locations[
                normalized_value
            ].append(index)

    duplicates = []

    for value, record_positions in (
        value_locations.items()
    ):
        if len(record_positions) > 1:
            duplicates.append(
                {
                    "field": field_name,
                    "value": value,
                    "record_positions": (
                        record_positions
                    ),
                    "occurrences": len(
                        record_positions
                    )
                }
            )

    return duplicates


def detect_source_duplicates(
    crm_records: list[dict[str, Any]],
    sales_records: list[dict[str, Any]],
    finance_records: list[dict[str, Any]],
    support_records: list[dict[str, Any]]
) -> dict[str, list[dict[str, Any]]]:
    """
    Detect duplicate identifiers within each source.
    """

    return {
        "crm": (
            find_duplicate_values(
                crm_records,
                "customer_id"
            )
            + find_duplicate_values(
                crm_records,
                "email"
            )
        ),
        "sales": find_duplicate_values(
            sales_records,
            "customer_number"
        ),
        "finance": find_duplicate_values(
            finance_records,
            "user_id"
        ),
        "support": find_duplicate_values(
            support_records,
            "email"
        )
    }


def build_crm_indexes(
    crm_records: list[dict[str, Any]]
) -> dict[str, dict[str, list[int]]]:
    """
    Build CRM lookup indexes.
    """

    customer_id_index: dict[
        str,
        list[int]
    ] = defaultdict(list)

    email_index: dict[
        str,
        list[int]
    ] = defaultdict(list)

    name_index: dict[
        str,
        list[int]
    ] = defaultdict(list)

    for index, record in enumerate(
        crm_records,
        start=1
    ):
        customer_id = normalize_text(
            record.get("customer_id")
        ).lower()

        email = normalize_email(
            record.get("email")
        )

        name = normalize_name(
            record.get("name")
        )

        if customer_id:
            customer_id_index[
                customer_id
            ].append(index)

        if email:
            email_index[
                email
            ].append(index)

        if name:
            name_index[
                name
            ].append(index)

    return {
        "customer_id": dict(
            customer_id_index
        ),
        "email": dict(
            email_index
        ),
        "name": dict(
            name_index
        )
    }


def create_match_result(
    source_name: str,
    source_position: int,
    source_identifier: str,
    match_method: str | None,
    crm_positions: list[int]
) -> dict[str, Any]:
    """
    Build one source-to-CRM match result.
    """

    if not crm_positions:
        match_status = "unmatched"

    elif len(crm_positions) == 1:
        match_status = "matched"

    else:
        match_status = "ambiguous"

    return {
        "source": source_name,
        "source_position": source_position,
        "source_identifier": source_identifier,
        "match_status": match_status,
        "match_method": match_method,
        "crm_record_positions": crm_positions
    }


def match_sales_to_crm(
    sales_records: list[dict[str, Any]],
    crm_indexes: dict[str, dict[str, list[int]]]
) -> list[dict[str, Any]]:
    """
    Match Sales to CRM by customer ID.
    """

    results = []

    for position, record in enumerate(
        sales_records,
        start=1
    ):
        customer_number = normalize_text(
            record.get("customer_number")
        ).lower()

        crm_positions = crm_indexes[
            "customer_id"
        ].get(
            customer_number,
            []
        )

        results.append(
            create_match_result(
                source_name="sales",
                source_position=position,
                source_identifier=(
                    customer_number or "missing"
                ),
                match_method=(
                    "customer_id"
                    if customer_number
                    else None
                ),
                crm_positions=crm_positions
            )
        )

    return results


def match_finance_to_crm(
    finance_records: list[dict[str, Any]],
    crm_indexes: dict[str, dict[str, list[int]]]
) -> list[dict[str, Any]]:
    """
    Match Finance to CRM by customer ID.
    """

    results = []

    for position, record in enumerate(
        finance_records,
        start=1
    ):
        user_id = normalize_text(
            record.get("user_id")
        ).lower()

        crm_positions = crm_indexes[
            "customer_id"
        ].get(
            user_id,
            []
        )

        results.append(
            create_match_result(
                source_name="finance",
                source_position=position,
                source_identifier=(
                    user_id or "missing"
                ),
                match_method=(
                    "customer_id"
                    if user_id
                    else None
                ),
                crm_positions=crm_positions
            )
        )

    return results


def match_support_to_crm(
    support_records: list[dict[str, Any]],
    crm_indexes: dict[str, dict[str, list[int]]]
) -> list[dict[str, Any]]:
    """
    Match Support to CRM by email, then by a
    controlled name-from-email fallback.
    """

    results = []

    for position, record in enumerate(
        support_records,
        start=1
    ):
        email = normalize_email(
            record.get("email")
        )

        crm_positions = []
        match_method = None

        if email:
            crm_positions = crm_indexes[
                "email"
            ].get(
                email,
                []
            )

            if crm_positions:
                match_method = "email"

        if not crm_positions and email:
            email_username = email.split(
                "@"
            )[0]

            possible_name = normalize_name(
                email_username.replace(
                    ".",
                    " "
                )
            )

            crm_positions = crm_indexes[
                "name"
            ].get(
                possible_name,
                []
            )

            if crm_positions:
                match_method = (
                    "name_from_email"
                )

        results.append(
            create_match_result(
                source_name="support",
                source_position=position,
                source_identifier=(
                    email or "missing"
                ),
                match_method=match_method,
                crm_positions=crm_positions
            )
        )

    return results


def summarize_match_results(
    match_results: list[dict[str, Any]]
) -> dict[str, int]:
    """
    Count match outcomes.
    """

    summary = {
        "total_records": len(
            match_results
        ),
        "matched": 0,
        "unmatched": 0,
        "ambiguous": 0
    }

    for result in match_results:
        status = result["match_status"]

        if status in summary:
            summary[status] += 1

    return summary


def group_records_by_field(
    records: list[dict[str, Any]],
    field_name: str
) -> dict[str, list[dict[str, Any]]]:
    """
    Group records by a normalized identifier.
    """

    grouped_records: dict[
        str,
        list[dict[str, Any]]
    ] = defaultdict(list)

    for record in records:
        key = normalize_text(
            record.get(field_name)
        ).lower()

        if key:
            grouped_records[key].append(
                record
            )

    return dict(grouped_records)


def resolve_sales_group(
    records: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """
    Resolve duplicate Sales records.

    Rules:
    - Sum total_orders.
    - Sum lifetime_value.
    - Use the newest last_purchase.
    - Use the sales region from the newest record.
    """

    if not records:
        return None

    resolved_record = records[0].copy()

    total_orders = 0
    lifetime_value = 0.0

    for record in records:
        try:
            total_orders += int(
                record.get(
                    "total_orders",
                    0
                )
            )
        except (
            TypeError,
            ValueError
        ):
            pass

        try:
            lifetime_value += float(
                record.get(
                    "lifetime_value",
                    0
                )
            )
        except (
            TypeError,
            ValueError
        ):
            pass

    newest_record = choose_newest_record(
        records,
        "last_purchase"
    )

    resolved_record["total_orders"] = (
        total_orders
    )

    resolved_record["lifetime_value"] = (
        round(
            lifetime_value,
            2
        )
    )

    if newest_record is not None:
        resolved_record["last_purchase"] = (
            newest_record.get(
                "last_purchase"
            )
        )

        resolved_record["sales_region"] = (
            newest_record.get(
                "sales_region"
            )
        )

    return resolved_record


def resolve_support_group(
    records: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """
    Resolve duplicate Support records.

    Rule:
    - Use the support record with the newest
      last_updated date.
    """

    return choose_newest_record(
        records,
        "last_updated"
    )


def build_resolved_source_indexes(
    sales_records: list[dict[str, Any]],
    finance_records: list[dict[str, Any]],
    support_records: list[dict[str, Any]]
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]]
]:
    """
    Build resolved lookup indexes for Day 5.
    """

    grouped_sales = group_records_by_field(
        sales_records,
        "customer_number"
    )

    sales_index = {}

    for customer_id, records in (
        grouped_sales.items()
    ):
        resolved_sales = resolve_sales_group(
            records
        )

        if resolved_sales is not None:
            sales_index[
                customer_id
            ] = resolved_sales

    grouped_finance = group_records_by_field(
        finance_records,
        "user_id"
    )

    finance_index = {}

    for customer_id, records in (
        grouped_finance.items()
    ):
        newest_finance = choose_newest_record(
            records,
            "last_updated"
        )

        if newest_finance is not None:
            finance_index[
                customer_id
            ] = newest_finance

    grouped_support = group_records_by_field(
        support_records,
        "email"
    )

    support_index = {}

    for email, records in (
        grouped_support.items()
    ):
        resolved_support = (
            resolve_support_group(
                records
            )
        )

        if resolved_support is not None:
            support_index[
                email
            ] = resolved_support

    return (
        sales_index,
        finance_index,
        support_index
    )


def find_support_record(
    crm_record: dict[str, Any],
    support_index: dict[
        str,
        dict[str, Any]
    ]
) -> dict[str, Any] | None:
    """
    Find a Support record by exact email, then
    use the controlled name-from-email fallback.
    """

    crm_email = normalize_email(
        crm_record.get("email")
    )

    exact_match = support_index.get(
        crm_email
    )

    if exact_match is not None:
        return exact_match

    crm_name = normalize_name(
        crm_record.get("name")
    )

    for support_email, candidate in (
        support_index.items()
    ):
        possible_name = normalize_name(
            support_email.split("@")[0].replace(
                ".",
                " "
            )
        )

        if (
            possible_name
            and possible_name == crm_name
        ):
            return candidate

    return None


def build_unified_customer_profiles(
    crm_records: list[dict[str, Any]],
    sales_records: list[dict[str, Any]],
    finance_records: list[dict[str, Any]],
    support_records: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Build the final canonical customer profiles.
    """

    resolved_crm_records, crm_decisions = (
        resolve_crm_records(
            crm_records
        )
    )

    (
        sales_index,
        finance_index,
        support_index
    ) = build_resolved_source_indexes(
        sales_records,
        finance_records,
        support_records
    )

    unified_customers = []
    lineage_records = []

    for crm_record in resolved_crm_records:
        customer_id = normalize_text(
            crm_record.get(
                "customer_id"
            )
        ).lower()

        sales_record = sales_index.get(
            customer_id
        )

        finance_record = finance_index.get(
            customer_id
        )

        support_record = find_support_record(
            crm_record,
            support_index
        )

        (
            resolved_customer,
            field_lineage
        ) = resolve_customer_attributes(
            crm_record=crm_record,
            sales_record=sales_record,
            finance_record=finance_record,
            support_record=support_record
        )

        resolved_customer[
            "has_sales_record"
        ] = sales_record is not None

        resolved_customer[
            "has_finance_record"
        ] = finance_record is not None

        resolved_customer[
            "has_support_record"
        ] = support_record is not None

        unified_customers.append(
            resolved_customer
        )

        lineage_records.append(
            {
                "customer_id": (
                    resolved_customer.get(
                        "customer_id"
                    )
                ),
                "field_sources": (
                    field_lineage
                )
            }
        )

    return {
        "customers": unified_customers,
        "field_lineage": lineage_records,
        "crm_resolution_decisions": (
            crm_decisions
        ),
        "summary": {
            "raw_crm_records": len(
                crm_records
            ),
            "unified_customers": len(
                unified_customers
            ),
            "customers_with_sales": sum(
                1
                for customer in unified_customers
                if customer[
                    "has_sales_record"
                ]
            ),
            "customers_with_finance": sum(
                1
                for customer in unified_customers
                if customer[
                    "has_finance_record"
                ]
            ),
            "customers_with_support": sum(
                1
                for customer in unified_customers
                if customer[
                    "has_support_record"
                ]
            )
        }
    }


def analyze_customer_matches(
    crm_records: list[dict[str, Any]],
    sales_records: list[dict[str, Any]],
    finance_records: list[dict[str, Any]],
    support_records: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Run duplicate analysis, matching, business rules,
    and unified-profile creation.
    """

    crm_indexes = build_crm_indexes(
        crm_records
    )

    duplicate_results = (
        detect_source_duplicates(
            crm_records,
            sales_records,
            finance_records,
            support_records
        )
    )

    sales_matches = match_sales_to_crm(
        sales_records,
        crm_indexes
    )

    finance_matches = match_finance_to_crm(
        finance_records,
        crm_indexes
    )

    support_matches = match_support_to_crm(
        support_records,
        crm_indexes
    )

    total_duplicate_groups = sum(
        len(groups)
        for groups in duplicate_results.values()
    )

    unified_profile_result = (
        build_unified_customer_profiles(
            crm_records,
            sales_records,
            finance_records,
            support_records
        )
    )

    return {
        "duplicate_analysis": {
            "total_duplicate_groups": (
                total_duplicate_groups
            ),
            "by_source": duplicate_results
        },
        "matching_analysis": {
            "sales": {
                "summary": summarize_match_results(
                    sales_matches
                ),
                "records": sales_matches
            },
            "finance": {
                "summary": summarize_match_results(
                    finance_matches
                ),
                "records": finance_matches
            },
            "support": {
                "summary": summarize_match_results(
                    support_matches
                ),
                "records": support_matches
            }
        },
        "business_rules": (
            describe_business_rules()
        ),
        "unified_profile_result": (
            unified_profile_result
        )
    }