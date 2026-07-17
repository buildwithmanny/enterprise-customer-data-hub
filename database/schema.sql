DROP VIEW IF EXISTS customer_360;

DROP TABLE IF EXISTS customer_support;
DROP TABLE IF EXISTS customer_finance;
DROP TABLE IF EXISTS customer_sales;
DROP TABLE IF EXISTS customers;


-- =========================================================
-- PRIMARY CUSTOMER TABLE
-- =========================================================

CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,

    name VARCHAR(150) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(30),
    address TEXT,

    customer_status VARCHAR(30) NOT NULL,

    has_sales_record BOOLEAN NOT NULL DEFAULT FALSE,
    has_finance_record BOOLEAN NOT NULL DEFAULT FALSE,
    has_support_record BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_customer_id_not_blank
        CHECK (
            LENGTH(TRIM(customer_id)) > 0
        ),

    CONSTRAINT chk_customer_name_not_blank
        CHECK (
            LENGTH(TRIM(name)) > 0
        ),

    CONSTRAINT chk_customer_status
        CHECK (
            customer_status IN (
                'active',
                'inactive'
            )
        )
);


-- =========================================================
-- SALES TABLE
-- One customer can have one consolidated Sales profile.
-- =========================================================

CREATE TABLE customer_sales (
    customer_id VARCHAR(20) PRIMARY KEY,

    total_orders INTEGER,
    lifetime_value NUMERIC(12, 2),
    last_purchase DATE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_sales_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
        ON UPDATE CASCADE
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


-- =========================================================
-- FINANCE TABLE
-- One customer can have one consolidated Finance profile.
-- =========================================================

CREATE TABLE customer_finance (
    customer_id VARCHAR(20) PRIMARY KEY,

    monthly_income NUMERIC(12, 2),
    credit_score INTEGER,
    debt NUMERIC(12, 2),
    risk_status VARCHAR(30),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_finance_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
        ON UPDATE CASCADE
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
        ),

    CONSTRAINT chk_finance_risk_status
        CHECK (
            risk_status IS NULL
            OR risk_status IN (
                'low',
                'medium',
                'high',
                'unknown'
            )
        )
);


-- =========================================================
-- SUPPORT TABLE
-- One customer can have one current consolidated
-- Customer Support profile.
-- =========================================================

CREATE TABLE customer_support (
    customer_id VARCHAR(20) PRIMARY KEY,

    last_ticket VARCHAR(30),
    ticket_status VARCHAR(30),
    customer_sentiment VARCHAR(30),
    support_priority VARCHAR(30),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_support_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT chk_ticket_status
        CHECK (
            ticket_status IS NULL
            OR ticket_status IN (
                'open',
                'pending',
                'resolved',
                'closed'
            )
        ),

    CONSTRAINT chk_customer_sentiment
        CHECK (
            customer_sentiment IS NULL
            OR customer_sentiment IN (
                'positive',
                'neutral',
                'negative'
            )
        ),

    CONSTRAINT chk_support_priority
        CHECK (
            support_priority IS NULL
            OR support_priority IN (
                'low',
                'medium',
                'high'
            )
        )
);


-- =========================================================
-- INDEXES
-- =========================================================

-- Customer identity and filtering indexes

CREATE INDEX idx_customers_email_lower
    ON customers (
        LOWER(email)
    )
    WHERE email IS NOT NULL;

CREATE INDEX idx_customers_status
    ON customers (
        customer_status
    );

CREATE INDEX idx_customers_source_coverage
    ON customers (
        has_sales_record,
        has_finance_record,
        has_support_record
    );


-- Sales analytics indexes

CREATE INDEX idx_sales_lifetime_value
    ON customer_sales (
        lifetime_value DESC
    );

CREATE INDEX idx_sales_last_purchase
    ON customer_sales (
        last_purchase DESC
    );


-- Finance analytics indexes

CREATE INDEX idx_finance_risk_status
    ON customer_finance (
        risk_status
    );

CREATE INDEX idx_finance_credit_score
    ON customer_finance (
        credit_score
    );

CREATE INDEX idx_finance_debt
    ON customer_finance (
        debt DESC
    );


-- Support analytics indexes

CREATE INDEX idx_support_ticket_status
    ON customer_support (
        ticket_status
    );

CREATE INDEX idx_support_priority
    ON customer_support (
        support_priority
    );


-- =========================================================
-- CUSTOMER 360 VIEW
-- Provides one business-friendly view across all tables.
-- =========================================================

CREATE VIEW customer_360 AS
SELECT
    c.customer_id,
    c.name,
    c.email,
    c.phone,
    c.address,
    c.customer_status,

    s.total_orders,
    s.lifetime_value,
    s.last_purchase,

    f.monthly_income,
    f.credit_score,
    f.debt,
    f.risk_status,

    cs.last_ticket,
    cs.ticket_status,
    cs.customer_sentiment,
    cs.support_priority,

    c.has_sales_record,
    c.has_finance_record,
    c.has_support_record,

    c.created_at,
    c.updated_at

FROM customers AS c

LEFT JOIN customer_sales AS s
    ON c.customer_id = s.customer_id

LEFT JOIN customer_finance AS f
    ON c.customer_id = f.customer_id

LEFT JOIN customer_support AS cs
    ON c.customer_id = cs.customer_id;