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

ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS campaign_id INTEGER;
ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS model_run_id INTEGER;
ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS predicted_ite DOUBLE PRECISION;
ALTER TABLE recommendations DROP CONSTRAINT IF EXISTS recommendations_campaign_id_fkey;
ALTER TABLE recommendations ADD CONSTRAINT recommendations_campaign_id_fkey
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id) ON DELETE SET NULL;
ALTER TABLE recommendations DROP CONSTRAINT IF EXISTS recommendations_model_run_id_fkey;
ALTER TABLE recommendations ADD CONSTRAINT recommendations_model_run_id_fkey
    FOREIGN KEY (model_run_id) REFERENCES model_runs(id) ON DELETE SET NULL;
