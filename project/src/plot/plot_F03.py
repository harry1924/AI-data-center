"""
F03 电价长序列（当前仅全国基准线，分州序列待EIA key补齐后另加）。

数据：data/processed/F03_national_price.csv (FRED APU000072610)
输出：figures/{png,svg}/F03_electricity_price_national.{png,svg}

重要口径说明（写入图注）：
  这条线是FRED的"Average Price: Electricity per KWh, U.S. City Average"，
  覆盖全部部门加权平均，口径与EIA分部门(RES)电价不完全相同，仅作为
  全国基准趋势参考。分州对比(密集州vs对照组)需要EIA API key，本图暂缺。
"""

import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _style import CATEGORICAL, INK_PRIMARY, INK_SECONDARY, INK_MUTED, apply_base_style, save_fig

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed" / "F03_national_price.csv"
PNG_DIR = Path(__file__).resolve().parents[2] / "figures" / "png"
SVG_DIR = Path(__file__).resolve().parents[2] / "figures" / "svg"
PNG_DIR.mkdir(parents=True, exist_ok=True)
SVG_DIR.mkdir(parents=True, exist_ok=True)


def main():
    rows = list(csv.DictReader(PROCESSED.open()))
    rows = [r for r in rows if r["date"] >= "2015-01"]
    dates = [datetime.strptime(r["date"], "%Y-%m") for r in rows]
    prices = [float(r["price_cents_per_kwh"]) for r in rows]

    fig, ax = plt.subplots(figsize=(9, 5))
    apply_base_style(ax, fig)

    ax.plot(dates, prices, color=CATEGORICAL["blue"], linewidth=2, solid_capstyle="round")

    start_val, end_val = prices[0], prices[-1]
    pct_change = (end_val / start_val - 1) * 100
    ax.annotate(
        f"{end_val:.1f}¢/kWh",
        xy=(dates[-1], end_val),
        xytext=(8, 0),
        textcoords="offset points",
        va="center",
        fontsize=10,
        fontweight="bold",
        color=INK_PRIMARY,
    )

    ax.set_title(
        "美国全国平均电价（城市平均，全部门加权），2015–2026",
        fontsize=13,
        fontweight="bold",
        color=INK_PRIMARY,
        loc="left",
        pad=14,
    )
    ax.set_ylabel("¢/kWh（美分/千瓦时，名义值）", fontsize=9.5)
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_ylim(bottom=0)

    fig.text(
        0.01, -0.04,
        f"数据源：FRED series APU000072610，全国城市平均电价（全部门加权），非EIA分部门口径 | "
        f"2015-01至2026-07累计+{pct_change:.0f}%（名义值，未做CPI平减）| "
        f"[注] 本图为兜底版本：仅有全国基准线，密集州vs对照组的分州对比因缺EIA API key暂缺，"
        f"需补齐后才是文档F03规格的完整版本",
        fontsize=7.8, color=INK_MUTED, wrap=True, transform=fig.transFigure,
    )

    save_fig(fig, PNG_DIR / "F03_electricity_price_national.png", SVG_DIR / "F03_electricity_price_national.svg")
    plt.close(fig)


if __name__ == "__main__":
    main()
