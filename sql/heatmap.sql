CREATE OR REPLACE VIEW v_heatmap AS
SELECT
    c.name AS cafe_name,
    d.weekday,
    EXTRACT(HOUR FROM o.order_time) AS order_hour,
    SUM(foi.quantity * p.base_price * (1 - foi.discount_pct / 100.0)) AS total_revenue
FROM fact_orders o
JOIN fact_orders_item foi ON o.order_id = foi.order_id
JOIN dim_product p ON foi.product_key = p.product_key
JOIN dim_date d ON o.date_id = d.date_id
JOIN dim_cafe c ON o.cafe_id = c.cafe_id
GROUP BY c.name, d.weekday, EXTRACT(HOUR FROM o.order_time)
ORDER BY c.name, d.weekday, order_hour;