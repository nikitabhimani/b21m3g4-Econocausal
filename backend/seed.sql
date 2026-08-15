-- Idempotent seed data for EconoCausal smoke tests.
INSERT INTO campaigns (campaign_id, campaign_name, description, default_discount_percentage)
VALUES (1, 'seed-discount-campaign', 'Minimal campaign used by smoke tests', 0.10)
ON CONFLICT (campaign_id) DO UPDATE SET
    campaign_name = EXCLUDED.campaign_name,
    description = EXCLUDED.description,
    default_discount_percentage = EXCLUDED.default_discount_percentage;

INSERT INTO customers (
    customer_id, campaign_id,
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
    (1, 1, 34, 12, 'standard', 3, 210.0, 70.0, 20, 10, 3, 1, 0, 0, 0.0, 1, 75.0, 0.0, 75.0, 0.05, 0.10, 0.05, 0.30),
    (2, 1, 52, 48, 'premium', 10, 1200.0, 120.0, 5, 25, 8, 4, 1, 1, 0.10, 1, 150.0, 15.0, 135.0, 0.08, 0.30, 0.22, 0.72)
ON CONFLICT (customer_id) DO UPDATE SET
    campaign_id = EXCLUDED.campaign_id,
    age = EXCLUDED.age,
    tenure_months = EXCLUDED.tenure_months,
    customer_segment = EXCLUDED.customer_segment,
    historical_orders = EXCLUDED.historical_orders,
    historical_revenue = EXCLUDED.historical_revenue,
    avg_order_value = EXCLUDED.avg_order_value,
    days_since_last_purchase = EXCLUDED.days_since_last_purchase,
    website_visits = EXCLUDED.website_visits,
    email_opens = EXCLUDED.email_opens,
    email_clicks = EXCLUDED.email_clicks,
    previous_campaign_response = EXCLUDED.previous_campaign_response,
    treatment_received = EXCLUDED.treatment_received,
    discount_percentage = EXCLUDED.discount_percentage,
    purchase = EXCLUDED.purchase,
    purchase_value = EXCLUDED.purchase_value,
    discount_cost = EXCLUDED.discount_cost,
    net_revenue = EXCLUDED.net_revenue,
    true_baseline_purchase_probability = EXCLUDED.true_baseline_purchase_probability,
    true_treatment_purchase_probability = EXCLUDED.true_treatment_purchase_probability,
    true_ite = EXCLUDED.true_ite,
    true_treatment_probability = EXCLUDED.true_treatment_probability;

SELECT setval(pg_get_serial_sequence('campaigns', 'campaign_id'), COALESCE((SELECT MAX(campaign_id) FROM campaigns), 1), true);
