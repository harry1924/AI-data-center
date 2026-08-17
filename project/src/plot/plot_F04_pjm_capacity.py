"""
F04：PJM容量拍卖出清价走势(2021/22-2028/29) + 独立市场监察人对"数据中心占比"的归因测算。

数据：data/processed/F04_pjm_capacity_price.csv、F04_pjm_dc_attribution.csv
输出：figures/{png,svg}/F04_pjm_capacity.{png,svg}

这是本项目从第一版数据缺口报告起就标注为"❌未获取"的缺口(PJM官网/Monitoring
Analytics官网本身在这个环境里一直被代理拦截，无法直接WebFetch)，用WebSearch
交叉核对多家独立媒体对PJM官方拍卖结果PDF、Monitoring Analytics报告的转引，
数字在多个来源间一致，作为退而求其次的核实方式(env_status标注为
obtained_via_secondary_corroboration，不是obtained)。

2026-08-17第二次修订：应用户要求把历史往前补到2021/22交割年度(此前只画了
2024/25起的4年，用户问"能不能说明数据中心导致电价上升"，指出没有更早的
基线数据就没法判断2024/25是不是本来就异常)。这版能看到一个重要的V形走势：
2021/22→2024/25出清价连续3年走低(MOPR新规带来更多低价资源中标)，2025/26
才突然反转暴涨——这个"先降后反转暴涨"的形态，比单纯"一路上涨"更能说明
2025/26的暴涨是一次结构性转折，而不是某个长期趋势的自然延续。
2019/20、2020/21两个交割年度因FERC对MOPR规则的复议程序，PJM暂停了常规拍卖
排期，没有产出可比的单一出清价，图上用一个跳空标记出来，不编造数字。

设计：上图=各交割年度容量出清价，本质只是时间线/相关性证据；下图=独立市场
监察人做的反事实测算(把数据中心负荷从模型里剔除、重新计算出清价)，这才是
真正的归因证据。两者刻意分成两个图、并各自标注证据性质，避免读者把"两条线
一起涨"本身当成因果证明。
"""

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import CATEGORICAL, INK_PRIMARY, INK_SECONDARY, INK_MUTED, GRIDLINE, apply_base_style, save_fig

PRICE_CSV = Path(__file__).resolve().parents[2] / "data" / "processed" / "F04_pjm_capacity_price.csv"
ATTR_CSV = Path(__file__).resolve().parents[2] / "data" / "processed" / "F04_pjm_dc_attribution.csv"
PNG_DIR = Path(__file__).resolve().parents[2] / "figures" / "png"
SVG_DIR = Path(__file__).resolve().parents[2] / "figures" / "svg"

YEARS = ["2021/22", "2022/23", "2023/24", "2024/25", "2025/26", "2026/27", "2027/28", "2028/29"]
GAP_AFTER = "2021/22"  # 2019/20、2020/21缺口标在这一年之后


def main():
    price_rows = list(csv.DictReader(PRICE_CSV.open()))
    attr_rows = list(csv.DictReader(ATTR_CSV.open()))

    by_year = {y: [] for y in YEARS}
    for r in price_rows:
        by_year[r["delivery_year"]].append(r)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(13, 7.8), gridspec_kw={"height_ratios": [1.7, 1], "hspace": 0.5},
    )
    apply_base_style(ax1, fig)
    apply_base_style(ax2, fig)

    x = list(range(len(YEARS)))
    base_prices = []
    for i, y in enumerate(YEARS):
        recs = by_year[y]
        base = next(r for r in recs if "其余" in r["zone"] or "全部区域" in r["zone"])
        base_prices.append(float(base["price_usd_per_mwday"]))

    bar_colors = [
        CATEGORICAL["aqua"] if i <= YEARS.index("2024/25") else CATEGORICAL["blue"]
        for i in range(len(YEARS))
    ]
    ax1.bar(x, base_prices, width=0.55, color=bar_colors, zorder=2)
    for i, p in enumerate(base_prices):
        ax1.annotate(f"${p:,.2f}", xy=(i, p), xytext=(0, 5), textcoords="offset points",
                     ha="center", fontsize=9, fontweight="bold", color=bar_colors[i])

    # 输电受限区域的溢价散点：早年(2023/24 MAAC $49、2024/25 PEPCO $49)绝对金额太小、
    # 紧贴X轴，标了反而和柱顶标签/坐标轴打架，这两年的溢价改成只写进脚注，图上只标
    # 2025/26 BGE/DOM这种数值大、有空间容纳标注的年份
    for i, y in enumerate(YEARS):
        for r in by_year[y]:
            if "其余" in r["zone"] or "全部区域" in r["zone"]:
                continue
            p = float(r["price_usd_per_mwday"])
            if p < 100:
                continue
            xp = i + 0.30
            ax1.scatter([xp], [p], color=CATEGORICAL["red"], s=45, zorder=3, edgecolor="white", linewidth=1)
            ax1.annotate(f"{r['zone'].split('(')[0]} ${p:,.0f}", xy=(xp, p), xytext=(7, 0),
                         textcoords="offset points", va="center", fontsize=7.3, color=CATEGORICAL["red"])

    # 2019/20、2020/21缺口标记(MOPR复议程序导致拍卖停摆)
    gap_x = YEARS.index(GAP_AFTER) + 0.5
    ax1.axvline(gap_x, color=INK_MUTED, linewidth=1, linestyle=(0, (1, 2)), zorder=1)
    ax1.annotate(
        "... 2019/20、2020/21\n因MOPR复议程序停摆\n(无可比出清价，未编造) ...",
        xy=(gap_x, ax1.get_ylim()[1]), xytext=(0, 0), textcoords="offset points",
        ha="center", va="top", fontsize=7, color=INK_MUTED, style="italic",
    )

    ax1.set_xticks(x)
    ax1.set_xticklabels(YEARS, fontsize=9.5)
    ax1.set_ylabel("容量出清价 ($/MW-day)", fontsize=9.5)
    ax1.set_title(
        "① PJM容量拍卖出清价走势：2021/22 → 2028/29交割年度（时间线，相关性证据）",
        fontsize=12.5, fontweight="bold", color=INK_PRIMARY, loc="left", pad=12,
    )
    ax1.set_ylim(0, max(float(r["price_usd_per_mwday"]) for r in price_rows) * 1.3)

    handles1 = [
        plt.Rectangle((0, 0), 1, 1, facecolor=CATEGORICAL["aqua"], label="MOPR新规影响期：连续走低"),
        plt.Rectangle((0, 0), 1, 1, facecolor=CATEGORICAL["blue"], label="数据中心负荷计入后：反转暴涨"),
    ]
    ax1.legend(handles=handles1, loc="upper left", frameon=False, fontsize=8.3, labelcolor=INK_SECONDARY)

    # 下图：数据中心归因(三个不同口径)
    attr_labels = ["2025/26拍卖\n(占涨价增量)", "2027/28拍卖\n(占总成本)", "最近4次拍卖累计\n(占总成本)"]
    attr_pcts = [float(r["dc_pct"].rstrip("%")) for r in attr_rows]
    x2 = range(len(attr_rows))
    ax2.bar(x2, attr_pcts, width=0.5, color=CATEGORICAL["orange"], alpha=0.85, zorder=2)
    for i, (pct, r) in enumerate(zip(attr_pcts, attr_rows)):
        extra = f"(${r['dc_usd_b']}B" + (f"/${r['total_usd_b']}B)" if r["total_usd_b"] else ")")
        ax2.annotate(f"{pct:.0f}% {extra}", xy=(i, pct), xytext=(0, 5), textcoords="offset points",
                     ha="center", fontsize=9, fontweight="bold", color=CATEGORICAL["orange"])
    ax2.set_xticks(list(x2))
    ax2.set_xticklabels(attr_labels, fontsize=8.6)
    ax2.set_ylabel("数据中心占比", fontsize=9.5)
    ax2.set_ylim(0, max(attr_pcts) * 1.35)
    ax2.set_title(
        "② 独立市场监察人反事实测算：数据中心在容量成本中的占比（归因证据）",
        fontsize=12.5, fontweight="bold", color=INK_PRIMARY, loc="left", pad=10,
    )

    fig.text(
        0.01, -0.15,
        "数据源：PJM官方Base Residual Auction结果(pjm.com，本环境WebFetch被拦截，经RTO Insider/"
        "EnergyChoiceMatters/Renewable Energy World/PJM新闻稿摘要/KilowattLogic等多家独立信源交叉核对数字一致，"
        "标注为二手交叉核实而非直接读取原始PDF)；数据中心占比数据源：Monitoring Analytics(PJM独立市场监察人)，"
        "经Utility Dive/IEEFA/ZeroHedge转引 | "
        "①图和②图证据性质不同：①图只是把历年出清价按时间排列，价格上涨和数据中心负荷增长同时发生，"
        "这本身只是相关性、不是因果证明(电厂退役、燃料价格等其他因素同期也在变化)；②图是Monitoring Analytics"
        "用PJM实际的供需出清模型做的反事实测算(把数据中心负荷预测从模型里剔除、重新计算出清价)，"
        "才是把'数据中心'这一变量单独隔离出来的归因证据 | "
        "三个'数据中心占比'口径不同，不能直接比大小：2025/26那个是'占涨价增量的63%'(不是占总成本)，"
        "2027/28和累计两个是'占总成本的比例' | "
        "2021/22→2024/25出清价连续走低是MOPR新规扩大合格资源范围所致，与需求侧无关；2025/26起反转暴涨，"
        "2026/27、2027/28两个交割年度全区域统一触及FERC批准的价格上限，2028/29小幅回落但仍是2024/25基准价的11倍 | "
        "2023/24、2024/25两年也有输电受限区域溢价(MAAC \\$49.49，PEPCO \\$49.49)，但绝对金额较小、贴近坐标轴，"
        "图上未标注以免和柱顶数字重叠，仅在此说明",

        fontsize=7.3, color=INK_MUTED, wrap=True, transform=fig.transFigure,
    )

    save_fig(fig, PNG_DIR / "F04_pjm_capacity.png", SVG_DIR / "F04_pjm_capacity.svg")
    plt.close(fig)


if __name__ == "__main__":
    main()
