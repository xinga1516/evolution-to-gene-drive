#!/usr/bin/env python3
"""Recompute the final inferential statistics from canonical Source Data.

The script is intentionally deterministic.  Every Monte-Carlo permutation
test has a declared seed and uses the plus-one correction.  Exact tests are
enumerated when the state space is small enough.  Outputs are a common long
table so the displayed figure statistics and Supplementary Table S2 have one
machine-readable source of truth.
"""

from __future__ import annotations

import itertools
import hashlib
import json
import math
import platform
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import fisher_exact, rankdata, spearmanr, ttest_rel


REPO = Path(__file__).resolve().parents[1]
FILES = REPO / "data" / "source_data" / "files"
OUT = REPO / "results" / "statistics"
N_PERM = 10_000
N_PERM_F6 = 200_000

STANDARD_COLUMNS = [
    "record_id", "publication_item", "panel", "test_id", "family_id", "comparison",
    "estimand", "test", "independent_unit", "n_group1", "n_group2",
    "n_total", "estimate", "statistic", "p_raw", "p_adjusted",
    "adjustment", "permutations_or_enumerations", "extreme_permutations", "seed",
    "df", "ci_level", "ci_low", "ci_high", "status", "notes", "source_file",
    "source_sha256", "source_file_2", "source_sha256_2", "analysis_script", "software",
]


def significance(p: float | None) -> str:
    if p is None or not np.isfinite(p):
        return "NE"
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


def holm(values: list[float]) -> list[float]:
    """Holm adjusted P values, preserving input order and NaNs."""
    out = [np.nan] * len(values)
    valid = [(i, float(p)) for i, p in enumerate(values) if np.isfinite(p)]
    valid.sort(key=lambda z: z[1])
    running = 0.0
    m = len(valid)
    for rank, (index, p) in enumerate(valid):
        running = max(running, min(1.0, (m - rank) * p))
        out[index] = running
    return out


def perm_mean(a, b, seed: int, permutations: int = N_PERM):
    a = np.asarray(pd.Series(a).dropna(), float)
    b = np.asarray(pd.Series(b).dropna(), float)
    observed = float(a.mean() - b.mean())
    pooled = np.concatenate([a, b])
    rng = np.random.default_rng(seed)
    extreme = 0
    for _ in range(permutations):
        shuffled = rng.permutation(pooled)
        delta = shuffled[: len(a)].mean() - shuffled[len(a) :].mean()
        extreme += abs(delta) >= abs(observed) - 1e-15
    return observed, (extreme + 1) / (permutations + 1), extreme


def exact_spearman(x, y):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    observed = float(spearmanr(x, y).statistic)
    extreme = 0
    total = 0
    for permuted in itertools.permutations(y.tolist()):
        rho = float(spearmanr(x, permuted).statistic)
        extreme += abs(rho) >= abs(observed) - 1e-12
        total += 1
    return observed, extreme / total, extreme, total


def oneway_f(groups: list[np.ndarray]) -> float:
    groups = [np.asarray(x, float) for x in groups]
    grand = np.concatenate(groups).mean()
    ss_between = sum(len(x) * (x.mean() - grand) ** 2 for x in groups)
    ss_within = sum(((x - x.mean()) ** 2).sum() for x in groups)
    return float((ss_between / (len(groups) - 1)) / (ss_within / (sum(map(len, groups)) - len(groups))))


def perm_oneway(groups: list[np.ndarray], seed: int, permutations: int = N_PERM):
    groups = [np.asarray(pd.Series(x).dropna(), float) for x in groups]
    observed = oneway_f(groups)
    sizes = [len(x) for x in groups]
    pooled = np.concatenate(groups)
    rng = np.random.default_rng(seed)
    extreme = 0
    for _ in range(permutations):
        shuffled = rng.permutation(pooled)
        split = np.split(shuffled, np.cumsum(sizes)[:-1])
        extreme += oneway_f(split) >= observed - 1e-12
    return observed, (extreme + 1) / (permutations + 1), extreme


def fisher_freeman_halton(table: np.ndarray):
    """Two-sided exact test for a 2 x k table with fixed margins."""
    table = np.asarray(table, dtype=int)
    if table.shape[0] != 2:
        raise ValueError("only 2 x k tables are supported")
    cols = table.sum(axis=0)
    row0 = int(table[0].sum())
    total = int(cols.sum())
    denom = math.comb(total, row0)

    def probability(first_row):
        numerator = math.prod(math.comb(int(c), int(x)) for c, x in zip(cols, first_row))
        return numerator / denom

    observed_p = probability(table[0])
    exact_p = 0.0
    enumerations = 0

    def walk(j: int, remaining: int, prefix: list[int]):
        nonlocal exact_p, enumerations
        if j == len(cols) - 1:
            if 0 <= remaining <= cols[j]:
                allocation = [*prefix, remaining]
                p = probability(allocation)
                enumerations += 1
                if p <= observed_p + 1e-15:
                    exact_p += p
            return
        lower = max(0, remaining - int(cols[j + 1 :].sum()))
        upper = min(int(cols[j]), remaining)
        for x in range(lower, upper + 1):
            walk(j + 1, remaining - x, [*prefix, x])

    walk(0, row0, [])
    return min(1.0, exact_p), enumerations


def row(**kwargs) -> dict:
    result = {column: np.nan for column in STANDARD_COLUMNS}
    result.update(kwargs)
    return result


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def continuous_modifier_tests(item: str, source: Path, metric: str, *, seed_base: int, panel: str):
    data = pd.read_csv(source)
    rows = []
    for index, ((model, h), group) in enumerate(data.groupby(["model", "h"], sort=True)):
        neutral = group[group["treatment"].eq("Neutral control")][metric].dropna()
        variable = group[group["treatment"].eq("Functional modifier")][metric].dropna()
        seed = seed_base + index
        estimate, p, extreme = perm_mean(variable, neutral, seed)
        rows.append(row(
            publication_item=item, panel=panel,
            test_id=f"{item.replace(' ', '')}{panel}_{model}_{h}_{metric}",
            family_id=f"{item.replace(' ', '')}{panel}_within_condition",
            comparison=f"{model} {h:g}: variable mutations vs neutral mutations",
            estimand="mean(variable) - mean(neutral)",
            test="two-sided independent permutation test",
            independent_unit="simulation", n_group1=len(variable), n_group2=len(neutral),
            n_total=len(variable) + len(neutral), estimate=estimate, statistic=estimate,
            p_raw=p, p_adjusted=p, adjustment="none; four prespecified condition contrasts",
            permutations_or_enumerations=N_PERM, extreme_permutations=extreme, seed=seed, status="tested",
            notes="Monte-Carlo plus-one P value; final 20 records",
            source_file=source.relative_to(REPO).as_posix(),
        ))
    adjusted = holm([x["p_raw"] for x in rows])
    for result, p_adj in zip(rows, adjusted):
        result["p_adjusted"] = p_adj
        result["adjustment"] = "Holm across four prespecified condition contrasts within panel"
    return rows


def outcome_global_tests(item: str, source: Path, *, panel: str):
    data = pd.read_csv(source)
    if "model_std" in data:
        data["model"] = data["model_std"]
        data["h"] = data["drive_conversion"]
    elif "conversion" in data:
        data = data.rename(columns={"conversion": "h"})
    if "outcome" not in data:
        data["outcome"] = np.select(
            [data["elimination"].astype(bool), data["drive_loss"].astype(bool)],
            ["Elimination", "Drive loss"],
            default="Long-term persistence",
        )
    rows = []
    for (model, h), group in data.groupby(["model", "h"], sort=True):
        categories = ["Elimination", "Drive loss", "Long-term persistence"]
        table = []
        ns = []
        for treatment in ["Functional modifier", "Neutral control"]:
            outcomes = group[group["treatment"].eq(treatment)]["outcome"]
            ns.append(len(outcomes))
            normalized = outcomes.astype(str).str.lower().str.replace("_", " ")
            table.append([
                int(normalized.eq(category.lower()).sum()) for category in categories
            ])
        table = np.asarray(table)
        # Empty drive-loss columns carry no information and are removed.
        table = table[:, table.sum(axis=0) > 0]
        p, enumerations = fisher_freeman_halton(table)
        rows.append(row(
            publication_item=item, panel=panel,
            test_id=f"{item.replace(' ', '')}{panel}_{model}_{h}_outcome",
            family_id=f"{item.replace(' ', '')}{panel}_outcomes",
            comparison=f"{model} {h:g}: variable mutations vs neutral mutations",
            estimand="terminal outcome distribution",
            test="two-sided Fisher-Freeman-Halton exact test",
            independent_unit="simulation", n_group1=ns[0], n_group2=ns[1], n_total=sum(ns),
            estimate=np.nan, statistic=np.nan, p_raw=p,
            permutations_or_enumerations=enumerations, seed=np.nan, status="tested",
            notes=f"fixed-margin exact test; table={table.tolist()}",
            source_file=source.relative_to(REPO).as_posix(),
        ))
    adjusted = holm([x["p_raw"] for x in rows])
    for result, p_adj in zip(rows, adjusted):
        result["p_adjusted"] = p_adj
        result["adjustment"] = f"Holm across {len(rows)} prespecified condition contrasts"
    return rows


def panel_e_test(item: str, source: Path, trait_label: str):
    data = pd.read_csv(source)
    summary = data.groupby(["setting", "cohort"], sort=True).agg(
        n=("replicate", "size"),
        mean_nni=("final20_nni", "mean"),
        mean_attribute=("final20_attribute_weighted", "mean"),
    ).reset_index()
    neutral = summary[summary.cohort.eq("Neutral mutations")].set_index("setting")
    variable = summary[summary.cohort.eq("Variable mutations")].set_index("setting")
    settings = sorted(set(neutral.index) & set(variable.index))
    x = neutral.loc[settings, "mean_nni"].to_numpy()
    y = variable.loc[settings, "mean_attribute"].to_numpy()
    rho, p, extreme, total = exact_spearman(x, y)
    panel = "E"
    result = row(
        publication_item=item, panel=panel, test_id=f"{item.replace(' ', '')}E_exact_spearman",
        family_id=f"{item.replace(' ', '')}E_association",
        comparison=f"setting-level neutral NNI vs variable {trait_label}",
        estimand="Spearman rank correlation", test="two-sided exact Spearman permutation",
        independent_unit="modifier setting", n_group1=len(settings), n_group2=np.nan,
        n_total=len(settings), estimate=rho, statistic=rho, p_raw=p, p_adjusted=p,
        adjustment="none; one prespecified association", permutations_or_enumerations=total,
        extreme_permutations=extreme, seed=np.nan, status="tested",
        notes=("Final-20-record setting means. Observed per-cell simulation n: " +
               "; ".join(f"{s:g}: neutral {int(neutral.loc[s,'n'])}, variable {int(variable.loc[s,'n'])}" for s in settings)),
        source_file=source.relative_to(REPO).as_posix(),
    )
    setting = pd.DataFrame({
        "setting": settings,
        "neutral_mean_final20_nni": x,
        f"variable_mean_final20_{trait_label.replace(' ', '_')}": y,
        "n_neutral": [int(neutral.loc[s, "n"]) for s in settings],
        "n_variable": [int(variable.loc[s, "n"]) for s in settings],
    })
    return result, setting


def figure3_outcomes():
    data = pd.read_csv(FILES / "Figure3/final20_replicates.csv")
    rows = []
    for model, h in sorted(data[["model", "h"]].drop_duplicates().itertuples(index=False, name=None)):
        group = data[data.model.eq(model) & data.h.eq(h)]
        neutral = group[group.treatment.eq("Neutral control")].outcome.str.lower().eq("elimination")
        variable = group[group.treatment.eq("Functional modifier")].outcome.str.lower().eq("elimination")
        table = [[int(variable.sum()), int((~variable).sum())], [int(neutral.sum()), int((~neutral).sum())]]
        odds, p = fisher_exact(table, alternative="two-sided")
        rows.append(row(
            publication_item="Figure 3", panel="A", test_id=f"F3A_{model}_{h}_outcome",
            family_id="F3A_outcomes", comparison=f"{model} {h:g}: variable vs neutral mutations",
            estimand="elimination odds ratio", test="two-sided Fisher exact test",
            independent_unit="simulation", n_group1=len(variable), n_group2=len(neutral),
            n_total=len(variable) + len(neutral), estimate=odds, statistic=odds, p_raw=p,
            permutations_or_enumerations=np.nan, seed=np.nan, status="tested",
            notes=f"2x2 table={table}", source_file="data/source_data/files/Figure3/final20_replicates.csv",
        ))
    adjusted = holm([x["p_raw"] for x in rows])
    for result, p_adj in zip(rows, adjusted):
        result["p_adjusted"] = p_adj
        result["adjustment"] = "Holm across four prespecified condition contrasts"
    return rows


class HC3Result:
    def __init__(self, y: pd.Series, design: pd.DataFrame):
        self.names = list(design.columns)
        x = design.to_numpy(float)
        y = np.asarray(y, float)
        xtx_inv = np.linalg.inv(x.T @ x)
        beta = xtx_inv @ x.T @ y
        fitted = x @ beta
        residual = y - fitted
        leverage = np.einsum("ij,jk,ik->i", x, xtx_inv, x)
        scaled = residual / (1 - leverage)
        meat = x.T @ ((scaled[:, None] ** 2) * x)
        covariance = xtx_inv @ meat @ xtx_inv
        se = np.sqrt(np.diag(covariance))
        p = 2 * stats.norm.sf(np.abs(beta / se))
        self.params = pd.Series(beta, index=self.names)
        self.covariance = covariance
        self.bse = pd.Series(se, index=self.names)
        self.pvalues = pd.Series(p, index=self.names)
        self.fitted = fitted
        self.residual = residual

    def combination(self, weights):
        weights = np.asarray(weights, float)
        beta = self.params.to_numpy(float)
        estimate = float(weights @ beta)
        se = float(np.sqrt(weights @ self.covariance @ weights))
        p = float(2 * stats.norm.sf(abs(estimate / se)))
        return estimate, estimate - 1.96 * se, estimate + 1.96 * se, p

    def joint_wald(self, restrictions):
        r = np.asarray(restrictions, float)
        q = r @ self.params.to_numpy(float)
        middle = r @ self.covariance @ r.T
        statistic = float(q.T @ np.linalg.inv(middle) @ q)
        df = int(r.shape[0])
        p = max(float(stats.chi2.sf(statistic, df)), 1e-300)
        return statistic, df, p


def _f4_design(data: pd.DataFrame) -> pd.DataFrame:
    path = data.Path.eq("fixed_b").astype(float)
    return pd.DataFrame({
        "const": 1.0,
        "SD_001": data.SD_001,
        "Path_fixed_b": path,
        "SD_001_x_Path": data.SD_001 * path,
    })


def figure4_tests():
    raw = pd.read_csv(FILES / "Figure4/simulation_level_source.csv")
    metadata = pd.read_csv(FILES / "Figure_S2/simulation_level_source.csv")[[
        "group_id", "trait", "b", "m"
    ]].drop_duplicates("group_id")
    raw = raw.merge(metadata, on="group_id", validate="many_to_one")
    raw = raw[raw.is_ltp.astype(bool)].copy()
    raw = raw.rename(columns={
        "realised_initial_sd_last10_prerelease": "realized_sd",
        "final_attribute_mean_last10": "endpoint",
    })
    panel = {"dc": "A", "er": "B", "sf": "C"}
    b_min = {"dc": 0.0048, "er": 0.0140, "sf": 0.0113}
    rows, summaries, coefficients, contrasts, sensitivities, diagnostics = [], [], [], [], [], []
    primary = []
    for trait in ["dc", "er", "sf"]:
        group = raw[raw.trait.eq(trait)].copy()
        fixed_m = group[group.m.eq(50) & ~np.isclose(group.b, b_min[trait])].copy()
        fixed_m["Path"] = "fixed_m"
        fixed_b = group[np.isclose(group.b, b_min[trait]) & ~group.m.eq(50)].copy()
        fixed_b["Path"] = "fixed_b"
        full = pd.concat([fixed_m, fixed_b], ignore_index=True).dropna(subset=["realized_sd", "endpoint"])
        ranges = full.groupby("Path").realized_sd.agg(["min", "max"])
        low = float(ranges["min"].max())
        high = float(ranges["max"].min())
        common = full[full.realized_sd.between(low, high)].copy()
        reference = float(common.realized_sd.median())
        for frame in (full, common):
            frame["SD_001"] = (frame.realized_sd - reference) / 0.01
        model = HC3Result(common.endpoint, _f4_design(common))
        fixed_m_slope = model.combination([0, 1, 0, 0])
        fixed_b_slope = model.combination([0, 1, 0, 1])
        delta_slope = model.combination([0, 0, 0, 1])
        offset = model.combination([0, 0, 1, 0])
        sd_wald = model.joint_wald([[0, 1, 0, 0], [0, 0, 0, 1]])
        architecture_wald = model.joint_wald([[0, 0, 1, 0], [0, 0, 0, 1]])
        primary.append((trait, sd_wald[2], architecture_wald[2], delta_slope[3]))
        quantile_rows = []
        for label, value in zip(["low", "mid", "high"], np.quantile(common.realized_sd, [.25, .5, .75])):
            z = (value - reference) / .01
            result = model.combination([0, 0, 1, z])
            quantile_rows.append((label, value, *result))
        quantile_adjusted = holm([x[5] for x in quantile_rows])
        for values, p_adj in zip(quantile_rows, quantile_adjusted):
            label, value, estimate, ci_low, ci_high, p = values
            contrasts.append({
                "trait": trait, "quantile": label, "realized_sd": value,
                "fixed_b_minus_fixed_m": estimate, "CI_low": ci_low, "CI_high": ci_high,
                "p_raw": p, "p_Holm": p_adj,
            })
        for name, result in [
            ("fixed_m_slope_per_0.01", fixed_m_slope),
            ("fixed_b_slope_per_0.01", fixed_b_slope),
            ("fixed_b_minus_fixed_m_slope", delta_slope),
            ("path_offset_reference_SD", offset),
        ]:
            coefficients.append({
                "trait": trait, "term": name, "estimate": result[0],
                "CI_low": result[1], "CI_high": result[2], "p_value": result[3],
            })
        for term in model.names:
            estimate = float(model.params[term])
            se = float(model.bse[term])
            coefficients.append({
                "trait": trait, "term": f"model_{term}", "estimate": estimate,
                "CI_low": estimate - 1.96 * se, "CI_high": estimate + 1.96 * se,
                "p_value": float(model.pvalues[term]),
            })
        full_model = HC3Result(full.endpoint, _f4_design(full))
        full_sd = full_model.joint_wald([[0, 1, 0, 0], [0, 0, 0, 1]])
        full_arch = full_model.joint_wald([[0, 0, 1, 0], [0, 0, 0, 1]])
        sensitivities.append({
            "trait": trait, "n": len(full), "slope_fixed_m": float(full_model.params.SD_001),
            "slope_fixed_b": float(full_model.params.SD_001 + full_model.params.SD_001_x_Path),
            "delta_slope": float(full_model.params.SD_001_x_Path),
            "interaction_p": float(full_model.pvalues.SD_001_x_Path),
            "realized_SD_Wald_stat": full_sd[0], "realized_SD_p": full_sd[2],
            "architecture_Wald_stat": full_arch[0], "architecture_p": full_arch[2],
        })
        counts = common.groupby("Path").size()
        diagnostics.append({
            "trait": trait, "model_formula": "endpoint ~ SD_001 * Path", "covariance": "HC3",
            "n": len(common), "design_rank": int(np.linalg.matrix_rank(_f4_design(common).to_numpy(float))),
            "condition_number": float(np.linalg.cond(_f4_design(common).to_numpy(float))),
            "common_support_min": low, "common_support_max": high, "SD_reference_median": reference,
        })
        summaries.append({
            "trait": trait, "n_fixed_m_common": int(counts.get("fixed_m", 0)),
            "n_fixed_b_common": int(counts.get("fixed_b", 0)), "common_support_min": low,
            "common_support_max": high, "SD_reference_median": reference,
            "realized_SD_Wald_stat": sd_wald[0], "realized_SD_Wald_df": sd_wald[1], "realized_SD_p_raw": sd_wald[2],
            "architecture_Wald_stat": architecture_wald[0], "architecture_Wald_df": architecture_wald[1],
            "architecture_p_raw": architecture_wald[2], "interaction_p_raw": delta_slope[3],
        })
    summary = pd.DataFrame(summaries)
    summary["realized_SD_p_Holm"] = holm(summary.realized_SD_p_raw.tolist())
    summary["architecture_p_Holm"] = holm(summary.architecture_p_raw.tolist())
    summary["interaction_p_Holm"] = holm(summary.interaction_p_raw.tolist())
    summary.to_csv(OUT / "Figure4_common_support_statistical_summary.csv", index=False, encoding="utf-8-sig")
    coefficient_output = pd.DataFrame(coefficients)
    coefficient_output.loc[coefficient_output.p_value.eq(0), "p_value"] = 1e-300
    coefficient_output.to_csv(OUT / "Figure4_model_coefficients_HC3.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(contrasts).to_csv(OUT / "Figure4_conditional_path_contrasts.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(sensitivities).to_csv(OUT / "Figure4_full_range_sensitivity.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(diagnostics).to_csv(OUT / "Figure4_model_diagnostics_summary.csv", index=False, encoding="utf-8-sig")
    source = "data/source_data/files/Figure4/simulation_level_source.csv"
    source_2 = "data/source_data/files/Figure_S2/simulation_level_source.csv"
    pd.DataFrame([
        {"role": "endpoint simulations", "source_file": source, "source_sha256": file_sha256(REPO / source)},
        {"role": "group_id to trait/b/m metadata", "source_file": source_2, "source_sha256": file_sha256(REPO / source_2)},
    ]).to_csv(OUT / "Figure4_input_provenance.csv", index=False, encoding="utf-8-sig")
    for _, record in summary.iterrows():
        trait = record.trait
        for suffix, comparison, statistic, df, raw_p, adjusted_p, family in [
            ("realized_sd", "joint realized pre-release SD effect", record.realized_SD_Wald_stat, record.realized_SD_Wald_df, record.realized_SD_p_raw, record.realized_SD_p_Holm, "F4_realized_SD_across_traits"),
            ("architecture", "joint genetic-architecture effect", record.architecture_Wald_stat, record.architecture_Wald_df, record.architecture_p_raw, record.architecture_p_Holm, "F4_architecture_across_traits"),
            ("interaction", "slope difference between architecture paths", np.nan, np.nan, record.interaction_p_raw, record.interaction_p_Holm, "F4_interaction_across_traits"),
        ]:
            rows.append(row(
                publication_item="Figure 4", panel=panel[trait], test_id=f"F4{panel[trait]}_{trait}_{suffix}",
                family_id=family, comparison=comparison,
                estimand="joint HC3 Wald statistic" if suffix != "interaction" else "HC3 interaction coefficient",
                test="joint HC3 robust Wald test" if suffix != "interaction" else "two-sided HC3 robust coefficient test",
                independent_unit="simulation", n_group1=record.n_fixed_m_common,
                n_group2=record.n_fixed_b_common, n_total=record.n_fixed_m_common + record.n_fixed_b_common,
                statistic=statistic, p_raw=raw_p, p_adjusted=adjusted_p,
                adjustment="Holm across three traits", status="tested",
                df=df,
                notes=f"df={df}; empirical common support [{record.common_support_min}, {record.common_support_max}]",
                source_file=source, source_file_2=source_2,
            ))
    contrast_frame = pd.DataFrame(contrasts)
    summary_by_trait = summary.set_index("trait")
    for _, result in contrast_frame.iterrows():
        counts = summary_by_trait.loc[result.trait]
        rows.append(row(
            publication_item="Figure 4", panel=panel[result.trait],
            test_id=f"F4{panel[result.trait]}_{result.trait}_contrast_{result['quantile']}",
            family_id=f"F4_{result.trait}_conditional_contrasts",
            comparison=f"fixed-b minus fixed-m at {result['quantile']} realized SD",
            estimand="conditional path contrast", test="two-sided HC3 robust linear contrast",
            independent_unit="simulation", n_group1=counts.n_fixed_m_common,
            n_group2=counts.n_fixed_b_common, n_total=counts.n_fixed_m_common + counts.n_fixed_b_common,
            estimate=result.fixed_b_minus_fixed_m,
            statistic=result.fixed_b_minus_fixed_m, p_raw=result.p_raw, p_adjusted=result.p_Holm,
            adjustment="Holm across low/mid/high contrasts within trait", status="tested",
            ci_level=0.95, ci_low=result.CI_low, ci_high=result.CI_high,
            notes=f"realized SD={result.realized_sd}; CI [{result.CI_low}, {result.CI_high}]",
            source_file=source, source_file_2=source_2,
        ))
    coefficient_frame = pd.DataFrame(coefficients)
    reported_terms = {
        "fixed_m_slope_per_0.01": ("fixed-m path slope per 0.01 realized SD", "F4_slopes_prespecified"),
        "fixed_b_slope_per_0.01": ("fixed-b path slope per 0.01 realized SD", "F4_slopes_prespecified"),
        "path_offset_reference_SD": ("fixed-b minus fixed-m offset at reference SD", "F4_offsets_prespecified"),
    }
    for _, result in coefficient_frame[coefficient_frame.term.isin(reported_terms)].iterrows():
        comparison, family = reported_terms[result.term]
        counts = summary_by_trait.loc[result.trait]
        rows.append(row(
            publication_item="Figure 4", panel=panel[result.trait],
            test_id=f"F4{panel[result.trait]}_{result.trait}_{result.term}",
            family_id=family, comparison=comparison, estimand="HC3 model coefficient or linear combination",
            test="two-sided HC3 robust coefficient test", independent_unit="simulation",
            n_group1=counts.n_fixed_m_common, n_group2=counts.n_fixed_b_common,
            n_total=counts.n_fixed_m_common + counts.n_fixed_b_common,
            estimate=result.estimate, statistic=result.estimate, p_raw=result.p_value,
            p_adjusted=result.p_value, adjustment="none; prespecified reported coefficient",
            ci_level=0.95, ci_low=result.CI_low, ci_high=result.CI_high, status="tested",
            notes="Full interaction model within empirical common support",
            source_file=source, source_file_2=source_2,
        ))
    return rows


def figure5_tests():
    data = pd.read_csv(FILES / "Figure5/source_data_per_run.csv")
    rows = []
    comparisons = []
    for conversion in [0.95, 0.99]:
        evolving = data[data["mode"].eq("evolving") & data.conversion.eq(conversion)].set_index("origin_seed")
        fixed = data[data["mode"].eq("uniform") & data.conversion.eq(conversion)].set_index("origin_seed")
        for outcome in ["elimination", "drive loss"]:
            a = evolving.outcome.eq(outcome)
            b = fixed.outcome.eq(outcome)
            only_a = int((a & ~b).sum())
            only_b = int((~a & b).sum())
            discordant = only_a + only_b
            if discordant == 0:
                p = 1.0
            else:
                # Exact two-sided McNemar equals a binomial test at p=0.5.
                tail = sum(math.comb(discordant, k) for k in range(0, min(only_a, only_b) + 1)) / 2**discordant
                p = min(1.0, 2 * tail)
            comparisons.append((conversion, outcome, only_a, only_b, p, len(a)))
    adjusted = holm([x[4] for x in comparisons])
    for (conversion, outcome, only_a, only_b, p, n), p_adj in zip(comparisons, adjusted):
        rows.append(row(
            publication_item="Figure 5", panel="A", test_id=f"F5A_{conversion}_{outcome.replace(' ','_')}",
            family_id="F5A_four_outcome_tests", comparison=f"conversion {conversion:g}: evolving vs fixed dispersal, {outcome}",
            estimand="paired outcome discordance", test="two-sided exact McNemar test",
            independent_unit="matched origin seed", n_group1=n, n_group2=n, n_total=n,
            estimate=only_a - only_b, statistic=np.nan, p_raw=p, p_adjusted=p_adj,
            adjustment="Holm across four prespecified outcome contrasts", status="tested",
            notes=f"discordant evolving-only={only_a}; fixed-only={only_b}",
            source_file="data/source_data/files/Figure5/source_data_per_run.csv",
        ))
    nodrive = data[data["mode"].eq("nodrive")].set_index("origin_seed")
    paired_rows = []
    for conversion in [0.75, 0.85, 0.95, 0.99]:
        evolving = data[data["mode"].eq("evolving") & data.conversion.eq(conversion)].set_index("origin_seed")
        for endpoint, mask in [
            ("LTP", evolving.outcome.eq("long-term persistence")),
            ("Non-LTP", ~evolving.outcome.eq("long-term persistence")),
        ]:
            selected = evolving[mask]
            if len(selected) == 0:
                continue
            common = selected.index.intersection(nodrive.index)
            drive_values = selected.loc[common, "dispersal_E_percent"].to_numpy(float)
            reference = nodrive.loc[common, "dispersal_E_percent"].to_numpy(float)
            test = ttest_rel(drive_values, reference)
            differences = drive_values - reference
            paired_rows.append((conversion, endpoint, len(common), float(differences.mean()), float(test.statistic), float(test.pvalue), differences))
    adjusted = holm([x[5] for x in paired_rows])
    for (conversion, endpoint, n, effect, statistic, p, differences), p_adj in zip(paired_rows, adjusted):
        rows.append(row(
            publication_item="Figure 5", panel="B", test_id=f"F5B_{conversion}_{endpoint}",
            family_id="F5B_six_paired_tests", comparison=f"conversion {conversion:g} {endpoint}: evolving drive vs matched no-drive",
            estimand="mean paired adult dispersal change difference (percentage points)",
            test="two-sided paired t test", independent_unit="matched origin seed",
            n_group1=n, n_group2=n, n_total=n, estimate=effect, statistic=statistic,
            p_raw=p, p_adjusted=p_adj, adjustment="Holm across six estimable prespecified contrasts",
            status="tested", notes="Pairing by origin_seed",
            source_file="data/source_data/files/Figure5/source_data_per_run.csv",
        ))
        if n <= 20:
            observed = abs(float(np.mean(differences)))
            extreme = 0
            total = 0
            for signs in itertools.product([-1.0, 1.0], repeat=n):
                permuted = float(np.mean(differences * np.asarray(signs)))
                extreme += abs(permuted) >= observed - 1e-15
                total += 1
            p_exact = extreme / total
            rows.append(row(
                publication_item="Figure 5", panel="B",
                test_id=f"F5B_{conversion}_{endpoint}_exact_sign_flip_sensitivity",
                family_id="F5B_small_sample_sensitivity",
                comparison=f"conversion {conversion:g} {endpoint}: evolving drive vs matched no-drive",
                estimand="mean paired adult dispersal change difference (percentage points)",
                test="two-sided exact paired sign-flip permutation sensitivity",
                independent_unit="matched origin seed", n_group1=n, n_group2=n, n_total=n,
                estimate=effect, statistic=effect, p_raw=p_exact, p_adjusted=p_exact,
                adjustment="none; prespecified small-n sensitivity analysis",
                permutations_or_enumerations=total, extreme_permutations=extreme,
                status="tested", notes="Sensitivity analysis reported alongside the primary paired t test",
                source_file="data/source_data/files/Figure5/source_data_per_run.csv",
            ))
    return rows


def figure6_tests():
    a = pd.read_csv(FILES / "Figure6/panelA_replicates.csv")
    rows = []
    panel_a = []
    for index, group_name in enumerate(["P70", "P85", "S70", "S85"]):
        group = a[a.group.eq(group_name)]
        present = group[group.load.eq("present")].Nmin_relative
        absent = group[group.load.eq("absent")].Nmin_relative
        seed = 2026091401 + index
        estimate, p, extreme = perm_mean(present, absent, seed, N_PERM_F6)
        panel_a.append(row(
            publication_item="Figure 6", panel="A", test_id=f"F6A_{group_name}", family_id="F6A_four_load_tests",
            comparison=f"{group_name}: with vs without recessive load", estimand="mean(with load)-mean(without load)",
            test="two-sided independent permutation test", independent_unit="simulation",
            n_group1=len(present), n_group2=len(absent), n_total=len(present)+len(absent),
            estimate=estimate, statistic=estimate, p_raw=p,
            permutations_or_enumerations=N_PERM_F6, extreme_permutations=extreme, seed=seed, status="tested",
            notes="Monte-Carlo plus-one P value", source_file="data/source_data/files/Figure6/panelA_replicates.csv",
        ))
    adjusted = holm([x["p_raw"] for x in panel_a])
    for result, p_adj in zip(panel_a, adjusted):
        result["p_adjusted"] = p_adj
        result["adjustment"] = "Holm across four prespecified group contrasts"
    rows.extend(panel_a)

    group = a[a.group.eq("P70")]
    present = group[group.load.eq("present")].outcome.eq("elimination")
    absent = group[group.load.eq("absent")].outcome.eq("elimination")
    table = [[int(present.sum()), int((~present).sum())], [int(absent.sum()), int((~absent).sum())]]
    odds, p = fisher_exact(table, alternative="two-sided")
    rows.append(row(
        publication_item="Figure 6", panel="B", test_id="F6B_P70_elimination", family_id="F6B_prespecified",
        comparison="P70: with vs without recessive load", estimand="elimination odds ratio",
        test="two-sided Fisher exact test", independent_unit="simulation",
        n_group1=len(present), n_group2=len(absent), n_total=len(present)+len(absent),
        estimate=odds, statistic=odds, p_raw=p, p_adjusted=p,
        adjustment="none; one prespecified contrast", status="tested", notes=f"2x2 table={table}",
        source_file="data/source_data/files/Figure6/panelA_replicates.csv",
    ))

    d = pd.read_csv(FILES / "Figure6/panelD_final20_replicates.csv")
    panel_d = []
    for index, group_name in enumerate(["P70", "S70", "S85"]):
        group = d[d.group.eq(group_name)]
        present = group[group.load.eq("present")].N_long_term_relative
        absent = group[group.load.eq("absent")].N_long_term_relative
        seed = 2026091501 + index
        estimate, p, extreme = perm_mean(present, absent, seed, N_PERM_F6)
        panel_d.append(row(
            publication_item="Figure 6", panel="D", test_id=f"F6D_{group_name}", family_id="F6D_three_estimable_tests",
            comparison=f"{group_name}: with vs without recessive load among persistent trajectories",
            estimand="mean(with load)-mean(without load)", test="two-sided independent permutation test",
            independent_unit="simulation", n_group1=len(present), n_group2=len(absent), n_total=len(present)+len(absent),
            estimate=estimate, statistic=estimate, p_raw=p,
            permutations_or_enumerations=N_PERM_F6, extreme_permutations=extreme, seed=seed, status="tested",
            notes="Outcome-conditioned final-20-week relative population size; plus-one P value",
            source_file="data/source_data/files/Figure6/panelD_final20_replicates.csv",
        ))
    adjusted = holm([x["p_raw"] for x in panel_d])
    for result, p_adj in zip(panel_d, adjusted):
        result["p_adjusted"] = p_adj
        result["adjustment"] = "Holm across three estimable prespecified contrasts"
    rows.extend(panel_d)
    rows.append(row(
        publication_item="Figure 6", panel="D", test_id="F6D_P85", family_id="F6D_three_estimable_tests",
        comparison="P85: with vs without recessive load among persistent trajectories",
        estimand="mean(with load)-mean(without load)", test="two-sided independent permutation test",
        independent_unit="simulation", n_group1=0, n_group2=0, n_total=0, status="not estimable",
        notes="Both P85 conditions ended in population elimination; no persistent endpoint exists.",
        source_file="data/source_data/files/Figure6/panelD_final20_replicates.csv",
    ))
    return rows


def s1_tests():
    rows = []
    for panel in ["B", "C"]:
        source = FILES / f"Figure_S1/panel{panel}_final20_replicates.csv"
        data = pd.read_csv(source)
        panel_rows = []
        for index, (setting, group) in enumerate(data.groupby("setting", sort=True)):
            neutral = group[group.cohort.eq("Neutral mutations")].final20_nni
            variable = group[group.cohort.eq("Variable mutations")].final20_nni
            seed = (2026110100 if panel == "B" else 2026110200) + index
            estimate, p, extreme = perm_mean(variable, neutral, seed)
            panel_rows.append(row(
                publication_item="Supplementary Figure S1", panel=panel,
                test_id=f"S1{panel}_{setting:g}", family_id=f"S1{panel}_seven_settings",
                comparison=f"setting {setting:g}: variable vs neutral mutations",
                estimand="mean final-20-week NNI difference", test="two-sided independent permutation test",
                independent_unit="simulation", n_group1=len(variable), n_group2=len(neutral),
                n_total=len(variable)+len(neutral), estimate=estimate, statistic=estimate,
                p_raw=p, permutations_or_enumerations=N_PERM, extreme_permutations=extreme, seed=seed, status="tested",
                notes="Monte-Carlo plus-one P value",
                source_file=source.relative_to(REPO).as_posix(),
            ))
        adjusted = holm([x["p_raw"] for x in panel_rows])
        for result, p_adj in zip(panel_rows, adjusted):
            result["p_adjusted"] = p_adj
            result["adjustment"] = "Holm across seven settings within panel"
        rows.extend(panel_rows)
    return rows


def s2_tests():
    source = FILES / "Figure_S2/simulation_level_source.csv"
    data = pd.read_csv(source)
    summary = data[data.sd_stratum.gt(1)].groupby(
        ["trait", "sd_stratum", "m", "b"], sort=True
    ).agg(n_simulations=("replicate", "size"), normalized_response_mean=("normalized_response", "mean")).reset_index()
    rows = []
    panel_for_trait = {"dc": "A", "er": "B", "sf": "C"}
    for (trait, stratum), group in summary.groupby(["trait", "sd_stratum"], sort=True):
        group = group.sort_values("m")
        if len(group) < 2:
            rows.append(row(
                publication_item="Supplementary Figure S2", panel=panel_for_trait[trait],
                test_id=f"S2_{trait}_{stratum}", family_id=f"S2_{trait}_lower_SD",
                comparison=f"{trait}, SD stratum {stratum:g}", estimand="Spearman rank correlation",
                test="two-sided exact Spearman permutation", independent_unit="setting mean",
                n_total=len(group), status="not estimable", notes="Only one setting in stratum",
                source_file=source.relative_to(REPO).as_posix(),
            ))
            continue
        x = rankdata(group.m.to_numpy(), method="average")
        rho, p, extreme, total = exact_spearman(x, group.normalized_response_mean.to_numpy())
        rows.append(row(
            publication_item="Supplementary Figure S2", panel=panel_for_trait[trait],
            test_id=f"S2_{trait}_{stratum}", family_id=f"S2_{trait}_lower_SD",
            comparison=f"{trait}, SD stratum {stratum:g}", estimand="Spearman rank correlation",
            test="two-sided exact Spearman permutation", independent_unit="setting mean",
            n_total=len(group), estimate=rho, statistic=rho, p_raw=p, p_adjusted=p,
            adjustment="none; descriptive sensitivity trend by stratum",
            permutations_or_enumerations=total, extreme_permutations=extreme, status="tested",
            notes=f"setting simulation counts={group.n_simulations.tolist()}",
            source_file=source.relative_to(REPO).as_posix(),
        ))
    for trait in ["dc", "er", "sf"]:
        selected = [x for x in rows if x["panel"] == panel_for_trait[trait] and x["family_id"] == f"S2_{trait}_lower_SD" and x["status"] == "tested"]
        adjusted = holm([x["p_raw"] for x in selected])
        for result, p_adj in zip(selected, adjusted):
            result["p_adjusted"] = p_adj
            result["adjustment"] = "Holm across three estimable lower-SD strata within trait"
    return rows


def table_s3():
    source = FILES / "Figure_S4/pre_release_block_replicates.csv"
    data = pd.read_csv(source)
    source_relative = source.relative_to(REPO).as_posix()
    source_hash = file_sha256(source)
    script_relative = Path(__file__).resolve().relative_to(REPO).as_posix()
    script_hash = file_sha256(Path(__file__).resolve())
    labels = {
        "virtual_haploid_load": "Virtual haploid load",
        "copies_per_individual": "Mutation copies per individual",
        "population_N": "Population size",
        "mean_genetic_viability": "Mean genetic viability (W_load)",
    }
    records = []
    x = np.array([5124.5, 5374.5, 5624.5, 5874.5])
    for (condition, model), group in data.groupby(["condition_id", "model"], sort=True):
        for metric, label in labels.items():
            means = group.groupby("block", sort=True)[metric].mean().to_numpy(float)
            slope, intercept = np.polyfit(x, means, 1)
            fitted_start = intercept + slope * 5000
            fitted_end = intercept + slope * 5999
            final = means[-1]
            r_trend = abs(fitted_end - fitted_start) / abs(final)
            r_last = abs(means[-1] - means[-2]) / abs(final)
            records.append({
                "diagnostic_id": f"{condition}_{metric}", "condition_id": condition,
                "model": model, "metric": metric, "metric_label": label,
                "analysis_level": "replicate block means followed by across-replicate means",
                "window_start": 5000, "window_end": 5999, "block_length": 250,
                "n_blocks": 4, "n_independent_simulations": group.replicate.nunique(),
                **{f"M{i+1}": means[i] for i in range(4)},
                "linear_slope_per_week": slope, "fitted_value_5000": fitted_start,
                "fitted_value_5999": fitted_end, "R_trend": r_trend, "R_last": r_last,
                "pass_epsilon_0p025": r_trend < .025 and r_last < .025,
                "pass_epsilon_0p05": r_trend < .05 and r_last < .05,
                "pass_epsilon_0p1": r_trend < .10 and r_last < .10,
                "source_file": source_relative, "source_sha256": source_hash,
                "analysis_script": script_relative, "analysis_script_sha256": script_hash,
                "archive_commit": "recorded by the enclosing Git commit",
            })
    return pd.DataFrame(records)


def write_outputs():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    rows += outcome_global_tests("Figure 1", FILES / "Figure1/endpoint_replicates.csv", panel="A")
    rows += continuous_modifier_tests("Figure 1", FILES / "Figure1/final20_replicates.csv", "final20_attribute_weighted", seed_base=2026100100, panel="B")
    rows += continuous_modifier_tests("Figure 1", FILES / "Figure1/final20_replicates.csv", "final20_n_over_k", seed_base=2026100200, panel="C")
    rows += outcome_global_tests("Figure 2", FILES / "Figure2/endpoint_replicates.csv", panel="A")
    rows += continuous_modifier_tests("Figure 2", FILES / "Figure2/final20_replicates.csv", "final20_attribute_weighted", seed_base=2026100300, panel="B")
    rows += continuous_modifier_tests("Figure 2", FILES / "Figure2/final20_replicates.csv", "final20_n_over_k", seed_base=2026100400, panel="C")
    f2e, f2e_settings = panel_e_test("Figure 2", FILES / "Figure2/panelE_final20_replicates.csv", "embryo resistance")
    rows.append(f2e)
    rows += figure3_outcomes()
    rows += continuous_modifier_tests("Figure 3", FILES / "Figure3/final20_replicates.csv", "final20_attribute_weighted", seed_base=2026100500, panel="B")
    rows += continuous_modifier_tests("Figure 3", FILES / "Figure3/final20_replicates.csv", "final20_n_over_k", seed_base=2026100600, panel="C")
    f3e, f3e_settings = panel_e_test("Figure 3", FILES / "Figure3/panelE_final20_replicates.csv", "female heterozygote fitness")
    rows.append(f3e)
    rows += figure4_tests()
    rows += figure5_tests()
    rows += figure6_tests()
    rows += s1_tests()
    rows += s2_tests()

    results = pd.DataFrame(rows, columns=STANDARD_COLUMNS)
    # Numerical survival functions may underflow for extremely large Wald z.
    # Preserve a conservative finite reporting floor instead of writing P=0.
    for column in ["p_raw", "p_adjusted"]:
        zero = results[column].eq(0)
        results.loc[zero, column] = 1e-300
        results.loc[zero, "notes"] = results.loc[zero, "notes"].fillna("").astype(str) + "; numerical P underflow reported as <1e-300"
    results["record_id"] = results["test_id"]
    results["analysis_script"] = "scripts/compute_final_statistics.py"
    results["software"] = f"Python {platform.python_version()}; numpy {np.__version__}; pandas {pd.__version__}; scipy {stats.__version__ if hasattr(stats, '__version__') else '1.14.1'}"
    source_hashes = {}
    for source in results.source_file.dropna().unique():
        path = REPO / source
        source_hashes[source] = file_sha256(path) if path.is_file() else np.nan
    results["source_sha256"] = results.source_file.map(source_hashes)
    source_hashes_2 = {}
    for source in results.source_file_2.dropna().unique():
        path = REPO / source
        source_hashes_2[source] = file_sha256(path) if path.is_file() else np.nan
    results["source_sha256_2"] = results.source_file_2.map(source_hashes_2)
    results["significance_raw"] = results.p_raw.map(significance)
    results["significance_adjusted"] = results.p_adjusted.map(significance)
    results.to_csv(OUT / "all_inferential_tests.csv", index=False, encoding="utf-8-sig")

    for publication, group in results.groupby("publication_item", sort=False):
        safe = publication.replace("Supplementary Figure ", "Figure_").replace("Figure ", "Figure").replace(" ", "_")
        group.to_csv(OUT / f"{safe}.csv", index=False, encoding="utf-8-sig")

    # Supplementary Table S2 is a direct filtered view of the common result table.
    table_s2 = results[results.status.isin(["tested", "not estimable"])].copy()
    table_s2.to_csv(OUT / "Table_S2.csv", index=False, encoding="utf-8-sig")
    f2e_settings.to_csv(OUT / "Figure2_panelE_setting_summary.csv", index=False, encoding="utf-8-sig")
    f3e_settings.to_csv(OUT / "Figure3_panelE_setting_summary.csv", index=False, encoding="utf-8-sig")
    stability = table_s3()
    stability.to_csv(OUT / "Table_S3.csv", index=False, encoding="utf-8-sig")

    sample_sizes = results[[
        "publication_item", "panel", "test_id", "independent_unit", "n_group1", "n_group2", "n_total", "status", "notes"
    ]]
    sample_sizes.to_csv(OUT / "sample_sizes.csv", index=False, encoding="utf-8-sig")

    mapping = pd.read_csv(REPO / "config/figure_data_map.csv")
    tested = set(zip(results.publication_item, results.panel.astype(str)))
    catalog = []
    for _, mapped in mapping.iterrows():
        panel = str(mapped.panel)
        key = (mapped.publication_item, panel)
        if mapped.publication_item == "Supplementary Figure S4":
            status = "operational_diagnostic_in_Table_S3"
        elif mapped.statistics_candidate == "not applicable":
            status = "descriptive_not_applicable"
        elif key in tested or mapped.publication_item in {"Supplementary Table S2", "Supplementary Table S3"}:
            status = "recomputed"
        else:
            status = "covered_by_companion_panel_or_table"
        catalog.append({
            "record_id": mapped.record_id, "publication_item": mapped.publication_item,
            "panel": panel, "current_content": mapped.current_content,
            "statistics_status": status, "statistics_file": (
                "results/statistics/Table_S3.csv" if mapped.record_id == "TS3" or mapped.publication_item == "Supplementary Figure S4" else
                "results/statistics/Table_S2.csv" if mapped.record_id == "TS2" else
                "results/statistics/all_inferential_tests.csv" if status == "recomputed" else "not applicable"
            ),
        })
    pd.DataFrame(catalog).to_csv(OUT / "statistics_catalog.csv", index=False, encoding="utf-8-sig")
    qa = {
        "inferential_records": int(len(results)),
        "tested_records": int(results.status.eq("tested").sum()),
        "not_estimable_records": int(results.status.eq("not estimable").sum()),
        "p_raw_out_of_range": int((results.p_raw.dropna().between(0, 1) == False).sum()),
        "p_adjusted_out_of_range": int((results.p_adjusted.dropna().between(0, 1) == False).sum()),
        "p_reported_as_zero": int(results.p_raw.eq(0).sum() + results.p_adjusted.eq(0).sum()),
        "missing_source_hashes": int(results.source_sha256.isna().sum()),
        "figure2E_expected": bool(np.isclose(results.loc[results.test_id.eq("Figure2E_exact_spearman"), "p_raw"].iloc[0], 62/5040)),
        "figure3E_expected": bool(np.isclose(results.loc[results.test_id.eq("Figure3E_exact_spearman"), "p_raw"].iloc[0], 2/5040)),
        "figure3E_variable_h099_n": int(pd.read_csv(FILES / "Figure3/panelE_final20_replicates.csv").query("setting == 0.99 and cohort == 'Variable mutations'").shape[0]),
        "table_s3_records": int(len(stability)),
    }
    (OUT / "qa_summary.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
    print(f"wrote {len(results)} inferential-test records and {len(stability)} stability diagnostics")


if __name__ == "__main__":
    write_outputs()
