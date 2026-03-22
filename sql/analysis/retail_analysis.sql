-- ============================================================
-- sql/analysis/retail_analysis.sql
-- US Retail Sales — Census MRTS Analysis
-- Techniques: CTEs, window functions, YoY growth,
-- seasonality index, rolling averages, phase comparison
-- ============================================================

-- 1. Annual summary with YoY growth
WITH annual AS (
    SELECT year,
           ROUND(SUM(sales_M), 0)        AS total_sales_M,
           COUNT(*)                       AS months
    FROM retail_monthly
    GROUP BY year
)
SELECT
    year,
    total_sales_M,
    ROUND(total_sales_M / 1000000.0, 3)  AS total_sales_T,
    ROUND(100.0 * (total_sales_M - LAG(total_sales_M) OVER (ORDER BY year))
          / NULLIF(LAG(total_sales_M) OVER (ORDER BY year), 0), 2)
                                         AS yoy_growth_pct
FROM annual ORDER BY year;


-- 2. Monthly YoY change + rolling 3-month average
SELECT
    date, year, month,
    sales_M,
    ROUND(sales_M / 1000.0, 1)           AS sales_B,
    ROUND(100.0 * (sales_M - LAG(sales_M, 12) OVER (ORDER BY date))
          / NULLIF(LAG(sales_M, 12) OVER (ORDER BY date), 0), 2)
                                         AS yoy_pct,
    ROUND(AVG(sales_M) OVER (
        ORDER BY date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) / 1000.0, 1)                       AS rolling_3m_B,
    phase
FROM retail_monthly
ORDER BY date;


-- 3. Phase comparison — COVID vs Boom vs Inflation
SELECT
    phase,
    COUNT(*)                             AS months,
    ROUND(AVG(sales_M) / 1000.0, 1)     AS avg_monthly_B,
    ROUND(SUM(sales_M) / 1000.0, 1)     AS total_B,
    ROUND(MAX(sales_M) / 1000.0, 1)     AS peak_B,
    ROUND(MIN(sales_M) / 1000.0, 1)     AS trough_B
FROM retail_monthly
GROUP BY phase
ORDER BY avg_monthly_B DESC;


-- 4. Seasonality index — which month is biggest?
WITH monthly_avg AS (
    SELECT month,
           ROUND(AVG(sales_M), 0)        AS avg_sales,
           ROUND(AVG(AVG(sales_M)) OVER (), 0) AS overall_avg
    FROM retail_monthly
    GROUP BY month
)
SELECT
    month,
    avg_sales,
    ROUND(100.0 * avg_sales / overall_avg, 1) AS seasonality_index,
    RANK() OVER (ORDER BY avg_sales DESC)      AS rank_by_sales
FROM monthly_avg ORDER BY month;


-- 5. Holiday season (Nov + Dec) contribution each year
WITH holiday AS (
    SELECT year,
           SUM(CASE WHEN month IN (11,12) THEN sales_M ELSE 0 END) AS holiday_M,
           SUM(sales_M)                                             AS annual_M
    FROM retail_monthly
    GROUP BY year
)
SELECT
    year,
    ROUND(holiday_M / 1000.0, 1)         AS holiday_B,
    ROUND(annual_M  / 1000.0, 1)         AS annual_B,
    ROUND(100.0 * holiday_M / annual_M, 1) AS holiday_pct_of_annual,
    ROUND(holiday_M - LAG(holiday_M) OVER (ORDER BY year), 0)
                                         AS yoy_holiday_change_M
FROM holiday ORDER BY year;


-- 6. Category performance: winners and losers 2019 vs 2023
SELECT
    category,
    MAX(CASE WHEN year=2019 THEN sales_M END)  AS sales_2019_M,
    MAX(CASE WHEN year=2021 THEN sales_M END)  AS sales_2021_M,
    MAX(CASE WHEN year=2023 THEN sales_M END)  AS sales_2023_M,
    ROUND(100.0 * (MAX(CASE WHEN year=2023 THEN sales_M END)
        - MAX(CASE WHEN year=2019 THEN sales_M END))
        / NULLIF(MAX(CASE WHEN year=2019 THEN sales_M END), 0), 1)
                                               AS growth_pct_19_to_23,
    RANK() OVER (ORDER BY
        (MAX(CASE WHEN year=2023 THEN sales_M END)
        - MAX(CASE WHEN year=2019 THEN sales_M END))
        / NULLIF(MAX(CASE WHEN year=2019 THEN sales_M END), 0)
        DESC)                                  AS growth_rank
FROM category_annual
GROUP BY category
ORDER BY growth_pct_19_to_23 DESC;


-- 7. COVID impact: best and worst months
SELECT
    date, year, month, sales_M,
    ROUND(sales_M / 1000.0, 1)           AS sales_B,
    phase,
    RANK() OVER (ORDER BY sales_M DESC)  AS rank_highest,
    RANK() OVER (ORDER BY sales_M ASC)   AS rank_lowest
FROM retail_monthly
WHERE rank_highest <= 10 OR rank_lowest <= 5
ORDER BY sales_M DESC;

-- 7. E-commerce market share by quarter
SELECT year, quarter,
    ecommerce_sales,
    total_retail_sales,
    ROUND(100.0 * ecommerce_sales / total_retail_sales, 1) AS ecomm_share_pct,
    ROUND(100.0 * ecommerce_sales / total_retail_sales -
          LAG(100.0 * ecommerce_sales / total_retail_sales)
          OVER (ORDER BY year, quarter), 2) AS qoq_share_change
FROM quarterly_retail
ORDER BY year, quarter;

-- 8. COVID impact by retail category
SELECT category,
    MAX(CASE WHEN year=2019 THEN annual_sales END) pre_covid,
    MAX(CASE WHEN year=2020 THEN annual_sales END) covid_year,
    ROUND(100.0*(MAX(CASE WHEN year=2020 THEN annual_sales END) -
                 MAX(CASE WHEN year=2019 THEN annual_sales END))
          / MAX(CASE WHEN year=2019 THEN annual_sales END), 1) AS yoy_change_pct
FROM category_sales
GROUP BY category ORDER BY yoy_change_pct;
