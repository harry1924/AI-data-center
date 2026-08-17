"""
F04：PJM容量拍卖出清价走势 + 独立市场监察人对"数据中心占比"的归因测算。

数据：data/processed/F04_pjm_capacity_price.csv、F04_pjm_dc_attribution.csv
输出：figures/{png,svg}/F04_pjm_capacity.{png,svg}

这是本项目从第一版数据缺口报告起就标注为"❌未获取"的缺口(PJM官网/Monitoring
Analytics官网本身在这个环境里一直被代理拦截，无法直接WebFetch)，这次用WebSearch
交叉核对4家以上独立媒体对PJM官方拍卖结果PDF、Monitoring Analytics报告的转引，
数字在多个来源间一致，作为退而求其次的核实方式(env_status标注为
obtained_via_secondary_corroboration，不是obtained)。

设计：上图=各交割年度容量出清价(RTO基准价柱状图 + 个别年份输电受限区域的
溢价用散点标出，2024/25年PEPCO、2025/26年BGE/DOM明显更高，2026/27起全区域
统一触顶)；下图=独立市场监察人测算的"数据中心占比"，三个数字口径不同
(占涨价增量的比例 vs 占总成本的比例 vs 累计四次拍卖)，用不同图案+文字标注区分，
不放在同一根柱子上强行比较。
"""

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import CATEGORICAL, INK_PRIMARY, INK_SECONDARY, INK_MUTED, apply_base_style, save_fig

PRICE_CSV = Path(__file__).resolve().parents[2] / "data" / "processed" / "F04_pjm_capacity_price.csv"
ATTR_CSV = Path(__file__).resolve().parents[2] / "data" / "processed" / "F04_pjm_dc_attribution.csv"
PNG_DIR = Path(__file__).resolve().parents[2] / "figures" / "png"
SVG_DIR = Path(__file__).resolve().parents[2] / "figures" / "svg"

YEARS = ["2024/25", "2025/26", "2026/27", "2027/28"]


def main():
    price_rows = list(csv.DictReader(PRICE_CSV.open()))
    attr_rows = list(csv.DictReader(ATTR_CSV.open()))

    by_year = {y: [] for y in YEARS}
    for r in price_rows:
        by_year[r["delivery_year"]].append(r)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(10, 7.6), gridspec_kw={"height_ratios": [1.7, 1], "hspace": 0.45},
    )
    apply_base_style(ax1, fig)
    apply_base_style(ax2, fig)

    x = range(len(YEARS))
    base_prices = []
    for i, y in enumerate(YEARS):
        recs = by_year[y]
        base = next(r for r in recs if "其余" in r["zone"] or "全部区域" in r["zone"])
        base_prices.append(float(base["price_usd_per_mwday"]))

    ax1.bar(x, base_prices, width=0.55, color=CATEGORICAL["blue"], zorder=2, label="RTO基准价(多数区域)")
    for i, p in enumerate(base_prices):
        ax1.annotate(f"${p:,.2f}", xy=(i, p), xytext=(0, 5), textcoords="offset points",
                     ha="center", fontsize=9.5, fontweight="bold", color=CATEGORICAL["blue"])

    # 输电受限区域的溢价散点(仅2024/25 PEPCO、2025/26 BGE/DOM有明显偏离)
    # 散点整体右移0.28个柱宽，并把文字进一步右移，避免和柱顶的RTO基准价标签重叠
    for i, y in enumerate(YEARS):
        for r in by_year[y]:
            if "其余" in r["zone"] or "全部区域" in r["zone"]:
                continue
            p = float(r["price_usd_per_mwday"])
            xp = i + 0.28
            ax1.scatter([xp], [p], color=CATEGORICAL["red"], s=55, zorder=3, edgecolor="white", linewidth=1)
            ax1.annotate(f"{r['zone'].split('(')[0]} ${p:,.0f}", xy=(xp, p), xytext=(8, 0),
                         textcoords="offset points", va="center", fontsize=8, color=CATEGORICAL["red"])

    ax1.set_xticks(list(x))
    ax1.set_xticklabels(YEARS, fontsize=10)
    ax1.set_ylabel("容量出清价 ($/MW-day)", fontsize=9.5)
    ax1.set_title(
        "PJM容量拍卖出清价：2024/25 → 2027/28交割年度",
        fontsize=13, fontweight="bold", color=INK_PRIMARY, loc="left", pad=12,
    )
    ax1.set_ylim(0, max(r["price_usd_per_mwday"] and float(r["price_usd_per_mwday"]) for r in price_rows) * 1.28)
    ax1.legend(loc="upper left", frameon=False, fontsize=8.5, labelcolor=INK_SECONDARY)

    # 下图：数据中心归因(三个不同口径)
    attr_labels = ["2025/26拍卖\n(占涨价增量)", "2027/28拍卖\n(占总成本)", "最近4次拍卖累计\n(占总成本)"]
    attr_pcts = [float(r["dc_pct"].rstrip("%")) for r in attr_rows]
    colors2 = [CATEGORICAL["orange"], CATEGORICAL["orange"], CATEGORICAL["orange"]]
    x2 = range(len(attr_rows))
    ax2.bar(x2, attr_pcts, width=0.5, color=colors2, alpha=0.85, zorder=2)
    for i, (pct, r) in enumerate(zip(attr_pcts, attr_rows)):
        extra = f"(${r['dc_usd_b']}B" + (f"/${r['total_usd_b']}B)" if r["total_usd_b"] else ")")
        ax2.annotate(f"{pct:.0f}% {extra}", xy=(i, pct), xytext=(0, 5), textcoords="offset points",
                     ha="center", fontsize=9, fontweight="bold", color=CATEGORICAL["orange"])
    ax2.set_xticks(list(x2))
    ax2.set_xticklabels(attr_labels, fontsize=8.6)
    ax2.set_ylabel("数据中心占比", fontsize=9.5)
    ax2.set_ylim(0, max(attr_pcts) * 1.35)
    ax2.set_title(
        "独立市场监察人(Monitoring Analytics)测算：数据中心在容量成本中的占比",
        fontsize=11, fontweight="bold", color=INK_PRIMARY, loc="left", pad=10,
    )

    fig.text(
        0.01, -0.14,
        "数据源：PJM官方Base Residual Auction结果(pjm.com，本环境WebFetch被拦截，经RTO Insider/"
        "EnergyChoiceMatters/Renewable Energy World/PJM新闻稿摘要等4家以上独立信源交叉核对数字一致，"
        "标注为二手交叉核实而非直接读取原始PDF) | "
        "数据中心占比数据源：Monitoring Analytics(PJM独立市场监察人)，经Utility Dive/IEEFA/ZeroHedge转引 | "
        "三个'数据中心占比'口径不同，不能直接比大小：2025/26那个是'占涨价增量的63%'(不是占总成本)，"
        "2027/28和累计两个是'占总成本的比例' | "
        "2026/27和2027/28两个交割年度全区域(含此前溢价明显的BGE/DOM)统一触及FERC批准的价格上限，"
        "不再是市场自由出清结果，这本身也是供给紧张程度的信号",
        fontsize=7.5, color=INK_MUTED, wrap=True, transform=fig.transFigure,
    )

    save_fig(fig, PNG_DIR / "F04_pjm_capacity.png", SVG_DIR / "F04_pjm_capacity.svg")
    plt.close(fig)


if __name__ == "__main__":
    main()
