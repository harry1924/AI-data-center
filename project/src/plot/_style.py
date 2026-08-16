"""
共享绘图样式：色板取自 dataviz skill 的验证过色板(references/palette.md)。
静态报告配图(嵌入Word/PDF)只做light模式，不做深色主题切换。
"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 中文字形：matplotlib默认DejaVu Sans不含CJK字形，改用系统自带的文泉驿正黑
plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# 分类色板(固定顺序，不循环) — 与 dataviz skill 验证结果一致
CATEGORICAL = {
    "blue": "#2a78d6",
    "orange": "#eb6834",
    "aqua": "#1baf7a",
    "yellow": "#eda100",
    "magenta": "#e87ba4",
    "green": "#008300",
    "violet": "#4a3aa7",
    "red": "#e34948",
}
CAT_ORDER = ["blue", "orange", "aqua", "yellow", "magenta", "green", "violet", "red"]
CAT_LIST = [CATEGORICAL[k] for k in CAT_ORDER]

SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"

STATUS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}


def apply_base_style(ax, fig):
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(BASELINE)
    ax.spines["bottom"].set_color(BASELINE)
    ax.tick_params(colors=INK_MUTED, labelsize=9)
    ax.yaxis.grid(True, color=GRIDLINE, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.xaxis.label.set_color(INK_SECONDARY)
    ax.yaxis.label.set_color(INK_SECONDARY)


def save_fig(fig, out_png, out_svg):
    fig.savefig(out_png, dpi=300, facecolor=SURFACE, bbox_inches="tight")
    fig.savefig(out_svg, facecolor=SURFACE, bbox_inches="tight")
    print(f"写入 {out_png}")
    print(f"写入 {out_svg}")
