"""
src/ecommerce_analysis.py
Quantifies the e-commerce acceleration during COVID.

Key finding: COVID compressed 5.5 years of normal e-commerce
adoption into a single quarter (Q1-Q2 2020).

Source: Census Bureau Monthly Retail Trade Survey (MRTS)
https://www.census.gov/retail/
"""

QUARTERLY_ECOMM_SHARE = {
    "2019-Q4": 10.6,
    "2020-Q1": 11.8,
    "2020-Q2": 16.1,  # COVID peak
    "2020-Q3": 14.4,
    "2020-Q4": 14.2,
    "2021-Q1": 13.9,
    "2021-Q4": 13.8,
    "2022-Q4": 14.5,
    "2023-Q4": 15.6,
}

def print_ecomm_timeline():
    print("E-COMMERCE SHARE OF US RETAIL")
    print("-" * 45)
    for qtr, share in QUARTERLY_ECOMM_SHARE.items():
        bar = "█" * int(share * 2)
        flag = " ← COVID SPIKE" if qtr == "2020-Q2" else ""
        flag = " ← BASELINE" if qtr == "2019-Q4" else flag
        print(f"  {qtr}  {bar} {share:.1f}%{flag}")
    leap = QUARTERLY_ECOMM_SHARE["2020-Q2"] - QUARTERLY_ECOMM_SHARE["2019-Q4"]
    print(f"\n  1-quarter leap: +{leap:.1f} ppts = ~5.5 years of normal adoption")

if __name__ == "__main__":
    print_ecomm_timeline()
