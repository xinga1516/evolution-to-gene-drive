from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


ROOT = Path(r"D:\champer实验室工作\文章figure1-8")
WEEKLY = (
    ROOT / "文章终稿数据" / "Figure6" / "retest_20rep_20260914_final"
    / "processed" / "weekly_metrics.csv"
)
OUT = ROOT / "single_panel_outputs" / "S4_recreated"
CANON_SRC = ROOT / "supplementary_final" / "source_data"
OUT.mkdir(parents=True, exist_ok=True)
CANON_SRC.mkdir(parents=True, exist_ok=True)

CONDITIONS = ["P70_L", "S70_L"]
LABELS = {"P70_L": "Panmictic", "S70_L": "Spatial"}
COLORS = {"P70_L": "#0072B2", "S70_L": "#D55E00"}
THRESHOLDS = (0.025, 0.05, 0.10)
BLOCKS = [(5000, 5249), (5250, 5499), (5500, 5749), (5750, 5999)]
MIDS = np.array([(lo + hi) / 2 for lo, hi in BLOCKS], dtype=float)

METRICS = [
    ("B", "virtual_haploid_load", "Virtual haploid load"),
    ("mutation_copies_per_individual", "copies_per_individual",
     "Mutation copies per individual"),
    ("N_total", "population_N", "Population size"),
    ("mean_Wload", "mean_genetic_viability", r"Mean genetic viability ($W_{\mathrm{load}}$)"),
]


def load_pre_release():
    usecols = [
        "condition_id", "load", "replicate", "tick", "release_tick",
        "B", "mutation_copies_per_individual", "N_total", "mean_Wload",
    ]
    data = pd.read_csv(WEEKLY, usecols=usecols, low_memory=False)
    data = data[
        data["load"].eq("present")
        & data["condition_id"].isin(CONDITIONS)
        & data["tick"].lt(data["release_tick"])
    ].copy()
    data["pre_release_generation"] = data["tick"].astype(int)
    return data


def build_blocks_and_diagnostics(data):
    block_rows = []
    for (condition, replicate), group in data.groupby(["condition_id", "replicate"]):
        for block_id, (lo, hi) in enumerate(BLOCKS, start=1):
            z = group[group["pre_release_generation"].between(lo, hi)]
            row = {
                "condition_id": condition,
                "model": LABELS[condition],
                "replicate": int(replicate),
                "block": block_id,
                "block_start": lo,
                "block_end": hi,
            }
            for raw, metric, _ in METRICS:
                row[metric] = pd.to_numeric(z[raw], errors="coerce").mean()
            block_rows.append(row)
    blocks = pd.DataFrame(block_rows)

    diagnostic_rows = []
    for condition in CONDITIONS:
        group = blocks[blocks["condition_id"].eq(condition)]
        n_independent = int(group["replicate"].nunique())
        for _, metric, metric_label in METRICS:
            means = (
                group.groupby("block")[metric].mean()
                .reindex([1, 2, 3, 4]).to_numpy(float)
            )
            slope, intercept = np.polyfit(MIDS, means, 1)
            fitted_5000 = intercept + slope * 5000
            fitted_5999 = intercept + slope * 5999
            m4 = means[3]
            r_trend = abs(fitted_5999 - fitted_5000) / abs(m4)
            r_last = abs(means[3] - means[2]) / abs(m4)
            row = {
                "diagnostic_id": f"{condition}_{metric}",
                "condition_id": condition,
                "model": LABELS[condition],
                "metric": metric,
                "metric_label": metric_label.replace(r" ($W_{\mathrm{load}}$)", " (W_load)"),
                "analysis_level": "replicate block means followed by across-replicate means",
                "window_start": 5000,
                "window_end": 5999,
                "block_length": 250,
                "n_blocks": 4,
                "n_independent_simulations": n_independent,
                "M1": means[0], "M2": means[1], "M3": means[2], "M4": means[3],
                "linear_slope_per_week": slope,
                "fitted_value_5000": fitted_5000,
                "fitted_value_5999": fitted_5999,
                "R_trend": r_trend,
                "R_last": r_last,
            }
            for epsilon in THRESHOLDS:
                suffix = str(epsilon).replace(".", "p")
                row[f"pass_epsilon_{suffix}"] = bool(
                    r_trend < epsilon and r_last < epsilon
                )
            diagnostic_rows.append(row)
    return blocks, pd.DataFrame(diagnostic_rows)


def draw_s4(data):
    plt.rcParams.update({
        "font.family": "Arial",
        "font.size": 11.5,
        "axes.labelsize": 12.5,
        "axes.titlesize": 12.5,
        "xtick.labelsize": 10.5,
        "ytick.labelsize": 10.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 1.0,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    })

    fig, axes = plt.subplots(2, 2, figsize=(10.8, 7.75))
    for ax, (raw, _, ylabel), letter in zip(axes.flat, METRICS, "abcd"):
        for condition in CONDITIONS:
            q = data[data["condition_id"].eq(condition)].copy()
            # The first ten population-size generations are known dirty data.
            if raw == "N_total":
                q = q[q["pre_release_generation"] > 10]
            summary = (
                q.groupby("pre_release_generation")[raw]
                .agg(mean="mean", q25=lambda z: z.quantile(0.25),
                     q75=lambda z: z.quantile(0.75))
                .reset_index()
            )
            x = summary["pre_release_generation"].to_numpy(float)
            ax.fill_between(x, summary["q25"].to_numpy(float),
                            summary["q75"].to_numpy(float),
                            color=COLORS[condition], alpha=0.13, linewidth=0)
            ax.plot(x, summary["mean"].to_numpy(float),
                    color=COLORS[condition], lw=1.45)

        ax.set_xlim(0, 6000)
        ax.set_xticks(np.arange(0, 6001, 1000))
        ax.set_xlabel("Pre-release generation")
        ax.set_ylabel(ylabel)
        # Restore the landscape plotting-rectangle ratio used by the original
        # S4 panels (width:height approximately 1.35:1).
        ax.set_box_aspect(0.74)
        ax.tick_params(direction="out", width=0.9, length=4)
        ax.text(-0.14, 1.035, letter, transform=ax.transAxes,
                fontsize=14, fontweight="bold", va="bottom")

    handles = [
        Line2D([0], [0], color=COLORS[c], lw=2.2, label=LABELS[c])
        for c in CONDITIONS
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.56, 0.91),
               ncol=2, frameon=False, fontsize=11.5, handlelength=2.3,
               columnspacing=2.4)
    fig.suptitle("Supplementary Fig. S4 | Pre-release convergence and population stability",
                 x=0.045, y=0.975, ha="left", fontsize=17.5, fontweight="bold")
    fig.subplots_adjust(left=0.10, right=0.985, bottom=0.095,
                        top=0.80, wspace=0.28, hspace=0.40)

    stem = OUT / "Supplementary_Figure_S4_recreated"
    fig.savefig(stem.with_suffix(".png"), dpi=600, facecolor="white")
    fig.savefig(stem.with_suffix(".svg"), facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)


def draw_table_s3(diagnostics):
    rows = []
    for _, r in diagnostics.iterrows():
        status = []
        for epsilon in THRESHOLDS:
            key = f"pass_epsilon_{str(epsilon).replace('.', 'p')}"
            status.append("PASS" if bool(r[key]) else "FAIL")
        rows.append({
            "Metric / model": f"{r['metric_label']} — {r['model']}",
            "Relative changes": (
                f"R_trend = {100*r['R_trend']:.2f}%; "
                f"R_last = {100*r['R_last']:.2f}%"
            ),
            "2.5% / 5% / 10%": " / ".join(status),
        })
    display = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(11.2, 6.4))
    ax.axis("off")
    fig.text(0.055, 0.94, "Supplemental Information", fontsize=18,
             fontweight="bold", family="Times New Roman")
    fig.text(0.055, 0.86,
             "Table S3. Relative operational-stability diagnostics before drive release",
             fontsize=14.2, fontweight="bold", family="Times New Roman")

    table = ax.table(
        cellText=display.values,
        colLabels=display.columns,
        cellLoc="left", colLoc="left",
        colWidths=[0.44, 0.32, 0.24],
        bbox=[0.035, 0.23, 0.93, 0.54],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10.9)
    table.scale(1, 1.55)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#555555")
        cell.set_linewidth(0.65)
        cell.set_facecolor("#F2F2F2" if row == 0 else "white")
        cell.PAD = 0.055
        cell.get_text().set_family("Times New Roman")
        if row == 0:
            cell.get_text().set_fontweight("bold")

    note = (
        "For each metric, M1–M4 are across-simulation means of replicate-level 250-week "
        "block means over weeks 5000–5999 (n=20 independent simulations per model). "
        "R_trend = |B-hat(5999) − B-hat(5000)|/M4 and R_last = |M4 − M3|/M4. "
        "PASS requires both quantities to be strictly below the stated practical-tolerance "
        "threshold. These are operational convergence diagnostics, not null-hypothesis tests."
    )
    fig.text(0.055, 0.145, note, fontsize=10.3, family="Times New Roman",
             va="top", wrap=True)

    stem = OUT / "Supplementary_Table_S3_relative_stability"
    fig.savefig(stem.with_suffix(".png"), dpi=600, facecolor="white")
    fig.savefig(stem.with_suffix(".svg"), facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)
    display.to_csv(stem.with_suffix(".csv"), index=False, encoding="utf-8-sig")


def main():
    data = load_pre_release()
    blocks, diagnostics = build_blocks_and_diagnostics(data)

    blocks.to_csv(OUT / "S4_pre_release_blocks_revised.csv", index=False)
    diagnostics.to_csv(OUT / "pre_release_diagnostics_relative.csv", index=False)
    # Update the canonical source-data tables used by S4/Table S3 only.
    blocks.to_csv(CANON_SRC / "S4_pre_release_blocks.csv", index=False)
    diagnostics.to_csv(CANON_SRC / "pre_release_diagnostics.csv", index=False)

    draw_s4(data)
    draw_table_s3(diagnostics)


if __name__ == "__main__":
    main()
