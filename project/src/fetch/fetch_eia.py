"""
拉取 EIA API v2 数据，供 F03（分州电价）、F06（全美用电分母）使用。

前置条件：
  - 免费申请 API key: https://www.eia.gov/opendata/register.php
  - 设置环境变量 EIA_API_KEY

用法：
  python fetch_eia.py --series retail-sales
  python fetch_eia.py --series power-annual

输出：
  data/raw/eia/retail_sales_{stateid}.json / .csv
  data/raw/eia/power_annual.csv
  每个输出旁附 _meta.json：来源URL、访问日期、口径说明
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from _http import curl_get_json

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "eia"
RAW_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.eia.gov/v2/electricity/retail-sales/data/"

# F03 选取州：全国 + 数据中心密集州 + 对照组低密度州
# 对照组原用WY/VT/MT，2026-08-16发现VT电价结构性偏高(~23-25美分/kWh，源于其电网结构，
# 与数据中心无关)会引入噪音，改用WY/ND/MT
STATES = ["US", "VA", "OH", "IL", "MD", "AZ", "GA", "WY", "ND", "MT"]


def _get(url: str, params: dict):
    return curl_get_json(url, params=params, headers={"User-Agent": "ai-data-center-report/1.0"})


def fetch_retail_sales(api_key: str):
    """F03: 分州居民电价月度序列, 2015-01 起"""
    all_rows = []
    for state in STATES:
        params = {
            "api_key": api_key,
            "frequency": "monthly",
            "data[0]": "price",
            "facets[stateid][]": state,
            "facets[sectorid][]": "RES",
            "start": "2015-01",
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "offset": 0,
            "length": 5000,
        }
        try:
            payload = _get(BASE_URL, params)
        except Exception as e:
            print(f"[WARN] {state} 拉取失败: {e}", file=sys.stderr)
            continue
        rows = payload.get("response", {}).get("data", [])
        for r in rows:
            all_rows.append(
                {
                    "period": r.get("period"),
                    "stateid": r.get("stateid"),
                    "price_cents_per_kwh": r.get("price"),
                }
            )
        print(f"{state}: {len(rows)} 行")

    out_csv = RAW_DIR / "F03_retail_sales_residential.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["period", "stateid", "price_cents_per_kwh"])
        writer.writeheader()
        writer.writerows(all_rows)

    meta = {
        "source": "EIA API v2 electricity/retail-sales",
        "url": BASE_URL,
        "series_params": {"sectorid": "RES", "states": STATES, "start": "2015-01"},
        "accessed": datetime.now(timezone.utc).isoformat(),
        "unit": "cents_per_kwh",
        "notes": "居民部门(RES)月度电价，用于F03。US为全国均值，VA/OH/IL/MD/AZ/GA为数据中心密集州，WY/VT/MT为低密度对照组。",
    }
    (RAW_DIR / "F03_retail_sales_residential_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"写入 {out_csv} ({len(all_rows)} 行)")


def fetch_power_annual_denominator(api_key: str):
    """F06 分母：全美年度总用电量(sales)"""
    url = "https://api.eia.gov/v2/electricity/retail-sales/data/"
    params = {
        "api_key": api_key,
        "frequency": "annual",
        "data[0]": "sales",
        "facets[stateid][]": "US",
        "facets[sectorid][]": "ALL",
        "start": "2010",
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "offset": 0,
        "length": 5000,
    }
    payload = _get(url, params)
    rows = payload.get("response", {}).get("data", [])
    out_csv = RAW_DIR / "F06_us_total_sales_annual.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["period", "sales_million_kwh"])
        writer.writeheader()
        for r in rows:
            writer.writerow({"period": r.get("period"), "sales_million_kwh": r.get("sales")})
    meta = {
        "source": "EIA API v2 electricity/retail-sales (全美总售电量，作F06分母)",
        "url": url,
        "accessed": datetime.now(timezone.utc).isoformat(),
        "unit": "million_kwh",
    }
    (RAW_DIR / "F06_us_total_sales_annual_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"写入 {out_csv} ({len(rows)} 行)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--series", choices=["retail-sales", "power-annual"], required=True)
    args = parser.parse_args()

    api_key = os.environ.get("EIA_API_KEY")
    if not api_key:
        print("请设置环境变量 EIA_API_KEY (免费申请: https://www.eia.gov/opendata/register.php)", file=sys.stderr)
        sys.exit(1)

    if args.series == "retail-sales":
        fetch_retail_sales(api_key)
    elif args.series == "power-annual":
        fetch_power_annual_denominator(api_key)


if __name__ == "__main__":
    main()
