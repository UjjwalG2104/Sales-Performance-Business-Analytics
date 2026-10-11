-- ==============================================================================
-- SalesIQ Database Schema (SQLite)
-- Relational Schema with Dimensional & Fact Tables + Analytical Views
-- ==============================================================================

PRAGMA foreign_keys = ON;

-- 1. Customers Dimension
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    segment TEXT NOT NULL
);

-- 2. Locations Dimension
CREATE TABLE IF NOT EXISTS dim_locations (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    country TEXT NOT NULL,
    region TEXT NOT NULL,
    state TEXT NOT NULL,
    city TEXT NOT NULL,
    postal_code TEXT,
    UNIQUE(country, region, state, city, postal_code)
);

-- 3. Products Dimension
CREATE TABLE IF NOT EXISTS dim_products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT NOT NULL
);

-- 4. Sales Orders Fact Table
CREATE TABLE IF NOT EXISTS fact_orders (
    order_line_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    order_date DATE NOT NULL,
    ship_date DATE,
    customer_id TEXT NOT NULL,
    location_id INTEGER NOT NULL,
    product_id TEXT NOT NULL,
    sales REAL NOT NULL,
    quantity INTEGER NOT NULL,
    discount REAL NOT NULL DEFAULT 0.0,
    profit REAL NOT NULL,
    shipping_cost REAL DEFAULT 0.0,
    FOREIGN KEY (customer_id) REFERENCES dim_customers (customer_id),
    FOREIGN KEY (location_id) REFERENCES dim_locations (location_id),
    FOREIGN KEY (product_id) REFERENCES dim_products (product_id)
);

-- Create Indexes for Query Performance
CREATE INDEX IF NOT EXISTS idx_orders_order_date ON fact_orders (order_date);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON fact_orders (customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_location_id ON fact_orders (location_id);
CREATE INDEX IF NOT EXISTS idx_orders_product_id ON fact_orders (product_id);

-- 5. Unified Analytical View for Reporting & Window Functions
CREATE VIEW IF NOT EXISTS v_sales_analytics AS
SELECT 
    f.order_line_id,
    f.order_id,
    f.order_date,
    f.ship_date,
    c.customer_id,
    c.customer_name,
    c.segment,
    l.country,
    l.region,
    l.state,
    l.city,
    l.postal_code,
    p.product_id,
    p.product_name,
    p.category,
    p.sub_category,
    f.sales,
    f.quantity,
    f.discount,
    f.profit,
    f.shipping_cost,
    ROUND((f.profit / NULLIF(f.sales, 0)) * 100, 2) AS profit_margin_pct
FROM fact_orders f
JOIN dim_customers c ON f.customer_id = c.customer_id
JOIN dim_locations l ON f.location_id = l.location_id
JOIN dim_products p ON f.product_id = p.product_id;
