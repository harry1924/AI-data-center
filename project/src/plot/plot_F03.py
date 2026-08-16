"""
F03 电价长序列：全国 vs 数据中心密集州 vs 低密度对照组，2015-01至2026-05。

数据：data/processed/F03_state_prices.csv (EIA API v2 electricity/retail-sales, sectorid=RES)
输出：figures/{png,svg}/F03_electricity_price_national.{png,svg}

设计：密集州(VA/OH/IL/MD/AZ/GA)和对照州(WY/VT/MT)各自的6/3条线不逐一画出
(避免10条线的色板超载)，改为"组内均值线+min-max包络带"，3个分组共3个categorical
色相(蓝=全国 橙=密集州 青=对照组)，符合dataviz方法论的色板容量上限。
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import CATEGORICAL, INK_PRIMARY, INK_SECONDARY, INK_MUTED, apply_base_style, save_fig

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed" / "F03_state_prices.csv"
PNG_DIR = Path(__file__).resolve().parents[2] / "figures" / "png"
SVG_DIR = Path(__file__).resolve().parents[2] / "figures" / "svg"

GROUP_COLOR = {"national": CATEGORICAL["blue"], "dense": CATEGORICAL["orange"], "control": CATEGORICAL["aqua"]}
GROUP_LABEL = {
    "national": "全国均值",
    "dense": "数据中心密集州(VA/OH/IL/MD/AZ/GA)",
    "control": "低密度对照组(WY/ND/MT)",
}


def main():
    rows = list(csv.DictReader(PROCESSED.open()))
    by_group_period = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["group"] not in GROUP_COLOR:
            continue
        by_group_period[r["group"]][r["period"]].append(float(r["price_cents_per_kwh"]))

    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    apply_base_style(ax, fig)

    end_labels = []
    for group in ["control", "dense", "national"]:
        period_vals = by_group_period[group]
        periods = sorted(period_vals.keys())
        dates = [datetime.strptime(p, "%Y-%m") for p in periods]
        means = [sum(period_vals[p]) / len(period_vals[p]) for p in periods]
        mins = [min(period_vals[p]) for p in periods]
        maxs = [max(period_vals[p]) for p in periods]

        color = GROUP_COLOR[group]
        if group != "national":
            ax.fill_between(dates, mins, maxs, color=color, alpha=0.13, linewidth=0, zorder=1)
        lw = 2.4 if group == "national" else 2
        ax.plot(dates, means, color=color, linewidth=lw, solid_capstyle="round", label=GROUP_LABEL[group], zorder=3)
        end_labels.append((dates[-1], means[-1], color))

    # 末端数值标签统一按值排序后错开纵向位置，避免三条线终点太近时文字重叠
    end_labels.sort(key=lambda t: t[1])
    min_gap = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.045
    adjusted_y = []
    for _, y, _ in end_labels:
        if adjusted_y and y - adjusted_y[-1] < min_gap:
            y = adjusted_y[-1] + min_gap
        adjusted_y.append(y)
    label_x = end_labels[0][0] + timedelta(days=45)
    for (orig_x, orig_y, color), y_pos in zip(end_labels, adjusted_y):
        if abs(y_pos - orig_y) > min_gap * 0.5:
            ax.plot([orig_x, label_x], [orig_y, y_pos], color=color, lw=0.6, alpha=0.5, zorder=2)
        ax.text(label_x, y_pos, f"{orig_y:.1f}¢", ha="left", va="center", fontsize=9.5, fontweight="bold", color=color)

    ax.set_title(
        "居民电价：全国 vs 数据中心密集州 vs 低密度对照组，2015–2026",
        fontsize=13, fontweight="bold", color=INK_PRIMARY, loc="left", pad=14,
    )
    ax.set_ylabel("¢/kWh（美分/千瓦时，名义值，居民部门）", fontsize=9.5)
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_ylim(bottom=0)
    ax.set_xlim(right=end_labels[0][0] + timedelta(days=220))
    ax.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=INK_SECONDARY)

    fig.text(
        0.01, -0.07,
        "数据源：EIA API v2 electricity/retail-sales, sectorid=RES(居民部门) | "
        "阴影带=组内州的月度最小-最大值范围，非置信区间 | "
        "密集州/对照组线为组内简单平均，非按用电量加权 | "
        "[注] 2026年3月密集州阴影带顶端的尖峰来自马里兰州单月飙升至35.85¢/kWh(2月20.08¢→"
        "3月35.85¢→4月22.07¢)，真实EIA数据，非异常剔除；具体成因待核实，可能与PJM容量市场"
        "费用结算周期(见F04)有关",
        fontsize=7.8, color=INK_MUTED, wrap=True, transform=fig.transFigure,
    )

    save_fig(fig, PNG_DIR / "F03_electricity_price_national.png", SVG_DIR / "F03_electricity_price_national.svg")
    plt.close(fig)


if __name__ == "__main__":
    main()
