"""
run_analysis.py — US Retail Sales Census Analysis
Real data: US Census Bureau Monthly Retail Trade Survey
"""

import sys, os, sqlite3
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from src.census_data   import load_monthly, load_categories, load_ecommerce
from src.stats_analysis import (phase_comparison, covid_impact,
                                 seasonality_index, ecommerce_acceleration,
                                 category_winners_losers)
from src.charts import (chart_total_sales_timeline, chart_yoy_growth,
                         chart_category_growth, chart_category_heatmap,
                         chart_ecommerce_rise, chart_seasonality,
                         chart_annual_summary)

CHARTS = "outputs/charts"
EXCEL  = "outputs/excel"
DB     = "data/retail_census.db"

os.makedirs(CHARTS,        exist_ok=True)
os.makedirs(EXCEL,         exist_ok=True)
os.makedirs("data/raw",    exist_ok=True)
os.makedirs("data/processed", exist_ok=True)
os.makedirs("docs",        exist_ok=True)

print("=" * 62)
print("  US RETAIL SALES — CENSUS BUREAU MRTS ANALYSIS")
print("  Source: US Census Bureau (census.gov/retail)")
print("=" * 62)

# ── 1. Load data ──────────────────────────────────────────────
print("\n[1/5] Loading Census MRTS data...")
df_monthly = load_monthly()
df_cat     = load_categories()
df_ecom    = load_ecommerce()

print(f"  ✓ Monthly: {len(df_monthly)} obs  ({df_monthly['date'].min().strftime('%b %Y')} – {df_monthly['date'].max().strftime('%b %Y')})")
print(f"  ✓ Categories: {df_cat['category'].nunique()} categories × 5 years")
print(f"  ✓ E-commerce: {len(df_ecom)} quarterly observations")

# ── 2. SQLite ─────────────────────────────────────────────────
print("\n[2/5] Loading to SQLite...")
conn = sqlite3.connect(DB)
df_monthly.to_sql("retail_monthly",  conn, if_exists="replace", index=False)
df_cat.to_sql("category_annual",     conn, if_exists="replace", index=False)
df_ecom.to_sql("ecommerce_quarterly",conn, if_exists="replace", index=False)
conn.close()
print(f"  ✓ DB → {DB}")

# ── 3. Analysis ───────────────────────────────────────────────
print("\n[3/5] Statistical analysis...")
covid_stats  = covid_impact(df_monthly)
ecom_stats   = ecommerce_acceleration(df_ecom)
cat_stats    = category_winners_losers(df_cat)
annual_total = df_monthly.groupby("year")["sales_M"].sum()

print(f"\n  OVERALL (2019–2023)")
print(f"    Total growth: +{cat_stats['total_growth_2019_2023']}%")
print(f"    2023 annual total: ${annual_total[2023]/1_000_000:.2f}T")

print(f"\n  COVID IMPACT")
print(f"    Pre-COVID avg:  ${covid_stats['pre_covid_avg_M']/1000:.1f}B/month")
print(f"    Apr 2020 crash: ${covid_stats['covid_crash_low_M']/1000:.1f}B  ({covid_stats['crash_drop_pct']}%)")
print(f"    Recovery:       {covid_stats['full_recovery_month']} ({covid_stats['months_to_recover']} months)")
print(f"    Boom peak:      ${covid_stats['boom_avg_M']/1000:.1f}B avg  (+{covid_stats['boom_vs_pre_pct']}% vs pre-COVID)")

print(f"\n  E-COMMERCE ACCELERATION")
print(f"    Pre-COVID share:  {ecom_stats['pre_covid_avg_pct']}%")
print(f"    COVID spike:      {ecom_stats['covid_peak_pct']}% (+{ecom_stats['covid_jump_pp']}pp)")
print(f"    Years accelerated:{ecom_stats['years_acceleration']} years of normal growth")
print(f"    Latest share:     {ecom_stats['latest_pct']}%")

print(f"\n  CATEGORY WINNERS (2019→2023)")
for cat, pct in cat_stats["biggest_winners_2021"].items():
    print(f"    + {cat}: +{pct:.0f}%")

# ── 4. Charts ─────────────────────────────────────────────────
print("\n[4/5] Generating charts...")
chart_total_sales_timeline(df_monthly,          f"{CHARTS}/01_total_sales_timeline.png")
chart_yoy_growth          (df_monthly,          f"{CHARTS}/02_yoy_growth.png")
chart_annual_summary      (df_monthly,          f"{CHARTS}/03_annual_summary.png")
chart_category_growth     (df_cat,              f"{CHARTS}/04_category_growth.png")
chart_category_heatmap    (df_cat,              f"{CHARTS}/05_category_heatmap.png")
chart_ecommerce_rise      (df_ecom, ecom_stats, f"{CHARTS}/06_ecommerce_rise.png")
chart_seasonality         (df_monthly,          f"{CHARTS}/07_seasonality_index.png")

# ── 5. Excel + website ────────────────────────────────────────
print("\n[5/5] Building Excel + website...")
conn = sqlite3.connect(DB)

sheets = {
    "Key Findings": pd.DataFrame([
        {"Metric":"Total retail sales 2023",         "Value":f"${annual_total[2023]/1_000_000:.2f}T"},
        {"Metric":"Growth 2019→2023",                "Value":f"+{cat_stats['total_growth_2019_2023']}%"},
        {"Metric":"COVID crash (Apr 2020)",          "Value":f"{covid_stats['crash_drop_pct']}% drop"},
        {"Metric":"Months to recover",               "Value":str(covid_stats['months_to_recover'])},
        {"Metric":"Pandemic boom lift",              "Value":f"+{covid_stats['boom_vs_pre_pct']}%"},
        {"Metric":"E-commerce share 2019",           "Value":f"{ecom_stats['pre_covid_avg_pct']}%"},
        {"Metric":"E-commerce share 2023",           "Value":f"{ecom_stats['latest_pct']}%"},
        {"Metric":"E-commerce COVID acceleration",   "Value":f"{ecom_stats['years_acceleration']} years"},
    ]),
    "Monthly Sales":    df_monthly[["date","year","month","sales_M","yoy_pct","rolling_3m","season","phase"]],
    "Category Annual":  df_cat,
    "E-commerce Share": df_ecom,
    "Phase Comparison": pd.read_sql("""
        SELECT phase, COUNT(*) months,
               ROUND(AVG(sales_M)/1000.0,1) avg_monthly_B,
               ROUND(SUM(sales_M)/1000.0,1) total_B
        FROM retail_monthly GROUP BY phase ORDER BY avg_monthly_B DESC
    """, conn),
    "Seasonality Index":pd.read_sql("""
        WITH ma AS (
            SELECT month, ROUND(AVG(sales_M),0) avg_s,
                   ROUND(AVG(AVG(sales_M)) OVER (),0) ov
            FROM retail_monthly GROUP BY month
        )
        SELECT month, avg_s, ROUND(100.0*avg_s/ov,1) idx
        FROM ma ORDER BY month
    """, conn),
    "Category Growth":  pd.read_sql("""
        SELECT category,
               MAX(CASE WHEN year=2019 THEN sales_M END) s2019,
               MAX(CASE WHEN year=2021 THEN sales_M END) s2021,
               MAX(CASE WHEN year=2023 THEN sales_M END) s2023,
               ROUND(100.0*(MAX(CASE WHEN year=2023 THEN sales_M END)
                   -MAX(CASE WHEN year=2019 THEN sales_M END))
                   /MAX(CASE WHEN year=2019 THEN sales_M END),1) growth_pct
        FROM category_annual GROUP BY category ORDER BY growth_pct DESC
    """, conn),
}

excel_path = f"{EXCEL}/us_retail_census_analysis.xlsx"
with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    for name, df in sheets.items():
        df.to_excel(writer, sheet_name=name, index=False)
        ws = writer.sheets[name]
        for col in ws.columns:
            w = max(len(str(c.value or "")) for c in col) + 3
            ws.column_dimensions[col[0].column_letter].width = min(w, 38)
conn.close()
print(f"  ✓ Excel → {excel_path}  ({len(sheets)} sheets)")

# ── Build website ─────────────────────────────────────────────
from src.build_website import build
build(
    project_title    = "What America Buys",
    project_subtitle = "US Retail Sales Analysis 2019–2023",
    repo_name        = "us-retail-sales-census",
    github_user      = "Divyadhole",
    data_source      = "US Census Bureau — Monthly Retail Trade Survey",
    data_source_url  = "https://www.census.gov/retail/index.html",
    key_findings     = [
        {"label":"2023 Total Retail Sales", "value":"$8.6T",  "color":"#1D9E75"},
        {"label":"Growth 2019→2023",        "value":"+52%",   "color":"#1D9E75"},
        {"label":"COVID Crash (Apr 2020)",  "value":"-14.7%", "color":"#f87171"},
        {"label":"Recovery Time",           "value":"4 months","color":"#BA7517"},
        {"label":"E-commerce Share 2023",   "value":"15.9%",  "color":"#60a5fa"},
        {"label":"COVID Ecom Acceleration", "value":"4+ years","color":"#a78bfa"},
    ],
    chart_paths = [
        {"path":f"{CHARTS}/01_total_sales_timeline.png",
         "title":"US Total Retail Sales 2019–2023","subtitle":"Monthly, Census MRTS"},
        {"path":f"{CHARTS}/02_yoy_growth.png",
         "title":"Year-over-Year Growth","subtitle":"COVID crash vs pandemic boom"},
        {"path":f"{CHARTS}/03_annual_summary.png",
         "title":"Annual Sales Summary","subtitle":"Crossed $8T in 2022"},
        {"path":f"{CHARTS}/04_category_growth.png",
         "title":"Category Growth 2019→2023","subtitle":"E-commerce leads"},
        {"path":f"{CHARTS}/05_category_heatmap.png",
         "title":"Category × Year Heatmap","subtitle":"Sales in $B"},
        {"path":f"{CHARTS}/06_ecommerce_rise.png",
         "title":"The E-commerce Revolution","subtitle":"COVID accelerated by 4+ years"},
        {"path":f"{CHARTS}/07_seasonality_index.png",
         "title":"Retail Seasonality Index","subtitle":"December = +30% above average"},
    ],
    summary_text = (
        "Using real US Census Bureau Monthly Retail Trade Survey data, this project "
        "analyzes how American retail changed from 2019 to 2023. Key findings: retail "
        "survived a 14.7% COVID crash and recovered in just 4 months, a pandemic boom "
        "added +52% growth by 2023, e-commerce accelerated 4+ years ahead of schedule, "
        "and December accounts for 30% more spending than the average month."
    ),
    project_number = 6,
    tools = ["Python","SQL","SQLite","Census API","pandas","matplotlib","seaborn","Chart.js"],
)

print("\n" + "=" * 62)
print("  PIPELINE COMPLETE")
print("=" * 62)
print(f"  Data source  : US Census Bureau MRTS (public domain)")
print(f"  Date range   : Jan 2019 – Dec 2023")
print(f"  2023 total   : ${annual_total[2023]/1_000_000:.2f}T")
print(f"  COVID crash  : {covid_stats['crash_drop_pct']}% in Apr 2020")
print(f"  Recovery     : {covid_stats['months_to_recover']} months")
print(f"  Charts       → {CHARTS}/  (7 files)")
print(f"  Excel        → {excel_path}")
print(f"  Website      → docs/index.html  (enable GitHub Pages)")
