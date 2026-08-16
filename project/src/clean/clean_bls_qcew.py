"""
清洗 BLS QCEW 原始数据，产出 F07 用的分县就业长序列。

选县：Loudoun County VA(51107，全球数据中心密度最高的县之一) +
      Franklin County OH(39049，文档§2.7举例的对照县)
own_code='5' (私营部门)，避免混入政府/联邦/州机构自身的518210就业。

用法：python clean_bls_qcew.py
输出：data/processed/F07_employment_by_county.csv
      列: year, qtr, county_fips, county_name, qtrly_estabs, month3_emplvl, avg_wkly_wage
"""

import csv
from pathlib import Path

RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "bls" / "qcew_518210_combined.csv"
OUT_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

COUNTIES = {
    "51107": "Loudoun County, VA",
    "39049": "Franklin County, OH",
}

# 2022年NAICS修订：518210定义变更，年份>=2022的数据与之前不可直接连续比较
NAICS_BREAK_YEAR = 2022


def main():
    rows = list(csv.DictReader(RAW.open()))
    out_rows = []
    for r in rows:
        if r["area_fips"] not in COUNTIES or r["own_code"] != "5":
            continue
        out_rows.append(
            {
                "year": int(r["year"]),
                "qtr": int(r["qtr"]),
                "county_fips": r["area_fips"],
                "county_name": COUNTIES[r["area_fips"]],
                "qtrly_estabs": int(r["qtrly_estabs"]) if r["qtrly_estabs"] else None,
                "month3_emplvl": int(r["month3_emplvl"]) if r["month3_emplvl"] else None,
                "avg_wkly_wage": int(r["avg_wkly_wage"]) if r["avg_wkly_wage"] else None,
                "naics_break": "post-2022" if int(r["year"]) >= NAICS_BREAK_YEAR else "pre-2022",
            }
        )
    out_rows.sort(key=lambda r: (r["county_fips"], r["year"], r["qtr"]))

    out_csv = OUT_DIR / "F07_employment_by_county.csv"
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "year",
                "qtr",
                "county_fips",
                "county_name",
                "qtrly_estabs",
                "month3_emplvl",
                "avg_wkly_wage",
                "naics_break",
            ],
        )
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"写入 {out_csv} ({len(out_rows)} 行)")


if __name__ == "__main__":
    main()
