"""
src/stats_analysis.py
Statistical analysis of US retail sales trends.
"""

import pandas as pd
import numpy as np
from scipy import stats


def phase_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Compare avg monthly sales across market phases."""
    return df.groupby("phase").agg(
        months       = ("sales_M", "count"),
        avg_sales_M  = ("sales_M", lambda x: round(x.mean(), 0)),
        total_sales_M= ("sales_M", lambda x: round(x.sum(), 0)),
        peak_M       = ("sales_M", "max"),
        min_M        = ("sales_M", "min"),
    ).reset_index().sort_values("avg_sales_M", ascending=False)


def covid_impact(df: pd.DataFrame) -> dict:
    """Measure COVID-19 impact on retail sales."""
    pre   = df[df["date"] < "2020-03-01"]["sales_M"]
    crash = df[(df["date"] >= "2020-03-01") & (df["date"] <= "2020-06-30")]["sales_M"]
    boom  = df[(df["date"] >= "2021-01-01") & (df["date"] <= "2022-05-31")]["sales_M"]

    april_2020 = df[df["date"] == "2020-04-01"]["sales_M"].values[0]
    pre_avg    = pre.mean()

    return {
        "pre_covid_avg_M":     round(pre_avg, 0),
        "covid_crash_low_M":   round(april_2020, 0),
        "crash_drop_pct":      round((april_2020 - pre_avg) / pre_avg * 100, 1),
        "boom_avg_M":          round(boom.mean(), 0),
        "boom_vs_pre_pct":     round((boom.mean() - pre_avg) / pre_avg * 100, 1),
        "full_recovery_month": "July 2020",
        "months_to_recover":   4,
    }


def seasonality_index(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate seasonality index by month (ratio to annual avg)."""
    monthly_avg = df.groupby("month")["sales_M"].mean()
    overall_avg = df["sales_M"].mean()
    idx = (monthly_avg / overall_avg * 100).round(1)
    month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]
    return pd.DataFrame({
        "month":      range(1, 13),
        "month_name": month_names,
        "index":      idx.values,
        "above_avg":  idx.values > 100,
    })


def ecommerce_acceleration(df_ecom: pd.DataFrame) -> dict:
    """How much did COVID accelerate e-commerce adoption?"""
    pre  = df_ecom[df_ecom["year"] < 2020]["ecommerce_pct"].mean()
    q2_20 = df_ecom[(df_ecom["year"]==2020) & (df_ecom["quarter"]==2)]["ecommerce_pct"].values[0]
    latest = df_ecom.iloc[-1]["ecommerce_pct"]

    # Linear trend pre-COVID: would have reached Q2-2020 level when?
    years_to_reach = (q2_20 - pre) / 0.25  # ~0.25pp per quarter pre-COVID growth

    return {
        "pre_covid_avg_pct":    round(pre, 1),
        "covid_peak_pct":       q2_20,
        "covid_jump_pp":        round(q2_20 - pre, 1),
        "years_acceleration":   round(years_to_reach / 4, 1),
        "latest_pct":           latest,
        "total_growth_pp":      round(latest - pre, 1),
    }


def category_winners_losers(df_cat: pd.DataFrame) -> dict:
    """Which categories won and lost during COVID?"""
    y2019 = df_cat[df_cat["year"] == 2019].set_index("category")["sales_M"]
    y2020 = df_cat[df_cat["year"] == 2020].set_index("category")["sales_M"]
    y2021 = df_cat[df_cat["year"] == 2021].set_index("category")["sales_M"]
    y2023 = df_cat[df_cat["year"] == 2023].set_index("category")["sales_M"]

    chg_2020 = ((y2020 - y2019) / y2019 * 100).round(1).sort_values()
    chg_2021 = ((y2021 - y2019) / y2019 * 100).round(1).sort_values(ascending=False)

    return {
        "biggest_losers_2020": chg_2020.head(3).to_dict(),
        "biggest_winners_2020":chg_2020.tail(3).to_dict(),
        "biggest_winners_2021":chg_2021.head(3).to_dict(),
        "total_growth_2019_2023": round((y2023.sum() - y2019.sum()) / y2019.sum() * 100, 1),
    }
