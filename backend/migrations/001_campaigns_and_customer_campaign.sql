-- Safe upgrade for databases created before campaigns existed.
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

ALTER TABLE customers ADD COLUMN IF NOT EXISTS campaign_id INTEGER;
ALTER TABLE customers DROP CONSTRAINT IF EXISTS customers_campaign_id_fkey;
ALTER TABLE customers ADD CONSTRAINT customers_campaign_id_fkey
    FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id) ON DELETE SET NULL;
