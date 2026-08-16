"""
F15 补充图：五大厂商资本开支前瞻(2025实际→2026官方指引→2027/2028分析师估计)。

数据：data/processed/F15_capex_outlook.csv (手工整理自各公司2026年最新财报电话会
官方口径 + 大摩Morgan Stanley对五大云厂商的统一建模估计，见该CSV的
source_name/source_url/note列)
输出：figures/{png,svg}/F15_capex_outlook.{png,svg}

设计说明：五家公司的财年边界、指引颗粒度、2027/2028数据完整度都不一样(MSFT/ORCL
用财年、AMZN/GOOGL/META用自然年；2027年官方大多不给具体数字，只有大摩用同一套
方法论给出的分析师估计；MSFT/GOOGL的2028、ORCL的2027-2028仍完全没有可用的具体
数字)，所以不用统一的"2025/2026/2027/2028"分组柱(会强行拉齐不可比的口径、并在
缺数字的格子里留白很怪)，改用五个小倍数子图，每家公司自己的时间轴、自己的柱子，
缺数据的格子用文字标注代替，不编造柱子。填充样式区分数据层级：实心=实际(SEC/官方
申报)，斜纹=公司官方前瞻指引，点纹+低透明度=第三方分析师估计(非官方，可信度更低，
且本身在2026年内已被上修过)。
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
                    i, 0.02, "无可靠\n数字", ha="center", va="bottom",
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
        "五大厂商资本开支前瞻：2025实际 → 2026官方指引 → 2027/2028分析师估计",
        fontsize=13.5, fontweight="bold", color=INK_PRIMARY, x=0.01, ha="left", y=1.12,
    )

    fig.text(
        0.01, -0.12,
        "数据源：实际值=SEC EDGAR XBRL(本项目F15主图，日历年求和；ORCL用官方财年口径55.7B以便与FY指引可比)；"
        "官方指引=各公司2026年最新一次财报电话会/新闻稿(转引自CNBC/CFO Dive/Intellectia等财经媒体)；"
        "2027/2028分析师估计=Morgan Stanley(大摩)对五大云厂商用同一套方法论的建模估计(转引自techtimes等财经媒体，"
        "无法直接访问原始研报核实)，单一机构来源，仅作补充标注，不代表市场普遍共识 | "
        "MSFT/ORCL用财年(MSFT:7-6月, ORCL:6-5月)，其余三家用自然年，各公司x轴刻度不代表同一时间窗口，不可跨公司直接对比x轴 | "
        "MSFT 2026指引从190B下修到175B是租赁会计分类调整(更多数据中心租约计入经营租赁而非资本开支)，非真实缩减 | "
        "ORCL FY2027的92.5B是gross口径，官方另给net(扣除客户预付/自供硬件报销约20-25B)约70B | "
        "大摩自己的估计在2026年内也被多次上修：META 2027从185.6B上修到225B(约+21%)、AMZN 2027上修约15%至308B、"
        "2028上修约29%至318B，说明分析师估计和官方指引一样不稳定、都在持续走高 | "
        "GOOGL 2027另有KuCoin引用的250B估计(比大摩284.8B低约14%)，反映分析师之间也有分歧 | "
        "MSFT/GOOGL的2028、ORCL的2027-2028仍未找到可靠的单一公司具体数字(只有五家合计约$1.4万亿这个总量级)，未强行编造",
        fontsize=7.4, color=INK_MUTED, wrap=True, transform=fig.transFigure,
    )

    save_fig(fig, PNG_DIR / "F15_capex_outlook.png", SVG_DIR / "F15_capex_outlook.svg")
    plt.close(fig)


if __name__ == "__main__":
    main()
