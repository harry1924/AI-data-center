"""
清洗 BLS PPI 变压器数据，产出 F17 用的月度序列。

用法：python clean_bls_ppi.py
输出：data/processed/F17_ppi_transformers.csv
      列: date(YYYY-MM), index_value
"""

import csv
from pathlib import Path

RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "bls" / "ppi_transformers.csv"
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    rows = list(csv.DictReader(RAW.open()))
    out_rows = []
    for r in rows:
        if r["series_name"] != "transformers" or not r["period"].startswith("M") or r["period"] == "M13":
            continue
        month = r["period"][1:]
        out_rows.append({"date": f"{r['year']}-{month}", "index_value": float(r["value"])})
    out_rows.sort(key=lambda r: r["date"])

    out_csv = OUT_DIR / "F17_ppi_transformers.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "index_value"])
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"写入 {out_csv} ({len(out_rows)} 行)")


if __name__ == "__main__":
    main()
