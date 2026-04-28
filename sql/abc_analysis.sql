CREATE OR REPLACE VIEW v_abc_analysis AS
WITH product_revenue AS (
    SELECT
        p.product_id,
        MAX(p.name) AS product_name,
        MAX(p.category) AS category,
        SUM(foi.quantity * p.base_price * (1 - foi.discount_pct / 100.0)) AS total_revenue
    FROM fact_orders_item foi
    JOIN dim_product p ON foi.product_key = p.product_key
    GROUP BY p.product_id
),
revenue_with_share AS (
    SELECT
        *,
        total_revenue / SUM(total_revenue) OVER () AS revenue_share
    FROM product_revenue
),
revenue_cumulative AS (
    SELECT
        *,
        SUM(revenue_share) OVER (ORDER BY total_revenue DESC) AS cumulative_share
    FROM revenue_with_share
)
SELECT
    product_id,
    product_name,
    category,
    total_revenue,
    revenue_share,
    cumulative_share,
    CASE
        WHEN cumulative_share <= 0.80 THEN 'A'
        WHEN cumulative_share <= 0.95 THEN 'B'
        ELSE 'C'
    END AS abc_category
FROM revenue_cumulative
ORDER BY total_revenue DESC;