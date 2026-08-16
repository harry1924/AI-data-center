"""
拉取 BLS 数据，供 F07（QCEW NAICS 518210 分县就业）、F17（PPI 变压器/电气设备）使用。

前置条件：
  - QCEW Open Data API 无需 key，但一次只能拉一个 年/季度/行业 组合的全国分县文件（体积较大）。
  - PPI 走标准 BLS 时间序列 API v2，注册免费 key: https://data.bls.gov/registrationEngine/
    设置环境变量 BLS_API_KEY（v1 无 key 也可用，但限流更严、单次查询年数上限更短）。

用法：
  python fetch_bls.py --dataset qcew --start-year 2010 --end-year 2026
  python fetch_bls.py --dataset ppi

输出：
  data/raw/bls/qcew_518210_{year}_{qtr}.csv
  data/raw/bls/qcew_518210_combined.csv
  data/raw/bls/ppi_transformers.csv

注意（对应文档 §5.2 陷阱检查）：
  2022 年 NAICS 修订导致 518210（数据处理、托管及相关服务）行业定义变化，
  2022 年前后的数值不可直接连续比较，清洗脚本需要在图上标出断点。
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "bls"
RAW_DIR.mkdir(parents=True, exist_ok=True)

NAICS_CODE = "518210"

# PPI 候选序列（需在 BLS PPI 数据库核实最终 series id 后使用）：
#   PCU335311335311 - Power, distribution & specialty transformer manufacturing (NAICS 335311)
#   PCU335335       - Electrical equipment, appliance & component manufacturing (NAICS 335)
#   WPU106          - 建材类相关 PPI 大类，用作对照
PPI_SERIES = {
    "transformers": "PCU335311335311",
    "electrical_equipment": "PCU335335",
}


def _get(url: str, headers=None, retries: int = 3):
    for attempt in range(retries):
        try:
            req = Request(url, headers=headers or {"User-Agent": "ai-data-center-report/1.0"})
            with urlopen(req, timeout=60) as resp:
                return resp.read().decode()
        except (HTTPError, URLError) as e:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)


def fetch_qcew(start_year: int, end_year: int):
    combined_rows = []
    fieldnames = None
    for year in range(start_year, end_year + 1):
        for qtr in [1, 2, 3, 4]:
            url = f"https://data.bls.gov/cew/data/api/{year}/{qtr}/industry/{NAICS_CODE}.csv"
            try:
                text = _get(url)
            except Exception as e:
                print(f"[WARN] {year}Q{qtr} 拉取失败(可能尚未发布): {e}", file=sys.stderr)
                continue
            out_path = RAW_DIR / f"qcew_{NAICS_CODE}_{year}_Q{qtr}.csv"
            out_path.write_text(text)
            reader = csv.DictReader(text.splitlines())
            rows = list(reader)
            if rows:
                fieldnames = fieldnames or list(rows[0].keys())
                combined_rows.extend(rows)
            print(f"{year}Q{qtr}: {len(rows)} 行")

    if combined_rows:
        out_csv = RAW_DIR / f"qcew_{NAICS_CODE}_combined.csv"
        with out_csv.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(combined_rows)
        print(f"写入 {out_csv} ({len(combined_rows)} 行)")

    meta = {
        "source": f"BLS QCEW Open Data API, NAICS {NAICS_CODE}",
        "url_template": "https://data.bls.gov/cew/data/api/{year}/{qtr}/industry/518210.csv",
        "accessed": datetime.now(timezone.utc).isoformat(),
        "naics_revision_note": "2022年NAICS修订变更518210定义，2022年前后数据不可直接连续比较，需在图上标注断点。",
    }
    (RAW_DIR / f"qcew_{NAICS_CODE}_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))


def fetch_ppi():
    api_key = os.environ.get("BLS_API_KEY")
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    headers = {"Content-type": "application/json"}
    series_ids = list(PPI_SERIES.values())

    payload = {
        "seriesid": series_ids,
        "startyear": "2010",
        "endyear": "2026",
    }
    if api_key:
        payload["registrationkey"] = api_key

    req = Request(url, data=json.dumps(payload).encode(), headers={**headers, "User-Agent": "ai-data-center-report/1.0"})
    with urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())

    if result.get("status") != "REQUEST_SUCCEEDED":
        print(f"[WARN] BLS API 返回: {result.get('message')}", file=sys.stderr)

    out_csv = RAW_DIR / "ppi_transformers.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["series_id", "series_name", "year", "period", "periodName", "value"])
        writer.writeheader()
        name_by_id = {v: k for k, v in PPI_SERIES.items()}
        for series in result.get("Results", {}).get("series", []):
            sid = series.get("seriesID")
            for item in series.get("data", []):
                writer.writerow(
                    {
                        "series_id": sid,
                        "series_name": name_by_id.get(sid, sid),
                        "year": item.get("year"),
                        "period": item.get("period"),
                        "periodName": item.get("periodName"),
                        "value": item.get("value"),
                    }
                )
    meta = {
        "source": "BLS PPI, series " + ",".join(series_ids),
        "url": url,
        "accessed": datetime.now(timezone.utc).isoformat(),
        "series_map": PPI_SERIES,
        "note": "series id 需在 https://data.bls.gov/PDQWeb/pc 核实后再正式使用",
    }
    (RAW_DIR / "ppi_transformers_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"写入 {out_csv}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["qcew", "ppi"], required=True)
    parser.add_argument("--start-year", type=int, default=2010)
    parser.add_argument("--end-year", type=int, default=2026)
    args = parser.parse_args()

    if args.dataset == "qcew":
        fetch_qcew(args.start_year, args.end_year)
    elif args.dataset == "ppi":
        fetch_ppi()


if __name__ == "__main__":
    main()
