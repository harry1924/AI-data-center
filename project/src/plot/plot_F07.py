"""
F07 就业结构：分县长序列（Loudoun County VA / Franklin County OH），2014–2025。

数据：data/processed/F07_employment_by_county.csv (BLS QCEW NAICS 518210)
输出：figures/{png,svg}/F07_employment_by_county.{png,svg}

必标：2022年NAICS修订断点（用竖直虚线+底色区分标注，不用连续线暗示可比）
"""

import csv
import sys
from pathlib import Path
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import CATEGORICAL, CAT_ORDER, INK_PRIMARY, INK_SECONDARY, INK_MUTED, GRIDLINE, apply_base_style, save_fig

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed" / "F07_employment_by_county.csv"
PNG_DIR = Path(__file__).resolve().parents[2] / "figures" / "png"
SVG_DIR = Path(__file__).resolve().parents[2] / "figures" / "svg"


def qtr_to_date(year, qtr):
    month = (qtr - 1) * 3 + 1
    return datetime(year, month, 1)


def main():
    rows = list(csv.DictReader(PROCESSED.open()))
    counties = sorted(set(r["county_name"] for r in rows))
    colors = {counties[0]: CATEGORICAL["blue"], counties[1]: CATEGORICAL["orange"]}

    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    apply_base_style(ax, fig)

    # 2022年NAICS修订断点：底色区分pre/post
    naics_break_date = datetime(2022, 1, 1)
    ax.axvspan(naics_break_date, datetime(2026, 1, 1), color=GRIDLINE, alpha=0.5, zorder=0)
    ax.axvline(naics_break_date, color=INK_MUTED, linewidth=1, linestyle="--", zorder=1)
    ax.text(
        naics_break_date, 0.98,
        " 2022年NAICS 518210定义修订",
        fontsize=8, color=INK_MUTED, va="top", ha="left",
        transform=ax.get_xaxis_transform(),
    )

    for county in counties:
        crows = [r for r in rows if r["county_name"] == county]
        crows.sort(key=lambda r: (int(r["year"]), int(r["qtr"])))
        dates = [qtr_to_date(int(r["year"]), int(r["qtr"])) for r in crows]
        emp = [int(r["month3_emplvl"]) for r in crows]
        ax.plot(dates, emp, color=colors[county], linewidth=2, solid_capstyle="round", label=county)
        ax.annotate(
            f"{emp[-1]:,}",
            xy=(dates[-1], emp[-1]),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color=colors[county],
        )

    ax.set_title(
        "数据中心密集县 vs 对照县：NAICS 518210就业人数，2014–2025",
        fontsize=13,
        fontweight="bold",
        color=INK_PRIMARY,
        loc="left",
        pad=14,
    )
    ax.set_ylabel("私营部门就业人数（季度末月）", fontsize=9.5)
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper left", frameon=False, fontsize=9.5, labelcolor=INK_SECONDARY)

    fig.text(
        0.01, -0.06,
        "数据源：BLS QCEW Open Data API, NAICS 518210, own_code=5(私营部门) | "
        "灰色底色=2022年NAICS修订后区间，518210定义变更，深浅两段不可直接连续解读为同一指标的延续 | "
        "Loudoun County VA为全球数据中心密度最高的县之一；Franklin County OH为对照",
        fontsize=7.8, color=INK_MUTED, wrap=True, transform=fig.transFigure,
    )

    save_fig(fig, PNG_DIR / "F07_employment_by_county.png", SVG_DIR / "F07_employment_by_county.svg")
    plt.close(fig)


if __name__ == "__main__":
    main()
