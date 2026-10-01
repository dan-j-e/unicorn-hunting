"""Shared chart styling (light surface, recessive axes, validated palette)."""

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from unicorn.raw import PROJECT_ROOT

SURFACE, INK, INK2, GRID, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#c3c2b7"
# Categorical slots in fixed order: blue, orange, aqua, yellow
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
BLUE, ORANGE, RED = SERIES[0], SERIES[1], "#e34948"
DIVERGING = LinearSegmentedColormap.from_list("div", [BLUE, "#f0efec", RED])
FIG_DIR = PROJECT_ROOT / "outputs" / "figures"


def apply_style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
        "text.color": INK, "axes.titlecolor": INK, "axes.titlesize": 11, "axes.titleweight": "bold",
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
        "axes.spines.right": False, "font.size": 9, "lines.linewidth": 2,
    })


def season_ticks(ax, starts=(2011, 2015, 2019, 2023)):
    ax.set_xticks(list(starts), [f"{s % 100:02d}-{(s + 1) % 100:02d}" for s in starts])
