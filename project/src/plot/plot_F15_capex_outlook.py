"""
F15 补充图：五大厂商资本开支前瞻(2025实际→2026/2027/2028指引或估计)。

数据：data/processed/F15_capex_outlook.csv (手工整理自各公司2026年最新财报电话会
官方口径 + 少量第三方分析师估计，见该CSV的source_name/source_url/note列)
输出：figures/{png,svg}/F15_capex_outlook.{png,svg}

设计说明：五家公司的财年边界、指引颗粒度、2027/2028数据完整度都不一样(MSFT/ORCL
用财年、AMZN/GOOGL/META用自然年；GOOGL/META的2027只有分析师估计、无官方数字；
AMZN 2027/2028、MSFT/GOOGL/META/ORCL的2028都完全没有具体数字)，所以不用统一的
"2025/2026/2027/2028"分组柱(会强行拉齐不可比的口径、并在缺数字的格子里留白很怪)，
改用五个小倍数子图，每家公司自己的时间轴、自己的柱子，缺数据的格子用文字标注
"无官方数字"代替，不编造柱子。填充样式区分数据层级：实心=实际(SEC申报)，
斜纹=公司官方前瞻指引，斜纹+低透明度=第三方分析师估计(非官方，可信度更低)。
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import CATEGORICAL, INK_PRIMARY, INK_SECONDARY, INK_MUTED, SURFACE, apply_base_style, save_fig

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed" / "F15_capex_outlook.csv"
PNG_DIR = Path(__file__).resolve().parents[2] / "figures" / "png"
SVG_DIR = Path(__file__).resolve().parents[2] / "figures" / "svg"

COMPANY_COLOR = {
    "MSFT": CATEGORICAL["blue"],
    "AMZN": CATEGORICAL["orange"],
    "GOOGL": CATEGORICAL["aqua"],
    "META": CATEGORICAL["yellow"],
    "ORCL": CATEGORICAL["magenta"],
}
COMPANY_ORDER = ["MSFT", "AMZN", "GOOGL", "META", "ORCL"]

TIER_STYLE = {
    "actual": dict(alpha=1.0, hatch=None),
    "official": dict(alpha=0.72, hatch="///"),
    "analyst": dict(alpha=0.42, hatch="..."),
}


def fmt_range(low, high, point):
    if low and high and low != high:
        return f"${low:g}–{high:g}B"
    return f"${point:g}B"


def main():
    rows = list(csv.DictReader(PROCESSED.open()))
    by_company = defaultdict(list)
    for r in rows:
        by_company[r["company"]].append(r)

    fig, axes = plt.subplots(1, 5, figsize=(16, 5.2))

    for ax, company in zip(axes, COMPANY_ORDER):
        apply_base_style(ax, fig)
        recs = by_company[company]
        # 保持CSV里的原始顺序(已按时间先后写好)
        x_labels = [r["period_label"] for r in recs]
        color = COMPANY_COLOR[company]

        y_max = 0
        for i, r in enumerate(recs):
            if r["period_type"] == "no_data":
                ax.text(
                    i, 0.02, "无官方\n数字", ha="center", va="bottom",
                    fontsize=7.3, color=INK_MUTED, transform=ax.get_xaxis_transform(),
                )
                continue
            point = float(r["point_usd_b"])
            style = TIER_STYLE[r["tier"]]
            ax.bar(
                i, point, width=0.62, color=color, zorder=2,
                alpha=style["alpha"], hatch=style["hatch"],
                edgecolor=color, linewidth=0.8,
            )
            label = fmt_range(
                float(r["low_usd_b"]) if r["low_usd_b"] else None,
                float(r["high_usd_b"]) if r["high_usd_b"] else None,
                point,
            )
            ax.annotate(
                label, xy=(i, point), xytext=(0, 3), textcoords="offset points",
                ha="center", fontsize=7.6, fontweight="bold", color=INK_PRIMARY,
            )
            y_max = max(y_max, point)

        ax.set_xticks(range(len(x_labels)))
        ax.set_xticklabels(x_labels, fontsize=8.3)
        ax.set_ylim(0, y_max * 1.28 if y_max else 1)
        ax.set_title(company, fontsize=12, fontweight="bold", color=color, loc="left", pad=10)
        if ax is axes[0]:
            ax.set_ylabel("资本开支 ($B)", fontsize=9)

    # 图例：数据层级(实心/斜纹/点纹)，与公司颜色区分开
    legend_ax = fig.add_axes([0.5, 0.90, 0.001, 0.001])
    legend_ax.axis("off")
    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=INK_SECONDARY, alpha=1.0, edgecolor=INK_SECONDARY, label="实际(SEC/官方财报)"),
        plt.Rectangle((0, 0), 1, 1, facecolor=INK_SECONDARY, alpha=0.72, hatch="///", edgecolor=INK_SECONDARY, label="官方前瞻指引"),
        plt.Rectangle((0, 0), 1, 1, facecolor=INK_SECONDARY, alpha=0.42, hatch="...", edgecolor=INK_SECONDARY, label="第三方分析师估计(非官方)"),
    ]
    fig.legend(
        handles=handles, loc="upper center", ncol=3, frameon=False, fontsize=9,
        labelcolor=INK_SECONDARY, bbox_to_anchor=(0.5, 1.04),
    )

    fig.suptitle(
        "五大厂商资本开支前瞻：2025实际 → 2026/2027(/2028)指引或估计",
        fontsize=13.5, fontweight="bold", color=INK_PRIMARY, x=0.01, ha="left", y=1.12,
    )

    fig.text(
        0.01, -0.10,
        "数据源：实际值=SEC EDGAR XBRL(本项目F15主图，日历年求和；ORCL用官方财年口径55.7B以便与FY指引可比)；"
        "官方指引=各公司2026年最新一次财报电话会/新闻稿(转引自CNBC/CFO Dive/Intellectia等财经媒体)；"
        "分析师估计=Citi/UBS/SemiAnalysis等第三方，方法论不透明，仅作补充标注 | "
        "MSFT/ORCL用财年(MSFT:7-6月, ORCL:6-5月)，其余三家用自然年，各公司x轴刻度不代表同一时间窗口，不可跨公司直接对比x轴 | "
        "MSFT 2026指引从190B下修到175B是租赁会计分类调整(更多数据中心租约计入经营租赁而非资本开支)，非真实缩减 | "
        "ORCL FY2027的92.5B是gross口径，官方另给net(扣除客户预付/自供硬件报销约20-25B)约70B | "
        "GOOGL 2027两个分析师估计(250B/308B)相差近25%，反映高度不确定性 | "
        "2028年除ORCL/MSFT定性表态'还会增长'外，五家均无任何具体数字，未强行编造",
        fontsize=7.6, color=INK_MUTED, wrap=True, transform=fig.transFigure,
    )

    save_fig(fig, PNG_DIR / "F15_capex_outlook.png", SVG_DIR / "F15_capex_outlook.svg")
    plt.close(fig)


if __name__ == "__main__":
    main()
