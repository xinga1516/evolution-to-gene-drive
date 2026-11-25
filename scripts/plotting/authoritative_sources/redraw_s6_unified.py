from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd


ROOT = Path(r"D:\champer实验室工作\文章figure1-8")
DATA = ROOT / "supplementary_final" / "source_data" / "S3_S4_S5_trajectory_values.csv"
OUT = ROOT / "single_panel_outputs" / "S6_unified"
OUT.mkdir(parents=True, exist_ok=True)

# S6a: colors sampled to match the supplied without/with-mutations reference.
COLORS_A = {
    "P70_L": "#2E8592",  # with recessive load / with mutations
    "P70_N": "#A6DCC8",  # without recessive load / without mutations
}

# S6b: retain the two S6a colors for 0.70 and use the supplied dark/light
# blue pair for 0.85.
COLORS_B = {
    "S70_L": "#2E8592",
    "S70_N": "#A6DCC8",
    "S85_L": "#0072B2",
    "S85_N": "#56B4E9",
}

LABELS = {
    "P70_L": "0.70, with recessive load",
    "P70_N": "0.70, without recessive load",
    "S70_L": "0.70, with recessive load",
    "S70_N": "0.70, without recessive load",
    "S85_L": "0.85, with recessive load",
    "S85_N": "0.85, without recessive load",
}


def load_data():
    data = pd.read_csv(
        DATA,
        usecols=["condition_id", "replicate", "week_relative_release", "N_total"],
    )
    return data[data["week_relative_release"].between(0, 1500)].copy()


def replicate_trajectories(ax, data, condition, color, alpha):
    """Draw one smoothed trajectory per independent simulation replicate."""
    subset = data[data["condition_id"].eq(condition)]
    for _, group in subset.groupby("replicate"):
        group = group.sort_values("week_relative_release")
        x = group["week_relative_release"].to_numpy()
        # A centred 20-week moving average is display-only smoothing; every
        # independent replicate remains a separate line.
        y = (group["N_total"].astype(float)
             .rolling(window=20, center=True, min_periods=1).mean()
             .to_numpy())
        ax.plot(x, y, color=color, linewidth=0.5, alpha=alpha,
                solid_capstyle="round", zorder=2)


def style_axis(ax, ylabel, letter):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.95)
    ax.spines["bottom"].set_linewidth(0.95)
    ax.tick_params(direction="out", width=0.9, length=4, labelsize=9.5)
    ax.set_xlim(-35, 1535)
    ax.set_xticks(range(0, 1501, 200))
    ax.set_xlabel("Weeks after release", fontsize=10.5)
    ax.set_ylabel(ylabel, fontsize=10.5)
    # Match the compact landscape plotting rectangles used in the approved
    # S5 reference (width:height approximately 1.35:1).
    ax.set_box_aspect(0.74)
    ax.text(-0.14, 1.035, letter, transform=ax.transAxes,
            fontsize=13, fontweight="bold", va="bottom")


def panel_legend(ax, conditions, colors, title, ncol):
    handles = [
        Line2D([0], [0], color=colors[c], lw=2.35, label=LABELS[c])
        for c in conditions
    ]
    # Keep a consistent legend block: title directly above entries, with a
    # controlled gap below the figure title and above the plotting rectangle.
    ax.legend(handles=handles, title=title, loc="lower center",
              bbox_to_anchor=(0.5, 1.105), ncol=ncol, frameon=False,
              fontsize=8.9, title_fontsize=10.5, handlelength=2.25,
              columnspacing=1.35, handletextpad=0.65, borderaxespad=0.0,
              labelspacing=0.55)


def main():
    data = load_data()
    plt.rcParams.update({
        "font.family": "Arial",
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    })

    # Compact landscape composition aligned with the approved S5 reference.
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.85))

    order_a = ("P70_L", "P70_N")
    draw_order_a = ("P70_N", "P70_L")
    for condition in draw_order_a:
        replicate_trajectories(axes[0], data, condition, COLORS_A[condition], alpha=0.7)
    style_axis(axes[0], "Panmictic population size", "a")
    panel_legend(axes[0], order_a, COLORS_A, "Panmictic", ncol=2)

    order_b = ("S70_L", "S70_N", "S85_L", "S85_N")
    draw_order_b = ("S70_N", "S85_N", "S70_L", "S85_L")
    for condition in draw_order_b:
        replicate_trajectories(axes[1], data, condition, COLORS_B[condition], alpha=0.7)
    style_axis(axes[1], "Spatial population size", "b")
    panel_legend(axes[1], order_b, COLORS_B, "Spatial", ncol=2)

    fig.suptitle("Supplementary Fig. S6 | Post-release population trajectories",
                 x=0.045, y=0.965, ha="left", fontsize=17.0,
                 fontweight="bold")

    # Explicit three-tier spacing: figure title, panel legends, plot fields.
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.15,
                        top=0.67, wspace=0.27)

    stem = OUT / "Supplementary_Figure_S6_unified"
    fig.savefig(stem.with_suffix(".png"), dpi=600, facecolor="white")
    fig.savefig(stem.with_suffix(".svg"), facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
