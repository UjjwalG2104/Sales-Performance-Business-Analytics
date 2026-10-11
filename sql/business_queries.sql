-- ==============================================================================
-- SalesIQ: 15 Core SQL Business Analytics Queries
-- Demonstrating Aggregations, Joins, Group By, Subqueries, CTEs & Window Functions
-- ==============================================================================

-- [QUERY 1]: Total Sales, Total Profit, and Overall Profit Margin
-- Purpose: Executive summary metric calculation
SELECT 
    ROUND(SUM(sales), 2) AS total_revenue,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND((SUM(profit) / NULLIF(SUM(sales), 0)) * 100, 2) AS profit_margin_pct,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(quantity) AS total_units_sold
FROM fact_orders;

-- [QUERY 2]: Monthly Revenue & Profit Aggregation
-- Purpose: Time series revenue and profitability tracking
SELECT 
    STRFTIME('%Y-%m', order_date) AS order_month,
    ROUND(SUM(sales), 2) AS monthly_revenue,
    ROUND(SUM(profit), 2) AS monthly_profit,
    COUNT(DISTINCT order_id) AS orders_count
FROM fact_orders
GROUP BY STRFTIME('%Y-%m', order_date)
ORDER BY order_month ASC;

-- [QUERY 3]: Top 10 Products by Revenue
-- Purpose: Identify flagship revenue generators
SELECT 
    p.product_id,
    p.product_name,
    p.category,
    p.sub_category,
    ROUND(SUM(f.sales), 2) AS total_sales,
    ROUND(SUM(f.profit), 2) AS total_profit,
    SUM(f.quantity) AS total_units
FROM fact_orders f
JOIN dim_products p ON f.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category, p.sub_category
ORDER BY total_sales DESC
LIMIT 10;

-- [QUERY 4]: Top 10 Customers by Sales and Their Profitability
-- Purpose: Identify high-value enterprise/retail accounts
SELECT 
    c.customer_id,
    c.customer_name,
    c.segment,
    COUNT(DISTINCT f.order_id) AS orders_placed,
    ROUND(SUM(f.sales), 2) AS total_spend,
    ROUND(SUM(f.profit), 2) AS total_profit_generated,
    ROUND((SUM(f.profit) / NULLIF(SUM(f.sales), 0)) * 100, 2) AS customer_margin_pct
FROM fact_orders f
JOIN dim_customers c ON f.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name, c.segment
ORDER BY total_spend DESC
LIMIT 10;

-- [QUERY 5]: Revenue and Profitability Breakdown by Geographic Region
-- Purpose: Assess regional operational performance
SELECT 
    l.region,
    COUNT(DISTINCT f.order_id) AS order_count,
    ROUND(SUM(f.sales), 2) AS regional_revenue,
    ROUND(SUM(f.profit), 2) AS regional_profit,
    ROUND((SUM(f.profit) / NULLIF(SUM(f.sales), 0)) * 100, 2) AS regional_margin_pct
FROM fact_orders f
JOIN dim_locations l ON f.location_id = l.location_id
GROUP BY l.region
ORDER BY regional_revenue DESC;

-- [QUERY 6]: Profit and Margin by Product Category & Sub-Category
-- Purpose: Product portfolio health analysis
SELECT 
    p.category,
    p.sub_category,
    ROUND(SUM(f.sales), 2) AS total_sales,
    ROUND(SUM(f.profit), 2) AS total_profit,
    ROUND((SUM(f.profit) / NULLIF(SUM(f.sales), 0)) * 100, 2) AS profit_margin_pct
FROM fact_orders f
JOIN dim_products p ON f.product_id = p.product_id
GROUP BY p.category, p.sub_category
ORDER BY p.category ASC, total_profit DESC;

-- [QUERY 7]: Products Generating Net Losses (Negative Profit Items)
-- Purpose: Identify margin bleeders and toxic discounting
SELECT 
    p.product_id,
    p.product_name,
    p.category,
    p.sub_category,
    ROUND(SUM(f.sales), 2) AS sales_volume,
    ROUND(SUM(f.profit), 2) AS net_loss,
    ROUND(AVG(f.discount) * 100, 1) AS avg_discount_pct,
    SUM(f.quantity) AS units_sold
FROM fact_orders f
JOIN dim_products p ON f.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category, p.sub_category
HAVING SUM(f.profit) < 0
ORDER BY net_loss ASC
LIMIT 15;

-- [QUERY 8]: Average Order Value (AOV) by Customer Segment
-- Purpose: Segment basket size analysis
WITH order_totals AS (
    SELECT 
        f.order_id,
        c.segment,
        SUM(f.sales) AS order_revenue
    FROM fact_orders f
    JOIN dim_customers c ON f.customer_id = c.customer_id
    GROUP BY f.order_id, c.segment
)
SELECT 
    segment,
    COUNT(order_id) AS distinct_orders,
    ROUND(SUM(order_revenue), 2) AS total_segment_sales,
    ROUND(AVG(order_revenue), 2) AS average_order_value
FROM order_totals
GROUP BY segment
ORDER BY average_order_value DESC;

-- [QUERY 9]: Category-Wise Sales Contribution Percentage
-- Purpose: Portfolio share of wallet computation using subqueries
SELECT 
    p.category,
    ROUND(SUM(f.sales), 2) AS category_revenue,
    ROUND(
        (SUM(f.sales) * 100.0) / (SELECT SUM(sales) FROM fact_orders), 
        2
    ) AS contribution_percentage
FROM fact_orders f
JOIN dim_products p ON f.product_id = p.product_id
GROUP BY p.category
ORDER BY category_revenue DESC;

-- [QUERY 10]: Month-Over-Month (MoM) Revenue Growth Rate
-- Purpose: Window functions (LAG) to monitor periodic momentum
WITH monthly_sales AS (
    SELECT 
        STRFTIME('%Y-%m', order_date) AS month,
        ROUND(SUM(sales), 2) AS current_sales
    FROM fact_orders
    GROUP BY STRFTIME('%Y-%m', order_date)
)
SELECT 
    month,
    current_sales,
    LAG(current_sales, 1) OVER (ORDER BY month) AS prior_month_sales,
    ROUND(
        ((current_sales - LAG(current_sales, 1) OVER (ORDER BY month)) / 
        NULLIF(LAG(current_sales, 1) OVER (ORDER BY month), 0)) * 100.0,
        2
    ) AS mom_growth_pct
FROM monthly_sales
ORDER BY month ASC;

-- [QUERY 11]: Year-Over-Year (YoY) Revenue Comparison by Quarter
-- Purpose: Annualized growth tracking across quarters
WITH quarterly_data AS (
    SELECT 
        STRFTIME('%Y', order_date) AS sales_year,
        'Q' || ((CAST(STRFTIME('%m', order_date) AS INTEGER) + 2) / 3) AS quarter,
        SUM(sales) AS quarter_sales
    FROM fact_orders
    GROUP BY sales_year, quarter
)
SELECT 
    q1.sales_year,
    q1.quarter,
    ROUND(q1.quarter_sales, 2) AS current_quarter_sales,
    ROUND(q2.quarter_sales, 2) AS prev_year_quarter_sales,
    ROUND(
        ((q1.quarter_sales - q2.quarter_sales) / NULLIF(q2.quarter_sales, 0)) * 100.0, 
        2
    ) AS yoy_growth_pct
FROM quarterly_data q1
LEFT JOIN quarterly_data q2 
    ON q1.quarter = q2.quarter 
    AND CAST(q1.sales_year AS INTEGER) = CAST(q2.sales_year AS INTEGER) + 1
ORDER BY q1.sales_year DESC, q1.quarter DESC;

-- [QUERY 12]: Product Ranking within Categories using Window Function (DENSE_RANK)
-- Purpose: Identify leaders and laggards within each product vertical
WITH product_sales AS (
    SELECT 
        p.category,
        p.product_name,
        ROUND(SUM(f.sales), 2) AS sales_amount,
        ROUND(SUM(f.profit), 2) AS profit_amount
    FROM fact_orders f
    JOIN dim_products p ON f.product_id = p.product_id
    GROUP BY p.category, p.product_name
)
SELECT 
    category,
    product_name,
    sales_amount,
    profit_amount,
    DENSE_RANK() OVER (PARTITION BY category ORDER BY sales_amount DESC) AS category_rank
FROM product_sales
ORDER BY category, category_rank ASC;

-- [QUERY 13]: Running Cumulative Total of Monthly Sales
-- Purpose: Cumulative burn-up tracking via Window Function (SUM OVER)
WITH monthly_summary AS (
    SELECT 
        STRFTIME('%Y-%m', order_date) AS sales_month,
        ROUND(SUM(sales), 2) AS monthly_sales
    FROM fact_orders
    GROUP BY STRFTIME('%Y-%m', order_date)
)
SELECT 
    sales_month,
    monthly_sales,
    ROUND(SUM(monthly_sales) OVER (ORDER BY sales_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS cumulative_sales
FROM monthly_summary
ORDER BY sales_month ASC;

-- [QUERY 14]: Customer RFM Proxy: Total Spend, Order Count & Recency Ranking
-- Purpose: Window ranking to segment VIP customers
WITH customer_aggregates AS (
    SELECT 
        c.customer_id,
        c.customer_name,
        c.segment,
        COUNT(DISTINCT f.order_id) AS total_orders,
        ROUND(SUM(f.sales), 2) AS total_spend,
        MAX(f.order_date) AS last_order_date
    FROM fact_orders f
    JOIN dim_customers c ON f.customer_id = c.customer_id
    GROUP BY c.customer_id, c.customer_name, c.segment
)
SELECT 
    customer_name,
    segment,
    total_orders,
    total_spend,
    last_order_date,
    NTILE(4) OVER (ORDER BY total_spend DESC) AS spend_quartile,
    RANK() OVER (ORDER BY total_spend DESC) AS revenue_rank
FROM customer_aggregates
ORDER BY revenue_rank ASC
LIMIT 20;

-- [QUERY 15]: Detailed Sales and Profit Comparison Across Shipping Costs & Discounts
-- Purpose: Complex multi-table join evaluating unit economics
SELECT 
    p.category,
    l.region,
    ROUND(SUM(f.sales), 2) AS gross_sales,
    ROUND(SUM(f.profit), 2) AS net_profit,
    ROUND(AVG(f.discount) * 100, 1) AS avg_discount_pct,
    ROUND(SUM(f.shipping_cost), 2) AS total_shipping_costs,
    ROUND((SUM(f.profit) / NULLIF(SUM(f.sales), 0)) * 100, 2) AS margin_pct
FROM fact_orders f
JOIN dim_products p ON f.product_id = p.product_id
JOIN dim_locations l ON f.location_id = l.location_id
GROUP BY p.category, l.region
ORDER BY p.category, net_profit DESC;
