"""
清洗 SEC EDGAR 原始数据，产出 F14/F15 用的 data/processed/F15_capex_quarterly.csv。

关键步骤：把 fiscal_period_end 日期换算成日历季度。因为原始数据用的是
真实日历日期(如 2026-06-30)，按"结束月份"分桶即可得到日历季度，不需要
额外的财年对齐逻辑——2026-06-30无论对MSFT(其财年Q4)还是别家公司，
都对应日历2026年Q2(4-6月)。

用法：python clean_sec_edgar.py
输出：data/processed/F15_capex_quarterly.csv
      列: calendar_quarter, company, capex_usd, ocf_usd, fcf_usd, capex_to_ocf_ratio
"""

import csv
from datetime import date
from pathlib import Path

RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "sec" / "capex_quarterly_by_fiscal_period.csv"
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def to_calendar_quarter(end_date_str: str) -> str:
    d = date.fromisoformat(end_date_str)
    q = (d.month - 1) // 3 + 1
    return f"{d.year}Q{q}"


def main():
    rows = list(csv.DictReader(RAW.open()))
    out_rows = []
    for r in rows:
        if not r["capex_usd"] or not r["operating_cash_flow_usd"]:
            continue
        capex = int(r["capex_usd"])
        ocf = int(r["operating_cash_flow_usd"])
        cq = to_calendar_quarter(r["fiscal_period_end"])
        out_rows.append(
            {
                "calendar_quarter": cq,
                "company": r["company"],
                "fiscal_period_end": r["fiscal_period_end"],
                "capex_usd": capex,
                "ocf_usd": ocf,
                "fcf_usd": ocf - capex,
                "capex_to_ocf_ratio": round(capex / ocf, 4) if ocf else None,
            }
        )

    # 只保留2015Q1起(文档F15要求范围)，且过滤掉单季度capex为负或异常小的记录(修订/口径切换噪音)
    out_rows = [r for r in out_rows if r["calendar_quarter"] >= "2015Q1" and r["capex_usd"] > 0]
    out_rows.sort(key=lambda r: (r["calendar_quarter"], r["company"]))

    out_csv = OUT_DIR / "F15_capex_quarterly.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "calendar_quarter",
                "company",
                "fiscal_period_end",
                "capex_usd",
                "ocf_usd",
                "fcf_usd",
                "capex_to_ocf_ratio",
            ],
        )
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"写入 {out_csv} ({len(out_rows)} 行)")


if __name__ == "__main__":
    main()
