from pathlib import Path
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.stats import gaussian_kde


ROOT = Path(r"D:\champer实验室工作\文章figure1-8")
OUT = ROOT / "single_panel_outputs" / "S1_three_panels_unified"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "code"))

GREEN = "#6CC4A1"
BLACK = "#202020"
SETTINGS = [0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 0.99]
STARS_B = ["**", "ns", "ns", "ns", "***", "ns", "**"]
STARS_C = ["***", "***", "***", "*", "***", "***", "***"]


def parse_nni(path, setting, cohort):
    """Read simulation-level NNI records from a concatenated SLiM output."""
    rows = []
    rep = 0
    generation_time = 3.167
    area = 1.0
    with Path(path).open("r", encoding="utf-8", errors="ignore") as handle:
        for raw in handle:
            line = raw.strip()
            if line.startswith("// Initial random seed:"):
                rep += 1
                generation_time = 3.167
                area = 1.0
            elif line.startswith("GENERATION TIME:"):
                generation_time = float(line.split(":", 1)[1])
            elif line.startswith("SIM BOUND:"):
                area = float(line.split(":", 1)[1])
            elif line.startswith("WT_ALLELES::"):
                if rep == 0:
                    rep = 1
                parts = line.split()
                generation, population, ann = (
                    int(parts[2]), int(parts[3]), float(parts[6])
                )
                if generation < 21 or population <= 0 or ann <= 0:
                    continue
                expected_ann = 0.5 / np.sqrt(population) * area
                rows.append({
                    "setting": setting,
                    "cohort": cohort,
                    "replicate": rep,
                    "week": (generation - 21) / generation_time,
                    "nni": ann / expected_ann,
                })
    return pd.DataFrame(rows)


def final_window_mean(data, group_cols, weeks=20):
    """Mean each replicate over its own final requested time window."""
    kept = []
    for _, group in data.groupby(group_cols, sort=False):
        end = group["week"].max()
        kept.append(group.loc[group["week"].ge(end - weeks)])
    tail = pd.concat(kept, ignore_index=True)
    return (tail.groupby(group_cols, as_index=False)["nni"].mean()
            .rename(columns={"nni": "value"}))


def bootstrap_mean_ci(values, rng, n_boot=10_000):
    values = np.asarray(values, dtype=float)
    draws = rng.choice(values, size=(n_boot, len(values)), replace=True)
    means = draws.mean(axis=1)
    return float(values.mean()), np.quantile(means, [0.025, 0.975])


def half_violin(ax, values, y, direction, width):
    values = np.asarray(values, dtype=float)
    if len(values) < 3 or np.ptp(values) == 0:
        return
    grid = np.linspace(values.min(), values.max(), 180)
    density = gaussian_kde(values)(grid)
    density = density / density.max() * width
    edge = y + direction * density
    ax.fill_between(grid, y, edge, color=GREEN, alpha=0.18, lw=0, zorder=1)
    ax.plot(grid, edge, color=GREEN, alpha=0.42, lw=0.72, zorder=2)


def load_data():
    # Panel a: use both the neutral-control and variable-mutation spatial runs;
    # summarize each replicate over its own final 20 weeks.
    fig1 = ROOT.parent / "文章figure终版" / "figure1+2  (可靠）"
    a_raw = pd.concat([
        parse_nni(fig1 / "first drive without mutations.out", 0.70,
                  "Neutral mutations"),
        parse_nni(fig1 / "first dirve with mutations.out", 0.70,
                  "Variable mutations"),
        parse_nni(fig1 / "second drive without mutations.out", 0.85,
                  "Neutral mutations"),
        parse_nni(fig1 / "second drive with mutations.out", 0.85,
                  "Variable mutations"),
    ], ignore_index=True)
    a = final_window_mean(
        a_raw, ["setting", "cohort", "replicate"], weeks=20
    )

    # Panel b: exact Figure 2E trajectories used by the locked S1.
    z = pd.read_csv(
        ROOT / "文章终稿数据" / "Figure3" / "raw_or_authoritative_source"
        / "source_tables" / "Figure3_panelE_logs14_trajectory_tidy.csv.gz"
    )
    b = final_window_mean(
        z.rename(columns={"h": "setting", "treatment": "cohort",
                          "rep": "replicate"}),
        ["setting", "cohort", "replicate"], weeks=20,
    )
    b["cohort"] = b.cohort.replace({
        "Neutral control": "Neutral mutations",
        "Functional modifier": "Variable mutations",
    })

    # Panel c: use the already-audited, completed Figure 3E source loader.
    from redraw_s1_figure3e_refined import load_data as load_c
    c = load_c()
    return a, b, c


def draw_group(ax, values, y, cohort, rng, violin_width=0.105):
    values = np.asarray(values, float)
    marker = "o" if cohort == "Neutral mutations" else "x"
    jitter = rng.normal(0, 0.014, len(values))
    if marker == "o":
        ax.scatter(values, y + jitter, s=10.5, marker="o", facecolors="none",
                   edgecolors=GREEN, linewidths=0.78, alpha=0.72, zorder=3)
        half_violin(ax, values, y, -1, violin_width)
    else:
        ax.scatter(values, y + jitter, s=11.5, marker="x", color=GREEN,
                   linewidths=0.78, alpha=0.72, zorder=3)
        half_violin(ax, values, y, +1, violin_width)

    mean, ci = bootstrap_mean_ci(values, rng)
    xerr = [[mean - ci[0]], [ci[1] - mean]]
    if marker == "o":
        ax.errorbar(mean, y, xerr=xerr, fmt="o", ms=4.5, mfc="white",
                    mec=BLACK, mew=1.05, ecolor=BLACK, elinewidth=0.92,
                    capsize=2.0, capthick=0.92, zorder=7)
    else:
        ax.errorbar(mean, y, xerr=xerr, fmt="x", ms=4.9, color=BLACK,
                    mew=1.08, ecolor=BLACK, elinewidth=0.92,
                    capsize=2.0, capthick=0.92, zorder=7)


def style_axis(ax, title, letter, ticks, labels, xlim=(0.695, 0.865)):
    ax.set_xlim(*xlim)
    ax.set_xticks([0.70, 0.75, 0.80, 0.85])
    ax.set_yticks(ticks, labels)
    ax.set_xlabel("Mean NNI over final 20 weeks")
    ax.set_ylabel("Drive conversion efficiency")
    ax.set_title(title, pad=8)
    ax.text(-0.18, 1.035, letter, transform=ax.transAxes,
            fontsize=13, fontweight="bold", va="bottom")
    ax.tick_params(length=3.7, width=0.95)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.95)
    ax.spines["bottom"].set_linewidth(0.95)


def draw_panel_a(ax, data, rng):
    positions = [0, 1]
    offsets = {"Neutral mutations": -0.145, "Variable mutations": 0.145}
    for y, setting in zip(positions, [0.70, 0.85]):
        for cohort in ("Neutral mutations", "Variable mutations"):
            values = data.loc[
                np.isclose(data.setting, setting) & data.cohort.eq(cohort),
                "value",
            ].to_numpy(float)
            draw_group(ax, values, y + offsets[cohort], cohort, rng,
                       violin_width=0.13)
    ax.set_ylim(1.38, -0.38)
    style_axis(ax, "Figure 1 spatial", "a", positions, ["0.70", "0.85"])


def draw_panel_multi(ax, data, title, letter, stars, rng, emp=False):
    offsets = {"Neutral mutations": -0.145, "Variable mutations": 0.145}
    for yi, setting in enumerate(SETTINGS):
        for cohort in ("Neutral mutations", "Variable mutations"):
            values = data.loc[
                np.isclose(data.setting.astype(float), setting)
                & data.cohort.eq(cohort), "value"
            ].dropna().to_numpy(float)
            if len(values):
                draw_group(ax, values, yi + offsets[cohort], cohort, rng)
        ax.text(0.8685, yi, stars[yi], ha="left", va="center",
                fontsize=9.2, fontweight="bold", clip_on=False)
    ax.set_ylim(6.52, -0.52)
    labels = ["0.70", "0.75", "0.80", "0.85", "0.90", "0.95", "Emp" if emp else "0.99"]
    style_axis(ax, title, letter, range(7), labels)


def main():
    a, b, c = load_data()
    rng = np.random.default_rng(20261115)
    plt.rcParams.update({
        "font.family": "Arial",
        "font.size": 9.4,
        "axes.labelsize": 16.0,
        "axes.titlesize": 10.8,
        "xtick.labelsize": 12.5,
        "ytick.labelsize": 12.5,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    })

    # All three plotting rectangles are exactly the same physical size.
    fig, axes = plt.subplots(1, 3, figsize=(13.8, 5.0))
    draw_panel_a(axes[0], a, rng)
    draw_panel_multi(axes[1], b, "Figure 2E", "b", STARS_B, rng, emp=False)
    draw_panel_multi(axes[2], c, "Figure 3E", "c", STARS_C, rng, emp=True)

    legend = [
        Line2D([0], [0], marker="o", linestyle="None", markerfacecolor="white",
               markeredgecolor=BLACK, markersize=4.8, label="Neutral mutations"),
        Line2D([0], [0], marker="x", linestyle="None", color=BLACK,
               markersize=5.0, label="Variable mutations"),
        Line2D([0], [0], marker="o", linestyle="None", markerfacecolor=GREEN,
               markeredgecolor=GREEN, markersize=5.0, label="Long-term persistence"),
    ]
    fig.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.57, 0.895),
               ncol=3, frameon=False, fontsize=9.2, handletextpad=0.55,
               columnspacing=2.0)
    fig.suptitle("Supplementary Fig. S1 | Final-20-week spatial NNI across modifier settings",
                 x=0.035, y=0.975, ha="left", fontsize=13.0, fontweight="bold")
    fig.subplots_adjust(left=0.065, right=0.975, bottom=0.16, top=0.78, wspace=0.42)

    stem = OUT / "Supplementary_Figure_S1_three_panels_unified"
    fig.savefig(stem.with_suffix(".png"), dpi=1200, facecolor="white")
    fig.savefig(stem.with_suffix(".svg"), facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
