"""
F09 并网队列时长与完成率（本报告的定盘星）。

数据：data/processed/F09_duration_ir_to_cod.csv, F09_completion_rate.csv, F09_annual_capacity.csv
      (源自LBNL Queued Up官方原始数据，用户提供，2026-08-16)
输出：figures/{png,svg}/F09_interconnection_queue_duration.{png,svg}

设计：三面板布局(左侧大图+右侧上下两个小图)，避免双轴：
  左：中位并网时长(月)+p25-p75包络带，2005-2025
  右上：完成率(%)，按申请年份cohort——必须标注"近年cohort因样本尚未成熟而系统性偏低"
        (右截尾偏差：2023年入队的项目不太可能在2025年底就已完成，不代表"完成率在崩溃")
  右下：年度新增申请容量(GW)，2000-2025
"""

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import CATEGORICAL, INK_PRIMARY, INK_SECONDARY, INK_MUTED, GRIDLINE, apply_base_style, save_fig

PROC = Path(__file__).resolve().parents[2] / "data" / "processed"
PNG_DIR = Path(__file__).resolve().parents[2] / "figures" / "png"
SVG_DIR = Path(__file__).resolve().parents[2] / "figures" / "svg"

MATURE_COHORT_CUTOFF = 2020  # 2020年及以前入队的项目，样本基本"成熟"(已有足够时间走完流程)


def main():
    duration = list(csv.DictReader((PROC / "F09_duration_ir_to_cod.csv").open()))
    completion = list(csv.DictReader((PROC / "F09_completion_rate.csv").open()))
    capacity = list(csv.DictReader((PROC / "F09_annual_capacity.csv").open()))

    fig = plt.figure(figsize=(12, 6.5))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.5, 1], height_ratios=[1, 1], wspace=0.28, hspace=0.45)
    ax_dur = fig.add_subplot(gs[:, 0])
    ax_comp = fig.add_subplot(gs[0, 1])
    ax_cap = fig.add_subplot(gs[1, 1])
    for ax in (ax_dur, ax_comp, ax_cap):
        apply_base_style(ax, fig)

    # --- 左：中位并网时长 ---
    years = [int(r["year"]) for r in duration]
    medians = [float(r["median"]) for r in duration]
    p25 = [float(r["p25"]) for r in duration]
    p75 = [float(r["p75"]) for r in duration]
    ax_dur.fill_between(years, p25, p75, color=CATEGORICAL["blue"], alpha=0.15, linewidth=0, label="p25–p75区间")
    ax_dur.plot(years, medians, color=CATEGORICAL["blue"], linewidth=2.4, marker="o", markersize=4, label="中位数")
    ax_dur.annotate(
        f"{medians[-1]:.0f}个月", xy=(years[-1], medians[-1]), xytext=(8, 4),
        textcoords="offset points", fontsize=11, fontweight="bold", color=CATEGORICAL["blue"],
    )
    ax_dur.annotate(
        f"{medians[0]:.0f}个月 ({years[0]})", xy=(years[0], medians[0]), xytext=(4, -16),
        textcoords="offset points", fontsize=9, color=INK_MUTED,
    )
    ax_dur.set_title(
        "中位并网时长(申请→商运)，2005–2025", fontsize=12.5, fontweight="bold", color=INK_PRIMARY, loc="left", pad=10,
    )
    ax_dur.set_ylabel("月", fontsize=9.5)
    ax_dur.set_xlim(years[0] - 0.5, years[-1] + 1.5)
    ax_dur.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=INK_SECONDARY)

    # --- 右上：完成率 ---
    c_years = [int(r["request_year"]) for r in completion]
    c_rate = [float(r["completion_rate_pct"]) for r in completion]
    mature = [(y, v) for y, v in zip(c_years, c_rate) if y <= MATURE_COHORT_CUTOFF]
    immature = [(y, v) for y, v in zip(c_years, c_rate) if y >= MATURE_COHORT_CUTOFF]
    my, mv = zip(*mature)
    iy, iv = zip(*immature)
    ax_comp.plot(my, mv, color=CATEGORICAL["aqua"], linewidth=2, marker="o", markersize=3.5, label="样本已成熟")
    ax_comp.plot(iy, iv, color=CATEGORICAL["aqua"], linewidth=2, linestyle=":", marker="o", markersize=3.5, alpha=0.55, label="样本未成熟(右截尾)")
    ax_comp.set_title("完成率：按申请年份cohort(%)", fontsize=11, fontweight="bold", color=INK_PRIMARY, loc="left", pad=8)
    ax_comp.set_ylabel("%", fontsize=9)
    ax_comp.legend(loc="upper right", frameon=False, fontsize=7.8, labelcolor=INK_SECONDARY)

    # --- 右下：年度新增申请容量 ---
    a_years = [int(r["request_year"]) for r in capacity]
    a_cap = [float(r["capacity_gw"]) for r in capacity]
    ax_cap.bar(a_years, a_cap, color=CATEGORICAL["orange"], width=0.75, zorder=2)
    ax_cap.set_title("年度新增并网申请容量(GW)", fontsize=11, fontweight="bold", color=INK_PRIMARY, loc="left", pad=8)
    ax_cap.set_ylabel("GW", fontsize=9)
    ax_cap.annotate(
        f"{a_cap[-1]:.0f}GW", xy=(a_years[-1], a_cap[-1]), xytext=(0, 4),
        textcoords="offset points", ha="center", fontsize=8.5, fontweight="bold", color=CATEGORICAL["orange"],
    )

    fig.suptitle(
        "并网队列：约束性瓶颈的直接证据（LBNL Queued Up官方数据）",
        fontsize=14.5, fontweight="bold", color=INK_PRIMARY, x=0.01, ha="left", y=1.01,
    )

    fig.text(
        0.01, -0.08,
        "数据源：LBNL Queued Up 2026版官方原始数据(emp.lbl.gov)，用户提供文件，非本会话直接下载 | "
        "左图口径：投产年份(非申请年份)的中位/p25-p75时长，样本3,310个项目(6个ISO+19个非ISO平衡区) | "
        "右上完成率口径：按申请年份分组，以2025年底的项目状态计算，虚线段年份(2020年后)因项目尚未走完全流程，"
        "完成率会系统性偏低，不代表真实完成率下降，仅反映右截尾统计偏差 | "
        "右下capacity为当年新增申请量，非当前队列中活跃的累计总量 | "
        "本图未采用原始文件里另一张'累计活跃容量'表，因该表2018→2019年数值出现无法解释的跳变，"
        "详见docs/SOURCES.md",
        fontsize=7.3, color=INK_MUTED, wrap=True, transform=fig.transFigure,
    )

    save_fig(
        fig,
        PNG_DIR / "F09_interconnection_queue_duration.png",
        SVG_DIR / "F09_interconnection_queue_duration.svg",
    )
    plt.close(fig)


if __name__ == "__main__":
    main()
