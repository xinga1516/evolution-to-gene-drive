#!/usr/bin/env python3
"""Redraw only Figure 6C, adding the terminal 2.0 y-axis tick."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


WORKSPACE = Path(__file__).resolve().parents[1]
ROOT = WORKSPACE / "文章终稿数据" / "Figure6" / "retest_20rep_20260914_final"
SOURCE = ROOT / "processed" / "Figure6_panelC_trajectory_source_data.csv"
FIG = ROOT / "figures"
COPY = WORKSPACE / "single_panel_outputs" / "Figure6C_yaxis_2p0"

PANEL_SIZE_INCH = (5.0, 4.5)
DPI = 600
FONT_FAMILY = "Arial"
FONT_SIZE = 15
LABEL_SIZE = 17
TICK_SIZE = 15
LEGEND_SIZE = 13


def save(fig, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    stem = directory / "Figure 6 panel C"
    fig.savefig(stem.with_suffix(".png"), dpi=DPI, facecolor="white")
    fig.savefig(stem.with_suffix(".tiff"), dpi=DPI, facecolor="white",
                pil_kwargs={"compression": "tiff_lzw"})
    fig.savefig(stem.with_suffix(".svg"), facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), facecolor="white")


def main() -> None:
    plt.rcParams.update({
        "font.family": FONT_FAMILY,
        "font.size": FONT_SIZE,
        "axes.labelsize": LABEL_SIZE,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    })
    traj = pd.read_csv(SOURCE)
    fig, ax = plt.subplots(figsize=PANEL_SIZE_INCH)
    trajectory_styles = {
        "P70": ("#7F7F7F", "Panmictic dc-0.70"),
        "S70": ("#C29A3A", "Spatial dc-0.70"),
        "S85": ("#BE7E4A", "Spatial dc-0.85"),
    }
    for group, (color, label) in trajectory_styles.items():
        sub = traj[traj.group == group]
        if sub.empty:
            continue
        for _, run in sub.groupby(["replicate", "seed"]):
            run = run.sort_values("week_relative_release").copy()
            run["B_smooth"] = run.B.rolling(20, center=True, min_periods=1).mean()
            ax.plot(run.week_relative_release, run.B_smooth,
                    color=color, lw=.35, alpha=.08, zorder=1)
        summary = (sub.groupby("week_relative_release").B
                   .agg(median="median", q05=lambda x: x.quantile(.05),
                        q25=lambda x: x.quantile(.25), q75=lambda x: x.quantile(.75),
                        q95=lambda x: x.quantile(.95)).reset_index())
        for stat in ["median", "q05", "q25", "q75", "q95"]:
            summary[stat] = summary[stat].rolling(20, center=True, min_periods=1).mean()
        x = summary.week_relative_release.to_numpy()
        ax.fill_between(x, summary.q05, summary.q95, color=color, alpha=.08, lw=0, zorder=2)
        ax.fill_between(x, summary.q25, summary.q75, color=color, alpha=.18, lw=0, zorder=3)
        ax.plot(x, summary["median"], color=color, lw=1.35, label=label, zorder=4)

    ax.axvline(0, color="#777777", ls=(0, (3, 3)), lw=.8, zorder=0)
    ax.set_xlim(-10, 1500)
    ax.set_xticks([0, 500, 1000, 1500])
    ax.set_ylim(0.2, 2.0)
    ax.set_yticks([0.5, 1.0, 1.5, 2.0])
    ax.set_xlabel("Weeks after release")
    ax.set_ylabel("Haploid inbreeding load, B")
    ax.legend(frameon=False, fontsize=LEGEND_SIZE - 1, loc="upper right",
              ncol=1, columnspacing=.7, handlelength=1.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=TICK_SIZE, width=0.8)
    ax.grid(False)
    ax.set_position([0.32, 0.22, 0.54, 0.54])

    save(fig, FIG)
    save(fig, COPY)
    plt.close(fig)


if __name__ == "__main__":
    main()
