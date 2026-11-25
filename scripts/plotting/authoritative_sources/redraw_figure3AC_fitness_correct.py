from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

from redraw_figure3B_fitness_correct import (
    SOURCE, OUT, LTP, ELIM, BLACK, ELIM_MEAN, ORDER, TREATMENTS,
    MARKERS, OFFSETS, bootstrap_mean, permutation_test, stars,
)


def configure_axis(ax, xlabel, reference=None):
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
    ax.set_xlabel(xlabel)
    if reference is not None:
        ax.axvline(reference, color="#777777", ls=(0, (3, 3)), lw=0.8, zorder=0)
    ax.set_position([0.27, 0.18, 0.62, 0.62])


def save(fig, name):
    for ext in ("png", "svg", "pdf"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=600, facecolor="white",
                    bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)


def draw_a(d):
    fig, ax = plt.subplots(figsize=(4.8, 4.65), dpi=600)
    rows = []
    for yi, (model, h, _) in enumerate(ORDER):
        cond = d[d.model.eq(model) & np.isclose(d.h, h)]
        counts = {}
        for treatment in TREATMENTS:
            td = cond[cond.treatment.eq(treatment)]
            n = len(td)
            elim = int(td.outcome.eq("Elimination").sum())
            ltp = int(td.outcome.eq("Long-term persistence").sum())
            counts[treatment] = (elim, ltp, n)
            y = yi + OFFSETS[treatment]
            left = 0.0
            for outcome, count, color in [
                ("Population elimination", elim, ELIM),
                ("Long-term persistence", ltp, LTP),
            ]:
                p = count / n
                ax.barh(y, p, left=left, height=0.25, color=color,
                        edgecolor="#4A4A4A", linewidth=0.65,
                        hatch="///" if treatment == "Functional modifier" else None)
                left += p
                rows.append({"condition": f"{model} {h:.2f}",
                             "treatment": treatment, "outcome": outcome,
                             "count": count, "n": n, "probability": p})
        ce, cl, cn = counts["Neutral control"]
        fe, fl, fn = counts["Functional modifier"]
        _, p = fisher_exact([[ce, cl], [fe, fl]], alternative="two-sided")
        ax.text(1.02, yi, stars(float(p)), transform=ax.get_yaxis_transform(),
                ha="left", va="center", fontsize=14, fontweight="bold")
        rows.append({"condition": f"{model} {h:.2f}", "test": "two-sided Fisher exact",
                     "n_neutral": cn, "n_variable": fn, "raw_p_value": float(p),
                     "significance": stars(float(p))})

    configure_axis(ax, "Outcome probability")
    ax.legend(handles=[
        Patch(facecolor=LTP, edgecolor="#4A4A4A", label="Long-term persistence"),
        Patch(facecolor=ELIM, edgecolor="#4A4A4A", label="Population elimination"),
        Patch(facecolor="white", edgecolor="#4A4A4A", label="Neutral mutations"),
        Patch(facecolor="white", edgecolor="#4A4A4A", hatch="///", label="Variable mutations"),
    ], frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.06),
       columnspacing=0.8, handlelength=1.15, handletextpad=0.35,
       labelspacing=0.25, fontsize=11.5)
    ax.text(0.50, 1.015, "0.99/0.96 = female/male conversion",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=9.5)
    save(fig, "Figure3A_fitness_outcomes_corrected")
    pd.DataFrame(rows).to_csv(OUT / "Figure3A_fitness_outcome_statistics.csv", index=False)


def draw_c(d):
    fig, ax = plt.subplots(figsize=(4.8, 4.65), dpi=600)
    rng = np.random.default_rng(20261214)
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
                vals = pd.to_numeric(td.loc[td.outcome.eq(outcome), "final20_n_over_k"],
                                     errors="coerce").dropna().to_numpy()
                if len(vals) >= 5 and np.ptp(vals) > 0:
                    v = ax.violinplot(vals, [y], vert=False, widths=0.31,
                                      showmeans=False, showmedians=False,
                                      showextrema=False, bw_method=0.55)
                    body = v["bodies"][0]
                    for path in body.get_paths():
                        path.vertices[:, 1] = (np.maximum(path.vertices[:, 1], y)
                                               if treatment == "Neutral control"
                                               else np.minimum(path.vertices[:, 1], y))
                    body.set_facecolor(color); body.set_edgecolor("none"); body.set_alpha(0.22)
                if len(vals):
                    jitter = rng.uniform(-0.035, 0.035, len(vals))
                    if marker == "o":
                        ax.scatter(vals, y+jitter, s=9, marker="o", facecolors="none",
                                   edgecolors=color, alpha=0.82, linewidth=0.55, zorder=3)
                    else:
                        ax.scatter(vals, y+jitter, s=10, marker="x", color=color,
                                   alpha=0.72, linewidth=0.55, zorder=3)
                    mean, lo, hi = bootstrap_mean(vals, 8000 + yi*20 + ti*5 + oi)
                    mc = BLACK if outcome == "Long-term persistence" else ELIM_MEAN
                    ax.errorbar(mean, y, xerr=[[mean-lo], [hi-mean]], fmt=marker,
                                ms=6.3, mfc="white" if marker == "o" else mc,
                                mec=mc, mew=1.35, ecolor=mc, lw=1.35,
                                capsize=2.4, zorder=7)
        a = pd.to_numeric(cond.loc[cond.treatment.eq("Neutral control"),
                                   "final20_n_over_k"], errors="coerce").dropna()
        b = pd.to_numeric(cond.loc[cond.treatment.eq("Functional modifier"),
                                   "final20_n_over_k"], errors="coerce").dropna()
        effect, p, extreme = permutation_test(a, b, 2700 + yi)
        ax.text(1.02, yi, stars(p), transform=ax.get_yaxis_transform(),
                ha="left", va="center", fontsize=14, fontweight="bold")
        rows.append({"condition": f"{model} {h:.2f}", "n_neutral": len(a),
                     "n_variable": len(b), "mean_difference_variable_minus_neutral": effect,
                     "permutations": 10000, "extreme_permutations": extreme,
                     "plus_one_p_value": p, "significance": stars(p)})

    configure_axis(ax, "Final relative population size")
    ax.legend(handles=[
        Line2D([], [], marker="o", ls="", color=BLACK, mfc="none", label="Neutral mutations"),
        Line2D([], [], marker="x", ls="", color=BLACK, label="Variable mutations"),
        Line2D([], [], marker="o", ls="", color=LTP, label="Long-term persistence"),
        Line2D([], [], marker="o", ls="", color=ELIM, label="Population elimination"),
    ], frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.06),
       columnspacing=0.8, handlelength=1.1, handletextpad=0.35, labelspacing=0.25)
    save(fig, "Figure3C_final20_population_corrected")
    pd.DataFrame(rows).to_csv(OUT / "Figure3C_10k_permutation_statistics.csv", index=False)


def main():
    d = pd.read_csv(SOURCE)
    d["final20_attribute_weighted"] = pd.to_numeric(d["final20_attribute_weighted"], errors="coerce").clip(0, 1)
    d["final20_n_over_k"] = pd.to_numeric(d["final20_n_over_k"], errors="coerce").clip(0, 1)
    draw_a(d)
    draw_c(d)


if __name__ == "__main__":
    main()
