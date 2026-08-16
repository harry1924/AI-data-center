"""
F15 四大厂商资本开支季度序列。

数据：data/processed/F15_capex_quarterly.csv (SEC EDGAR XBRL)
输出：figures/{png,svg}/F15_capex_quarterly.{png,svg}

设计说明：文档原规格是"堆叠柱(资本开支)+折线(capex/OCF比率)双轴"。
按dataviz方法论的反模式清单，双y轴图表是首位反模式(两个不同量纲的指标
应该拆成两个图/小倍数，而不是共享一个X轴分刻两个Y轴)，这里改为上下两个
子图共享X轴：上图=四家堆叠柱(资本开支，单位$B)，下图=整体capex/OCF比率(单位%)。
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import CATEGORICAL, INK_PRIMARY, INK_SECONDARY, INK_MUTED, apply_base_style, save_fig

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed" / "F15_capex_quarterly.csv"
PNG_DIR = Path(__file__).resolve().parents[2] / "figures" / "png"
SVG_DIR = Path(__file__).resolve().parents[2] / "figures" / "svg"

COMPANY_COLOR = {
    "MSFT": CATEGORICAL["blue"],
    "AMZN": CATEGORICAL["orange"],
    "GOOGL": CATEGORICAL["aqua"],
    "META": CATEGORICAL["yellow"],
}
COMPANY_ORDER = ["MSFT", "AMZN", "GOOGL", "META"]


def main():
    rows = list(csv.DictReader(PROCESSED.open()))
    quarters = sorted(set(r["calendar_quarter"] for r in rows))

    capex_by_q_company = defaultdict(dict)
    ocf_total_by_q = defaultdict(float)
    capex_total_by_q = defaultdict(float)
    for r in rows:
        q, c = r["calendar_quarter"], r["company"]
        capex = int(r["capex_usd"]) / 1e9
        ocf = int(r["ocf_usd"]) / 1e9
        capex_by_q_company[q][c] = capex
        ocf_total_by_q[q] += ocf
        capex_total_by_q[q] += capex

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(11, 7.5), sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1], "hspace": 0.12},
    )
    apply_base_style(ax1, fig)
    apply_base_style(ax2, fig)

    x = range(len(quarters))
    bottoms = [0.0] * len(quarters)
    for company in COMPANY_ORDER:
        vals = [capex_by_q_company[q].get(company, 0.0) for q in quarters]
        ax1.bar(x, vals, bottom=bottoms, color=COMPANY_COLOR[company], width=0.75, label=company, zorder=2)
        bottoms = [b + v for b, v in zip(bottoms, vals)]

    ax1.set_ylabel("季度资本开支（$B，十亿美元）", fontsize=9.5)
    ax1.set_title(
        "四大厂商资本开支季度序列，2015Q1–2026Q2",
        fontsize=13, fontweight="bold", color=INK_PRIMARY, loc="left", pad=14,
    )
    ax1.legend(loc="upper left", frameon=False, fontsize=9.5, ncol=4, labelcolor=INK_SECONDARY)

    ratio = [
        (capex_total_by_q[q] / ocf_total_by_q[q] * 100) if ocf_total_by_q[q] else None
        for q in quarters
    ]
    ax2.plot(x, ratio, color=CATEGORICAL["red"], linewidth=2, solid_capstyle="round", zorder=2)
    ax2.set_ylabel("资本开支/经营现金流 (%)", fontsize=9.5)
    ax2.set_ylim(0, max(v for v in ratio if v) * 1.15)

    last_val = ratio[-1]
    ax2.annotate(
        f"{last_val:.0f}%", xy=(x[-1], last_val), xytext=(8, 0),
        textcoords="offset points", va="center", fontsize=10, fontweight="bold", color=CATEGORICAL["red"],
    )

    tick_step = max(len(quarters) // 12, 1)
    tick_idx = list(range(0, len(quarters), tick_step))
    ax2.set_xticks(tick_idx)
    ax2.set_xticklabels([quarters[i] for i in tick_idx], rotation=45, ha="right", fontsize=8)

    fig.text(
        0.01, -0.02,
        "数据源：SEC EDGAR XBRL companyfacts API，标签PaymentsToAcquirePropertyPlantAndEquipment(资本开支)、"
        "NetCashProvidedByUsedInOperatingActivities(经营现金流) | 按财季结束日期换算为日历季度，"
        "MSFT财年6月结束但已按日历季对齐，可与其余三家直接比较 | 下图比率=四家合计资本开支/合计经营现金流",
        fontsize=7.8, color=INK_MUTED, wrap=True, transform=fig.transFigure,
    )

    save_fig(fig, PNG_DIR / "F15_capex_quarterly.png", SVG_DIR / "F15_capex_quarterly.svg")
    plt.close(fig)


if __name__ == "__main__":
    main()
