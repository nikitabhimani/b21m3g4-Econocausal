-- Views for dashboard and summaries

-- Customer summary: counts and rates
CREATE OR REPLACE VIEW customer_summary AS
SELECT
    COUNT(*) AS customers,
    SUM(CASE WHEN treatment_received = 1 THEN 1 ELSE 0 END) AS treated_customers,
    SUM(CASE WHEN treatment_received = 0 THEN 1 ELSE 0 END) AS control_customers,
    AVG(treatment_received::int) AS treatment_rate,
    AVG(purchase::int) AS purchase_rate,
    AVG(CASE WHEN treatment_received = 1 THEN purchase::int END) AS treated_purchase_rate,
    AVG(CASE WHEN treatment_received = 0 THEN purchase::int END) AS control_purchase_rate,
    AVG(true_ite) AS average_true_ite,
    SUM(purchase_value) AS total_revenue,
    SUM(discount_cost) AS total_discount_cost
FROM customers;

-- Revenue summary grouped by segment
CREATE OR REPLACE VIEW revenue_summary AS
SELECT
    customer_segment,
    COUNT(*) AS customers,
    SUM(purchase_value) AS total_revenue,
    AVG(purchase_value) AS avg_purchase_value,
    SUM(discount_cost) AS total_discount_cost
FROM customers
GROUP BY customer_segment;
