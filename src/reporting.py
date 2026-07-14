from typing import Any


def collect_validation_failures(
    validation_reports: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Combine validation errors from all source datasets
    into one stakeholder-readable list.
    """

    validation_failures = []

    for report in validation_reports:
        dataset_name = report["dataset"]

        for error in report["errors"]:
            validation_failures.append(
                {
                    "dataset": dataset_name,
                    "row": error["row"],
                    "record_id": error["record_id"],
                    "field": error["field"],
                    "issue": error["issue"],
                    "value": error["value"]
                }
            )

    return validation_failures


def collect_match_records_by_status(
    customer_match_report: dict[str, Any],
    target_status: str
) -> list[dict[str, Any]]:
    """
    Collect match records with a specific status.

    Supported statuses include:
    - unmatched
    - ambiguous
    - matched
    """

    matching_analysis = customer_match_report[
        "matching_analysis"
    ]

    matching_records = []

    for source_name, source_analysis in (
        matching_analysis.items()
    ):
        for record in source_analysis["records"]:
            if record["match_status"] == target_status:
                matching_records.append(
                    {
                        "source": source_name,
                        "source_position": (
                            record["source_position"]
                        ),
                        "source_identifier": (
                            record["source_identifier"]
                        ),
                        "match_method": (
                            record["match_method"]
                        ),
                        "crm_record_positions": (
                            record[
                                "crm_record_positions"
                            ]
                        )
                    }
                )

    return matching_records


def collect_duplicate_groups(
    customer_match_report: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    Flatten duplicate groups across all source systems.
    """

    duplicates_by_source = customer_match_report[
        "duplicate_analysis"
    ]["by_source"]

    duplicate_groups = []

    for source_name, duplicates in (
        duplicates_by_source.items()
    ):
        for duplicate in duplicates:
            duplicate_groups.append(
                {
                    "source": source_name,
                    "field": duplicate["field"],
                    "value": duplicate["value"],
                    "occurrences": (
                        duplicate["occurrences"]
                    ),
                    "record_positions": (
                        duplicate["record_positions"]
                    )
                }
            )

    return duplicate_groups


def collect_crm_review_decisions(
    customer_match_report: dict[str, Any]
) -> list[dict[str, Any]]:
    """
    Collect CRM duplicate-resolution and missing-ID
    decisions that may be useful during manual review.
    """

    unified_result = customer_match_report[
        "unified_profile_result"
    ]

    decisions = unified_result[
        "crm_resolution_decisions"
    ]

    review_decisions = []

    for decision in decisions:
        if "customer_id" in decision:
            review_decisions.append(
                {
                    "review_type": (
                        "crm_duplicate_resolution"
                    ),
                    "customer_id": (
                        decision["customer_id"]
                    ),
                    "records_reviewed": (
                        decision["records_reviewed"]
                    ),
                    "rule_applied": (
                        decision["rule_applied"]
                    ),
                    "selected_last_updated": (
                        decision[
                            "selected_last_updated"
                        ]
                    ),
                    "selected_address": (
                        decision["selected_address"]
                    )
                }
            )

        else:
            review_decisions.append(
                {
                    "review_type": (
                        "missing_customer_id"
                    ),
                    "source_position": (
                        decision["source_position"]
                    ),
                    "reason": decision["reason"],
                    "record": decision["record"]
                }
            )

    return review_decisions


def build_manual_review_queue(
    validation_failures: list[dict[str, Any]],
    unmatched_records: list[dict[str, Any]],
    ambiguous_records: list[dict[str, Any]],
    crm_review_decisions: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Create one consolidated queue of records requiring
    investigation or business review.
    """

    review_queue = []

    for failure in validation_failures:
        review_queue.append(
            {
                "review_type": (
                    "validation_failure"
                ),
                "source": failure["dataset"],
                "record_reference": (
                    failure["record_id"]
                ),
                "details": failure
            }
        )

    for record in unmatched_records:
        review_queue.append(
            {
                "review_type": (
                    "unmatched_record"
                ),
                "source": record["source"],
                "record_reference": (
                    record["source_identifier"]
                ),
                "details": record
            }
        )

    for record in ambiguous_records:
        review_queue.append(
            {
                "review_type": (
                    "ambiguous_match"
                ),
                "source": record["source"],
                "record_reference": (
                    record["source_identifier"]
                ),
                "details": record
            }
        )

    for decision in crm_review_decisions:
        review_queue.append(
            {
                "review_type": (
                    decision["review_type"]
                ),
                "source": "crm",
                "record_reference": (
                    decision.get("customer_id")
                    or decision.get(
                        "source_position"
                    )
                ),
                "details": decision
            }
        )

    return review_queue


def build_issue_counts(
    validation_failures: list[dict[str, Any]],
    duplicate_groups: list[dict[str, Any]],
    unmatched_records: list[dict[str, Any]],
    ambiguous_records: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Count issues by category and by validation issue.
    """

    validation_issue_counts: dict[str, int] = {}

    for failure in validation_failures:
        issue_name = failure["issue"]

        validation_issue_counts[issue_name] = (
            validation_issue_counts.get(
                issue_name,
                0
            )
            + 1
        )

    duplicate_counts_by_source: dict[str, int] = {}

    for duplicate in duplicate_groups:
        source_name = duplicate["source"]

        duplicate_counts_by_source[
            source_name
        ] = (
            duplicate_counts_by_source.get(
                source_name,
                0
            )
            + 1
        )

    unmatched_counts_by_source: dict[str, int] = {}

    for record in unmatched_records:
        source_name = record["source"]

        unmatched_counts_by_source[
            source_name
        ] = (
            unmatched_counts_by_source.get(
                source_name,
                0
            )
            + 1
        )

    ambiguous_counts_by_source: dict[str, int] = {}

    for record in ambiguous_records:
        source_name = record["source"]

        ambiguous_counts_by_source[
            source_name
        ] = (
            ambiguous_counts_by_source.get(
                source_name,
                0
            )
            + 1
        )

    return {
        "validation_issues": (
            validation_issue_counts
        ),
        "duplicate_groups_by_source": (
            duplicate_counts_by_source
        ),
        "unmatched_records_by_source": (
            unmatched_counts_by_source
        ),
        "ambiguous_matches_by_source": (
            ambiguous_counts_by_source
        )
    }


def build_operational_merge_summary(
    validation_reports: list[dict[str, Any]],
    customer_match_report: dict[str, Any]
) -> dict[str, Any]:
    """
    Build the final Day 9 operational merge report.

    The report includes:
    - duplicate groups
    - unmatched records
    - ambiguous matches
    - validation failures
    - manual-review queue
    - canonical-profile summary
    """

    validation_failures = (
        collect_validation_failures(
            validation_reports
        )
    )

    duplicate_groups = (
        collect_duplicate_groups(
            customer_match_report
        )
    )

    unmatched_records = (
        collect_match_records_by_status(
            customer_match_report,
            "unmatched"
        )
    )

    ambiguous_records = (
        collect_match_records_by_status(
            customer_match_report,
            "ambiguous"
        )
    )

    crm_review_decisions = (
        collect_crm_review_decisions(
            customer_match_report
        )
    )

    manual_review_queue = (
        build_manual_review_queue(
            validation_failures,
            unmatched_records,
            ambiguous_records,
            crm_review_decisions
        )
    )

    issue_counts = build_issue_counts(
        validation_failures,
        duplicate_groups,
        unmatched_records,
        ambiguous_records
    )

    unified_result = customer_match_report[
        "unified_profile_result"
    ]

    matching_analysis = customer_match_report[
        "matching_analysis"
    ]

    total_source_records = sum(
        source["summary"]["total_records"]
        for source in matching_analysis.values()
    )

    total_matched_records = sum(
        source["summary"]["matched"]
        for source in matching_analysis.values()
    )

    return {
        "report_name": (
            "Enterprise Customer Data Hub "
            "Merge Summary"
        ),
        "report_version": 1,
        "executive_summary": {
            "source_datasets_validated": len(
                validation_reports
            ),
            "source_records_validated": sum(
                report["total_records"]
                for report in validation_reports
            ),
            "validation_failures": len(
                validation_failures
            ),
            "duplicate_groups_found": len(
                duplicate_groups
            ),
            "source_records_evaluated_for_matching": (
                total_source_records
            ),
            "matched_source_records": (
                total_matched_records
            ),
            "unmatched_records": len(
                unmatched_records
            ),
            "ambiguous_matches": len(
                ambiguous_records
            ),
            "canonical_customers_created": (
                unified_result[
                    "summary"
                ]["unified_customers"]
            ),
            "manual_review_items": len(
                manual_review_queue
            )
        },
        "issue_counts": issue_counts,
        "duplicates_found": duplicate_groups,
        "unmatched_records": unmatched_records,
        "ambiguous_matches": ambiguous_records,
        "validation_failures": (
            validation_failures
        ),
        "crm_resolution_decisions": (
            crm_review_decisions
        ),
        "manual_review_queue": (
            manual_review_queue
        ),
        "source_matching_summary": {
            source_name: analysis["summary"]
            for source_name, analysis in (
                matching_analysis.items()
            )
        },
        "unified_customer_summary": (
            unified_result["summary"]
        ),
        "business_rules": (
            customer_match_report[
                "business_rules"
            ]
        ),
        "field_lineage": (
            unified_result[
                "field_lineage"
            ]
        )
    }