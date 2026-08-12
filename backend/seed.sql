-- Seed data for EconoCausal customers table (minimal rows for smoke tests)
INSERT INTO customers (
    customer_id,
    age,
    tenure_months,
    customer_segment,
    historical_orders,
    historical_revenue,
    avg_order_value,
    days_since_last_purchase,
    website_visits,
    email_opens,
    email_clicks,
    previous_campaign_response,
    treatment_received,
    discount_percentage,
    purchase,
    purchase_value,
    discount_cost,
    net_revenue,
    true_baseline_purchase_probability,
    true_treatment_purchase_probability,
    true_ite,
    true_treatment_probability
)
VALUES
    (1, 34, 12, 'standard', 3, 210.0, 70.0, 20, 10, 3, 1, 0, 0, 0.0, 1, 75.0, 0.0, 75.0, 0.05, 0.10, 0.05, 0.30),
    (2, 52, 48, 'premium', 10, 1200.0, 120.0, 5, 25, 8, 4, 1, 1, 0.10, 1, 150.0, 15.0, 135.0, 0.08, 0.30, 0.22, 0.72);
