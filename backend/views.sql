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

-- Campaign-level view. Customers not associated with a campaign appear under
-- a stable "unassigned" label, so the generated v1 dataset remains visible.
CREATE OR REPLACE VIEW campaign_summary AS
SELECT
    COALESCE(ca.campaign_id, 0) AS campaign_id,
    COALESCE(ca.campaign_name, 'unassigned') AS campaign_name,
    COUNT(c.customer_id) AS customers,
    COUNT(c.customer_id) FILTER (WHERE c.treatment_received = 1) AS treated_customers,
    COALESCE(SUM(c.purchase_value), 0) AS total_revenue,
    COALESCE(SUM(c.discount_cost), 0) AS total_discount_cost,
    COALESCE(SUM(c.net_revenue), 0) AS total_net_revenue
FROM customers c
LEFT JOIN campaigns ca ON ca.campaign_id = c.campaign_id
GROUP BY ca.campaign_id, ca.campaign_name;

CREATE OR REPLACE VIEW treatment_summary AS
SELECT
    treatment_received,
    COUNT(*) AS customers,
    AVG(purchase::int) AS purchase_rate,
    AVG(discount_percentage) AS avg_discount_percentage,
    AVG(true_ite) AS avg_true_ite,
    COALESCE(SUM(purchase_value), 0) AS total_revenue,
    COALESCE(SUM(discount_cost), 0) AS total_discount_cost,
    COALESCE(SUM(net_revenue), 0) AS total_net_revenue
FROM customers
GROUP BY treatment_received;
