-- =========================================================
-- ENTERPRISE CUSTOMER DATA HUB
-- DAY 12: SQL ANALYTICS
-- =========================================================
--
-- Purpose:
-- Run business-oriented analytics against the
-- PostgreSQL customer data hub.
--
-- Core questions:
-- 1. Which customers are missing Finance records?
-- 2. Are duplicate customer emails present?
-- 3. Which customers have the highest lifetime value?
-- 4. What is the average customer credit score?
--
-- Additional analysis:
-- 5. Customer source coverage
-- 6. Financial risk distribution
-- 7. Open support cases
-- 8. Customers requiring potential attention
-- 9. Customer 360 overview
--
-- =========================================================


-- =========================================================
-- 1. CUSTOMER COUNTS
-- =========================================================

SELECT
    COUNT(*) AS total_customers
FROM customers;


-- =========================================================
-- 2. CUSTOMERS MISSING FINANCE RECORDS
-- =========================================================
--
-- Business question:
-- Which canonical customers do not have Finance data?
--
-- LEFT JOIN keeps every customer.
-- WHERE f.customer_id IS NULL isolates customers with
-- no matching Finance record.
-- =========================================================

SELECT
    c.customer_id,
    c.name,
    c.email,
    c.customer_status
FROM customers AS c

LEFT JOIN customer_finance AS f
    ON c.customer_id = f.customer_id

WHERE f.customer_id IS NULL

ORDER BY
    c.customer_id;


-- =========================================================
-- 3. COUNT CUSTOMERS MISSING FINANCE RECORDS
-- =========================================================

SELECT
    COUNT(*) AS customers_missing_finance
FROM customers AS c

LEFT JOIN customer_finance AS f
    ON c.customer_id = f.customer_id

WHERE f.customer_id IS NULL;


-- =========================================================
-- 4. DUPLICATE EMAILS
-- =========================================================
--
-- LOWER() makes the comparison case-insensitive.
--
-- Example:
-- JOHN@EMAIL.COM
-- john@email.com
--
-- would be treated as the same email.
--
-- HAVING is used after GROUP BY to filter groups.
-- =========================================================

SELECT
    LOWER(email) AS normalized_email,
    COUNT(*) AS customer_count
FROM customers

WHERE email IS NOT NULL
AND TRIM(email) <> ''

GROUP BY
    LOWER(email)

HAVING COUNT(*) > 1

ORDER BY
    customer_count DESC,
    normalized_email;


-- =========================================================
-- 5. DUPLICATE EMAIL DETAIL
-- =========================================================
--
-- Shows the actual customer records associated with
-- duplicate emails.
-- =========================================================

WITH duplicate_emails AS (

    SELECT
        LOWER(email) AS normalized_email

    FROM customers

    WHERE email IS NOT NULL
    AND TRIM(email) <> ''

    GROUP BY
        LOWER(email)

    HAVING COUNT(*) > 1
)

SELECT
    c.customer_id,
    c.name,
    c.email,
    c.customer_status

FROM customers AS c

INNER JOIN duplicate_emails AS d
    ON LOWER(c.email) = d.normalized_email

ORDER BY
    LOWER(c.email),
    c.customer_id;


-- =========================================================
-- 6. HIGHEST LIFETIME VALUE CUSTOMERS
-- =========================================================
--
-- Returns the highest-value customers based on
-- consolidated Sales data.
-- =========================================================

SELECT
    c.customer_id,
    c.name,
    s.total_orders,
    s.lifetime_value,
    s.last_purchase

FROM customers AS c

INNER JOIN customer_sales AS s
    ON c.customer_id = s.customer_id

WHERE s.lifetime_value IS NOT NULL

ORDER BY
    s.lifetime_value DESC

LIMIT 10;


-- =========================================================
-- 7. AVERAGE CREDIT SCORE
-- =========================================================
--
-- AVG automatically ignores NULL values.
--
-- ROUND returns a cleaner business-readable result.
-- =========================================================

SELECT
    ROUND(
        AVG(credit_score),
        2
    ) AS average_credit_score

FROM customer_finance

WHERE credit_score IS NOT NULL;


-- =========================================================
-- 8. CREDIT SCORE SUMMARY
-- =========================================================
--
-- Provides more context than the average alone.
-- =========================================================

SELECT
    COUNT(credit_score) AS customers_with_credit_score,

    ROUND(
        AVG(credit_score),
        2
    ) AS average_credit_score,

    MIN(credit_score) AS minimum_credit_score,

    MAX(credit_score) AS maximum_credit_score

FROM customer_finance;


-- =========================================================
-- 9. CUSTOMER SOURCE COVERAGE
-- =========================================================
--
-- Shows how many canonical customers have records
-- available from each departmental system.
-- =========================================================

SELECT
    COUNT(*) AS total_customers,

    COUNT(*) FILTER (
        WHERE has_sales_record = TRUE
    ) AS customers_with_sales,

    COUNT(*) FILTER (
        WHERE has_finance_record = TRUE
    ) AS customers_with_finance,

    COUNT(*) FILTER (
        WHERE has_support_record = TRUE
    ) AS customers_with_support,

    COUNT(*) FILTER (
        WHERE
            has_sales_record = TRUE
            AND has_finance_record = TRUE
            AND has_support_record = TRUE
    ) AS customers_with_complete_coverage

FROM customers;


-- =========================================================
-- 10. CUSTOMERS WITH INCOMPLETE SOURCE COVERAGE
-- =========================================================

SELECT
    customer_id,
    name,
    has_sales_record,
    has_finance_record,
    has_support_record

FROM customers

WHERE
    has_sales_record = FALSE
    OR has_finance_record = FALSE
    OR has_support_record = FALSE

ORDER BY
    customer_id;


-- =========================================================
-- 11. FINANCIAL RISK DISTRIBUTION
-- =========================================================
--
-- Shows how customers are distributed across
-- Finance risk categories.
-- =========================================================

SELECT
    COALESCE(
        risk_status,
        'missing'
    ) AS risk_status,

    COUNT(*) AS customer_count

FROM customer_finance

GROUP BY
    risk_status

ORDER BY
    customer_count DESC;


-- =========================================================
-- 12. HIGH-RISK CUSTOMERS
-- =========================================================

SELECT
    c.customer_id,
    c.name,
    f.credit_score,
    f.monthly_income,
    f.debt,
    f.risk_status

FROM customers AS c

INNER JOIN customer_finance AS f
    ON c.customer_id = f.customer_id

WHERE f.risk_status = 'high'

ORDER BY
    f.debt DESC NULLS LAST;


-- =========================================================
-- 13. AVERAGE LIFETIME VALUE
-- =========================================================

SELECT
    ROUND(
        AVG(lifetime_value),
        2
    ) AS average_lifetime_value

FROM customer_sales

WHERE lifetime_value IS NOT NULL;


-- =========================================================
-- 14. SALES PERFORMANCE SUMMARY
-- =========================================================

SELECT
    COUNT(*) AS customers_with_sales,

    SUM(total_orders) AS total_orders,

    ROUND(
        SUM(lifetime_value),
        2
    ) AS total_lifetime_value,

    ROUND(
        AVG(lifetime_value),
        2
    ) AS average_lifetime_value

FROM customer_sales;


-- =========================================================
-- 15. OPEN OR PENDING SUPPORT CASES
-- =========================================================

SELECT
    c.customer_id,
    c.name,
    s.last_ticket,
    s.ticket_status,
    s.customer_sentiment,
    s.support_priority

FROM customers AS c

INNER JOIN customer_support AS s
    ON c.customer_id = s.customer_id

WHERE s.ticket_status IN (
    'open',
    'pending'
)

ORDER BY
    CASE s.support_priority

        WHEN 'high'
            THEN 1

        WHEN 'medium'
            THEN 2

        WHEN 'low'
            THEN 3

        ELSE 4

    END,

    c.customer_id;


-- =========================================================
-- 16. HIGH-RISK CUSTOMERS WITH OPEN SUPPORT ISSUES
-- =========================================================
--
-- This query combines Finance and Support information.
--
-- It identifies customers who:
-- - Are financially high risk
-- - Have an open or pending support case
--
-- This demonstrates cross-domain analytics.
-- =========================================================

SELECT
    c.customer_id,
    c.name,

    f.credit_score,
    f.debt,
    f.risk_status,

    s.last_ticket,
    s.ticket_status,
    s.support_priority

FROM customers AS c

INNER JOIN customer_finance AS f
    ON c.customer_id = f.customer_id

INNER JOIN customer_support AS s
    ON c.customer_id = s.customer_id

WHERE
    f.risk_status = 'high'

AND s.ticket_status IN (
    'open',
    'pending'
)

ORDER BY
    f.debt DESC NULLS LAST;


-- =========================================================
-- 17. HIGH-VALUE CUSTOMERS WITH ACTIVE SUPPORT ISSUES
-- =========================================================
--
-- Demonstrates combining Sales and Support data.
-- =========================================================

SELECT
    c.customer_id,
    c.name,

    sales.lifetime_value,
    sales.total_orders,

    support.last_ticket,
    support.ticket_status,
    support.support_priority

FROM customers AS c

INNER JOIN customer_sales AS sales
    ON c.customer_id = sales.customer_id

INNER JOIN customer_support AS support
    ON c.customer_id = support.customer_id

WHERE support.ticket_status IN (
    'open',
    'pending'
)

ORDER BY
    sales.lifetime_value DESC NULLS LAST;


-- =========================================================
-- 18. CUSTOMER 360 ANALYTICS VIEW
-- =========================================================
--
-- The customer_360 view was created on Day 11.
--
-- This demonstrates how a business analyst can query
-- the integrated profile without manually recreating
-- all three joins.
-- =========================================================

SELECT
    customer_id,
    name,
    customer_status,

    total_orders,
    lifetime_value,

    credit_score,
    debt,
    risk_status,

    last_ticket,
    ticket_status,
    support_priority

FROM customer_360

ORDER BY
    customer_id;


-- =========================================================
-- 19. CUSTOMER 360: MOST COMPLETE HIGH-VALUE CUSTOMERS
-- =========================================================

SELECT
    customer_id,
    name,
    lifetime_value,
    credit_score,
    risk_status,
    ticket_status

FROM customer_360

WHERE
    has_sales_record = TRUE
    AND has_finance_record = TRUE
    AND has_support_record = TRUE

ORDER BY
    lifetime_value DESC NULLS LAST

LIMIT 10;


-- =========================================================
-- END OF DAY 12 ANALYTICS
-- =========================================================