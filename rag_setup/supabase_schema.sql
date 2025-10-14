-- ===================================================
-- Supabase Schema for Rappi Analytics
-- ===================================================
-- Execute this in Supabase SQL Editor before running migrate_to_supabase.py
--
-- This creates 2 tables:
-- 1. metrics_input - All business metrics (Perfect Orders, Lead Penetration, etc.)
-- 2. orders - Order counts per zone
-- ===================================================

-- ===================================================
-- Table 1: metrics_input
-- ===================================================
-- Contains all business metrics with time series data (L0W to L8W)

CREATE TABLE IF NOT EXISTS metrics_input (
    id BIGSERIAL PRIMARY KEY,
    country VARCHAR(10),        -- Country code: MX, CO, BR, CL, AR, PE, EC, CR, UY
    city VARCHAR(100),          -- City name
    zone VARCHAR(200),          -- Zone name
    zone_type VARCHAR(50),      -- Zone classification (Wealthy, Non Wealthy, etc.)
    metric VARCHAR(100),        -- Metric name (Perfect Orders, Lead Penetration, etc.)
    l0w_value NUMERIC(10,4),    -- Current week value
    l1w_value NUMERIC(10,4),    -- 1 week ago
    l2w_value NUMERIC(10,4),    -- 2 weeks ago
    l3w_value NUMERIC(10,4),    -- 3 weeks ago
    l4w_value NUMERIC(10,4),    -- 4 weeks ago
    l5w_value NUMERIC(10,4),    -- 5 weeks ago
    l6w_value NUMERIC(10,4),    -- 6 weeks ago
    l7w_value NUMERIC(10,4),    -- 7 weeks ago
    l8w_value NUMERIC(10,4),    -- 8 weeks ago
    created_at TIMESTAMP DEFAULT NOW()
);

-- Unique constraint for UPSERT (prevents duplicates)
-- This allows upsert on country+zone+metric combination
CREATE UNIQUE INDEX IF NOT EXISTS idx_metrics_input_unique
    ON metrics_input(country, zone, metric)
    WHERE country IS NOT NULL AND zone IS NOT NULL AND metric IS NOT NULL;

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_metrics_input_metric ON metrics_input(metric);
CREATE INDEX IF NOT EXISTS idx_metrics_input_country ON metrics_input(country);
CREATE INDEX IF NOT EXISTS idx_metrics_input_zone ON metrics_input(zone);
CREATE INDEX IF NOT EXISTS idx_metrics_input_country_metric ON metrics_input(country, metric);

-- Comments
COMMENT ON TABLE metrics_input IS 'All business metrics with time series data (L0W-L8W)';
COMMENT ON COLUMN metrics_input.metric IS 'Metric name - MUST be filtered in all queries';
COMMENT ON COLUMN metrics_input.l0w_value IS 'Current week value';
COMMENT ON COLUMN metrics_input.l8w_value IS '8 weeks ago value';


-- ===================================================
-- Table 2: orders
-- ===================================================
-- Contains order counts per zone with time series data (L0W to L8W)

CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    country VARCHAR(10),        -- Country code
    city VARCHAR(100),          -- City name
    zone VARCHAR(200),          -- Zone name
    l0w INTEGER,                -- Current week order count
    l1w INTEGER,                -- 1 week ago order count
    l2w INTEGER,                -- 2 weeks ago
    l3w INTEGER,                -- 3 weeks ago
    l4w INTEGER,                -- 4 weeks ago
    l5w INTEGER,                -- 5 weeks ago
    l6w INTEGER,                -- 6 weeks ago
    l7w INTEGER,                -- 7 weeks ago
    l8w INTEGER,                -- 8 weeks ago
    created_at TIMESTAMP DEFAULT NOW()
);

-- Unique constraint for UPSERT (prevents duplicates)
-- This allows upsert on country+zone combination
CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_unique
    ON orders(country, zone)
    WHERE country IS NOT NULL AND zone IS NOT NULL;

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_orders_country ON orders(country);
CREATE INDEX IF NOT EXISTS idx_orders_zone ON orders(zone);
CREATE INDEX IF NOT EXISTS idx_orders_country_zone ON orders(country, zone);

-- Comments
COMMENT ON TABLE orders IS 'Order counts per zone with time series data (L0W-L8W)';
COMMENT ON COLUMN orders.l0w IS 'Current week order count';
COMMENT ON COLUMN orders.l8w IS '8 weeks ago order count';


-- ===================================================
-- Row Level Security (RLS)
-- ===================================================
-- Enable RLS for both tables

ALTER TABLE metrics_input ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Create policies for authenticated users
CREATE POLICY "Enable read access for authenticated users" ON metrics_input
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Enable insert access for authenticated users" ON metrics_input
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Enable read access for authenticated users" ON orders
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Enable insert access for authenticated users" ON orders
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');


-- ===================================================
-- Sample Queries
-- ===================================================

-- Top 5 zones by Perfect Orders
-- SELECT zone, country, l0w_value as perfect_order_rate
-- FROM metrics_input
-- WHERE metric = 'Perfect Orders'
--   AND l0w_value IS NOT NULL
-- ORDER BY l0w_value DESC
-- LIMIT 5;

-- Average Pro Adoption by country
-- SELECT country,
--        AVG(l0w_value) as avg_pro_adoption,
--        COUNT(DISTINCT zone) as num_zones
-- FROM metrics_input
-- WHERE metric = 'Pro Adoption'
--   AND l0w_value IS NOT NULL
-- GROUP BY country
-- ORDER BY avg_pro_adoption DESC;

-- Total orders by country (current week)
-- SELECT country,
--        SUM(l0w) as total_orders_l0w,
--        COUNT(*) as num_zones
-- FROM orders
-- WHERE l0w IS NOT NULL
-- GROUP BY country
-- ORDER BY total_orders_l0w DESC;


-- ===================================================
-- Verification
-- ===================================================

-- Check table structure
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'metrics_input'
-- ORDER BY ordinal_position;

-- Count records
-- SELECT
--     (SELECT COUNT(*) FROM metrics_input) as metrics_count,
--     (SELECT COUNT(*) FROM orders) as orders_count;
