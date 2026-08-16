"""
F02补充图：企业AI采用率(工作场景AI使用深度)，2023-09至2026-08。

回答用户提出的需求："AI应用深度增加/工作中使用增加"的真实时间序列。
数据源：Census Bureau BTOS(Business Trends and Outlook Survey)核心AI问题，
        全国口径，双周颗粒度，76期。这是一手政府统计数据(A级)，不是WebSearch转述。

设计要点：
  - v1问法("生产商品/服务中使用AI")与v2问法("任意业务环节使用AI")问法不同，
    2025-11-17起v1停用换成v2，两条线用不同颜色+虚线分隔标注，绝不可连成一条线
  - "当前使用"与"预期6个月后使用"是两个不同问题，分开画，"预期"用浅色/虚线
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import CATEGORICAL, INK_PRIMARY, INK_SECONDARY, INK_MUTED, GRIDLINE, apply_base_style, save_fig

PROC = Path(__file__).resolve().parents[2] / "data" / "processed" / "F02_business_ai_adoption.csv"
PNG_DIR = Path(__file__).resolve().parents[2] / "figures" / "png"
SVG_DIR = Path(__file__).resolve().parents[2] / "figures" / "svg"

METRIC_STYLE = {
    "current_v1_goods_services": {"color": CATEGORICAL["blue"], "ls": "-", "label": "当前使用(生产商品/服务场景)"},
    "expected_v1_goods_services": {"color": CATEGORICAL["blue"], "ls": "--", "label": "预期6个月后使用(同一问法)"},
    "current_v2_any_function": {"color": CATEGORICAL["orange"], "ls": "-", "label": "当前使用(任意业务环节，新问法)"},
    "expected_v2_any_function": {"color": CATEGORICAL["orange"], "ls": "--", "label": "预期6个月后使用(新问法)"},
}
QUESTION_CHANGE_DATE = datetime(2025, 11, 17)


def main():
    rows = list(csv.DictReader(PROC.open()))
    by_metric = defaultdict(list)
    for r in rows:
        by_metric[r["metric"]].append((datetime.strptime(r["date"], "%Y-%m-%d"), float(r["pct"])))
    for m in by_metric:
        by_metric[m].sort()

    fig, ax = plt.subplots(figsize=(10, 5.5))
    apply_base_style(ax, fig)

    ax.axvline(QUESTION_CHANGE_DATE, color=INK_MUTED, linewidth=1, linestyle=":", zorder=1)
    ax.text(
        QUESTION_CHANGE_DATE, 0.97, " 2025-11-17起\n 问法改为更宽泛的\n “任意业务环节”",
        transform=ax.get_xaxis_transform(), fontsize=7.5, color=INK_MUTED, va="top", ha="left",
    )

    for metric, style in METRIC_STYLE.items():
        pts = by_metric.get(metric, [])
        if not pts:
            continue
        dates = [p[0] for p in pts]
        vals = [p[1] for p in pts]
        lw = 2.2 if style["ls"] == "-" else 1.4
        alpha = 1.0 if style["ls"] == "-" else 0.65
        ax.plot(dates, vals, color=style["color"], linestyle=style["ls"], linewidth=lw, alpha=alpha, label=style["label"])
        ax.annotate(
            f"{vals[-1]:.1f}%", xy=(dates[-1], vals[-1]), xytext=(6, 0), textcoords="offset points",
            va="center", fontsize=9, fontweight="bold", color=style["color"], alpha=alpha,
        )

    first_v1 = by_metric["current_v1_goods_services"][0]
    ax.annotate(
        f"{first_v1[1]:.1f}% ({first_v1[0].strftime('%Y-%m')})", xy=(first_v1[0], first_v1[1]),
        xytext=(0, -18), textcoords="offset points", fontsize=8.5, color=INK_MUTED,
    )

    ax.set_title(
        "企业AI采用率：\"在工作中使用AI\"的双周官方统计，2023–2026",
        fontsize=13, fontweight="bold", color=INK_PRIMARY, loc="left", pad=14,
    )
    ax.set_ylabel("%（受访企业中回答“是”的比例）", fontsize=9.5)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper left", frameon=False, fontsize=8.5, labelcolor=INK_SECONDARY)

    fig.text(
        0.01, -0.10,
        "数据源：U.S. Census Bureau, Business Trends and Outlook Survey (BTOS)，全国口径(州/行业/规模分层汇总)，"
        "双周采集，样本约1.2M家企业/年 | API: census.gov/hfp/btos/api（未在标准data.census.gov目录中，"
        "从前端JS逆向找到）| 蓝线=原问法\"生产商品或服务中使用AI\"(2023-09至2025-11)，橙线=新问法\"任意业务环节"
        "使用AI\"(2025-11起)，两者问法不同，图上刻意用不同颜色且不连线，避免暗示可比 | "
        "此图衡量的是\"企业/雇主\"层面的AI采用，与F02主图的Pew个人使用率(蓝线)是两个不同维度(组织 vs 个人)",
        fontsize=7.3, color=INK_MUTED, wrap=True, transform=fig.transFigure,
    )

    save_fig(
        fig,
        PNG_DIR / "F02_business_ai_adoption.png",
        SVG_DIR / "F02_business_ai_adoption.svg",
    )
    plt.close(fig)


if __name__ == "__main__":
    main()
