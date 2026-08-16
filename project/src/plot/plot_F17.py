"""
F17 建设成本与设备价格（当前仅有变压器PPI指数一手数据；M4/M5建设成本$/MW数据待补）。

数据：data/processed/F17_ppi_transformers.csv (BLS PPI series PCU335311335311)
输出：figures/{png,svg}/F17_ppi_transformers.{png,svg}
"""

import csv
import sys
from pathlib import Path
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import CATEGORICAL, INK_PRIMARY, INK_MUTED, apply_base_style, save_fig

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed" / "F17_ppi_transformers.csv"
PNG_DIR = Path(__file__).resolve().parents[2] / "figures" / "png"
SVG_DIR = Path(__file__).resolve().parents[2] / "figures" / "svg"


def main():
    rows = list(csv.DictReader(PROCESSED.open()))
    dates = [datetime.strptime(r["date"], "%Y-%m") for r in rows]
    values = [float(r["index_value"]) for r in rows]

    fig, ax = plt.subplots(figsize=(9, 5))
    apply_base_style(ax, fig)

    ax.plot(dates, values, color=CATEGORICAL["orange"], linewidth=2, solid_capstyle="round")

    pct = (values[-1] / values[0] - 1) * 100
    ax.annotate(
        f"{values[-1]:.0f}",
        xy=(dates[-1], values[-1]),
        xytext=(8, 0),
        textcoords="offset points",
        va="center",
        fontsize=10,
        fontweight="bold",
        color=INK_PRIMARY,
    )
    ax.annotate(
        f"{dates[0].strftime('%Y-%m')}: {values[0]:.0f}",
        xy=(dates[0], values[0]),
        xytext=(6, 14),
        textcoords="offset points",
        ha="left",
        fontsize=9,
        color=INK_MUTED,
    )

    ax.set_title(
        f"变压器制造业生产者价格指数(PPI)，2017–2026（{pct:+.0f}%）",
        fontsize=13,
        fontweight="bold",
        color=INK_PRIMARY,
        loc="left",
        pad=14,
    )
    ax.set_ylabel("PPI指数（1982=100基准）", fontsize=9.5)
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    fig.text(
        0.01, -0.06,
        "数据源：BLS PPI series PCU335311335311（电力/配电/专用变压器制造业）| "
        "[注] 本图仅含设备价格侧的一手数据；文档F17规格还要求叠加M4/M5(JLL/Turner & Townsend)"
        "的建设成本$/MW数据作对照，因需登录这两个源官网，本轮未获取，图中暂缺",
        fontsize=7.8, color=INK_MUTED, wrap=True, transform=fig.transFigure,
    )

    save_fig(fig, PNG_DIR / "F17_ppi_transformers.png", SVG_DIR / "F17_ppi_transformers.svg")
    plt.close(fig)


if __name__ == "__main__":
    main()
