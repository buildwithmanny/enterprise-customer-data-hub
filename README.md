# Enterprise Customer Data Hub

## Overview

The Enterprise Customer Data Hub is a Python and PostgreSQL data integration project that combines customer records from multiple departmental systems into one unified customer profile.

The project simulates a realistic enterprise environment where CRM, Sales, Finance, and Customer Support systems store overlapping customer information using different structures and identifiers.

The pipeline validates source data, identifies duplicates, matches customer records, applies documented merge rules, generates consolidated customer profiles, and loads the final data into PostgreSQL.

## Project Status

Version 1 is functional.

Current capabilities include:

- Loading CSV and JSON source files
- Validating each dataset independently
- Detecting missing values and invalid formats
- Identifying duplicate customer records
- Matching records using customer ID, email, and name
- Applying source-specific merge rules
- Generating unified customer profiles
- Exporting validation and merge reports
- Loading consolidated records into PostgreSQL
- Running basic SQL queries across related tables

Automated testing, improved reporting, database constraints, analytics, and final documentation will be added during the next project phase.

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

The first version uses the following rules:

- CRM is the primary source for customer identity.
- CRM supplies customer names and contact information.
- The newest CRM record supplies the customer address.
- Finance supplies income, debt, credit score, and risk information.
- Sales supplies order and lifetime-value metrics.
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
│   └── validator.py
├── tests/
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
- Git and GitHub

## Setup

### 1. Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

### 2. Create the PostgreSQL database

```sql
CREATE DATABASE customer_data_hub;
```

### 3. Create the local environment file

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

The department-specific tables reference the main `customers` table through foreign keys.

## Current Limitations

- CRM remains the primary source of customer identity.
- Source-only records are reported but not automatically promoted to canonical customers.
- Name matching is limited and intentionally conservative.
- Some invalid source values are retained in validation reports rather than automatically corrected.
- Automated tests have not yet been added.

## Next Phase

Planned improvements include:

- Automated tests
- Improved error reporting
- Additional messy-data scenarios
- Stronger PostgreSQL constraints and indexes
- SQL analytics
- Architecture and entity-relationship diagrams
- Performance and scalability documentation