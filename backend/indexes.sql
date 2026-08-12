-- Recommended indexes for customers table

-- Index on treatment flag for fast aggregation / filters
CREATE INDEX IF NOT EXISTS idx_customers_treatment_received
ON customers (treatment_received);

-- Index on purchase flag
CREATE INDEX IF NOT EXISTS idx_customers_purchase
ON customers (purchase);

-- Index on customer_segment for segment-level queries
CREATE INDEX IF NOT EXISTS idx_customers_segment
ON customers (customer_segment);

-- Index on purchase_value for range queries
CREATE INDEX IF NOT EXISTS idx_customers_purchase_value
ON customers (purchase_value);
