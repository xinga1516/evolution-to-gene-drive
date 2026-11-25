from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "文章终稿数据" / "Figure4" / "processed_source_final"
ASSOC_SOURCE = (
    ROOT / "new_main_figure_task" / ".endpoint20_raw" / "Figure4" / "unique"
    / "11"
    / "11d1e8b802dc31b4f9dccc5c1f735f97b52e3a0f139fa91b1d0bf57ba3b05b0a_Figure4_source_panelE_association.csv"
)
OUT = ROOT / "single_panel_outputs"
OUT.mkdir(exist_ok=True)


def draw() -> None:
    # This is the exact final-20-week association table used by the approved
    # reference panel.  In particular, it preserves the original relative
    # positions of the empirical 0.99/0.96 point and the 0.95 setting.
    assoc = pd.read_csv(ASSOC_SOURCE)
    test = pd.read_csv(DATA / "Figure4_panelE_exact_spearman.csv").iloc[0]

    plt.rcParams.update({
        "font.family": "Arial",
        "font.size": 15,
        "axes.labelsize": 17,
        "xtick.labelsize": 15,
        "ytick.labelsize": 15,
        "legend.fontsize": 11,
        "axes.linewidth": 0.8,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    })

    fig, ax = plt.subplots(figsize=(4.5, 4.5), dpi=600)
    color = "#A6B097"

    for row in assoc.itertuples(index=False):
        is_emp = abs(float(row.h) - 0.99) < 1e-9
        marker = "D" if is_emp else "o"
        label = "0.99/0.96" if is_emp else f"{row.h:.2f}"

        ax.errorbar(
            row.control_nni_mean,
            row.functional_final_attribute_mean,
            xerr=[
                [row.control_nni_mean - row.control_nni_lo],
                [row.control_nni_hi - row.control_nni_mean],
            ],
            yerr=[
                [row.functional_final_attribute_mean - row.functional_final_attribute_lo],
                [row.functional_final_attribute_hi - row.functional_final_attribute_mean],
            ],
            fmt=marker, ms=5.2, mfc=color, mec="white", mew=0.7,
            ecolor=color, elinewidth=1.0, capsize=2.2, zorder=3,
        )

        # All setting labels use the same regular weight.  In particular,
        # 0.70 and 0.99/0.96 are no longer bold.
        ax.annotate(
            label,
            (row.control_nni_mean, row.functional_final_attribute_mean),
            xytext=(4, 4), textcoords="offset points",
            ha="left", fontsize=10,
            fontweight="normal", color="#252525",
        )

    ax.axhline(0.5, color="#777777", ls=(0, (3, 3)), lw=0.8, zorder=0)

    ax.legend(
        handles=[
            Line2D([], [], marker="o", ls="", color=color,
                   label="Systematic scan"),
            Line2D([], [], marker="D", ls="", color=color,
                   label="0.99/0.96 (female/male)"),
        ],
        frameon=False, loc="upper left", bbox_to_anchor=(0.005, 0.995),
        borderaxespad=0, handletextpad=0.45, labelspacing=0.35,
        fontsize=11,
    )

    ax.text(
        0.985, 0.035,
        f"Spearman ρ={test.rho:.2f}\n$P$={test.p_value:.7f}",
        transform=ax.transAxes, ha="right", va="bottom", fontsize=10.5,
    )

    ax.set_xlabel("Mean NNI over final 20 weeks\n(Neutral mutations)")
    ax.set_ylabel(
        "Final-20-week female heterozygote fitness\n"
        "(population-size weighted; Variable mutations)",
        fontsize=11,
    )
    ax.set_xlim(0.785, 0.864)
    ax.set_ylim(0.195, 0.82)
    ax.set_xticks([0.80, 0.82, 0.84, 0.86])
    ax.set_yticks([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(False)
    ax.set_position([0.27, 0.18, 0.62, 0.62])

    stem = OUT / "Figure3E_redrawn_v2_complete_axis"
    # Preserve the panel geometry while expanding the exported canvas to
    # include the full two-line y-axis title.  No artist positions change.
    fig.savefig(stem.with_suffix(".png"), dpi=600, facecolor="white",
                bbox_inches="tight", pad_inches=0.30)
    fig.savefig(OUT / "Figure3E_redrawn_v2_complete_axis_tight.png",
                dpi=600, facecolor="white", bbox_inches="tight", pad_inches=0.20)
    fig.savefig(stem.with_suffix(".svg"), facecolor="white",
                bbox_inches="tight", pad_inches=0.30)
    fig.savefig(stem.with_suffix(".pdf"), facecolor="white",
                bbox_inches="tight", pad_inches=0.30)
    plt.close(fig)


if __name__ == "__main__":
    draw()
