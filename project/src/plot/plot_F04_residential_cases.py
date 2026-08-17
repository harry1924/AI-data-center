"""
F04补充图：三个地区居民电价案例——总账单涨幅 vs 其中"数据中心相关容量成本"部分。

数据：data/processed/F04_residential_case_studies.csv
输出：figures/{png,svg}/F04_residential_cases.{png,svg}

这是对用户最初提供的DC/VA/UEC三个案例的重做版本。核实发现原三行都有问题
(算术对不上、UEC那行引用了另一家不相关电力公司的数字、且和一手资料的因果
表述相反，见对话记录)，这版改用统一口径：只采信"有名有姓的机构，把数据中心
相关容量成本从总账单涨幅里明确拆分出多少美元"这一类数字，拆不出来的就不编，
只画有依据的部分。DC 2025-06这一行能同时展示"总涨幅"和"其中数据中心部分"，
用背景浅色柱(总涨幅)+前景深色柱(数据中心相关部分)的嵌套柱表达；马里兰、俄亥俄
两行只有"数据中心相关部分"这一个数字、没有可比的总账单基准，只画这一段，
用文字标注"无可比总账单基准"。
"""

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import CATEGORICAL, INK_PRIMARY, INK_SECONDARY, INK_MUTED, apply_base_style, save_fig

CSV_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "F04_residential_case_studies.csv"
PNG_DIR = Path(__file__).resolve().parents[2] / "figures" / "png"
SVG_DIR = Path(__file__).resolve().parents[2] / "figures" / "svg"


def main():
    rows = list(csv.DictReader(CSV_PATH.open()))

    labels = [
        "华盛顿特区 Pepco\n2025-06",
        "华盛顿特区 Pepco\n2026-07",
        "马里兰州西部\nPotomac Edison, 2026",
        "俄亥俄州 AEP Ohio\n2026",
    ]

    fig, ax = plt.subplots(figsize=(9.5, 6))
    apply_base_style(ax, fig)

    x = range(len(rows))
    for i, r in enumerate(rows):
        total = float(r["total_change_usd"]) if r["total_change_usd"] else None
        attributed = float(r["dc_capacity_attributed_usd"]) if r["dc_capacity_attributed_usd"] else None

        if total is not None:
            ax.bar(i, total, width=0.55, color=CATEGORICAL["blue"], alpha=0.25, zorder=2)
            ax.annotate(
                f"总涨幅 ${total:,.2f}/月", xy=(i, total), xytext=(0, 4), textcoords="offset points",
                ha="center", fontsize=8.3, color=CATEGORICAL["blue"],
            )
        if attributed is not None:
            ax.bar(i, attributed, width=0.55, color=CATEGORICAL["red"], zorder=3)
            ax.annotate(
                f"数据中心相关\n${attributed:,.2f}/月", xy=(i, attributed / 2), ha="center", va="center",
                fontsize=8.6, fontweight="bold", color="white",
            )
        else:
            ax.text(
                i, 0.03, "无可拆分数字\n(仅列一个因素,\n未强行编造)", ha="center", va="bottom",
                fontsize=7.6, color=INK_MUTED, transform=ax.get_xaxis_transform(),
            )

        tier = r["attribution_tier"]
        tier_label = {"B": "B级(独立机构量化)", "C": "C级(方向一致,无量化拆分)"}[tier]
        ax.annotate(
            tier_label, xy=(i, -0.13), xycoords=("data", "axes fraction"),
            ha="center", fontsize=7.3, color=INK_MUTED,
        )

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("月度电费影响 ($)", fontsize=9.5)
    ax.set_ylim(0, 24)
    ax.set_title(
        "四个居民电价案例：总涨幅 vs 独立机构量化的\"数据中心相关容量成本\"部分",
        fontsize=12.5, fontweight="bold", color=INK_PRIMARY, loc="left", pad=14,
    )

    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor=CATEGORICAL["blue"], alpha=0.25, label="总账单涨幅(仅DC两行有可比基准)"),
        plt.Rectangle((0, 0), 1, 1, facecolor=CATEGORICAL["red"], label="其中：数据中心相关容量成本(独立机构量化)"),
    ]
    ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=8.5, labelcolor=INK_SECONDARY)

    fig.text(
        0.01, -0.16,
        "数据源：DC两行=DC Office of the People's Counsel + Synapse Energy Economics联合报告(2025-06)/"
        "DCPSC官方SOS费率说明(2026-07)；马里兰/俄亥俄两行=IEEFA报告'Projected data center growth spurs "
        "PJM capacity prices by factor of 10'，基于Monitoring Analytics的PJM容量成本归因测算 | "
        "DC 2025-06的before/after两个价格是用官方公布的+17.7%/+$20.81反推得到，不是独立引用的原始账单 | "
        "DC 2026-07、马里兰、俄亥俄暂无法找到与DC 2025-06同等细致的独立拆分依据，标注为C级或数据缺口，"
        "不代表这几个地区没有数据中心相关成本，只是没找到同等质量的量化拆分 | "
        "俄亥俄州AEP Ohio另有2026年4月约$7.90/月的BTCR输电费涨价(未计入本图)，且自2025-07-23起已实施"
        "数据中心专属关税(至少85%照付不议)以减少居民侧分摊，是值得注意的政策纠偏动作",
        fontsize=7.4, color=INK_MUTED, wrap=True, transform=fig.transFigure,
    )

    save_fig(fig, PNG_DIR / "F04_residential_cases.png", SVG_DIR / "F04_residential_cases.svg")
    plt.close(fig)


if __name__ == "__main__":
    main()
