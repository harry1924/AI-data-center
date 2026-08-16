"""
清洗 Census BTOS 企业AI采用率数据。

数据：data/raw/census_btos/F02_btos_ai_use_national.csv
输出：data/processed/F02_business_ai_adoption.csv
      列: date(该两周采集期的结束日), metric, pct
      metric取值：current_v1_goods_services / expected_v1_goods_services /
                 current_v2_any_function / expected_v2_any_function
      只保留 answer='Yes' 的行(即"是"的百分比)
"""

import csv
from datetime import datetime
from pathlib import Path

RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "census_btos" / "F02_btos_ai_use_national.csv"
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_end_date(date_range: str) -> str:
    # "9/11/2023 - 9/24/2023" -> 取结束日期
    end = date_range.split(" - ")[1].strip()
    d = datetime.strptime(end, "%m/%d/%Y")
    return d.strftime("%Y-%m-%d")


def main():
    rows = list(csv.DictReader(RAW.open()))
    out_rows = []
    for r in rows:
        if r["answer"] != "Yes":
            continue
        out_rows.append(
            {
                "date": parse_end_date(r["date_range"]),
                "period_id": int(r["period_id"]),
                "metric": r["metric"],
                "pct": float(r["pct"]),
            }
        )
    out_rows.sort(key=lambda x: (x["metric"], x["period_id"]))

    out_csv = OUT_DIR / "F02_business_ai_adoption.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "period_id", "metric", "pct"])
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"写入 {out_csv} ({len(out_rows)} 行)")


if __name__ == "__main__":
    main()
