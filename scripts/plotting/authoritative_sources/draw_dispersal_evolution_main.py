#!/usr/bin/env python3
"""Rebuild the 2x2 dispersal-evolution main figure from a formal run snapshot."""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import binomtest, t as student_t, ttest_1samp, ttest_rel
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


MAIN_CONVERSIONS = (0.75, 0.85, 0.95, 0.99)
MODES = ("evolving", "uniform")
OUTCOMES = ("elimination", "long-term persistence", "drive loss")
BOOTSTRAP_REPS = 10_000
RNG_SEED = 20261019
FINAL_WINDOW = 20
# Final outcome palette approved for Figure 7.  The no-drive control is a
# persistent endpoint and therefore uses the long-term-persistence colour.
VARIABLE = "#C29A3A"
FIXED = "#EDC3AE"
NEUTRAL = "#7F7F7F"
# Outcome-composition panels use the author's fixed three-colour mapping.
OUTCOME_COLORS = {
    "elimination": "#F4A261",
    "drive loss": "#4E79B7",
    "long-term persistence": "#6CC4A1",
}
RAIN_LTP = OUTCOME_COLORS["long-term persistence"]
RAIN_ELIM = OUTCOME_COLORS["elimination"]
RAIN_LOSS = OUTCOME_COLORS["drive loss"]


def find_runs_root(root: Path) -> Path:
    candidates = [root / "runs", root / root.name / "runs"]
    candidates.extend(p for p in root.rglob("runs") if p.is_dir())
    for candidate in candidates:
        if all((candidate / mode).is_dir() for mode in ("evolving", "uniform", "nodrive")):
            return candidate
    raise FileNotFoundError(f"Could not locate runs root below {root}")


def metadata(path: Path) -> dict[str, str]:
    frame = pd.read_csv(path, dtype=str)
    return dict(zip(frame["key"], frame["value"]))


def holm(pvalues: list[float]) -> list[float]:
    p = np.asarray(pvalues, dtype=float)
    out = np.full(len(p), np.nan)
    valid = np.flatnonzero(np.isfinite(p))
    if not len(valid):
        return out.tolist()
    order = valid[np.argsort(p[valid])]
    adjusted = np.maximum.accumulate((len(order) - np.arange(len(order))) * p[order])
    out[order] = np.minimum(adjusted, 1.0)
    return out.tolist()


def fisher_freeman_halton_2xk(table: np.ndarray) -> float:
    """Deterministic two-sided exact test for a 2×k table with fixed margins."""
    table = np.asarray(table, dtype=int)
    if table.shape[0] != 2 or np.any(table < 0):
        raise ValueError("Expected a non-negative 2×k table")
    columns = table.sum(axis=0)
    row0 = int(table[0].sum())
    total = int(columns.sum())
    denominator = math.comb(total, row0)

    def probability(first_row):
        numerator = 1
        for col_total, cell in zip(columns, first_row):
            numerator *= math.comb(int(col_total), int(cell))
        return numerator / denominator

    observed = probability(table[0])
    pvalue = 0.0

    def enumerate_rows(index, remaining, prefix):
        nonlocal pvalue
        if index == len(columns) - 1:
            if 0 <= remaining <= columns[index]:
                candidate = prefix + [remaining]
                prob = probability(candidate)
                if prob <= observed + 1e-15:
                    pvalue += prob
            return
        lower = max(0, remaining - int(columns[index + 1 :].sum()))
        upper = min(int(columns[index]), remaining)
        for value in range(lower, upper + 1):
            enumerate_rows(index + 1, remaining - value, prefix + [value])

    enumerate_rows(0, row0, [])
    return min(float(pvalue), 1.0)


def bootstrap_mean_ci(values, rng, reps=BOOTSTRAP_REPS):
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if not len(x):
        return np.nan, np.nan, np.nan
    draws = rng.choice(x, size=(reps, len(x)), replace=True).mean(axis=1)
    return float(x.mean()), *np.quantile(draws, [0.025, 0.975]).tolist()


def classify(log_text: str) -> str | None:
    if "SUPPRESSED" in log_text:
        return "elimination"
    if "POP_PERSISTS" in log_text:
        return "drive loss"
    if "ENDING_AFTER_1500_WEEKS" in log_text:
        return "long-term persistence"
    return None


def final_window(frame: pd.DataFrame, n: int = FINAL_WINDOW) -> pd.DataFrame | None:
    """Return the final n distinct recorded ticks for one simulation."""
    clean = frame.dropna(subset=["tick"]).copy()
    ticks = np.sort(clean["tick"].astype(int).unique())
    if len(ticks) < n:
        return None
    return clean.loc[clean["tick"].astype(int).isin(ticks[-n:])].copy()


def read_run(run_dir: Path, mode: str, conversion: float | None) -> tuple[dict, list[dict]]:
    reasons = []
    row = {"mode": mode, "conversion": conversion, "path": str(run_dir)}
    try:
        meta = metadata(run_dir / "data_metadata.csv")
        row["origin_seed"] = int(meta["checkpoint_origin_seed"])
        row["branch_seed"] = int(meta["branch_seed"])
        row["spatial_area"] = float(meta.get("spatial_area", 1.0))
    except Exception as exc:
        reasons.append({**row, "reason": f"metadata: {exc}"})
        return row, reasons

    try:
        status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
        row["exit_code"] = int(status.get("exit_code", -999))
    except Exception as exc:
        row["exit_code"] = -999
        reasons.append({**row, "reason": f"status: {exc}"})

    try:
        log_text = (run_dir / "slim.log").read_text(encoding="utf-8", errors="replace")
        row["outcome"] = "no drive" if mode == "nodrive" else classify(log_text)
        if mode != "nodrive" and row["outcome"] is None:
            reasons.append({**row, "reason": "unclassifiable outcome log"})
    except Exception as exc:
        row["outcome"] = None
        reasons.append({**row, "reason": f"log: {exc}"})

    try:
        pop = pd.read_csv(run_dir / "data_population.csv", usecols=["tick", "n_age_gt0"])
        pop["tick"] = pd.to_numeric(pop["tick"], errors="coerce")
        baseline = pop.loc[pop["tick"] == 100, "n_age_gt0"]
        row["baseline_adult_n"] = float(baseline.iloc[0]) if len(baseline) else np.nan
        late = final_window(pop)
        row["late_adult_n"] = float(late["n_age_gt0"].mean()) if late is not None else np.nan
        row["relative_population_size"] = row["late_adult_n"] / row["baseline_adult_n"]
        if late is None:
            reasons.append({**row, "reason": "population has fewer than 20 recorded ticks"})
    except Exception as exc:
        row["baseline_adult_n"] = row["late_adult_n"] = row["relative_population_size"] = np.nan
        reasons.append({**row, "reason": f"population: {exc}"})

    try:
        traits = pd.read_csv(run_dir / "data_traits.csv", usecols=["tick", "cohort", "mean"])
        traits = traits.loc[traits["cohort"] == "age_gt0"].copy()
        traits["tick"] = pd.to_numeric(traits["tick"], errors="coerce")
        baseline = traits.loc[traits["tick"] == 100, "mean"]
        row["baseline_adult_dispersal"] = float(baseline.iloc[0]) if len(baseline) else np.nan
        paired = traits.merge(pop[["tick", "n_age_gt0"]], on="tick", how="inner")
        paired["mean"] = pd.to_numeric(paired["mean"], errors="coerce")
        paired["n_age_gt0"] = pd.to_numeric(paired["n_age_gt0"], errors="coerce")
        paired = paired[np.isfinite(paired["mean"]) & (paired["n_age_gt0"] > 0)].copy()
        weighted = final_window(paired)
        if weighted is not None:
            denom = float(weighted["n_age_gt0"].sum())
            row["late_adult_dispersal"] = (
                float(np.average(weighted["mean"], weights=weighted["n_age_gt0"]))
                if denom > 0 and len(weighted) == FINAL_WINDOW else np.nan
            )
        else:
            row["late_adult_dispersal"] = np.nan
        row["dispersal_E_percent"] = 100.0 * (
            row["late_adult_dispersal"] / row["baseline_adult_dispersal"] - 1.0
        )
        row["dispersal_delta"] = row["late_adult_dispersal"] - row["baseline_adult_dispersal"]
        weighted100 = final_window(paired, 100)
        if weighted100 is not None and float(weighted100["n_age_gt0"].sum()) > 0:
            row["last100_adult_dispersal"] = float(np.average(
                weighted100["mean"], weights=weighted100["n_age_gt0"]))
            row["last100_dispersal_E_percent"] = 100.0 * (
                row["last100_adult_dispersal"] / row["baseline_adult_dispersal"] - 1.0)
        else:
            row["last100_adult_dispersal"] = row["last100_dispersal_E_percent"] = np.nan
        if weighted is None:
            reasons.append({**row, "reason": "traits have fewer than 20 adult ticks"})
    except Exception as exc:
        for key in ("baseline_adult_dispersal", "late_adult_dispersal", "dispersal_E_percent", "dispersal_delta",
                    "last100_adult_dispersal", "last100_dispersal_E_percent"):
            row[key] = np.nan
        reasons.append({**row, "reason": f"traits: {exc}"})

    try:
        spatial = pd.read_csv(run_dir / "data_spatial.csv", usecols=["tick", "n_age_gt0", "wt_alleles", "drive_alleles", "nni_mean"])
        spatial["tick"] = pd.to_numeric(spatial["tick"], errors="coerce")
        late = final_window(spatial)
        late100 = final_window(spatial, 100)
        if late is None:
            row["late_normalized_nni"] = np.nan
            reasons.append({**row, "reason": "spatial has fewer than 20 recorded ticks"})
        else:
            denom = 0.5 * np.sqrt(row["spatial_area"] / late["n_age_gt0"].astype(float))
            row["late_normalized_nni"] = float((late["nni_mean"].astype(float) / denom).mean())
            row["late_wt_present"] = bool((late["wt_alleles"].astype(float) > 0).all())
            row["late_drive_present"] = bool((late["drive_alleles"].astype(float) > 0).all())
        if late100 is not None:
            denom100 = 0.5 * np.sqrt(row["spatial_area"] / late100["n_age_gt0"].astype(float))
            row["last100_normalized_nni"] = float((late100["nni_mean"].astype(float) / denom100).mean())
        else:
            row["last100_normalized_nni"] = np.nan
    except Exception as exc:
        row["late_normalized_nni"] = row["last100_normalized_nni"] = np.nan
        reasons.append({**row, "reason": f"spatial: {exc}"})
    return row, reasons


def collect(runs_root: Path):
    rows, reasons = [], []
    for mode in MODES:
        for conversion in MAIN_CONVERSIONS:
            group = runs_root / mode / f"drive_c_{conversion:g}"
            if not group.is_dir():
                reasons.append({"mode": mode, "conversion": conversion, "reason": "group directory missing"})
                continue
            for run_dir in sorted(group.glob("seed_*")):
                row, why = read_run(run_dir, mode, conversion)
                rows.append(row); reasons.extend(why)
    nodrive_root = runs_root / "nodrive"
    nodrive_seeds = sorted(p for p in nodrive_root.rglob("seed_*") if p.is_dir())
    for run_dir in nodrive_seeds:
        row, why = read_run(run_dir, "nodrive", None)
        rows.append(row); reasons.extend(why)
    return pd.DataFrame(rows), pd.DataFrame(reasons)


def paired_multicategory_exact(table: np.ndarray) -> float:
    """Exact within-pair label-swap test of equal three-category marginals."""
    table = np.asarray(table, dtype=int)
    pairs = [(i, j, int(table[i, j] + table[j, i])) for i in range(3) for j in range(i + 1, 3)]
    observed = table.sum(axis=1) - table.sum(axis=0)
    observed_stat = float(np.square(observed).sum())
    probability = 0.0
    for choices in itertools.product(*[range(n + 1) for _, _, n in pairs]):
        diff = np.zeros(3, dtype=int)
        weight = 1.0
        for (i, j, n), k in zip(pairs, choices):
            delta = 2 * k - n
            diff[i] += delta
            diff[j] -= delta
            weight *= math.comb(n, k) / (2 ** n)
        if float(np.square(diff).sum()) >= observed_stat - 1e-12:
            probability += weight
    return min(1.0, probability)


def paired_outcome_tables(data: pd.DataFrame):
    overall, category = [], []
    valid = data[(data["mode"].isin(MODES)) & data["outcome"].isin(OUTCOMES) & (data["exit_code"] == 0)]
    for conv in MAIN_CONVERSIONS:
        sub = valid[valid["conversion"] == conv]
        paired = sub.pivot(index="origin_seed", columns="mode", values="outcome").dropna(subset=list(MODES))
        transition = np.array([[int(((paired["evolving"] == a) & (paired["uniform"] == b)).sum()) for b in OUTCOMES] for a in OUTCOMES])
        table = np.array([[int((paired[m] == o).sum()) for o in OUTCOMES] for m in MODES])
        p = paired_multicategory_exact(transition)
        overall.append({"conversion": conv, "n_pairs": len(paired), "table_evolving": table[0].tolist(), "table_fixed": table[1].tolist(), "transition_evolving_rows_fixed_cols": transition.tolist(), "p_raw": p})
        for idx, outcome in enumerate(OUTCOMES):
            evo_only = int(((paired["evolving"] == outcome) & (paired["uniform"] != outcome)).sum())
            fixed_only = int(((paired["evolving"] != outcome) & (paired["uniform"] == outcome)).sum())
            discordant = evo_only + fixed_only
            pcat = float(binomtest(evo_only, discordant, 0.5, alternative="two-sided").pvalue) if discordant else 1.0
            category.append({"conversion": conv, "outcome": outcome, "n_pairs": len(paired), "evolving_yes": table[0, idx], "fixed_yes": table[1, idx], "discordant_evolving_only": evo_only, "discordant_fixed_only": fixed_only, "p_raw": pcat})
    adj = holm([r["p_raw"] for r in overall])
    for row, p in zip(overall, adj): row["p_holm_4"] = p
    adj = holm([r["p_raw"] for r in category])
    for row, p in zip(category, adj): row["p_holm_12"] = p
    return pd.DataFrame(overall), pd.DataFrame(category)

def prespecified_four_outcome_tests(category: pd.DataFrame) -> pd.DataFrame:
    q = category[(category["conversion"].isin([0.95, 0.99])) &
                 (category["outcome"].isin(["elimination", "drive loss"]))].copy()
    q["p_holm_4"] = holm(q["p_raw"].tolist())
    return q.drop(columns=["p_holm_12"], errors="ignore")


def analysis_sets(data: pd.DataFrame):
    ok = data["exit_code"].eq(0)
    persistent = data["outcome"].eq("long-term persistence") & data.get("late_wt_present", False) & data.get("late_drive_present", False)
    metric = data[["dispersal_E_percent", "relative_population_size", "late_normalized_nni"]].notna().all(axis=1)
    no = data[(data["mode"] == "nodrive") & ok & data["dispersal_E_percent"].notna()].copy()
    evo = data[(data["mode"] == "evolving") & ok & persistent & metric].copy()
    fixed = data[(data["mode"] == "uniform") & ok & persistent & metric].copy()
    return no, evo, fixed


def statistics(data: pd.DataFrame, rng):
    no, evo, fixed = analysis_sets(data)
    no_map = no.set_index("origin_seed")
    b_rows = []
    paired_b = []
    eligible = data[(data["mode"] == "evolving") & data["exit_code"].eq(0)
                    & data["outcome"].isin(OUTCOMES)
                    & data["dispersal_E_percent"].notna()].copy()
    for conv in MAIN_CONVERSIONS:
        g = eligible[eligible["conversion"] == conv].copy()
        g["endpoint_group"] = np.where(g["outcome"].eq("long-term persistence"), "LTP", "Non-LTP")
        g["nodrive_E"] = g["origin_seed"].map(no_map["dispersal_E_percent"])
        g = g.dropna(subset=["nodrive_E"])
        g["extra_E_percentage_points"] = g["dispersal_E_percent"] - g["nodrive_E"]
        paired_b.append(g)
        for endpoint_group, e in g.groupby("endpoint_group", sort=False):
            if len(e) < 2:
                continue
            t = ttest_1samp(e["extra_E_percentage_points"], 0.0, nan_policy="omit")
            mean, lo, hi = bootstrap_mean_ci(e["dispersal_E_percent"], rng)
            b_rows.append({"comparison": f"{endpoint_group} evolving drive E - matched no-drive E",
                           "endpoint_group": endpoint_group, "conversion": conv, "n": len(e),
                           "display_mean": mean, "display_ci_low": lo, "display_ci_high": hi,
                           "mean_effect": float(e["extra_E_percentage_points"].mean()),
                           "t": float(t.statistic), "p_raw": float(t.pvalue)})
    for row, p in zip(b_rows, holm([r["p_raw"] for r in b_rows])):
        row["p_holm_family"] = p

    # Panel C uses every classifiable simulation.  Elimination is a genuine
    # zero-population endpoint; drive-loss and LTP retain their run-specific
    # final-20-generation population summaries.  Panel D remains the
    # prespecified LTP-only last-100-tick analysis.
    all_evo = data[(data["mode"] == "evolving") & data["exit_code"].eq(0)
                   & data["outcome"].isin(OUTCOMES)].copy()
    all_fixed = data[(data["mode"] == "uniform") & data["exit_code"].eq(0)
                     & data["outcome"].isin(OUTCOMES)].copy()
    all_evo.loc[all_evo["outcome"].eq("elimination"), "relative_population_size"] = 0.0
    all_fixed.loc[all_fixed["outcome"].eq("elimination"), "relative_population_size"] = 0.0
    c_rows, paired_c, d_rows = [], [], []
    for conv in MAIN_CONVERSIONS:
        ec = all_evo[all_evo["conversion"] == conv].set_index("origin_seed")
        fc = all_fixed[all_fixed["conversion"] == conv].set_index("origin_seed")
        seeds = sorted(set(ec.index) & set(fc.index))
        pair = pd.DataFrame({
            "origin_seed": seeds,
            "conversion": conv,
            "evolving_relative_N": ec.loc[seeds, "relative_population_size"].to_numpy(),
            "fixed_relative_N": fc.loc[seeds, "relative_population_size"].to_numpy(),
            "evolving_outcome": ec.loc[seeds, "outcome"].to_numpy(),
            "fixed_outcome": fc.loc[seeds, "outcome"].to_numpy(),
        })
        pair["population_difference"] = pair["evolving_relative_N"] - pair["fixed_relative_N"]
        paired_c.append(pair)
        t = ttest_rel(pair["evolving_relative_N"], pair["fixed_relative_N"], nan_policy="omit")
        diff = pair["population_difference"].astype(float)
        mean = float(diff.mean())
        sem = float(diff.std(ddof=1) / np.sqrt(len(diff)))
        margin = float(student_t.ppf(0.975, len(diff) - 1) * sem)
        lo, hi = mean - margin, mean + margin
        c_rows.append({"conversion": conv, "paired_n": len(pair), "mean_evolving_minus_fixed": mean, "ci_low": lo, "ci_high": hi, "t": float(t.statistic), "p_raw": float(t.pvalue)})
        # D is intentionally calculated from the LTP-only last-100-tick set.
        ed = evo[evo["conversion"] == conv].set_index("origin_seed")
        fd = fixed[fixed["conversion"] == conv].set_index("origin_seed")
        dseeds = sorted(set(ed.index) & set(fd.index))
        dvalid = pd.DataFrame({
            "fixed_normalized_NNI": fd.loc[dseeds, "last100_normalized_nni"].to_numpy(),
            "extra_E_percentage_points": ed.loc[dseeds, "last100_dispersal_E_percent"].to_numpy()
              - pd.Series(dseeds).map(no_map["last100_dispersal_E_percent"]).to_numpy(),
        }).dropna()
        xmean, xlo, xhi = bootstrap_mean_ci(dvalid["fixed_normalized_NNI"], rng)
        ymean, ylo, yhi = bootstrap_mean_ci(dvalid["extra_E_percentage_points"], rng)
        d_rows.append({"conversion": conv, "n": len(dvalid), "fixed_nni_mean": xmean, "fixed_nni_ci_low": xlo, "fixed_nni_ci_high": xhi, "extra_E_mean": ymean, "extra_E_ci_low": ylo, "extra_E_ci_high": yhi})
    for row, p in zip(c_rows, holm([r["p_raw"] for r in c_rows])): row["p_holm_4"] = p
    return pd.DataFrame(b_rows), pd.concat(paired_b, ignore_index=True), pd.DataFrame(c_rows), pd.concat(paired_c, ignore_index=True), pd.DataFrame(d_rows)


def p_symbol(p):
    if not np.isfinite(p): return "NA"
    if p < 0.001: return "***"
    if p < 0.01: return "**"
    if p < 0.05: return "*"
    return "ns"


def half_violin_horizontal(ax, values, y, color, side, width=0.31):
    values = np.asarray(values, float)
    values = values[np.isfinite(values)]
    if len(values) < 2 or np.ptp(values) == 0:
        return
    violin = ax.violinplot(values, positions=[y], orientation="horizontal", widths=width,
                           showextrema=False, bw_method=0.55)
    body = violin["bodies"][0]
    body.set_facecolor(color); body.set_edgecolor("none"); body.set_alpha(0.26)
    verts = body.get_paths()[0].vertices
    verts[:, 1] = np.maximum(verts[:, 1], y) if side == "upper" else np.minimum(verts[:, 1], y)


def horizontal_cloud(ax, values, y, color, side, rng, seed, marker="o", summary_color="#222222"):
    values = np.asarray(values, float)
    values = values[np.isfinite(values)]
    half_violin_horizontal(ax, values, y, color, side)
    if not len(values):
        return
    jitter = rng.uniform(-0.045, 0.045, len(values))
    if marker == "o":
        ax.scatter(values, np.full(len(values), y) + jitter, s=9, marker="o", facecolors="none", edgecolors=color,
                   alpha=0.55, lw=.45, rasterized=True, zorder=3)
    else:
        ax.scatter(values, np.full(len(values), y) + jitter, s=10, marker=marker, c=color,
                   alpha=0.55, lw=.55, rasterized=True, zorder=3)
    mean, lo, hi = bootstrap_mean_ci(values, np.random.default_rng(seed))
    ax.errorbar(mean, y, xerr=[[mean-lo], [hi-mean]], fmt=marker, ms=4.5,
                mfc="white" if marker == "o" else summary_color, mec=summary_color, mew=1.0, ecolor=summary_color,
                elinewidth=1.0, capsize=2, zorder=5)


def panel_letter(ax, letter):
    ax.text(-0.13, 1.08, letter, transform=ax.transAxes, fontsize=14,
            fontweight="bold", ha="left", va="top")


def plot_figure(data, overall, bstats, paired_b, cstats, paired_c, dstats, out_path: Path):
    plt.rcParams.update({
        "font.family": "Arial", "font.size": 14, "axes.labelsize": 16,
        "xtick.labelsize": 14, "ytick.labelsize": 14, "legend.fontsize": 11.5,
        "axes.linewidth": 0.8, "savefig.transparent": False,
    })
    fig, axes = plt.subplots(2, 2, figsize=(10.2, 10.2))
    fig.subplots_adjust(left=.11, right=.97, bottom=.09, top=.88, wspace=.36, hspace=.42)
    for ax in axes.flat:
        ax.set_box_aspect(1)

    # A: exact Figure 2–4 outcome grammar: paired horizontal 100% bars,
    # fixed control hatched above and evolving treatment solid below.
    ax = axes[0, 0]
    valid = data[(data["mode"].isin(MODES)) & data["outcome"].isin(OUTCOMES) & data["exit_code"].eq(0)]
    ypos = np.arange(len(MAIN_CONVERSIONS), dtype=float)
    offsets = {"uniform": -0.17, "evolving": 0.17}
    visual_outcomes = ("elimination", "drive loss", "long-term persistence")
    for yi, conv in enumerate(MAIN_CONVERSIONS):
        for mode in ("uniform", "evolving"):
            sub = valid[(valid["conversion"] == conv) & (valid["mode"] == mode)]
            n = len(sub); left = 0.0
            for outcome in visual_outcomes:
                value = float((sub["outcome"] == outcome).sum() / n) if n else 0.0
                if value > 0:
                    ax.barh(yi + offsets[mode], value, left=left, height=.27,
                            color=OUTCOME_COLORS[outcome], edgecolor="#333333", lw=.35,
                            hatch="///" if mode == "uniform" else None)
                left += value
            # Sample-size annotations are supplied as editable PPT text boxes.
            # Keeping the plot panel clean also matches the Figure 2–5 workflow.
    ax.set_xlim(0, 1.14); ax.set_yticks(ypos, [f"{x:.2f}" for x in MAIN_CONVERSIONS]); ax.invert_yaxis()
    ax.set_xlabel("Outcome probability"); ax.set_ylabel("Drive conversion")
    handles = [Patch(facecolor=OUTCOME_COLORS[o], edgecolor="#333333", label=o.capitalize()) for o in visual_outcomes]
    handles += [Patch(facecolor="white", edgecolor="#333333", hatch="///", label="Fixed dispersal"),
                Patch(facecolor="white", edgecolor="#333333", label="Evolving dispersal")]
    ax.legend(handles=handles, frameon=False, ncol=2, loc="lower center",
              bbox_to_anchor=(.50, 1.03), columnspacing=.55, handlelength=1.05)
    panel_letter(ax, "A")

    # B: all outcomes use each run's population-weighted final-20-generation endpoint.
    ax = axes[0, 1]
    no, _, _ = analysis_sets(data)
    eligible = data[(data["mode"] == "evolving") & data["exit_code"].eq(0)
                    & data["outcome"].isin(OUTCOMES) & data["dispersal_E_percent"].notna()].copy()
    rng_b = np.random.default_rng(RNG_SEED + 20)
    horizontal_cloud(ax, no["dispersal_E_percent"].dropna().to_numpy(), 0, RAIN_LTP, "upper", rng_b, RNG_SEED + 100)
    for yi, conv in enumerate(MAIN_CONVERSIONS, start=1):
        g = eligible[eligible["conversion"] == conv]
        ltp = g[g["outcome"].eq("long-term persistence")]["dispersal_E_percent"].to_numpy(float)
        horizontal_cloud(ax, ltp, yi, RAIN_LTP, "lower", rng_b, RNG_SEED + 100 + yi)
        for outcome, color, offset in [("elimination", RAIN_ELIM, -.045),
                                       ("drive loss", RAIN_LOSS, .045)]:
            vals = g[g["outcome"].eq(outcome)]["dispersal_E_percent"].to_numpy(float)
            if len(vals):
                ax.scatter(vals, np.full(len(vals), yi + offset) + rng_b.uniform(-.025, .025, len(vals)),
                           s=11, c=color, alpha=.75, lw=0, rasterized=True, zorder=5)
        stat = bstats[(bstats["conversion"] == conv) & bstats["endpoint_group"].eq("Non-LTP")]
        if len(stat):
            r = stat.iloc[0]
            ax.errorbar(r.display_mean, yi,
                        xerr=[[r.display_mean-r.display_ci_low], [r.display_ci_high-r.display_mean]],
                        fmt="o", ms=4.8, mfc="white", mec=RAIN_ELIM, mew=1.0,
                        ecolor=RAIN_ELIM, elinewidth=1.1, capsize=2.2, zorder=7)
    ax.axvline(0, color="#777777", ls=(0, (3, 3)), lw=.8, zorder=0)
    ax.set_yticks(range(5), ["No drive"] + [f"{c:.2f}" for c in MAIN_CONVERSIONS]); ax.invert_yaxis()
    ax.set_xlabel("Adult dispersal change (%)"); ax.set_ylabel("")
    ax.legend(handles=[Line2D([], [], marker="o", ls="", color=RAIN_LTP, label="No drive")],
              frameon=False, loc="lower center", bbox_to_anchor=(.5, 1.03), ncol=2, fontsize=11.5,
              handletextpad=.3, columnspacing=.7)
    panel_letter(ax, "B")

    # C: all classifiable outcomes; elimination is plotted at zero.
    ax = axes[1, 0]
    rng_c = np.random.default_rng(RNG_SEED + 30)
    for yi, conv in enumerate(MAIN_CONVERSIONS):
        sub = paired_c[paired_c["conversion"] == conv]
        # Marker encodes dispersal treatment; colour encodes the outcome of
        # the corresponding member of the matched pair.
        for value, outcome_col, offset, side, marker in [
            ("fixed_relative_N", "fixed_outcome", -.12, "upper", "o"),
            ("evolving_relative_N", "evolving_outcome", .12, "lower", "x"),
        ]:
            for oi, outcome in enumerate(OUTCOMES):
                vals = sub.loc[sub[outcome_col].eq(outcome), value].dropna().to_numpy(float)
                cloud_color = OUTCOME_COLORS[outcome]
                horizontal_cloud(ax, vals, yi + offset, cloud_color, side,
                                 rng_c, RNG_SEED + 300 + yi * 20 + oi + (10 if marker == "x" else 0),
                                 marker=marker,
                                 summary_color=RAIN_ELIM if outcome == "elimination" else "#222222")
        # Significance symbols and conditional n values are supplied as editable
        # PPT text boxes, rather than baked into the rasterized panel.
    ax.set_yticks(range(len(MAIN_CONVERSIONS)), [f"{c:.2f}" for c in MAIN_CONVERSIONS]); ax.invert_yaxis()
    ax.set_xlabel("Final-20-generation adult N / tick-100 adult N"); ax.set_ylabel("Drive conversion")
    ax.legend(handles=[Line2D([], [], marker="o", mfc="none", ls="", color="#222222", label="Fixed dispersal"),
                       Line2D([], [], marker="x", ls="", color="#222222", label="Evolving dispersal"),
                       ],
              frameon=False, loc="lower center", bbox_to_anchor=(.5, 1.03), ncol=3, fontsize=11.5,
              handletextpad=.3, columnspacing=.65)
    panel_letter(ax, "C")

    # D: preserve the prespecified axes; styling matches setting-level panels.
    ax = axes[1, 1]
    for _, row in dstats.iterrows():
        ax.errorbar(row.fixed_nni_mean, row.extra_E_mean,
                    xerr=[[row.fixed_nni_mean-row.fixed_nni_ci_low], [row.fixed_nni_ci_high-row.fixed_nni_mean]],
                    yerr=[[row.extra_E_mean-row.extra_E_ci_low], [row.extra_E_ci_high-row.extra_E_mean]],
                    fmt="o", ms=5.0, mfc=VARIABLE, mec="white", mew=.7,
                    ecolor=VARIABLE, elinewidth=1.1, capsize=2.3)
        ax.annotate(f"{row.conversion:.2f}", (row.fixed_nni_mean, row.extra_E_mean),
                    xytext=(5, 5), textcoords="offset points", fontsize=11.5)
    ax.axhline(0, color="#777777", lw=.8, ls=(0, (3, 3)))
    ax.set_xlabel("Fixed dispersal: late adult normalized NNI")
    ax.set_ylabel("Extra dispersal change vs matched no-drive\n(percentage points)")
    panel_letter(ax, "D")

    for ax in axes.flat:
        sns.despine(ax=ax); ax.grid(False)
    fig.savefig(out_path, dpi=600, facecolor="white")
    plt.close(fig)


def write_chinese_report(data, overall, bstats, cstats, dstats, output: Path):
    branch_counts = (
        data[data["mode"].isin(MODES) & data["conversion"].isin(MAIN_CONVERSIONS)]
        .groupby(["mode", "conversion"])
        .size()
    )
    count_summary = "；".join(
        f"{mode} conversion={conv:.2f} n={int(branch_counts.get((mode, conv), 0))}"
        for conv in MAIN_CONVERSIONS
        for mode in MODES
    )
    nodrive_n = int((data["mode"] == "nodrive").sum())
    eliminated_without_late = int(
        (
            data["outcome"].eq("elimination")
            & data[["late_adult_dispersal", "relative_population_size", "late_normalized_nni"]]
            .isna()
            .any(axis=1)
        ).sum()
    )
    c_sig = int((cstats["p_holm_4"] < 0.05).sum())
    outcome_lines = []
    for _, row in overall.iterrows():
        outcome_lines.append(
            f"- conversion={row.conversion:.2f}：evolving {row.table_evolving}，fixed {row.table_fixed}；"
            f"配对三分类精确label-swap检验p={row.p_raw:.4g}，Holm校正p={row.p_holm_4:.4g}。"
        )
    b_lines = []
    for _, row in bstats.iterrows():
        label = "no-drive相对零变化" if pd.isna(row.conversion) else f"conversion={row.conversion:.2f}相对matched no-drive的额外变化"
        b_lines.append(
            f"- {label}：n={int(row.n)}，均值={row.mean_effect:.3f}个百分点，"
            f"展示值95% bootstrap CI [{row.display_ci_low:.3f}, {row.display_ci_high:.3f}]，"
            f"与匹配no-drive的双侧t检验p={row.p_raw:.4g}，Holm校正p={row.p_holm_family:.4g}。"
        )
    c_lines = []
    for _, row in cstats.iterrows():
        c_lines.append(
            f"- conversion={row.conversion:.2f}：配对n={int(row.paired_n)}，evolving−fixed={row.mean_evolving_minus_fixed:.4f}，"
            f"95% bootstrap CI [{row.ci_low:.4f}, {row.ci_high:.4f}]，"
            f"配对双侧t检验p={row.p_raw:.4g}，Holm校正p={row.p_holm_4:.4g}。"
        )
    text = f"""# Dispersal evolution主图：当前数据快照说明

## 数据范围

- 当前快照主图仅纳入conversion 0.75、0.85、0.95、0.99。
- 各分支运行数：{count_summary}；no-drive n={nodrive_n}。
- 独立重复和配对单位均为checkpoint origin seed；CSV内部branch seed不用于配对。
- fixed分支的dispersal固定值取同origin-seed evolving分支tick 100的all-live平均值；它不是所有重复共享的统一常数。
- tick 100为baseline，tick 101释放drive；时间单位为weeks。
- 成人定义为age>0。所有结局均使用各模拟自身最后20个有效记录代；adult dispersal按同代adult population size加权。
- 95% CI使用10,000次origin-seed bootstrap，随机种子{RNG_SEED}。

## 当前结果

### Panel a：outcome composition

计数顺序均为[elimination, long-term persistence, drive loss]。

{chr(10).join(outcome_lines)}

配对三分类整体比较共4项统一Holm校正；outcome-versus-rest的12项exact McNemar比较另见`panel_a_category_exact_mcnemar_tests.csv`并在该家族内Holm校正。

### Panel b：全部结局的dispersal evolution（按LTP与Non-LTP分层）

E = 100 × (末20代adult-population-size加权平均adult dispersal / tick100 adult dispersal − 1)。

{chr(10).join(b_lines)}

点和误差条总结各结局组的原始dispersal change及其bootstrap 95% CI；P值检验与匹配no-drive的差值。两者对应不同但相关的估计量。结局分层为事后描述，不能单独证明定向选择。

### Panel c：全部可分类结局的relative population size

{chr(10).join(c_lines)}

4项Holm校正后有{c_sig}项达到0.05；未达到阈值的比较不构成两组等效的证据。

### Panel d：fixed空间结构与额外dispersal变化

每个conversion仅显示一个组均值点及origin-seed bootstrap横纵轴95% CI；n=4个组均值不进行相关显著性检验。完整数值见`panel_d_group_summary.csv`。

## 图注草案

**Dispersal evolution and drive outcomes in spatial populations.** **a,** Outcome composition for evolving and fixed dispersal at each drive-conversion value. Bars show elimination, drive loss and long-term persistence (LTP). **b,** Relative change in adult dispersal for all endpoints. Each run uses its own final 20 recorded generations; adult dispersal is weighted by adult population size. Yellow, ochre and peach points denote LTP, elimination and drive loss. Ochre diamonds and intervals show the pooled non-LTP mean and 95% simulation bootstrap CI. Within each conversion and endpoint group, changes were compared with matched no-drive windows by two-sided paired t-tests, Holm-adjusted across all displayed tests. **c,** Final-20-generation adult population size relative to tick 100 for all matched classifiable branches; elimination is assigned a population endpoint of zero. **d,** Last-100-tick fixed-dispersal adult normalized NNI versus extra dispersal change in the matched evolving branch, restricted to LTP. Adult metrics use individuals with age>0. Tick 100 is the baseline and drive release occurred at tick 101. Each simulation is one independent replicate; panel-specific n and exact p values are provided in Source Data.

## 当前边界

- 四个conversion的evolving和fixed分支均已达到100次独立origin-seed运行，不作补值。
- {eliminated_without_late}个运行不足20个有效末段记录；这些指标保持缺失，不填0。
- 技术失败与其他排除项见`screening_exclusions.csv`；所有统计使用实际可用的独立origin seed。
"""
    output.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    runs_root = find_runs_root(args.input_root)
    rng = np.random.default_rng(RNG_SEED)
    data, exclusions = collect(runs_root)
    overall, category = paired_outcome_tables(data)
    prespecified_four = prespecified_four_outcome_tests(category)
    bstats, paired_b, cstats, paired_c, dstats = statistics(data, rng)
    data.to_csv(args.output_dir / "source_data_per_run.csv", index=False)
    source_analysis = data.copy()
    source_analysis["relative_population_size_raw"] = source_analysis["relative_population_size"]
    source_analysis.loc[source_analysis["outcome"].eq("elimination"), "relative_population_size"] = 0.0
    source_analysis.to_csv(args.output_dir / "source_data_per_run_analysis_endpoints.csv", index=False)
    exclusions.to_csv(args.output_dir / "screening_exclusions.csv", index=False)
    overall.to_csv(args.output_dir / "panel_a_overall_paired_exact_tests.csv", index=False)
    category.to_csv(args.output_dir / "panel_a_category_exact_mcnemar_tests.csv", index=False)
    prespecified_four.to_csv(args.output_dir / "panel_a_prespecified_four_exact_mcnemar_tests.csv", index=False)
    bstats.to_csv(args.output_dir / "panel_b_tests.csv", index=False)
    paired_b.to_csv(args.output_dir / "panel_b_paired_source.csv", index=False)
    cstats.to_csv(args.output_dir / "panel_c_tests.csv", index=False)
    paired_c.to_csv(args.output_dir / "panel_c_paired_source.csv", index=False)
    dstats.to_csv(args.output_dir / "panel_d_group_summary.csv", index=False)
    plot_figure(data, overall, bstats, paired_b, cstats, paired_c, dstats, args.output_dir / "dispersal_evolution_main_figure.png")
    write_chinese_report(data, overall, bstats, cstats, dstats, args.output_dir / "analysis_summary_CN.md")
    counts = data.groupby(["mode", "conversion"], dropna=False).size().rename("available_runs").reset_index()
    counts.to_csv(args.output_dir / "available_run_counts.csv", index=False)
    print(counts.to_string(index=False))
    print(f"Wrote outputs to {args.output_dir}")


if __name__ == "__main__":
    main()
