"""
src/charts.py — US Retail Sales Census charts
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mtick
import seaborn as sns
from pathlib import Path

P = {"teal":"#1D9E75","blue":"#185FA5","amber":"#BA7517","red":"#A32D2D",
     "purple":"#534AB7","coral":"#D85A30","neutral":"#5F5E5A",
     "light":"#F1EFE8","mid":"#B4B2A9","green":"#3B6D11"}

BASE = {"figure.facecolor":"white","axes.facecolor":"#FAFAF8",
        "axes.spines.top":False,"axes.spines.right":False,"axes.spines.left":False,
        "axes.grid":True,"axes.grid.axis":"y","grid.color":"#ECEAE4","grid.linewidth":0.6,
        "font.family":"DejaVu Sans","axes.titlesize":12,"axes.titleweight":"bold",
        "axes.labelsize":10,"xtick.labelsize":8.5,"ytick.labelsize":9,
        "xtick.bottom":False,"ytick.left":False}

def save(fig, path):
    fig.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  ✓ {Path(path).name}")

def fmt_B(x, _): return f"${x/1000:.1f}B"
def fmt_T(x, _): return f"${x/1_000_000:.2f}T"


def chart_total_sales_timeline(df: pd.DataFrame, path: str):
    """Monthly retail sales 2019–2023 with phase annotations."""
    phase_colors = {
        "Pre-COVID":     P["blue"],
        "COVID Shock":   P["red"],
        "Recovery":      P["amber"],
        "Pandemic Boom": P["teal"],
        "Inflation Era": P["purple"],
    }
    bar_colors = [phase_colors[p] for p in df["phase"]]

    with plt.rc_context({**BASE, "axes.grid.axis":"both"}):
        fig, ax = plt.subplots(figsize=(14, 6))

        ax.bar(df["date"], df["sales_M"], color=bar_colors,
               width=25, alpha=0.88)
        ax.plot(df["date"], df["rolling_3m"], color="white",
                lw=2.5, zorder=3, label="3-month rolling avg")
        ax.plot(df["date"], df["rolling_3m"], color=P["neutral"],
                lw=1.5, zorder=4, linestyle="--", alpha=0.8)

        # Annotate COVID crash
        crash = df[df["date"] == "2020-04-01"].iloc[0]
        ax.annotate("COVID Crash\nApr 2020",
                    xy=(crash["date"], crash["sales_M"]),
                    xytext=(pd.Timestamp("2020-07-01"), 520_000),
                    fontsize=8.5, color=P["red"], fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=P["red"], lw=1.2))

        # Annotate pandemic boom peak
        peak = df.loc[df["sales_M"].idxmax()]
        ax.annotate(f"Peak: ${peak['sales_M']/1000:.0f}B\nDec 2021",
                    xy=(peak["date"], peak["sales_M"]),
                    xytext=(pd.Timestamp("2021-07-01"), 760_000),
                    fontsize=8.5, color=P["teal"], fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=P["teal"], lw=1.2))

        ax.yaxis.set_major_formatter(mtick.FuncFormatter(fmt_B))
        ax.set_ylabel("Monthly Sales (USD Billions)")
        ax.set_title("US Total Retail Sales 2019–2023\nSource: US Census Bureau Monthly Retail Trade Survey")

        patches = [mpatches.Patch(color=v, label=k, alpha=0.88)
                   for k, v in phase_colors.items()]
        ax.legend(handles=patches, fontsize=8.5, loc="upper left",
                  ncol=5, framealpha=0.9)
        ax.spines["left"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        fig.tight_layout()
        save(fig, path)


def chart_yoy_growth(df: pd.DataFrame, path: str):
    """Year-over-year % change in monthly retail sales."""
    df2 = df.dropna(subset=["yoy_pct"]).copy()
    colors = [P["teal"] if v >= 0 else P["red"] for v in df2["yoy_pct"]]

    with plt.rc_context(BASE):
        fig, ax = plt.subplots(figsize=(14, 5))
        ax.bar(df2["date"], df2["yoy_pct"], color=colors, width=25, alpha=0.88)
        ax.axhline(0, color=P["neutral"], lw=1)

        # Highlight COVID crash
        ax.axvspan(pd.Timestamp("2020-03-01"), pd.Timestamp("2020-06-30"),
                   alpha=0.08, color=P["red"])
        ax.axvspan(pd.Timestamp("2021-01-01"), pd.Timestamp("2022-05-31"),
                   alpha=0.07, color=P["teal"])

        ax.yaxis.set_major_formatter(mtick.PercentFormatter())
        ax.set_ylabel("YoY Change (%)")
        ax.set_title("Year-over-Year Retail Sales Growth\nCOVID crash (red shading) vs Pandemic Boom (teal shading)")

        up   = mpatches.Patch(color=P["teal"], alpha=0.88, label="Growth")
        down = mpatches.Patch(color=P["red"],  alpha=0.88, label="Decline")
        ax.legend(handles=[up, down], fontsize=9)
        ax.spines["left"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        fig.tight_layout()
        save(fig, path)


def chart_category_growth(df_cat: pd.DataFrame, path: str):
    """Category revenue growth 2019 vs 2023."""
    base = df_cat[df_cat["year"] == 2019].set_index("category")["sales_M"]
    end  = df_cat[df_cat["year"] == 2023].set_index("category")["sales_M"]
    growth = ((end - base) / base * 100).sort_values(ascending=True)

    short_names = {
        "Motor Vehicles & Parts":          "Motor Vehicles",
        "Furniture & Home Furnishings":    "Furniture",
        "Electronics & Appliances":        "Electronics",
        "Building Materials & Garden":     "Building Materials",
        "Food & Beverage Stores":          "Food & Beverage",
        "Health & Personal Care":          "Health & Personal Care",
        "Gasoline Stations":               "Gas Stations",
        "Clothing & Accessories":          "Clothing",
        "Sporting Goods & Hobby":          "Sporting Goods",
        "General Merchandise":             "General Merchandise",
        "Nonstore Retailers (E-commerce)": "E-commerce",
        "Food Services & Drinking":        "Food Services",
    }
    labels = [short_names.get(i, i) for i in growth.index]
    colors = [P["red"] if v < 20 else P["teal"] if v > 40 else P["amber"]
              for v in growth.values]

    with plt.rc_context({**BASE, "axes.grid.axis":"x"}):
        fig, ax = plt.subplots(figsize=(11, 6))
        bars = ax.barh(labels, growth.values, color=colors, height=0.65, alpha=0.88)
        ax.axvline(0, color=P["neutral"], lw=0.8)
        for bar, v in zip(bars, growth.values):
            ax.text(v + 0.5, bar.get_y() + bar.get_height()/2,
                    f"+{v:.0f}%" if v >= 0 else f"{v:.0f}%",
                    va="center", fontsize=9, fontweight="bold",
                    color=P["teal"] if v >= 40 else P["red"] if v < 20 else P["amber"])
        ax.set_xlabel("Total Growth 2019 → 2023 (%)")
        ax.set_title("Retail Category Growth 2019–2023\nE-commerce leads; clothing & gas stations lag")
        fig.tight_layout()
        save(fig, path)


def chart_category_heatmap(df_cat: pd.DataFrame, path: str):
    """Heatmap: category × year sales ($B)."""
    short = {
        "Motor Vehicles & Parts":          "Motor Vehicles",
        "Furniture & Home Furnishings":    "Furniture",
        "Electronics & Appliances":        "Electronics",
        "Building Materials & Garden":     "Building Mats",
        "Food & Beverage Stores":          "Food & Bev",
        "Health & Personal Care":          "Health",
        "Gasoline Stations":               "Gas Stations",
        "Clothing & Accessories":          "Clothing",
        "Sporting Goods & Hobby":          "Sporting Goods",
        "General Merchandise":             "Gen Merch",
        "Nonstore Retailers (E-commerce)": "E-commerce",
        "Food Services & Drinking":        "Food Services",
    }
    df2 = df_cat.copy()
    df2["category"] = df2["category"].map(short).fillna(df2["category"])
    pivot = df2.pivot(index="category", columns="year", values="sales_M")
    pivot = pivot.div(1000).round(1)  # convert to $B
    pivot = pivot.sort_values(2023, ascending=False)

    with plt.rc_context({**BASE, "axes.grid":False}):
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(pivot, annot=True, fmt=".0f", cmap="YlGn",
                    linewidths=0.5, linecolor="#E0DED8",
                    cbar_kws={"label":"Sales ($B)"}, ax=ax)
        ax.set_title("Retail Sales by Category & Year ($B)\n"
                     "Darker = higher sales", fontweight="bold")
        ax.set_ylabel("")
        plt.xticks(rotation=0)
        plt.yticks(rotation=0)
        fig.tight_layout()
        save(fig, path)


def chart_ecommerce_rise(df_ecom: pd.DataFrame, stats: dict, path: str):
    """E-commerce share of total retail — the structural shift."""
    with plt.rc_context({**BASE, "axes.grid.axis":"both"}):
        fig, ax = plt.subplots(figsize=(11, 5))

        ax.fill_between(df_ecom["date"], df_ecom["ecommerce_pct"],
                        alpha=0.18, color=P["teal"])
        ax.plot(df_ecom["date"], df_ecom["ecommerce_pct"],
                "o-", color=P["teal"], lw=2.2, markersize=6)

        # COVID acceleration annotation
        q2_date = pd.Timestamp("2020-04-01")
        q2_val  = stats["covid_peak_pct"]
        ax.annotate(
            f"COVID spike: {q2_val}%\n+{stats['covid_jump_pp']}pp jump\n"
            f"= {stats['years_acceleration']} years of normal growth",
            xy=(q2_date, q2_val),
            xytext=(pd.Timestamp("2020-07-01"), 17.5),
            fontsize=8.5, color=P["red"], fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=P["red"], lw=1.2))

        ax.axhline(stats["pre_covid_avg_pct"], color=P["neutral"],
                   linestyle="--", lw=1.2, alpha=0.7,
                   label=f"Pre-COVID avg: {stats['pre_covid_avg_pct']}%")

        ax.set_ylabel("E-commerce as % of Total Retail")
        ax.set_title(f"The E-commerce Revolution — COVID Accelerated Adoption by {stats['years_acceleration']} Years\n"
                     f"Source: US Census Bureau E-commerce Report")
        ax.legend(fontsize=9)
        ax.set_ylim(8, 20)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter())
        ax.spines["left"].set_visible(True)
        ax.spines["bottom"].set_visible(True)
        fig.tight_layout()
        save(fig, path)


def chart_seasonality(df: pd.DataFrame, path: str):
    """Monthly seasonality index — when does America shop?"""
    from src.stats_analysis import seasonality_index
    s = seasonality_index(df)

    colors = [P["red"] if v >= 110 else P["teal"] if v < 95 else P["amber"]
              for v in s["index"]]

    with plt.rc_context({**BASE, "axes.grid.axis":"y"}):
        fig, ax = plt.subplots(figsize=(11, 5))
        bars = ax.bar(s["month_name"], s["index"], color=colors, width=0.65, alpha=0.88)
        ax.axhline(100, color=P["neutral"], lw=1.2, linestyle="--",
                   label="Average (100)")
        for bar, v in zip(bars, s["index"]):
            ax.text(bar.get_x() + bar.get_width()/2, v + 0.5,
                    f"{v}", ha="center", fontsize=9, fontweight="bold")
        ax.set_ylabel("Seasonality Index (100 = avg month)")
        ax.set_title("US Retail Seasonality Index by Month\n"
                     "December dominates — holiday shopping drives +30% above average")
        ax.legend(fontsize=9)
        ax.set_ylim(80, 140)
        high = mpatches.Patch(color=P["red"],  alpha=0.88, label="Peak season (>110)")
        mid  = mpatches.Patch(color=P["amber"],alpha=0.88, label="Average season")
        low  = mpatches.Patch(color=P["teal"], alpha=0.88, label="Slow season (<95)")
        ax.legend(handles=[high, mid, low], fontsize=9)
        fig.tight_layout()
        save(fig, path)


def chart_annual_summary(df: pd.DataFrame, path: str):
    """Annual total retail sales with growth labels."""
    annual = df.groupby("year")["sales_M"].sum().reset_index()
    annual["sales_B"] = annual["sales_M"] / 1000
    annual["yoy"] = annual["sales_B"].pct_change() * 100

    colors = [P["blue"], P["red"], P["teal"], P["purple"], P["amber"]]

    with plt.rc_context(BASE):
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(annual["year"].astype(str), annual["sales_B"],
                      color=colors, width=0.6, alpha=0.9)
        for bar, v, row in zip(bars, annual["sales_B"], annual.itertuples()):
            ax.text(bar.get_x() + bar.get_width()/2, v + 50,
                    f"${v/1000:.2f}T", ha="center", fontsize=10, fontweight="bold")
            if not pd.isna(row.yoy):
                color = P["teal"] if row.yoy > 0 else P["red"]
                ax.text(bar.get_x() + bar.get_width()/2, v - 800,
                        f"{'+'if row.yoy>0 else ''}{row.yoy:.1f}%",
                        ha="center", fontsize=9, color=color, fontweight="bold")
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x/1000:.1f}T"))
        ax.set_ylabel("Annual Retail Sales")
        ax.set_title("US Annual Retail Sales 2019–2023\n"
                     "Total retail crossed $9T for the first time in 2023")
        ax.set_ylim(0, annual["sales_B"].max() * 1.18)
        fig.tight_layout()
        save(fig, path)
