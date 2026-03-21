"""
src/fetch_census.py
Fetches REAL data from Census Bureau Retail Trade API.
No API key required.

API: https://api.census.gov/data/timeseries/eits/mrts
Docs: https://www.census.gov/data/developers/data-sets/mrts.html
"""

import requests
import pandas as pd
from pathlib import Path

CENSUS_API = "https://api.census.gov/data/timeseries/eits/mrts"

# NAICS category codes
CATEGORIES = {
    "44X72":  "Total Retail & Food Services",
    "441":    "Motor Vehicles & Parts",
    "442":    "Furniture & Home Furnishings",
    "443":    "Electronics & Appliances",
    "444":    "Building Materials & Garden",
    "445":    "Food & Beverage Stores",
    "446":    "Health & Personal Care",
    "447":    "Gasoline Stations",
    "448":    "Clothing & Accessories",
    "451":    "Sporting Goods & Hobby",
    "452":    "General Merchandise",
    "4541":   "Nonstore Retailers (E-commerce)",
    "722":    "Food Services & Drinking",
}


def fetch_category(category_code: str, start: str = "2019-01",
                   end: str = "2023-12") -> pd.DataFrame:
    """Fetch monthly retail sales for one NAICS category."""
    params = {
        "get":       "cell_value,error_data,time_slot_id",
        "for":       "us:*",
        "category_code": category_code,
        "seasonally_adj": "no",
        "time":      f"from {start} to {end}",
    }
    resp = requests.get(CENSUS_API, params=params, timeout=20)
    if resp.status_code != 200:
        raise Exception(f"Census API error {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    headers = data[0]
    rows    = data[1:]
    df = pd.DataFrame(rows, columns=headers)
    df["sales_M"] = pd.to_numeric(df["cell_value"], errors="coerce")
    df["date"]    = pd.to_datetime(df["time"])
    df["category_code"] = category_code
    df["category"] = CATEGORIES.get(category_code, category_code)
    return df[["date","category","category_code","sales_M"]].dropna()


def fetch_all(output_dir: str = "data/raw") -> pd.DataFrame:
    """Fetch all categories and merge into one DataFrame."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    frames = []
    for code, name in CATEGORIES.items():
        print(f"  Fetching {name}...")
        try:
            df = fetch_category(code)
            df.to_csv(f"{output_dir}/mrts_{code}.csv", index=False)
            frames.append(df)
        except Exception as e:
            print(f"    Warning: {e}")

    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(f"{output_dir}/mrts_all.csv", index=False)
    print(f"  ✓ Saved {len(combined)} rows to {output_dir}/mrts_all.csv")
    return combined


if __name__ == "__main__":
    fetch_all()
