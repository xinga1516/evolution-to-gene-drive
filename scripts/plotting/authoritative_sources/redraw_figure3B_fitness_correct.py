from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT / "new_main_figure_task" / "final20_attribute_panels_20261024"
    / "Figure4_final20_source_100rep.csv"
)
OUT = ROOT / "single_panel_outputs" / "Figure3B_fitness_corrected"
OUT.mkdir(parents=True, exist_ok=True)

LTP = "#6CC4A1"
ELIM = "#F4A261"
BLACK = "#202020"
ELIM_MEAN = "#C8752C"
ORDER = [
    ("Panmictic", 0.70, "0.70"),
    ("Panmictic", 0.99, "0.99/0.96"),
    ("Spatial", 0.70, "0.70"),
    ("Spatial", 0.99, "0.99/0.96"),
]
TREATMENTS = ["Neutral control", "Functional modifier"]
MARKERS = {"Neutral control": "o", "Functional modifier": "x"}
OFFSETS = {"Neutral control": -0.16, "Functional modifier": 0.16}
N_BOOT = 10_000
N_PERM = 10_000


def bootstrap_mean(values, seed):
    x = np.asarray(values, float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return np.nan, np.nan, np.nan
    if len(x) == 1:
        return float(x[0]), np.nan, np.nan
    rng = np.random.default_rng(seed)
    means = np.empty(N_BOOT)
    for start in range(0, N_BOOT, 1000):
        n = min(1000, N_BOOT - start)
        means[start:start+n] = x[rng.integers(0, len(x), (n, len(x)))].mean(1)
    lo, hi = np.quantile(means, [0.025, 0.975])
    return float(x.mean()), float(lo), float(hi)


def permutation_test(a, b, seed):
    a = np.asarray(a, float); a = a[np.isfinite(a)]
    b = np.asarray(b, float); b = b[np.isfinite(b)]
    observed = float(b.mean() - a.mean())
    pooled = np.concatenate([a, b])
    rng = np.random.default_rng(seed)
    extreme = 0
    for _ in range(N_PERM):
        p = rng.permutation(pooled)
        stat = p[len(a):].mean() - p[:len(a)].mean()
        extreme += abs(stat) >= abs(observed) - 1e-15
    return observed, (extreme + 1) / (N_PERM + 1), extreme


def stars(p):
    if p < 0.001: return "***"
    if p < 0.01: return "**"
    if p < 0.05: return "*"
    return "ns"


def main():
    d = pd.read_csv(SOURCE)
    d["final20_attribute_weighted"] = pd.to_numeric(
        d["final20_attribute_weighted"], errors="coerce"
    ).clip(0, 1)

    plt.rcParams.update({
        "font.family": "Arial", "font.size": 15,
        "axes.labelsize": 17, "xtick.labelsize": 15,
        "ytick.labelsize": 15, "legend.fontsize": 11.5,
        "axes.linewidth": 0.8, "svg.fonttype": "none", "pdf.fonttype": 42,
    })
    fig, ax = plt.subplots(figsize=(4.8, 4.65), dpi=600)
    rng = np.random.default_rng(20261114)
    rows = []

    for yi, (model, h, _) in enumerate(ORDER):
        cond = d[d.model.eq(model) & np.isclose(d.h, h)]
        for ti, treatment in enumerate(TREATMENTS):
            td = cond[cond.treatment.eq(treatment)]
            y = yi + OFFSETS[treatment]
            marker = MARKERS[treatment]
            for oi, (outcome, color) in enumerate([
                ("Long-term persistence", LTP), ("Elimination", ELIM)
            ]):
                vals = pd.to_numeric(
                    td.loc[td.outcome.eq(outcome), "final20_attribute_weighted"],
                    errors="coerce",
                ).dropna().to_numpy()
                if len(vals) >= 5 and np.ptp(vals) > 0:
                    v = ax.violinplot(vals, [y], vert=False, widths=0.31,
                                      showmeans=False, showmedians=False,
                                      showextrema=False, bw_method=0.55)
                    body = v["bodies"][0]
                    for path in body.get_paths():
                        path.vertices[:, 1] = (
                            np.maximum(path.vertices[:, 1], y)
                            if treatment == "Neutral control"
                            else np.minimum(path.vertices[:, 1], y)
                        )
                    body.set_facecolor(color); body.set_edgecolor("none"); body.set_alpha(0.22)
                if len(vals):
                    jitter = rng.uniform(-0.035, 0.035, len(vals))
                    if marker == "o":
                        ax.scatter(vals, y + jitter, s=9, marker="o", facecolors="none",
                                   edgecolors=color, alpha=0.82, linewidth=0.55, zorder=3)
                    else:
                        ax.scatter(vals, y + jitter, s=10, marker="x", color=color,
                                   alpha=0.72, linewidth=0.55, zorder=3)
                    mean, lo, hi = bootstrap_mean(vals, 5000 + yi * 20 + ti * 5 + oi)
                    mean_color = BLACK if outcome == "Long-term persistence" else ELIM_MEAN
                    ax.errorbar(mean, y, xerr=[[mean-lo], [hi-mean]], fmt=marker,
                                ms=6.3, mfc="white" if marker == "o" else mean_color,
                                mec=mean_color, mew=1.35, ecolor=mean_color,
                                lw=1.35, capsize=2.4, zorder=7)

        a = pd.to_numeric(cond.loc[cond.treatment.eq("Neutral control"),
                                   "final20_attribute_weighted"], errors="coerce").dropna()
        b = pd.to_numeric(cond.loc[cond.treatment.eq("Functional modifier"),
                                   "final20_attribute_weighted"], errors="coerce").dropna()
        effect, p, extreme = permutation_test(a, b, 700 + yi)
        ax.text(1.02, yi, stars(p), transform=ax.get_yaxis_transform(),
                ha="left", va="center", fontsize=14, fontweight="bold")
        rows.append({
            "condition": f"{model} {h:.2f}", "n_neutral": len(a),
            "n_variable": len(b), "mean_difference_variable_minus_neutral": effect,
            "permutations": N_PERM, "extreme_permutations": extreme,
            "plus_one_p_value": p, "significance": stars(p),
        })

    ax.set_yticks(range(4), [x[2] for x in ORDER])
    ax.text(-0.10, 0.75, "Panmictic", transform=ax.transAxes,
            ha="right", va="center", fontsize=15)
    ax.text(-0.10, 0.25, "Spatial", transform=ax.transAxes,
            ha="right", va="center", fontsize=15)
    ax.text(-0.10, 1.015, "Drive conversion", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=12, fontweight="bold")
    ax.invert_yaxis()
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlim(0, 1)
    ax.set_xticks([0, 0.25, 0.50, 0.75, 1.00])
    ax.axvline(0.50, color="#777777", ls=(0, (3, 3)), lw=0.8, zorder=0)
    ax.set_xlabel("Final female heterozygote fitness")
    ax.legend(handles=[
        Line2D([], [], marker="o", ls="", color=BLACK, mfc="none", label="Neutral mutations"),
        Line2D([], [], marker="x", ls="", color=BLACK, label="Variable mutations"),
        Line2D([], [], marker="o", ls="", color=LTP, label="Long-term persistence"),
        Line2D([], [], marker="o", ls="", color=ELIM, label="Population elimination"),
    ], frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.06),
       columnspacing=0.8, handlelength=1.1, handletextpad=0.35, labelspacing=0.25)
    ax.set_position([0.27, 0.18, 0.62, 0.62])

    for ext in ("png", "svg", "pdf"):
        fig.savefig(OUT / f"Figure3B_final20_female_fitness_corrected.{ext}",
                    dpi=600, facecolor="white", bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    pd.DataFrame(rows).to_csv(OUT / "Figure3B_10k_permutation_statistics.csv", index=False)


if __name__ == "__main__":
    main()
