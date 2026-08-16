"""
F03 补充图：密集州 vs 对照组电价年度差距，2021-2026。

数据：data/processed/F03_state_prices.csv (同F03主图数据源，按年度聚合)
输出：figures/{png,svg}/F03_annual_price_gap.{png,svg}

设计：F03主图是月度趋势线，这张是年度汇总视角，专门突出"差距"这个指标——
上图分组柱对比密集州/对照组年度均价，下图柱状图画差距百分比，避免双Y轴。
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import CATEGORICAL, INK_PRIMARY, INK_SECONDARY, INK_MUTED, apply_base_style, save_fig

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed" / "F03_state_prices.csv"
PNG_DIR = Path(__file__).resolve().parents[2] / "figures" / "png"
SVG_DIR = Path(__file__).resolve().parents[2] / "figures" / "svg"

YEARS = [str(y) for y in range(2021, 2027)]


def main():
    rows = list(csv.DictReader(PROCESSED.open()))
    by_group_period = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["group"] not in ("dense", "control"):
            continue
        by_group_period[r["group"]][r["period"]].append(float(r["price_cents_per_kwh"]))

    years, dense_avg, control_avg, gap_pct, month_counts = [], [], [], [], []
    for y in YEARS:
        periods = sorted(p for p in by_group_period["dense"] if p.startswith(y))
        if not periods:
            continue
        d = sum(sum(by_group_period["dense"][p]) / len(by_group_period["dense"][p]) for p in periods) / len(periods)
        c = sum(sum(by_group_period["control"][p]) / len(by_group_period["control"][p]) for p in periods) / len(periods)
        years.append(y)
        dense_avg.append(d)
        control_avg.append(c)
        gap_pct.append((d - c) / c * 100)
        month_counts.append(len(periods))

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(9, 7), sharex=True, gridspec_kw={"height_ratios": [1.6, 1], "hspace": 0.1},
    )
    apply_base_style(ax1, fig)
    apply_base_style(ax2, fig)

    x = range(len(years))
    w = 0.36
    ax1.bar([i - w / 2 for i in x], dense_avg, width=w, color=CATEGORICAL["orange"], label="密集州均价", zorder=2)
    ax1.bar([i + w / 2 for i in x], control_avg, width=w, color=CATEGORICAL["aqua"], label="对照组均价", zorder=2)
    for i, (d, c) in enumerate(zip(dense_avg, control_avg)):
        ax1.annotate(f"{d:.1f}", xy=(i - w / 2, d), xytext=(0, 3), textcoords="offset points",
                     ha="center", fontsize=8.5, color=CATEGORICAL["orange"], fontweight="bold")
        ax1.annotate(f"{c:.1f}", xy=(i + w / 2, c), xytext=(0, 3), textcoords="offset points",
                     ha="center", fontsize=8.5, color=CATEGORICAL["aqua"], fontweight="bold")

    ax1.set_ylabel("年均电价 (¢/kWh)", fontsize=9.5)
    ax1.set_title(
        "密集州 vs 对照组：居民电价年度差距，2021–2026",
        fontsize=13, fontweight="bold", color=INK_PRIMARY, loc="left", pad=14,
    )
    ax1.legend(loc="upper left", frameon=False, fontsize=9.5, labelcolor=INK_SECONDARY)
    ax1.set_ylim(0, max(dense_avg) * 1.22)

    ax2.bar(x, gap_pct, width=0.55, color=CATEGORICAL["red"], zorder=2)
    for i, g in enumerate(gap_pct):
        ax2.annotate(f"+{g:.1f}%", xy=(i, g), xytext=(0, 4), textcoords="offset points",
                     ha="center", fontsize=9, fontweight="bold", color=CATEGORICAL["red"])
    ax2.set_ylabel("差距 (%)", fontsize=9.5)
    ax2.set_ylim(0, max(gap_pct) * 1.25)

    labels = [f"{y}\n({m}个月)" if m < 12 else y for y, m in zip(years, month_counts)]
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(labels, fontsize=9.5)

    fig.text(
        0.01, -0.05,
        "数据源：同F03主图(EIA API v2 electricity/retail-sales, sectorid=RES) | "
        "密集州=VA/OH/IL/MD/AZ/GA简单平均，对照组=WY/ND/MT简单平均，均为文档规划指定的州名单，"
        "非独立验证过数据中心装机容量排名 | 2026年仅5个月数据(至5月)，其余年份均为完整12个月 | "
        "差距从2021年13.4%在2022年跳升到24.1%后持续扩大，2024年曾小幅回落",
        fontsize=7.8, color=INK_MUTED, wrap=True, transform=fig.transFigure,
    )

    save_fig(fig, PNG_DIR / "F03_annual_price_gap.png", SVG_DIR / "F03_annual_price_gap.svg")
    plt.close(fig)


if __name__ == "__main__":
    main()
