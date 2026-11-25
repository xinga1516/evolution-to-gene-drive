from __future__ import annotations

import importlib.util
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCRIPT = ROOT / "new_main_figure_task" / "draw_dispersal_evolution_main.py"
SOURCE_DIR = (
    ROOT / "new_main_figure_task"
    / "figure7_final20_all_outcomes_warmB_20261024_v5"
)
OUT = ROOT / "single_panel_outputs"
OUT.mkdir(exist_ok=True)


def load_source():
    spec = importlib.util.spec_from_file_location("dispersal_source", SOURCE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {SOURCE_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def draw() -> None:
    mod = load_source()
    data = pd.read_csv(SOURCE_DIR / "source_data_per_run.csv")
    bstats = pd.read_csv(SOURCE_DIR / "panel_b_tests.csv")

    plt.rcParams.update({
        "font.family": "Arial", "font.size": 14,
        "axes.labelsize": 16, "xtick.labelsize": 14,
        "ytick.labelsize": 14, "legend.fontsize": 11.5,
        "axes.linewidth": 0.8, "savefig.transparent": False,
        "svg.fonttype": "none", "pdf.fonttype": 42,
    })

    fig, ax = plt.subplots(figsize=(5.2, 5.2), dpi=600)
    no_drive, _, _ = mod.analysis_sets(data)
    eligible = data[
        data["mode"].eq("evolving")
        & data["exit_code"].eq(0)
        & data["outcome"].isin(mod.OUTCOMES)
        & data["dispersal_E_percent"].notna()
    ].copy()

    rng = np.random.default_rng(mod.RNG_SEED + 20)
    mod.horizontal_cloud(
        ax,
        no_drive["dispersal_E_percent"].dropna().to_numpy(),
        0, mod.RAIN_LTP, "upper", rng, mod.RNG_SEED + 100,
    )

    # A distinct dark brown separates the pooled non-long-term summary from
    # the orange population-elimination observations.
    non_ltp_mean_color = "#8B5E34"

    for yi, conversion in enumerate(mod.MAIN_CONVERSIONS, start=1):
        group = eligible[eligible["conversion"].eq(conversion)]
        ltp = group.loc[
            group["outcome"].eq("long-term persistence"),
            "dispersal_E_percent",
        ].to_numpy(float)
        mod.horizontal_cloud(
            ax, ltp, yi, mod.RAIN_LTP, "lower", rng,
            mod.RNG_SEED + 100 + yi,
        )

        for outcome, color, offset in [
            ("elimination", mod.RAIN_ELIM, -0.045),
            ("drive loss", mod.RAIN_LOSS, 0.045),
        ]:
            values = group.loc[
                group["outcome"].eq(outcome), "dispersal_E_percent"
            ].to_numpy(float)
            if len(values):
                ax.scatter(
                    values,
                    np.full(len(values), yi + offset)
                    + rng.uniform(-0.025, 0.025, len(values)),
                    s=11, c=color, alpha=0.75, lw=0,
                    rasterized=True, zorder=5,
                )

        stat = bstats[
            bstats["conversion"].eq(conversion)
            & bstats["endpoint_group"].eq("Non-LTP")
        ]
        if len(stat):
            row = stat.iloc[0]
            ax.errorbar(
                row.display_mean, yi,
                xerr=[
                    [row.display_mean - row.display_ci_low],
                    [row.display_ci_high - row.display_mean],
                ],
                fmt="o", ms=4.8, mfc="white",
                mec=non_ltp_mean_color, mew=1.0,
                ecolor=non_ltp_mean_color, elinewidth=1.1,
                capsize=2.2, zorder=7,
            )

    ax.axvline(0, color="#777777", ls=(0, (3, 3)), lw=0.8, zorder=0)
    ax.set_yticks(
        range(5), ["No drive"] + [f"{x:.2f}" for x in mod.MAIN_CONVERSIONS]
    )
    ax.invert_yaxis()
    ax.set_xlim(-42, 93)
    ax.set_xticks([-40, -20, 0, 20, 40, 60, 80])
    ax.set_xlabel("Adult dispersal change (%)")
    ax.set_ylabel("")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(False)

    handles = [
        Line2D([], [], marker="o", ls="", color=mod.RAIN_LTP,
               label="Long-term persistence"),
        Line2D([], [], marker="o", ls="", color=mod.RAIN_ELIM,
               label="Population elimination"),
        Line2D([], [], marker="o", ls="", color=mod.RAIN_LOSS,
               label="Drive loss"),
        Line2D([], [], marker="o", ls="", mfc="white", mec=mod.RAIN_LTP,
               color=mod.RAIN_LTP, label="No-drive reference"),
        Line2D([], [], marker="o", ls="-", mfc="white",
               mec=non_ltp_mean_color, color=non_ltp_mean_color,
               label="Non-long-term mean"),
    ]
    ax.legend(
        handles=handles, frameon=False, loc="lower center",
        bbox_to_anchor=(0.51, 1.025), ncol=2, fontsize=10.5,
        handletextpad=0.3, columnspacing=0.55, labelspacing=0.35,
    )

    ax.set_position([0.22, 0.16, 0.70, 0.65])
    stem = OUT / "Figure5B_redrawn_nonLTP_mean_color"
    fig.savefig(stem.with_suffix(".png"), dpi=600, facecolor="white")
    fig.savefig(OUT / "Figure5B_redrawn_nonLTP_mean_color_tight.png",
                dpi=600, facecolor="white", bbox_inches="tight", pad_inches=0.04)
    fig.savefig(stem.with_suffix(".svg"), facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    draw()
