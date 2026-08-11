CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    age INTEGER,
    tenure_months INTEGER,
    customer_segment TEXT,
    historical_orders INTEGER,
    historical_revenue DOUBLE PRECISION,
    avg_order_value DOUBLE PRECISION,
    days_since_last_purchase INTEGER,
    website_visits INTEGER,
    email_opens INTEGER,
    email_clicks INTEGER,
    previous_campaign_response INTEGER,
    treatment_received INTEGER,
    discount_percentage DOUBLE PRECISION,
    purchase INTEGER,
    purchase_value DOUBLE PRECISION,
    discount_cost DOUBLE PRECISION,
    net_revenue DOUBLE PRECISION,
    true_baseline_purchase_probability DOUBLE PRECISION,
    true_treatment_purchase_probability DOUBLE PRECISION,
    true_ite DOUBLE PRECISION,
    true_treatment_probability DOUBLE PRECISION
);

CREATE TABLE IF NOT EXISTS model_runs (
    id SERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metrics JSONB
);

CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    recommended_discount DOUBLE PRECISION,
    expected_profit DOUBLE PRECISION,
    expected_cost DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
