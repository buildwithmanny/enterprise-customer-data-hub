# Enterprise Customer Data Hub

## Overview

The Enterprise Customer Data Hub is a Python and PostgreSQL data integration project that combines customer records from multiple departmental systems into one unified customer profile.

The project simulates a realistic enterprise environment where CRM, Sales, Finance, and Customer Support systems store overlapping customer information using different structures and identifiers.

The pipeline validates source data, identifies duplicates, matches customer records, applies documented merge rules, generates consolidated customer profiles, and loads the final data into PostgreSQL.

## Project Status

Version 1 is complete.

The project implements an end to end customer data integration workflow from multi source ingestion and validation through customer matching, consolidation, PostgreSQL storage, automated testing, and SQL analytics.

Current capabilities include:

- Loading CSV and JSON source files
- Validating each dataset independently
- Detecting missing values and invalid formats
- Identifying duplicate customer records
- Matching records using customer ID, email, and name
- Applying source specific merge rules
- Handling messy and incomplete source data
- Generating unified customer profiles
- Exporting validation and merge reports
- Loading consolidated records into PostgreSQL
- Enforcing database constraints and relationships
- Using indexes to support database queries
- Running SQL analytics across related tables
- Testing duplicate detection, merge logic, missing records, and messy-data scenarios

## Data Sources

The project integrates four simulated enterprise sources:

### CRM

Contains customer identity and contact information.

### Sales

Contains order counts, lifetime value, and purchase activity.

### Finance

Contains income, debt, credit score, and financial risk information.

### Customer Support

Contains ticket activity, customer sentiment, and support priority.

## Pipeline

```text
CRM CSV
Sales CSV
Finance JSON
Support CSV
        |
        v
Load Source Data
        |
        v
Validate Each Dataset
        |
        v
Detect Duplicates and Match Records
        |
        v
Apply Business Rules
        |
        v
Create Unified Customer Profiles
        |
        v
Load into PostgreSQL
        |
        v
Run SQL Queries and Generate Reports
```

## Business Rules

The current version uses the following rules:

- CRM is the primary source for customer identity.
- CRM supplies customer names and contact information.
- The newest CRM record supplies the customer address.
- Finance supplies income, debt, credit score, and risk information.
- Sales supplies order and lifetime value metrics.
- Customer Support supplies the most recent support status.
- Missing source information remains blank rather than deleting the customer.
- Ambiguous matches are flagged rather than silently resolved.
- Customers missing a reliable CRM customer ID require manual review.

## Project Structure

```text
enterprise-customer-data-hub/
├── data/
│   ├── crm.csv
│   ├── finance.json
│   ├── sales.csv
│   └── support.csv
├── database/
│   ├── analytics.sql
│   ├── load_data.py
│   └── schema.sql
├── reports/
│   ├── merge_summary.json
│   ├── merged_customers.csv
│   └── validation_report.json
├── src/
│   ├── business_rules.py
│   ├── loader.py
│   ├── main.py
│   ├── merger.py
│   ├── postgres_loader.py
│   ├── reporting.py
│   └── validator.py
├── tests/
│   ├── conftest.py
│   ├── test_merger.py
│   └── test_messy_data.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Technologies

- Python
- PostgreSQL
- SQL
- CSV
- JSON
- Psycopg
- python-dotenv
- Pytest
- Git and GitHub

## Setup

### 1. Install Dependencies

```bash
python3 -m pip install -r requirements.txt
```

### 2. Create the PostgreSQL Database

```sql
CREATE DATABASE customer_data_hub;
```

### 3. Create the Local Environment File

Copy `.env.example` to `.env` and add your local PostgreSQL password.

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=customer_data_hub
DB_USER=postgres
DB_PASSWORD=your_local_password
```

Do not commit `.env`.

## Run the File Pipeline

```bash
python3 src/main.py
```

This generates:

- `reports/validation_report.json`
- `reports/merge_summary.json`
- `reports/merged_customers.csv`

## Run Automated Tests

```bash
python3 -m pytest -v
```

The test suite verifies key integration behavior, including duplicate detection, merge rules, missing records, and messy-data scenarios.

## Load Data into PostgreSQL

```bash
python3 database/load_data.py
```

This:

- Tests the PostgreSQL connection
- Creates the database tables
- Loads the unified customer profiles
- Runs basic SQL queries

## PostgreSQL Tables

- `customers`
- `customer_sales`
- `customer_finance`
- `customer_support`

The department-specific tables reference the main `customers` table through foreign keys. Database constraints and indexes help maintain data integrity and support efficient queries.

## SQL Analytics

The PostgreSQL database supports analytical queries across the consolidated customer data, including:

- Customers missing Finance records
- Duplicate customer emails
- Customers with the highest lifetime value
- Average customer credit score
- Cross department analysis using SQL joins

## Performance and Scalability

The current project uses small simulated datasets, but processing one million or more customer records would require changes to how data is processed and updated.

### Batch Processing

Instead of loading entire datasets into memory at once, source records could be processed in batches. This would reduce memory usage and allow large datasets to move through validation, transformation, and database loading in manageable groups.

### Indexing

Indexes on frequently searched and joined fields such as customer ID and email would become increasingly important as the database grows. Indexes improve lookup and join performance, although they also introduce additional storage and write overhead.

### Incremental Updates

Rather than rebuilding every customer profile during each pipeline run, the system could identify records that were added or changed since the previous run. Processing only new or updated records would reduce unnecessary computation and database writes.

### Database Joins

At larger scale, PostgreSQL should handle relational joins between customer and department specific tables rather than relying entirely on Python to combine large datasets in memory. Query performance would depend on appropriate indexes, join keys, and database design.

Together, these approaches would allow the pipeline to evolve from a small batch integration project toward a system capable of processing larger enterprise datasets efficiently.

## Current Limitations

- CRM remains the primary source of customer identity.
- Source only records are reported but not automatically promoted to canonical customers.
- Name matching is limited and intentionally conservative.
- Some invalid source values are retained in validation reports rather than automatically corrected.
- The pipeline currently processes small local datasets rather than production scale data.
- Incremental processing has not yet been implemented.

## Future Improvements

Potential future improvements include:

- Incremental data processing
- Batch processing for larger datasets
- Architecture and entity relationship diagrams
- Expanded data quality monitoring
- Additional integration and edge case testing
- More advanced customer matching strategies