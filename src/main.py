import csv
import json
from pathlib import Path
from typing import Any

from loader import load_csv, load_json
from merger import analyze_customer_matches
from reporting import (
    build_operational_merge_summary
)
from validator import (
    validate_crm,
    validate_finance,
    validate_sales,
    validate_support
)


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

DATA_DIRECTORY = (
    PROJECT_ROOT / "data"
)

REPORTS_DIRECTORY = (
    PROJECT_ROOT / "reports"
)


MERGED_CUSTOMER_FIELDS = [
    "customer_id",
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
    "support_priority",
    "has_sales_record",
    "has_finance_record",
    "has_support_record"
]


def display_dataset_summary(
    dataset_name: str,
    records: list[dict[str, Any]]
) -> None:
    """
    Print a basic dataset summary.
    """

    print(f"\n{'=' * 60}")
    print(dataset_name)
    print(f"{'=' * 60}")
    print(f"Records loaded: {len(records)}")

    if records:
        print("First record:")
        print(records[0])
    else:
        print("The dataset is empty.")


def display_validation_summary(
    report: dict[str, Any]
) -> None:
    """
    Print a validation summary.
    """

    print(f"\n{'-' * 60}")
    print(
        f"{report['dataset'].upper()} VALIDATION"
    )
    print(f"{'-' * 60}")
    print(
        f"Total records:   "
        f"{report['total_records']}"
    )
    print(
        f"Valid records:   "
        f"{report['valid_records']}"
    )
    print(
        f"Invalid records: "
        f"{report['invalid_records']}"
    )
    print(
        f"Total errors:    "
        f"{report['total_errors']}"
    )

    if report["errors"]:
        print("\nErrors:")

        for error in report["errors"]:
            print(
                f"Row {error['row']} | "
                f"Record {error['record_id']} | "
                f"{error['field']} | "
                f"{error['issue']} | "
                f"Value: {error['value']}"
            )


def save_json_report(
    output_path: Path,
    report_data: dict[str, Any]
) -> None:
    """
    Save a dictionary as formatted JSON.
    """

    REPORTS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_path.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            report_data,
            file,
            indent=2
        )

    print(
        f"\nReport saved to: {output_path}"
    )


def save_merged_customers_csv(
    customers: list[dict[str, Any]]
) -> Path:
    """
    Save canonical customer profiles to CSV.
    """

    REPORTS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = (
        REPORTS_DIRECTORY
        / "merged_customers.csv"
    )

    with output_path.open(
        "w",
        encoding="utf-8",
        newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=MERGED_CUSTOMER_FIELDS,
            extrasaction="ignore"
        )

        writer.writeheader()

        for customer in customers:
            writer.writerow(
                {
                    field: (
                        ""
                        if customer.get(field) is None
                        else customer.get(field)
                    )
                    for field in (
                        MERGED_CUSTOMER_FIELDS
                    )
                }
            )

    return output_path


def build_validation_report(
    reports: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Combine source validation reports.
    """

    return {
        "datasets": reports,
        "summary": {
            "total_datasets": len(
                reports
            ),
            "total_records": sum(
                report["total_records"]
                for report in reports
            ),
            "valid_records": sum(
                report["valid_records"]
                for report in reports
            ),
            "invalid_records": sum(
                report["invalid_records"]
                for report in reports
            ),
            "total_errors": sum(
                report["total_errors"]
                for report in reports
            )
        }
    }


def display_duplicate_summary(
    customer_match_report: dict[str, Any]
) -> None:
    """
    Print source duplicate analysis.
    """

    duplicate_analysis = (
        customer_match_report[
            "duplicate_analysis"
        ]
    )

    print(f"\n{'=' * 60}")
    print("DUPLICATE CUSTOMER ANALYSIS")
    print(f"{'=' * 60}")

    print(
        "Total duplicate groups: "
        f"{duplicate_analysis['total_duplicate_groups']}"
    )

    for source_name, duplicates in (
        duplicate_analysis["by_source"].items()
    ):
        print(
            f"\n{source_name.upper()}: "
            f"{len(duplicates)} duplicate group(s)"
        )

        if not duplicates:
            print("  No duplicates found.")
            continue

        for duplicate in duplicates:
            print(
                f"  Field: {duplicate['field']} | "
                f"Value: {duplicate['value']} | "
                f"Occurrences: "
                f"{duplicate['occurrences']} | "
                f"Positions: "
                f"{duplicate['record_positions']}"
            )


def display_matching_summary(
    customer_match_report: dict[str, Any]
) -> None:
    """
    Print cross-source match results.
    """

    matching_analysis = (
        customer_match_report[
            "matching_analysis"
        ]
    )

    print(f"\n{'=' * 60}")
    print("CROSS-SOURCE CUSTOMER MATCHING")
    print(f"{'=' * 60}")

    for source_name, analysis in (
        matching_analysis.items()
    ):
        summary = analysis["summary"]

        print(f"\n{source_name.upper()} TO CRM")
        print(f"{'-' * 40}")
        print(
            f"Total records: "
            f"{summary['total_records']}"
        )
        print(
            f"Matched:       "
            f"{summary['matched']}"
        )
        print(
            f"Unmatched:     "
            f"{summary['unmatched']}"
        )
        print(
            f"Ambiguous:     "
            f"{summary['ambiguous']}"
        )


def display_unified_profile_summary(
    customer_match_report: dict[str, Any]
) -> None:
    """
    Print the unified-profile summary.
    """

    result = customer_match_report[
        "unified_profile_result"
    ]

    summary = result["summary"]

    print(f"\n{'=' * 60}")
    print("UNIFIED CUSTOMER PROFILES")
    print(f"{'=' * 60}")

    print(
        f"Raw CRM records:       "
        f"{summary['raw_crm_records']}"
    )

    print(
        f"Unified customers:     "
        f"{summary['unified_customers']}"
    )

    print(
        f"With Sales data:       "
        f"{summary['customers_with_sales']}"
    )

    print(
        f"With Finance data:     "
        f"{summary['customers_with_finance']}"
    )

    print(
        f"With Support data:     "
        f"{summary['customers_with_support']}"
    )


def display_operational_report_summary(
    merge_summary: dict[str, Any]
) -> None:
    """
    Print the high-level Day 9 error-reporting summary.
    """

    summary = merge_summary[
        "executive_summary"
    ]

    print(f"\n{'=' * 60}")
    print("DAY 9 OPERATIONAL MERGE SUMMARY")
    print(f"{'=' * 60}")

    print(
        f"Source records validated:   "
        f"{summary['source_records_validated']}"
    )

    print(
        f"Validation failures:        "
        f"{summary['validation_failures']}"
    )

    print(
        f"Duplicate groups found:     "
        f"{summary['duplicate_groups_found']}"
    )

    print(
        f"Matched source records:     "
        f"{summary['matched_source_records']}"
    )

    print(
        f"Unmatched records:          "
        f"{summary['unmatched_records']}"
    )

    print(
        f"Ambiguous matches:          "
        f"{summary['ambiguous_matches']}"
    )

    print(
        f"Canonical customers:        "
        f"{summary['canonical_customers_created']}"
    )

    print(
        f"Manual review items:        "
        f"{summary['manual_review_items']}"
    )


def main() -> None:
    """
    Load, validate, match, resolve, export, and
    produce operational error reports.
    """

    try:
        print("Loading CRM...")
        crm_records = load_csv(
            DATA_DIRECTORY / "crm.csv"
        )

        print("Loading Sales...")
        sales_records = load_csv(
            DATA_DIRECTORY / "sales.csv"
        )

        print("Loading Finance...")
        finance_records = load_json(
            DATA_DIRECTORY / "finance.json"
        )

        print("Loading Support...")
        support_records = load_csv(
            DATA_DIRECTORY / "support.csv"
        )

        display_dataset_summary(
            "CRM DATA",
            crm_records
        )

        display_dataset_summary(
            "SALES DATA",
            sales_records
        )

        display_dataset_summary(
            "FINANCE DATA",
            finance_records
        )

        display_dataset_summary(
            "SUPPORT DATA",
            support_records
        )

        print(f"\n{'=' * 60}")
        print(
            "All source files loaded successfully."
        )
        print(f"{'=' * 60}")

        validation_reports = [
            validate_crm(
                crm_records
            ),
            validate_sales(
                sales_records
            ),
            validate_finance(
                finance_records
            ),
            validate_support(
                support_records
            )
        ]

        for report in validation_reports:
            display_validation_summary(
                report
            )

        final_validation_report = (
            build_validation_report(
                validation_reports
            )
        )

        save_json_report(
            REPORTS_DIRECTORY
            / "validation_report.json",
            final_validation_report
        )

        customer_match_report = (
            analyze_customer_matches(
                crm_records,
                sales_records,
                finance_records,
                support_records
            )
        )

        display_duplicate_summary(
            customer_match_report
        )

        display_matching_summary(
            customer_match_report
        )

        display_unified_profile_summary(
            customer_match_report
        )

        unified_customers = (
            customer_match_report[
                "unified_profile_result"
            ]["customers"]
        )

        merged_output_path = (
            save_merged_customers_csv(
                unified_customers
            )
        )

        print(
            f"\nMerged customer file saved to: "
            f"{merged_output_path}"
        )

        operational_merge_summary = (
            build_operational_merge_summary(
                validation_reports,
                customer_match_report
            )
        )

        save_json_report(
            REPORTS_DIRECTORY
            / "merge_summary.json",
            operational_merge_summary
        )

        display_operational_report_summary(
            operational_merge_summary
        )

        print(f"\n{'=' * 60}")
        print(
            "Day 9 error reporting completed "
            "successfully."
        )
        print(f"{'=' * 60}")

    except FileNotFoundError as error:
        print(
            f"File error: {error}"
        )

    except json.JSONDecodeError as error:
        print(
            f"JSON formatting error: {error}"
        )

    except ValueError as error:
        print(
            f"Data structure error: {error}"
        )

    except Exception as error:
        print(
            f"Unexpected error: {error}"
        )


if __name__ == "__main__":
    main()