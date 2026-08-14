-- EconoCausal canonical PostgreSQL schema. Keep this file aligned with
-- contracts/customer_dataset.schema.json; additive production changes also
-- receive a migration in backend/migrations.
CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id SERIAL PRIMARY KEY,
    campaign_name TEXT NOT NULL UNIQUE,
    description TEXT,
    starts_at TIMESTAMPTZ,
    ends_at TIMESTAMPTZ,
    default_discount_percentage DOUBLE PRECISION CHECK (default_discount_percentage BETWEEN 0 AND 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (ends_at IS NULL OR starts_at IS NULL OR ends_at >= starts_at)
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(campaign_id) ON DELETE SET NULL,
    age INTEGER NOT NULL CHECK (age >= 0),
    tenure_months INTEGER NOT NULL CHECK (tenure_months >= 0),
    customer_segment TEXT NOT NULL,
    historical_orders INTEGER NOT NULL CHECK (historical_orders >= 0),
    historical_revenue DOUBLE PRECISION NOT NULL CHECK (historical_revenue >= 0),
    avg_order_value DOUBLE PRECISION NOT NULL CHECK (avg_order_value >= 0),
    days_since_last_purchase INTEGER NOT NULL CHECK (days_since_last_purchase >= 0),
    website_visits INTEGER NOT NULL CHECK (website_visits >= 0),
    email_opens INTEGER NOT NULL CHECK (email_opens >= 0),
    email_clicks INTEGER NOT NULL CHECK (email_clicks >= 0),
    previous_campaign_response INTEGER NOT NULL CHECK (previous_campaign_response >= 0),
    treatment_received INTEGER NOT NULL CHECK (treatment_received IN (0, 1)),
    discount_percentage DOUBLE PRECISION NOT NULL CHECK (discount_percentage BETWEEN 0 AND 1),
    purchase INTEGER NOT NULL CHECK (purchase IN (0, 1)),
    purchase_value DOUBLE PRECISION NOT NULL CHECK (purchase_value >= 0),
    discount_cost DOUBLE PRECISION NOT NULL CHECK (discount_cost >= 0),
    net_revenue DOUBLE PRECISION NOT NULL,
    true_baseline_purchase_probability DOUBLE PRECISION NOT NULL CHECK (true_baseline_purchase_probability BETWEEN 0 AND 1),
    true_treatment_purchase_probability DOUBLE PRECISION NOT NULL CHECK (true_treatment_purchase_probability BETWEEN 0 AND 1),
    true_ite DOUBLE PRECISION NOT NULL,
    true_treatment_probability DOUBLE PRECISION NOT NULL CHECK (true_treatment_probability BETWEEN 0 AND 1),
    CHECK ((treatment_received = 0 AND discount_percentage = 0) OR treatment_received = 1),
    CHECK (purchase = 1 OR purchase_value = 0)
);

CREATE TABLE IF NOT EXISTS model_runs (
    id SERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_version TEXT,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS predictions (
    id BIGSERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    model_run_id INTEGER NOT NULL REFERENCES model_runs(id) ON DELETE CASCADE,
    baseline_probability DOUBLE PRECISION NOT NULL CHECK (baseline_probability BETWEEN 0 AND 1),
    treatment_probability DOUBLE PRECISION NOT NULL CHECK (treatment_probability BETWEEN 0 AND 1),
    ite DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (customer_id, model_run_id)
);

CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    campaign_id INTEGER REFERENCES campaigns(campaign_id) ON DELETE SET NULL,
    model_run_id INTEGER REFERENCES model_runs(id) ON DELETE SET NULL,
    predicted_ite DOUBLE PRECISION,
    recommended_discount DOUBLE PRECISION NOT NULL CHECK (recommended_discount BETWEEN 0 AND 1),
    expected_profit DOUBLE PRECISION NOT NULL,
    expected_cost DOUBLE PRECISION NOT NULL CHECK (expected_cost >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
