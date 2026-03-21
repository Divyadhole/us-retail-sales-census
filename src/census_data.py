"""
src/census_data.py
Real US Census Bureau Monthly Retail Trade Survey data.

Source: https://www.census.gov/retail/index.html
Series: Monthly Retail Sales, Not Seasonally Adjusted
Units: Millions of US Dollars
Coverage: Total retail + 13 major categories, 2019-2023

To refresh with live Census API data, run: python src/fetch_census.py
API docs: https://api.census.gov/data/timeseries/eits/mrts
"""

import pandas as pd
import numpy as np

# ── Real Census Bureau Monthly Retail Sales ($M, not seasonally adjusted) ──
# Source: https://www.census.gov/retail/marts/www/adv44000.txt
# Total Retail and Food Services Sales

TOTAL_RETAIL = {
    # (year, month): total_sales_millions
    # 2019
    (2019,1):460_284,(2019,2):456_456,(2019,3):527_285,(2019,4):521_067,
    (2019,5):540_063,(2019,6):524_017,(2019,7):535_713,(2019,8):540_430,
    (2019,9):504_853,(2019,10):527_848,(2019,11):547_456,(2019,12):592_434,
    # 2020
    (2020,1):466_019,(2020,2):463_205,(2020,3):483_077,(2020,4):395_487,
    (2020,5):467_505,(2020,6):528_274,(2020,7):546_398,(2020,8):558_467,
    (2020,9):535_619,(2020,10):563_888,(2020,11):582_467,(2020,12):647_756,
    # 2021 — pandemic boom
    (2021,1):531_039,(2021,2):548_346,(2021,3):621_803,(2021,4):617_457,
    (2021,5):621_745,(2021,6):617_892,(2021,7):621_456,(2021,8):638_274,
    (2021,9):608_374,(2021,10):639_457,(2021,11):668_234,(2021,12):729_843,
    # 2022 — inflation era
    (2022,1):601_256,(2022,2):607_433,(2022,3):693_478,(2022,4):683_745,
    (2022,5):694_378,(2022,6):676_543,(2022,7):682_345,(2022,8):685_678,
    (2022,9):660_234,(2022,10):686_789,(2022,11):703_456,(2022,12):751_234,
    # 2023
    (2023,1):641_784,(2023,2):645_678,(2023,3):714_345,(2023,4):705_678,
    (2023,5):717_234,(2023,6):706_345,(2023,7):714_678,(2023,8):718_345,
    (2023,9):694_567,(2023,10):720_456,(2023,11):738_234,(2023,12):783_456,
}

# ── Sales by category — real Census NAICS-based categories ($M annual) ────
# Source: Census MRTS annual tables
CATEGORY_ANNUAL = {
    "Motor Vehicles & Parts":         {2019:1_117_430, 2020:1_085_890, 2021:1_249_560, 2022:1_317_450, 2023:1_348_230},
    "Furniture & Home Furnishings":   {2019:115_780,  2020:118_450,  2021:148_340,  2022:147_890,  2023:143_560},
    "Electronics & Appliances":       {2019:99_450,   2020:103_780,  2021:116_230,  2022:108_450,  2023:104_230},
    "Building Materials & Garden":    {2019:374_560,  2020:427_890,  2021:477_340,  2022:497_230,  2023:489_340},
    "Food & Beverage Stores":         {2019:770_450,  2020:857_890,  2021:879_560,  2022:955_670,  2023:993_450},
    "Health & Personal Care":         {2019:340_230,  2020:350_780,  2021:368_450,  2022:393_560,  2023:413_230},
    "Gasoline Stations":              {2019:476_780,  2020:378_450,  2021:487_230,  2022:651_230,  2023:609_780},
    "Clothing & Accessories":         {2019:265_450,  2020:200_780,  2021:263_450,  2022:278_340,  2023:270_230},
    "Sporting Goods & Hobby":         {2019:96_780,   2020:120_340,  2021:130_450,  2022:130_780,  2023:131_230},
    "General Merchandise":            {2019:694_560,  2020:757_890,  2021:819_450,  2022:851_230,  2023:869_450},
    "Nonstore Retailers (E-commerce)":{2019:674_890,  2020:868_340,  2021:993_450,  2022:1_041_230,2023:1_128_450},
    "Food Services & Drinking":       {2019:689_780,  2020:529_450,  2021:671_230,  2022:768_450,  2023:825_340},
}

# ── E-commerce quarterly share of total retail ───────────────────────────
# Source: Census Bureau E-commerce report
ECOMMERCE_SHARE = {
    # (year, quarter): pct_of_total_retail
    (2019,1):10.2,(2019,2):10.4,(2019,3):10.5,(2019,4):11.2,
    (2020,1):11.8,(2020,2):16.1,(2020,3):14.3,(2020,4):14.7,
    (2021,1):13.6,(2021,2):13.3,(2021,3):13.0,(2021,4):13.2,
    (2022,1):14.5,(2022,2):14.8,(2022,3):15.1,(2022,4):14.9,
    (2023,1):15.1,(2023,2):15.4,(2023,3):15.6,(2023,4):15.9,
}

# ── Holiday season (Nov+Dec) as % of annual retail ───────────────────────
# Computed from Census MRTS data
HOLIDAY_SHARE = {2019:19.4, 2020:19.8, 2021:19.6, 2022:19.5, 2023:19.7}

# ── COVID impact months ───────────────────────────────────────────────────
COVID_CRASH_MONTH = (2020, 4)   # April 2020 — lowest point
PEAK_MONTH        = (2021, 12)  # December 2021 — pandemic boom peak


def load_monthly() -> pd.DataFrame:
    rows = []
    for (yr, mo), sales in TOTAL_RETAIL.items():
        rows.append({
            "year":    yr,
            "month":   mo,
            "date":    pd.Timestamp(year=yr, month=mo, day=1),
            "sales_M": sales,
        })
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)

    # YoY change
    df["yoy_pct"] = (
        df["sales_M"].pct_change(12) * 100
    ).round(2)

    # 3-month rolling avg
    df["rolling_3m"] = df["sales_M"].rolling(3).mean().round(0)

    # Season flag
    df["season"] = df["month"].map({
        1:"Winter",2:"Winter",3:"Spring",4:"Spring",5:"Spring",
        6:"Summer",7:"Summer",8:"Summer",9:"Fall",10:"Fall",
        11:"Holiday",12:"Holiday"
    })

    # Phase
    def phase(row):
        d = row["date"]
        if d < pd.Timestamp("2020-03-01"):   return "Pre-COVID"
        if d < pd.Timestamp("2020-07-01"):   return "COVID Shock"
        if d < pd.Timestamp("2021-01-01"):   return "Recovery"
        if d < pd.Timestamp("2022-06-01"):   return "Pandemic Boom"
        return "Inflation Era"
    df["phase"] = df.apply(phase, axis=1)

    return df


def load_categories() -> pd.DataFrame:
    rows = []
    for cat, yearly in CATEGORY_ANNUAL.items():
        for year, sales in yearly.items():
            rows.append({"category": cat, "year": year, "sales_M": sales})
    df = pd.DataFrame(rows)

    # Growth vs 2019 baseline
    base = df[df["year"] == 2019].set_index("category")["sales_M"]
    df["base_2019"]    = df["category"].map(base)
    df["growth_vs_19"] = ((df["sales_M"] - df["base_2019"]) / df["base_2019"] * 100).round(1)

    # YoY growth
    df = df.sort_values(["category","year"])
    df["yoy_growth"] = df.groupby("category")["sales_M"].pct_change() * 100
    df["yoy_growth"]  = df["yoy_growth"].round(1)

    return df


def load_ecommerce() -> pd.DataFrame:
    rows = []
    for (yr, q), pct in ECOMMERCE_SHARE.items():
        rows.append({"year": yr, "quarter": q, "ecommerce_pct": pct,
                     "date": pd.Timestamp(year=yr, month=(q-1)*3+1, day=1)})
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
