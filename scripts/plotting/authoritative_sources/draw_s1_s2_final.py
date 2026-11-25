from __future__ import annotations

import io
import itertools
import math
import re
import zipfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[2]
FINAL = ROOT / "文章终稿数据"
SUP = FINAL / "Supplementary"
S1 = SUP / "Figure S1"
S2 = SUP / "Figure S2"
SEED = 20260915
BOOT = 10_000
BLUE = "#0072B2"
ORANGE = "#E69F00"
GRAY = "#777777"
SD_COLORS = ["#56B4E9", "#009E73", "#E69F00", "#CC79A7"]


def style() -> None:
    plt.rcParams.update({
        "font.family": "Arial", "font.size": 9.5, "axes.labelsize": 10,
        "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
        "legend.fontsize": 8, "axes.linewidth": 0.8,
        "pdf.fonttype": 42, "ps.fonttype": 42,
    })


def save(fig: plt.Figure, stem: Path) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".png"), dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight", facecolor="white")
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def parse_member(zf: zipfile.ZipFile, member: str, model: str, h: float, treatment: str) -> pd.DataFrame:
    name = Path(member).name
    match = re.search(r"_(\d+)\.out$", name)
    rep = int(match.group(1)) if match else -1
    release = 21
    attr = math.nan
    rows: list[dict] = []
    with zf.open(member) as raw:
        for bline in raw:
            line = bline.decode("utf-8", "ignore").strip()
            if line.startswith("RELEASE_TICK:"):
                release = int(float(line.split(":", 1)[1]))
            elif line.startswith("average attribute:"):
                attr = float(line.split(":", 1)[1])
            elif line.startswith("GEN:"):
                parts = line.split()
                if len(parts) < 4:
                    continue
                gen = int(float(parts[1]))
                week = (gen - release) / 3.167
                if week < 0:
                    continue
                drive = np.nan if parts[3] == "NAN" else float(parts[3])
                rows.append({"simulation_id": name, "replicate": rep, "population_model": model,
                             "conversion_label": "0.70" if h == .70 else "Emp",
                             "conversion_female": h, "conversion_male": .70 if h == .70 else .96,
                             "treatment": treatment, "week_after_release": week,
                             "drive_allele_frequency": drive,
                             "population_mean_somatic_fitness_attribute": attr})
    return pd.DataFrame(rows)


def build_s1_source() -> pd.DataFrame:
    cached = S1 / "data" / "Figure_S1_simulation_week_source.csv.gz"
    if cached.exists():
        out = pd.read_csv(cached, dtype={"conversion_label": str})
        out["conversion_label"] = out["conversion_label"].replace({"0.7": "0.70", "0.70": "0.70"})
        out = out.drop_duplicates(
            ["replicate", "population_model", "conversion_label", "treatment", "week_after_release"]
        )
        out.to_csv(cached, index=False, compression="gzip")
        coverage = out.groupby(["population_model", "conversion_label", "treatment"], as_index=False).agg(
            n_simulations=("simulation_id", "nunique"), min_week=("week_after_release", "min"), max_week=("week_after_release", "max"))
        coverage.to_csv(S1 / "data" / "Figure_S1_coverage.csv", index=False)
        return out
    z1 = ROOT / "_cleanup_archive" / "figure1_6_deduplicated_data_20260907" / "data_Figure_4.zip"
    z2 = ROOT / "_cleanup_archive" / "figure1_6_deduplicated_data_20260907" / "data_incoming_figure4_5_groups_20260827.zip"
    specs = [
        (z1, "fig4_pan070_sf_control_topup", "Panmictic", .70, "Neutral mutations"),
        (z1, "fig4_pan070_sf_functional_topup", "Panmictic", .70, "Variable mutations"),
        (z1, "fig4_pan099_sf_control_defaultfix", "Panmictic", .99, "Neutral mutations"),
        (z1, "fig4_pan099_sf_functional_defaultfix", "Panmictic", .99, "Variable mutations"),
        (z2, "fig4_spt070_sf_control_topup", "Spatial", .70, "Neutral mutations"),
        (z2, "fig4_spt070_sf_functional_topup", "Spatial", .70, "Variable mutations"),
        (z1, "fig4_spa099_sf_control_defaultfix", "Spatial", .99, "Neutral mutations"),
        (z1, "fig4_spa099_sf_functional_defaultfix", "Spatial", .99, "Variable mutations"),
    ]
    frames = []
    for zp, token, model, h, tr in specs:
        with zipfile.ZipFile(zp) as zf:
            members = [m for m in zf.namelist() if token in m and m.endswith(".out")]
            for member in members:
                d = parse_member(zf, member, model, h, tr)
                if not d.empty:
                    frames.append(d)
    out = pd.concat(frames, ignore_index=True)
    out = out.drop_duplicates(["replicate", "population_model", "conversion_label", "treatment", "week_after_release"])
    (S1 / "data").mkdir(parents=True, exist_ok=True)
    out.to_csv(S1 / "data" / "Figure_S1_simulation_week_source.csv.gz", index=False, compression="gzip")
    coverage = out.groupby(["population_model", "conversion_label", "treatment"], as_index=False).agg(
        n_simulations=("simulation_id", "nunique"), min_week=("week_after_release", "min"), max_week=("week_after_release", "max"))
    coverage.to_csv(S1 / "data" / "Figure_S1_coverage.csv", index=False)
    return out


def plot_s1(d: pd.DataFrame) -> None:
    regimes = [("Panmictic", "0.70"), ("Panmictic", "Emp"), ("Spatial", "0.70"), ("Spatial", "Emp")]
    titles = ["Pan–0.70", "Pan–Emp", "Spa–0.70", "Spa–Emp"]
    for idx, ((model, conv), title) in enumerate(zip(regimes, titles), 1):
        sub = d[(d.population_model == model) & (d.conversion_label == conv)]
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(3.25, 3.25), sharex=True, dpi=300)
        for tr, ls in [("Neutral mutations", "--"), ("Variable mutations", "-")]:
            g = sub[sub.treatment == tr]
            for ax, col, color in [(ax1, "drive_allele_frequency", BLUE), (ax2, "population_mean_somatic_fitness_attribute", ORANGE)]:
                s = g.groupby("week_after_release")[col].agg(median="median", q25=lambda x: x.quantile(.25), q75=lambda x: x.quantile(.75)).reset_index()
                for stat in ["median", "q25", "q75"]:
                    s[stat] = s[stat].rolling(10, center=True, min_periods=1).mean()
                ax.fill_between(s.week_after_release, s.q25, s.q75, color=color, alpha=.16, linewidth=0)
                ax.plot(s.week_after_release, s["median"], color=color, ls=ls, lw=1.1, label=tr)
        ax1.set_ylabel("Drive allele\nfrequency")
        ax2.set_ylabel("Mean somatic-fitness\nattribute")
        ax2.set_xlabel("Weeks after release")
        ax1.set_ylim(0, 1)
        ax2.axhline(.5, color="#999999", lw=.7, ls=":")
        ax1.text(.02, .93, title, transform=ax1.transAxes, va="top", fontweight="bold")
        ax1.legend(frameon=False, loc="lower right", handlelength=2.2)
        for ax in (ax1, ax2):
            ax.spines[["top", "right"]].set_visible(False)
        fig.subplots_adjust(left=.22, right=.97, bottom=.16, top=.96, hspace=.10)
        save(fig, S1 / "panels" / f"Figure S1 Panel {chr(64+idx)}")


def bootstrap_mean(x: np.ndarray, rng: np.random.Generator) -> tuple[float, float, float]:
    x = x[np.isfinite(x)]
    draws = rng.choice(x, size=(BOOT, len(x)), replace=True).mean(axis=1)
    return float(x.mean()), float(np.quantile(draws, .025)), float(np.quantile(draws, .975))


def exact_spearman(x: np.ndarray, y: np.ndarray) -> tuple[float, float, int]:
    obs = float(spearmanr(x, y).statistic)
    vals = list(itertools.permutations(y.tolist()))
    extreme = sum(abs(float(spearmanr(x, p).statistic)) >= abs(obs) - 1e-12 for p in vals)
    return obs, extreme / len(vals), len(vals)


def build_s2() -> tuple[pd.DataFrame, pd.DataFrame]:
    src = pd.read_csv(FINAL / "Figure5" / "processed_source_final" / "Figure5_LTP_simulation_level_source.csv")
    src["delta_z"] = src.final_attribute_mean_last10 - src.pre_release_attribute_mean_last10
    src["normalized_response"] = src.delta_z.abs() / src.realised_initial_sd_last10_prerelease
    src["m_rank"] = src.m.map({50: 1, 100: 2, 200: 3, 400: 4, 800: 5})
    src["b_rank_within_m"] = src.groupby(["trait", "m"])["b"].rank(method="dense", ascending=False).astype(int)
    src["sd_stratum"] = src["b_rank_within_m"]
    lower = src[src.sd_stratum > 1].copy()
    rng = np.random.default_rng(SEED)
    rows, tests = [], []
    for keys, g in lower.groupby(["trait", "sd_stratum", "m", "b"], sort=True):
        mean, lo, hi = bootstrap_mean(g.normalized_response.to_numpy(float), rng)
        rows.append(dict(trait=keys[0], sd_stratum=int(keys[1]), m=int(keys[2]), b=float(keys[3]),
                         n_simulations=len(g), realised_initial_sd_mean=g.realised_initial_sd_last10_prerelease.mean(),
                         normalized_response_mean=mean, ci95_lo=lo, ci95_hi=hi))
    summary = pd.DataFrame(rows)
    for (trait, stratum), g in summary.groupby(["trait", "sd_stratum"]):
        if len(g) < 2:
            tests.append(dict(trait=trait, sd_stratum=stratum, n_settings=len(g), rho=np.nan, raw_p_value=np.nan,
                              total_permutations=np.nan, status="not estimable: one setting"))
        else:
            rho, p, total = exact_spearman(g.m_rank.to_numpy() if "m_rank" in g else g.m.rank().to_numpy(), g.normalized_response_mean.to_numpy())
            tests.append(dict(trait=trait, sd_stratum=stratum, n_settings=len(g), rho=rho, raw_p_value=p,
                              total_permutations=total, status="exact two-sided Spearman permutation"))
    tests = pd.DataFrame(tests)
    (S2 / "data").mkdir(parents=True, exist_ok=True)
    src.to_csv(S2 / "data" / "Figure_S2_simulation_level_source.csv", index=False)
    summary.to_csv(S2 / "data" / "Figure_S2_setting_summary.csv", index=False)
    tests.to_csv(S2 / "data" / "Figure_S2_exact_spearman_tests.csv", index=False)
    return summary, tests


def plot_s2(summary: pd.DataFrame) -> None:
    names = {"dc": "Conversion modifier", "er": "Embryo-resistance modifier", "sf": "Somatic-fitness modifier"}
    for i, trait in enumerate(["dc", "er", "sf"], 1):
        sub = summary[summary.trait == trait]
        fig, ax = plt.subplots(figsize=(3.55, 3.25), dpi=300)
        for j, stratum in enumerate(sorted(sub.sd_stratum.unique())):
            g = sub[sub.sd_stratum == stratum].sort_values("m")
            base_x = g.m.map({50: 0, 100: 1, 200: 2, 400: 3, 800: 4}).to_numpy(float)
            x = base_x + (j - 1.5) * .035
            ax.errorbar(x, g.normalized_response_mean,
                        yerr=[g.normalized_response_mean-g.ci95_lo, g.ci95_hi-g.normalized_response_mean],
                        color=SD_COLORS[j], marker="o", ms=4, lw=1, capsize=2,
                        label=f"Lower SD {int(stratum-1)}")
            for xx, (_, r) in zip(x, g.iterrows()):
                ax.annotate(f"b={r.b:g}", (xx, r.normalized_response_mean),
                            xytext=(3, -8), textcoords="offset points", ha="left", va="top",
                            fontsize=6.0, rotation=35)
        ax.set_xlim(-.45, 4.45)
        ax.set_xticks(range(5), ["m=50", "m=100", "m=200", "m=400", "m=800"], rotation=25)
        ax.set_xlabel("Genetic-architecture gradient")
        ax.set_ylabel(r"Normalized response magnitude, $|\Delta z|/SD_{initial}$")
        ax.text(.02, .98, names[trait], transform=ax.transAxes, va="top", fontweight="bold")
        ax.legend(frameon=False, loc="best", fontsize=7.0)
        ax.spines[["top", "right"]].set_visible(False)
        fig.subplots_adjust(left=.23, right=.97, bottom=.22, top=.97)
        save(fig, S2 / "panels" / f"Figure S2 Panel {chr(64+i)}")


def write_docs() -> None:
    (S1 / "statistical_methods.md").write_text("""# Supplementary Figure S1 methods\n\nEach independent simulation is one replicate. The plotted variables are the directly recorded drive allele frequency and population mean somatic-fitness modifier attribute. Within each regime, treatment and recorded week, the line is the median and the ribbon is Q25–Q75 across simulations still contributing a record; displayed trajectories use a centered 10-generation moving average for visual smoothing. Trajectories stop when records stop; no values are extrapolated after termination. The figure is descriptive and contains no week-by-week hypothesis tests. Emp denotes the empirically based conversion parameterization (female/male homing-phase cut rates 0.99/0.96).\n""", encoding="utf-8")
    (S1 / "results_summary.md").write_text("""# Supplementary Figure S1 summary\n\nFour regimes are shown: Pan–0.70, Pan–Emp, Spa–0.70 and Spa–Emp. This formal first-version analysis uses drive allele frequency, not observed heterozygote frequency. Solid lines denote Variable mutations and dashed lines denote Neutral mutations.\n""", encoding="utf-8")
    (S2 / "statistical_methods.md").write_text("""# Supplementary Figure S2 methods\n\nThe final design contains 15 parameter settings per modifier class in a prespecified triangular 5+4+3+2+1 grid, with 100 independent long-term-persistent simulations per setting. The highest-SD diagonal is reserved for Figure 5. S2 displays the remaining four lower-SD diagonals, containing 4, 3, 2 and 1 settings. Points are setting-level arithmetic means of |Δz|/SD_initial; error bars are percentile-bootstrap 95% confidence intervals from 10,000 simulation-level resamples within settings (seed 20260915). Exact two-sided Spearman permutation trends are reported within each modifier × lower-SD stratum when at least two architecture settings exist. A one-setting stratum is reported as not estimable, not ns.\n""", encoding="utf-8")
    (S2 / "results_summary.md").write_text("""# Supplementary Figure S2 summary\n\nS2 uses the complete available 15-setting triangular design for each modifier class. It does not imply a balanced 5×5 factorial design and does not label structurally absent cells as missing data. Exact trend-test results are stored in `data/Figure_S2_exact_spearman_tests.csv`.\n""", encoding="utf-8")


def main() -> None:
    style()
    s1 = build_s1_source()
    plot_s1(s1)
    s2, _ = build_s2()
    plot_s2(s2)
    write_docs()


if __name__ == "__main__":
    main()
