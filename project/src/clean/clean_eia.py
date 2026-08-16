"""
清洗 EIA 分州电价数据，产出 F03 完整版（全国+密集州+对照组）。

数据源：data/raw/eia/F03_retail_sales_residential.csv (EIA API v2, sectorid=RES)
输出：data/processed/F03_state_prices.csv
      列: period(YYYY-MM), stateid, price_cents_per_kwh, group(national/dense/control)
"""

import csv
from pathlib import Path

RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "eia" / "F03_retail_sales_residential.csv"
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DENSE_STATES = {"VA", "OH", "IL", "MD", "AZ", "GA"}
# 原选WY/VT/MT做低密度对照组，但VT电价结构性偏高(~23-25美分/kWh，约为其余对照州两倍，
# 与佛蒙特州自身电网结构/无化石燃料发电有关，与数据中心无关)，作对照组会引入不相关噪音，
# 2026-08-16改用ND替换VT(ND同样是数据中心密度很低的州，且电价水平与WY/MT接近，不是异常值)
CONTROL_STATES = {"WY", "ND", "MT"}


def group_of(stateid: str) -> str:
    if stateid == "US":
        return "national"
    if stateid in DENSE_STATES:
        return "dense"
    if stateid in CONTROL_STATES:
        return "control"
    return "other"


def main():
    rows = list(csv.DictReader(RAW.open()))
    out_rows = []
    for r in rows:
        if not r["price_cents_per_kwh"]:
            continue
        out_rows.append(
            {
                "period": r["period"],
                "stateid": r["stateid"],
                "price_cents_per_kwh": float(r["price_cents_per_kwh"]),
                "group": group_of(r["stateid"]),
            }
        )
    out_rows.sort(key=lambda r: (r["stateid"], r["period"]))

    out_csv = OUT_DIR / "F03_state_prices.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["period", "stateid", "price_cents_per_kwh", "group"])
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"写入 {out_csv} ({len(out_rows)} 行)")


if __name__ == "__main__":
    main()
