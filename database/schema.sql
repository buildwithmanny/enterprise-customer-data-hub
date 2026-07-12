DROP TABLE IF EXISTS customer_support;
DROP TABLE IF EXISTS customer_finance;
DROP TABLE IF EXISTS customer_sales;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(30),
    address TEXT,
    customer_status VARCHAR(30),

    has_sales_record BOOLEAN NOT NULL DEFAULT FALSE,
    has_finance_record BOOLEAN NOT NULL DEFAULT FALSE,
    has_support_record BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE customer_sales (
    customer_id VARCHAR(20) PRIMARY KEY,
    total_orders INTEGER,
    lifetime_value NUMERIC(12, 2),
    last_purchase DATE,

    CONSTRAINT fk_sales_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_total_orders_nonnegative
        CHECK (
            total_orders IS NULL
            OR total_orders >= 0
        ),

    CONSTRAINT chk_lifetime_value_nonnegative
        CHECK (
            lifetime_value IS NULL
            OR lifetime_value >= 0
        )
);

CREATE TABLE customer_finance (
    customer_id VARCHAR(20) PRIMARY KEY,
    monthly_income NUMERIC(12, 2),
    credit_score INTEGER,
    debt NUMERIC(12, 2),
    risk_status VARCHAR(30),

    CONSTRAINT fk_finance_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
        ON DELETE CASCADE,

    CONSTRAINT chk_monthly_income_nonnegative
        CHECK (
            monthly_income IS NULL
            OR monthly_income >= 0
        ),

    CONSTRAINT chk_credit_score_range
        CHECK (
            credit_score IS NULL
            OR credit_score BETWEEN 300 AND 850
        ),

    CONSTRAINT chk_debt_nonnegative
        CHECK (
            debt IS NULL
            OR debt >= 0
        )
);

CREATE TABLE customer_support (
    customer_id VARCHAR(20) PRIMARY KEY,
    last_ticket VARCHAR(30),
    ticket_status VARCHAR(30),
    customer_sentiment VARCHAR(30),
    support_priority VARCHAR(30),

    CONSTRAINT fk_support_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_customers_email
    ON customers(email);

CREATE INDEX idx_customers_status
    ON customers(customer_status);

CREATE INDEX idx_finance_risk_status
    ON customer_finance(risk_status);

CREATE INDEX idx_support_ticket_status
    ON customer_support(ticket_status);