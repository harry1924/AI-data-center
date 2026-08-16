"""
F02补充图：AI付费客户情况（回应用户"AI付费客户在增加吗"的问题）。

数据：data/raw/manual/bofa_ai_payments_2026-08-16.csv
性质说明：这不是一条密集的时间序列图——美国银行研究所(B级，基于自有信用卡/ACH交易数据，
非全国代表性抽样)只公开了起止两个精确锚点(2024年均值=100, 2026年2月=138)，
中间月度走势虽然在其报告里以图表形式呈现，但PDF是矢量图非数据表格，为避免编造未经证实的
中间读数，这里只用报告文字明确给出的精确数字，不做逐月插值。

图型：左侧使用真实的三个B级统计做成横向条形图(households paying, index growth, spend
tier growth)；右侧把ChatGPT付费订阅数(C级，单一公司口径，媒体转述)作为里程碑散点标注，
不连成线，明确标注为"非独立审计口径，仅供参考"。
"""

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import CATEGORICAL, INK_PRIMARY, INK_SECONDARY, INK_MUTED, GRIDLINE, apply_base_style, save_fig

RAW = Path(__file__).resolve().parents[2] / "data" / "raw" / "manual" / "bofa_ai_payments_2026-08-16.csv"
PNG_DIR = Path(__file__).resolve().parents[2] / "figures" / "png"
SVG_DIR = Path(__file__).resolve().parents[2] / "figures" / "svg"


def main():
    rows = list(csv.DictReader(RAW.open()))
    by_metric = {}
    for r in rows:
        by_metric.setdefault(r["metric"], []).append(r)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 5), gridspec_kw={"width_ratios": [1, 1.3], "wspace": 0.32})
    apply_base_style(ax1, fig)
    apply_base_style(ax2, fig)

    # --- 左：美国银行研究所家庭AI付费指数 (仅两个精确锚点) ---
    idx_2024 = 100
    idx_2026 = float(by_metric["households_paying_index_2026_02"][0]["value"])
    ax1.bar([0, 1], [idx_2024, idx_2026], color=[GRIDLINE, CATEGORICAL["blue"]], width=0.55, zorder=2)
    ax1.set_xticks([0, 1])
    ax1.set_xticklabels(["2024年均值\n(基准=100)", "2026年2月"], fontsize=9.5)
    ax1.set_ylabel("家庭AI付费数量指数(2024均值=100)", fontsize=9)
    ax1.annotate(f"{idx_2026:.0f}\n(+38%)", xy=(1, idx_2026), xytext=(0, 6), textcoords="offset points",
                 ha="center", fontsize=10.5, fontweight="bold", color=CATEGORICAL["blue"])
    ax1.annotate("100", xy=(0, idx_2024), xytext=(0, 6), textcoords="offset points",
                 ha="center", fontsize=10.5, fontweight="bold", color=INK_SECONDARY)
    ax1.set_title("美国家庭AI付费数量", fontsize=11.5, fontweight="bold", color=INK_PRIMARY, loc="left", pad=10)
    ax1.set_ylim(0, idx_2026 * 1.25)

    # --- 右：ChatGPT付费订阅里程碑(C级，单一公司口径，仅作散点参考) ---
    milestone_rows = sorted(
        [r for r in rows if r["metric"] == "chatgpt_paid_subscribers_millions"],
        key=lambda r: r["period"],
    )
    labels = [r["period"] for r in milestone_rows]
    values = [float(r["value"]) for r in milestone_rows]
    x = range(len(labels))
    ax2.scatter(x, values, color=CATEGORICAL["red"], s=55, zorder=3)
    ax2.plot(x, values, color=CATEGORICAL["red"], linewidth=1, linestyle=":", alpha=0.4, zorder=2)
    for xi, v in zip(x, values):
        ax2.annotate(f"{v:g}M", xy=(xi, v), xytext=(0, 8), textcoords="offset points",
                     ha="center", fontsize=8.5, color=CATEGORICAL["red"])
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(labels, fontsize=8, rotation=20, ha="right")
    ax2.set_ylabel("百万付费订阅用户", fontsize=9)
    ax2.set_title(
        "ChatGPT付费订阅数(公司自述，媒体转述口径)", fontsize=11.5, fontweight="bold", color=INK_PRIMARY, loc="left", pad=10,
    )

    fig.suptitle("AI付费客户：真实但稀疏的证据", fontsize=14, fontweight="bold", color=INK_PRIMARY, x=0.01, ha="left", y=1.04)

    fig.text(
        0.01, -0.13,
        "左图数据源：Bank of America Institute《Not quite mAInstream》(2026-03-30)，基于美国银行自有信用卡/ACH"
        "交易数据识别AI商户消费，非全国代表性抽样，只覆盖该行活跃零售/理财客户 | 2026年2月：约3%的美国银行家庭"
        "为AI服务付费，家庭月支出中位数$20(+10.4% YoY)，$21-40档位家庭占比较2024年+50%，7%家庭月支出超$100 | "
        "指数图仅采用报告文字明确给出的两个精确锚点，未对报告内矢量图表做逐月像素读数以避免编造未经证实的中间值 | "
        "右图数据源：第三方统计聚合站(Business of Apps等)转述OpenAI公司自身披露的里程碑数字，非独立审计，"
        "非连续序列，图上刻意用散点+虚线弱连接而非实线，避免暗示为精确连续增长曲线",
        fontsize=7.2, color=INK_MUTED, wrap=True, transform=fig.transFigure,
    )

    save_fig(fig, PNG_DIR / "F02_ai_paying_customers.png", SVG_DIR / "F02_ai_paying_customers.svg")
    plt.close(fig)


if __name__ == "__main__":
    main()
