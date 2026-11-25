from __future__ import annotations

import importlib.util
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "new_main_figure_task" / "rebuild_final20_attribute_panels.py"
OUT = ROOT / "single_panel_outputs"
OUT.mkdir(exist_ok=True)


def load_source():
    spec = importlib.util.spec_from_file_location("final20_source", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {SOURCE}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def draw() -> None:
    mod = load_source()
    # Use the already materialised, author-approved source table rather than
    # reparsing the large concatenated simulation logs for this visual-only
    # single-panel redraw.
    data = pd.read_csv(
        ROOT / "new_main_figure_task" / "final20_attribute_panels_20261024"
        / "Figure2_final20_source.csv"
    )

    fig, ax = plt.subplots(figsize=(4.5, 4.5), dpi=600)
    rng = np.random.default_rng(20261024)
    offsets = {"Neutral control": -0.16, "Functional modifier": 0.16}
    markers = {"Neutral control": "o", "Functional modifier": "x"}
    outcome_colors = {
        "Long-term persistence": mod.RAIN_LTP,
        "Elimination": mod.RAIN_ELIMINATION,
        "Drive loss": mod.RAIN_DRIVE_LOSS,
    }
    # Darker orange is reserved for the elimination summary marker and CI.
    elimination_summary = "#C66A2B"

    for yi, condition in enumerate(mod.ORDER):
        model, h_text = condition.rsplit(" ", 1)
        group = data[data.model.eq(model) & np.isclose(data.h, float(h_text))]

        for ti, treatment in enumerate(mod.TREATMENTS):
            sub = group[group.treatment.eq(treatment)]
            y = yi + offsets[treatment]
            marker = markers[treatment]

            for oi, (outcome, color) in enumerate(outcome_colors.items()):
                values = pd.to_numeric(
                    sub.loc[sub.outcome.eq(outcome), "final20_attribute_weighted"],
                    errors="coerce",
                ).dropna().to_numpy(float)

                if len(values) >= 5 and np.ptp(values) > 0:
                    violin = ax.violinplot(
                        values, [y], vert=False, widths=0.31,
                        showextrema=False, bw_method=0.55,
                    )
                    body = violin["bodies"][0]
                    for path in body.get_paths():
                        if treatment == "Neutral control":
                            path.vertices[:, 1] = np.maximum(path.vertices[:, 1], y)
                        else:
                            path.vertices[:, 1] = np.minimum(path.vertices[:, 1], y)
                    body.set_facecolor(color)
                    body.set_edgecolor("none")
                    body.set_alpha(0.22)

                if not len(values):
                    continue

                jitter = rng.uniform(-0.035, 0.035, len(values))
                if marker == "o":
                    ax.scatter(
                        values, y + jitter, s=9, marker="o",
                        facecolors="none", edgecolors=color,
                        alpha=0.82, linewidth=0.55, zorder=3,
                    )
                else:
                    ax.scatter(
                        values, y + jitter, s=10, marker="x", color=color,
                        alpha=0.72, linewidth=0.55, zorder=3,
                    )

                # A single LTP observation in Panmictic 0.85 variable is a raw
                # point, not an estimable group summary.  Do not draw it again
                # as the oversized dark x that caused the reported artefact.
                if len(values) < 2:
                    continue

                mean, low, high = mod.bootstrap(
                    values, 5000 + yi * 20 + ti * 5 + oi
                )
                summary_color = (
                    elimination_summary if outcome == "Elimination" else "#4F4F4F"
                )
                ax.errorbar(
                    mean, y,
                    xerr=[[mean - low], [high - mean]],
                    fmt=marker, ms=6.3,
                    mfc="white" if marker == "o" else summary_color,
                    mec=summary_color, mew=1.35,
                    ecolor=summary_color, elinewidth=1.35,
                    capsize=2.4, zorder=7,
                )

        # Preserve the approved significance annotations from Figure 1B.
        ax.text(
            1.02, yi, "***", transform=ax.get_yaxis_transform(),
            ha="left", va="center", fontsize=14, fontweight="bold",
        )

        initial = float(h_text)
        ax.vlines(
            initial, yi - 0.38, yi + 0.38,
            color="#777777", ls=(0, (3, 3)), lw=0.8, zorder=0,
        )

    ax.set_yticks(range(4), ["0.70", "0.85", "0.70", "0.85"])
    ax.text(-0.10, 0.75, "Panmictic", transform=ax.transAxes,
            ha="right", va="center", fontsize=15)
    ax.text(-0.10, 0.25, "Spatial", transform=ax.transAxes,
            ha="right", va="center", fontsize=15)
    ax.invert_yaxis()
    ax.set_xlim(0, 1)
    ax.set_xlabel("Final drive conversion")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(False)
    ax.set_position([0.27, 0.18, 0.62, 0.62])

    stem = OUT / "Figure1B_redrawn_pan085_mean_fixed"
    fig.savefig(stem.with_suffix(".png"), dpi=600, facecolor="white")
    fig.savefig(OUT / "Figure1B_redrawn_pan085_mean_fixed_tight.png",
                dpi=600, facecolor="white", bbox_inches="tight", pad_inches=0.04)
    fig.savefig(stem.with_suffix(".svg"), facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    draw()
