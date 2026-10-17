-- Run against data/retail.sqlite after executing src/prepare_data.py.
-- Revenue is gross positive sales; cancellations are counted separately.
SELECT ROUND(SUM(GrossSalesGBP), 2) AS gross_sales_gbp,
       COUNT(DISTINCT CASE WHEN OrderStatus = 'Sale' THEN OrderKey END) AS valid_orders,
       COUNT(DISTINCT CASE WHEN OrderStatus = 'Cancellation' THEN OrderKey END) AS cancelled_orders,
       ROUND(SUM(GrossSalesGBP) /
         COUNT(DISTINCT CASE WHEN OrderStatus = 'Sale' THEN OrderKey END), 2) AS average_order_value_gbp,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN OrderStatus = 'Cancellation' THEN OrderKey END) /
         COUNT(DISTINCT OrderKey), 2) AS cancellation_rate_pct
FROM retail_activity;

SELECT Month, ROUND(SUM(GrossSalesGBP), 2) AS gross_sales_gbp,
       COUNT(DISTINCT CASE WHEN OrderStatus = 'Sale' THEN OrderKey END) AS valid_orders
FROM retail_activity GROUP BY Month ORDER BY Month;

SELECT Country, ROUND(SUM(GrossSalesGBP), 2) AS gross_sales_gbp
FROM retail_activity GROUP BY Country ORDER BY gross_sales_gbp DESC LIMIT 10;

SELECT StockCode, MAX(Product) AS example_name,
       ROUND(SUM(GrossSalesGBP), 2) AS gross_sales_gbp, SUM(UnitsSold) AS units
FROM retail_activity WHERE OrderStatus = 'Sale' AND IsMerchandise = 1
GROUP BY StockCode ORDER BY gross_sales_gbp DESC LIMIT 10;
