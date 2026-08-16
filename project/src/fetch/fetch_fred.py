"""
拉取 FRED 序列，供 F03 兜底 / F05 全国电价使用。

默认方法：fredgraph.csv 公开导出端点，**无需 API key**（2026-08-16 实测可用）。
可选方法：官方 series/observations API，需 FRED_API_KEY，用 --use-api-key 启用。

依赖：无第三方包，通过 _http.py 用 curl 子进程发请求
（标准库 urllib / requests 在本环境代理下实测会间歇性挂起，curl 稳定，故统一改用）

用法：
  python fetch_fred.py                  # 默认：无key CSV导出
  python fetch_fred.py --use-api-key    # 需要 export FRED_API_KEY=xxx

输出：
  data/raw/fred/APU000072610.csv        列: date, price_dollars_per_kwh
  data/raw/fred/APU000072610_meta.json
"""

import argparse
import csv
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from _http import curl_get, curl_get_json

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "fred"
RAW_DIR.mkdir(parents=True, exist_ok=True)

SERIES_ID = "APU000072610"
CSV_EXPORT_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
API_URL = "https://api.stlouisfed.org/fred/series/observations"
HEADERS = {"User-Agent": "ai-data-center-report/1.0"}


def fetch_via_csv_export(series_id: str):
    body = curl_get(CSV_EXPORT_URL, params={"id": series_id}, headers=HEADERS, timeout=30)
    reader = csv.reader(io.StringIO(body.decode()))
    next(reader)  # 跳过表头 "observation_date,SERIES_ID"
    rows = list(reader)

    out_csv = RAW_DIR / f"{series_id}.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "price_dollars_per_kwh"])
        writer.writerows(rows)

    meta = {
        "source": f"FRED series {series_id} (Average Price: Electricity per KWh in U.S. City Average)",
        "url": f"{CSV_EXPORT_URL}?id={series_id}",
        "accessed": datetime.now(timezone.utc).isoformat(),
        "unit": "dollars_per_kwh",
        "frequency": "monthly",
        "method": "公开CSV导出端点，无需API key",
        "notes": "单位是美元/kWh；清洗时按需*100转换为cents_per_kwh。",
    }
    (RAW_DIR / f"{series_id}_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"写入 {out_csv} ({len(rows)} 行)")


def fetch_via_api(api_key: str, series_id: str):
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": "1978-01-01",
    }
    payload = curl_get_json(API_URL, params=params, headers=HEADERS, timeout=30)
    obs = payload.get("observations", [])

    out_csv = RAW_DIR / f"{series_id}.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "price_dollars_per_kwh"])
        writer.writeheader()
        for o in obs:
            val = o.get("value")
            writer.writerow({"date": o.get("date"), "price_dollars_per_kwh": None if val == "." else val})

    meta = {
        "source": f"FRED series {series_id}",
        "url": f"https://fred.stlouisfed.org/series/{series_id}",
        "accessed": datetime.now(timezone.utc).isoformat(),
        "unit": "dollars_per_kwh",
        "frequency": "monthly",
        "method": "官方API，需API key",
    }
    (RAW_DIR / f"{series_id}_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"写入 {out_csv} ({len(obs)} 行)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-api-key", action="store_true")
    args = parser.parse_args()

    if args.use_api_key:
        api_key = os.environ.get("FRED_API_KEY")
        if not api_key:
            print("请设置环境变量 FRED_API_KEY", file=sys.stderr)
            sys.exit(1)
        fetch_via_api(api_key, SERIES_ID)
    else:
        fetch_via_csv_export(SERIES_ID)


if __name__ == "__main__":
    main()
