from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "文章终稿数据" / "Figure3" / "processed_source"
OUT = ROOT / "single_panel_outputs"
OUT.mkdir(exist_ok=True)


def draw() -> None:
    assoc = pd.read_csv(DATA / "Figure3_source_panelE_association.csv")
    test = pd.read_csv(DATA / "Figure3_panelE_exact_spearman.csv").iloc[0]

    plt.rcParams.update({
        "font.family": "Arial",
        "font.size": 13,
        "axes.labelsize": 14.5,
        "xtick.labelsize": 13,
        "ytick.labelsize": 13,
        "axes.linewidth": 0.8,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    })

    # Match the spacious aspect and plot-box proportions of the approved
    # earlier panel rather than forcing the axes into a compact square.
    fig, ax = plt.subplots(figsize=(5.2, 4.8), dpi=600)
    color = "#A6B097"

    for row in assoc.itertuples(index=False):
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
            fmt="o", ms=5.2, mfc=color, mec="white", mew=0.7,
            ecolor=color, elinewidth=1.0, capsize=2.2, zorder=3,
        )
        right_side = row.control_nni_mean > 0.83
        is_070 = abs(float(row.h) - 0.70) < 1e-9
        ax.annotate(
            f"{row.h:.2f}",
            (row.control_nni_mean, row.functional_final_attribute_mean),
            # Keep the 0.70 label clear of its horizontal/vertical error-bar
            # cross; all other setting labels retain their prior positions.
            xytext=(7, 4) if is_070 else (-5 if right_side else 4, 4),
            textcoords="offset points",
            ha="left" if is_070 else ("right" if right_side else "left"),
            va="bottom", fontsize=9.5, color="#252525",
        )

    ax.axhline(0.5, color="#777777", ls=(0, (3, 3)), lw=0.8, zorder=0)

    # Route the explanatory callout through clear whitespace.  Its arrowhead
    # terminates at the printed "0.90" label rather than at the point/errorbar.
    target = assoc.loc[assoc["h"].round(2).eq(0.90)].iloc[0]
    ax.annotate(
        "Drive conversion\nefficiency",
        xy=(target.control_nni_mean + 0.0032,
            target.functional_final_attribute_mean + 0.011),
        xycoords="data",
        xytext=(0.010, 0.985), textcoords="axes fraction",
        ha="left", va="top", fontsize=9.2, color="#333333",
        arrowprops={
            "arrowstyle": "->", "color": "#555555", "lw": 0.9,
            "connectionstyle": "arc3,rad=-0.16", "shrinkA": 4, "shrinkB": 3,
        },
    )

    ax.text(
        0.035, 0.045,
        f"Spearman ρ={test.rho:.2f}\n$P$={test.p_value:.4f}",
        transform=ax.transAxes, ha="left", va="bottom", fontsize=9.5,
    )

    ax.set_xlabel("Mean NNI over final 20 weeks\n(Neutral mutations)")
    ax.set_ylabel("Final-20-week embryo resistance\n(Variable mutations)")
    ax.set_xlim(0.692, 0.861)
    ax.set_ylim(0.272, 0.755)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(False)
    ax.set_position([0.245, 0.18, 0.68, 0.68])

    stem = OUT / "Figure2E_redrawn_arrow_to_090"
    fig.savefig(stem.with_suffix(".png"), dpi=600, facecolor="white",
                bbox_inches="tight", pad_inches=0.12)
    fig.savefig(OUT / "Figure2E_redrawn_arrow_to_090_tight.png",
                dpi=600, facecolor="white", bbox_inches="tight", pad_inches=0.06)
    fig.savefig(stem.with_suffix(".svg"), facecolor="white",
                bbox_inches="tight", pad_inches=0.12)
    fig.savefig(stem.with_suffix(".pdf"), facecolor="white",
                bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)


if __name__ == "__main__":
    draw()
