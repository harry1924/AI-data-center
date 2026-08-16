"""
拉取 FRED 序列，供 F03 兜底 / F05 全国电价使用。

前置条件：
  - 免费申请 API key: https://fred.stlouisfed.org/docs/api/api_key.html
  - 设置环境变量 FRED_API_KEY

用法：
  python fetch_fred.py

输出：
  data/raw/fred/APU000072610.csv
"""

import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "fred"
RAW_DIR.mkdir(parents=True, exist_ok=True)

SERIES_ID = "APU000072610"
BASE_URL = "https://api.stlouisfed.org/fred/series/observations"


def fetch_series(api_key: str, series_id: str):
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": "1978-01-01",
    }
    url = f"{BASE_URL}?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "ai-data-center-report/1.0"})
    with urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode())

    obs = payload.get("observations", [])
    out_csv = RAW_DIR / f"{series_id}.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "price_cents_per_kwh"])
        writer.writeheader()
        for o in obs:
            val = o.get("value")
            writer.writerow({"date": o.get("date"), "price_cents_per_kwh": None if val == "." else val})

    meta = {
        "source": f"FRED series {series_id} (美国城市平均电价)",
        "url": f"https://fred.stlouisfed.org/series/{series_id}",
        "accessed": datetime.now(timezone.utc).isoformat(),
        "unit": "cents_per_kwh",
        "frequency": "monthly",
    }
    (RAW_DIR / f"{series_id}_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"写入 {out_csv} ({len(obs)} 行)")


def main():
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        print("请设置环境变量 FRED_API_KEY (免费申请: https://fred.stlouisfed.org/docs/api/api_key.html)", file=sys.stderr)
        sys.exit(1)
    fetch_series(api_key, SERIES_ID)


if __name__ == "__main__":
    main()
