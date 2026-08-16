"""
清洗 FRED 全国电价数据，产出 F03(兜底)/F05 用的月度序列。

用法：python clean_fred.py
输出：data/processed/F03_national_price.csv
      列: date(YYYY-MM), price_cents_per_kwh
"""

import csv
from pathlib import Path

RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "fred" / "APU000072610.csv"
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    rows = list(csv.DictReader(RAW.open()))
    out_rows = []
    for r in rows:
        if not r["price_dollars_per_kwh"]:
            continue
        out_rows.append(
            {
                "date": r["date"][:7],
                "price_cents_per_kwh": round(float(r["price_dollars_per_kwh"]) * 100, 3),
            }
        )
    out_rows.sort(key=lambda r: r["date"])

    out_csv = OUT_DIR / "F03_national_price.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "price_cents_per_kwh"])
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"写入 {out_csv} ({len(out_rows)} 行)")


if __name__ == "__main__":
    main()
