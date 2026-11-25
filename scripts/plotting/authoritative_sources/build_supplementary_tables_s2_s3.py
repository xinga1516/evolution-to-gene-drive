from __future__ import annotations

from pathlib import Path
import hashlib
import numpy as np
import pandas as pd


ROOT = Path(r"D:\champer实验室工作\文章figure1-8")
OUT = ROOT / "supplementary_final"
SRC = OUT / "source_data"
TABLE = OUT / "tables"
TABLE.mkdir(parents=True, exist_ok=True)


def holm(values: pd.Series) -> pd.Series:
    x = pd.to_numeric(values, errors="coerce")
    good = x.notna()
    p = x[good].to_numpy(float)
    out = np.full(len(x), np.nan)
    if len(p):
        order = np.argsort(p)
        running = 0.0
        adj = np.empty(len(p))
        for rank, idx in enumerate(order):
            running = max(running, (len(p) - rank) * p[idx])
            adj[idx] = min(1.0, running)
        out[np.flatnonzero(good)] = adj
    return pd.Series(out, index=values.index)


S2_COLUMNS = [
    "figure_panel", "analysis_id", "endpoint_or_outcome", "comparison", "regime",
    "n_1", "n_2", "independent_unit", "test", "effect_estimate",
    "test_statistic", "df", "discordant_1_only", "discordant_2_only",
    "p_raw_relation", "p_raw", "p_adjusted_relation", "p_adjusted", "adjustment_family",
    "family_size", "status", "source_file", "notes",
]


rows: list[dict] = []


def add(**kwargs):
    row = {c: "" for c in S2_COLUMNS}
    row.update(kwargs)
    rows.append(row)


# Supplementary Fig. S1: final-100-week NNI, treatment comparisons.
f = SRC / "S1_nni_tests.csv"
d = pd.read_csv(f)
panel_map = {"Figure 1 spatial": "Supplementary Fig. S1a", "Figure 2E": "Supplementary Fig. S1b", "Figure 3E": "Supplementary Fig. S1c"}
for _, r in d.iterrows():
    add(
        figure_panel=panel_map.get(r.panel, r.panel), analysis_id=f"{r.family_id}_{r.setting}",
        endpoint_or_outcome="final-100-week normalized nearest-neighbor index",
        comparison="Variable minus control", regime=str(r.setting), n_1=r.n_variable,
        n_2=r.n_control, independent_unit="simulation",
        test="two-sided independent permutation test of mean difference",
        effect_estimate=r.effect_variable_minus_control, p_raw=r.p_raw,
        p_adjusted=r.p_holm, adjustment_family=r.family_id,
        family_size=r.testable_comparisons, status=r.test_status,
        source_file=str(f.relative_to(ROOT)), notes="10,000 permutations; percentile-bootstrap 95% CI reported in Source Data",
    )


def perm_p(a, b, seed, B):
    a = np.asarray(a, float); b = np.asarray(b, float)
    a = a[np.isfinite(a)]; b = b[np.isfinite(b)]
    if len(a) < 2 or len(b) < 2:
        return np.nan
    obs = abs(b.mean() - a.mean()); pooled = np.r_[a, b]; n_a = len(a)
    rng = np.random.default_rng(seed); hits = 0
    for _ in range(B):
        q = rng.permutation(pooled)
        hits += abs(q[n_a:].mean() - q[:n_a].mean()) >= obs - 1e-15
    return (hits + 1) / (B + 1)


def add_final20_stats(figure: int, panel: str, path: Path, source_path: Path, endpoint: str, permutations: int):
    z = pd.read_csv(path); source = pd.read_csv(source_path)
    tests = z[z.treatment.astype(str).str.contains("vs variable", case=False, na=False)].copy()
    for i, r in tests.reset_index(drop=True).iterrows():
        non_ltp = str(r.treatment).lower().startswith("non-ltp")
        model, htxt = str(r.condition).rsplit(" ", 1); h = float(htxt)
        metric = r.metric
        q = source[source.model.eq(model) & np.isclose(source.h.astype(float), h)].copy()
        if non_ltp:
            q = q[q.outcome.ne("Long-term persistence")]
        control = pd.to_numeric(q.loc[q.treatment.eq("Neutral control"), metric], errors="coerce").dropna().to_numpy()
        variable = pd.to_numeric(q.loc[q.treatment.eq("Functional modifier"), metric], errors="coerce").dropna().to_numpy()
        seed = int(hashlib.sha256(f"{figure}|{panel}|{r.condition}|{non_ltp}|{metric}".encode()).hexdigest()[:8], 16)
        p = perm_p(control, variable, seed, permutations)
        effect = variable.mean() - control.mean() if len(control) and len(variable) else np.nan
        add(
            figure_panel=f"Figure {figure}{panel}", analysis_id=f"Fig{figure}_{panel}_{i+1}",
            endpoint_or_outcome=endpoint,
            comparison=f"Functional modifier minus neutral control ({'non-long-term outcomes' if non_ltp else 'all outcomes'})",
            regime=r.condition, n_1=len(variable), n_2=len(control), independent_unit="simulation",
            test="two-sided independent permutation test of mean difference",
            effect_estimate=effect, p_raw=p,
            adjustment_family="none; prespecified within-condition comparison", family_size=1,
            status="tested" if pd.notna(p) else "not estimable", source_file=str(source_path.relative_to(ROOT)),
            notes=f"{permutations:,} permutations; plus-one Monte Carlo P value; recalculated from current locked simulation-level source",
        )


base = ROOT / "new_main_figure_task" / "final20_attribute_panels_20261024"
add_final20_stats(2, "B", base / "Figure2_panelA_stats.csv", base / "Figure2_final20_source.csv", "final-20-generation adult-population-weighted drive conversion", 10_000)
add_final20_stats(2, "C", base / "Figure2_panelC_stats.csv", base / "Figure2_final20_source.csv", "final relative population size (final 20 generations; elimination = 0)", 10_000)
add_final20_stats(3, "B", base / "Figure3_panelA_authoritative_restored_stats.csv", base / "Figure3_authoritative_restored_source.csv", "final embryo resistance (last 10 recorded population-average attribute values)", 100_000)
add_final20_stats(3, "C", base / "Figure3_panelB_authoritative_restored_stats.csv", base / "Figure3_authoritative_restored_source.csv", "final relative population size (last 100 population records; elimination = 0)", 100_000)
add_final20_stats(4, "B", base / "Figure4_panelA_stats.csv", base / "Figure4_final20_source.csv", "final-20-generation adult-population-weighted female heterozygote fitness", 10_000)
add_final20_stats(4, "C", base / "Figure4_panelB_stats.csv", base / "Figure4_final20_source.csv", "final relative population size (final 20 generations; elimination = 0)", 10_000)


# Current outcome-composition tests. Figure 2 retains its four-setting Holm family.
# Figures 3 and 4 each use the single prespecified Panmictic 0.70 contrast.
f = ROOT / "文章终稿数据" / "figure2-5_final_panel_packages_20260908" / "Figure 2" / "statistics" / "S2_outcome_global.csv"
d = pd.read_csv(f)
for _, r in d.iterrows():
    fig = int(str(r["Figure/panel"]).split()[1][0])
    if fig != 2:
        continue
    current_panel = "A" if fig in {2, 3, 4} else "B"
    p_adj = pd.to_numeric(pd.Series([r.get("Holm global P")]), errors="coerce").iloc[0]
    add(
        figure_panel=f"Figure {fig}{current_panel}", analysis_id=f"Fig{fig}_{current_panel}_{r['Regime']}",
        endpoint_or_outcome="outcome composition", comparison="Functional modifier versus neutral control",
        regime=r["Regime"], n_1=r["N_treat"], n_2=r["N_comp"], independent_unit="simulation",
        test="two-sided Fisher–Freeman–Halton exact test", p_raw=r["Raw global FFH P"], p_adjusted=p_adj,
        adjustment_family=(r["Family ID"] if pd.notna(p_adj) else ("single prespecified contrast" if fig == 4 else "descriptive; no multiplicity adjustment")),
        family_size=(len(d[d["Family ID"].eq(r["Family ID"])]) if pd.notna(p_adj) else 1), status="tested",
        source_file=str(f.relative_to(ROOT)), notes=f"Treatment E/DL/P={r['Treatment E/DL/P']}; comparator E/DL/P={r['Comparator E/DL/P']}",
    )

f = ROOT / "文章终稿数据" / "Figure3" / "processed_source" / "Figure3_panelD_fisher_tests.csv"
for _, r in pd.read_csv(f).iterrows():
    add(figure_panel="Figure 3A", analysis_id="Fig3_A_Panmictic_0.70", endpoint_or_outcome="outcome composition",
        comparison=r.contrast, regime=r.condition, n_1=r.functional_total, n_2=r.control_total,
        independent_unit="simulation", test=r.test, p_raw=r.raw_p_value,
        adjustment_family=r.multiplicity_adjustment, family_size=1, status="tested",
        source_file=str(f.relative_to(ROOT)), notes=f"events: functional {r.functional_events}/{r.functional_total}; control {r.control_events}/{r.control_total}")

# Figure 4A in the locked deck is the 100-replicate outcome snapshot (7/100 at Panmictic 0.70).
f = ROOT / "文章终稿数据" / "Figure4" / "processed_source_final" / "Figure4_panelD_tests.csv"
for _, r in pd.read_csv(f).iterrows():
    add(figure_panel="Figure 4A", analysis_id=f"Fig4_A_{r.condition}", endpoint_or_outcome="outcome composition",
        comparison="Functional modifier versus neutral control", regime=r.condition, n_1=100, n_2=100,
        independent_unit="simulation", test=r.test, effect_estimate=r.odds_ratio, p_raw=r.raw_p,
        adjustment_family="none; prespecified direct contrast", family_size=1, status="tested",
        source_file=str(f.relative_to(ROOT)), notes="Locked 100-replicate outcome snapshot; Figure 4B–C use the later 20-replicate final-20 endpoint snapshot")

# Locked setting-level association tests, remapped to current panel E.
for fig, endpoint, f in [
    (3, "NNI–embryo-resistance association", ROOT / "文章终稿数据" / "Figure3" / "processed_source" / "Figure3_panelE_exact_spearman.csv"),
    (4, "NNI–fitness association", ROOT / "文章终稿数据" / "Figure4" / "processed_source_final" / "Figure4_panelE_exact_spearman.csv"),
]:
    q = pd.read_csv(f)
    for _, r in q.iterrows():
        add(figure_panel=f"Figure {fig}E", analysis_id=f"Fig{fig}_E", endpoint_or_outcome=endpoint,
            comparison="setting-level association", regime="seven settings", n_1=r.n_settings, independent_unit="parameter setting",
            test=r.method, effect_estimate=r.rho, p_raw=r.p_value, adjustment_family="none", family_size=1,
            status="tested", source_file=str(f.relative_to(ROOT)), notes="Exact Spearman enumeration over 7 settings (7! permutations)")


# Figure 5: locked v159 pre-release realized-SD common-support analysis.
f = ROOT / "文章终稿数据" / "figure2-5_final_panel_packages_20260908" / "Figure 5" / "common_support_replot" / "statistics" / "Figure5_common_support_statistical_summary.csv"
d = pd.read_csv(f)
trait_name = {"dc": "drive conversion", "er": "embryo resistance", "sf": "female heterozygote fitness"}
for _, r in d.iterrows():
    panel = {"dc":"A", "er":"B", "sf":"C"}[r.trait]
    entries = [
        ("realized pre-release SD effect", r.realized_SD_p_raw, r.realized_SD_p_Holm, r.realized_SD_Wald_stat, r.realized_SD_Wald_df, "joint HC3 Wald", "Figure 5 realized-SD effect across three traits"),
        ("genetic-architecture effect", r.architecture_p_raw, r.architecture_p_Holm, r.architecture_Wald_stat, r.architecture_Wald_df, "joint HC3 Wald", "Figure 5 architecture effect across three traits"),
        ("fixed-m architecture slope", r.slope_fixed_m_p, np.nan, r.slope_fixed_m_per_0_01, np.nan, "HC3 slope coefficient", "none; prespecified coefficient"),
        ("fixed-b architecture slope", r.slope_fixed_b_p, np.nan, r.slope_fixed_b_per_0_01, np.nan, "HC3 slope coefficient", "none; prespecified coefficient"),
        ("slope difference between architectures", r.delta_slope_p, r.interaction_p_Holm, r.delta_slope, np.nan, "HC3 interaction coefficient", "Figure 5 interaction across three traits"),
        ("architecture offset at reference SD", r.path_offset_p, np.nan, r.path_offset_reference_SD, np.nan, "HC3 model contrast", "none; prespecified model contrast"),
        ("architecture contrast at low realized SD", r.delta_low_p_raw, r.delta_low_p_Holm, r.delta_low, np.nan, "HC3 conditional contrast", f"Figure 5 {r.trait} conditional low-mid-high"),
        ("architecture contrast at median realized SD", r.delta_mid_p_raw, r.delta_mid_p_Holm, r.delta_mid, np.nan, "HC3 conditional contrast", f"Figure 5 {r.trait} conditional low-mid-high"),
        ("architecture contrast at high realized SD", r.delta_high_p_raw, r.delta_high_p_Holm, r.delta_high, np.nan, "HC3 conditional contrast", f"Figure 5 {r.trait} conditional low-mid-high"),
    ]
    for kind, raw, adj, stat, dfv, test_name, family in entries:
        if raw == 0:
            raw = 1e-300
        raw_relation = "reported as <" if raw == 1e-300 else "exact"
        adj_relation = "reported as <" if adj == 3e-300 else ("exact" if pd.notna(adj) else "")
        add(
            figure_panel=f"Figure 5{panel}",
            analysis_id=f"Fig5_{r.trait}_{kind.replace('-', '_').replace(' ', '_')}",
            endpoint_or_outcome=trait_name[r.trait], comparison=kind,
            regime="empirical common support", n_1=r.n_fixed_m_common, n_2=r.n_fixed_b_common, independent_unit="simulation",
            test=test_name, test_statistic=stat, df=dfv, p_raw_relation=raw_relation, p_raw=raw,
            p_adjusted_relation=adj_relation, p_adjusted=adj,
            adjustment_family=family,
            family_size=(3 if pd.notna(adj) else 1), status="tested", source_file=str(f.relative_to(ROOT)),
            notes=f"Pre-release realized-SD common support [{r.common_support_min}, {r.common_support_max}]",
        )


# Figure 6: locked 20-replicate retest.
f = ROOT / "文章终稿数据" / "Figure6" / "retest_20rep_20260914_final" / "processed" / "figure6_statistics.csv"
d = pd.read_csv(f)
for _, r in d.iterrows():
    n_with = 20 if r.panel == "B" else r.n_with
    n_without = 20 if r.panel == "B" else r.n_without
    add(
        figure_panel=f"Figure 6{r.panel}", analysis_id=f"Fig6_{r.panel}_{r.group}",
        endpoint_or_outcome=r.estimand, comparison="With recessive load versus without recessive load",
        regime=r.group, n_1=n_with, n_2=n_without, independent_unit="simulation",
        test=r.test, effect_estimate=r.estimate, p_raw=r.p_raw, p_adjusted=r.p_holm,
        adjustment_family=(f"Fig6{r.panel} endpoint-specific regime family" if r.panel in {"A", "D"} else "none"),
        family_size=(4 if r.panel == "A" else (3 if r.panel == "D" else 1)),
        status="tested" if pd.notna(r.p_raw) else "not estimable", source_file=str(f.relative_to(ROOT)),
        notes="Figure 6C trajectory is descriptive and has no formal P value",
    )


# Figure 7: locked final-20 all-outcomes v5 analyses.
f7 = ROOT / "new_main_figure_task" / "figure7_final20_all_outcomes_warmB_20261024_v5"
f = f7 / "panel_a_prespecified_four_exact_mcnemar_tests.csv"
d = pd.read_csv(f)
for _, r in d.iterrows():
    add(
        figure_panel="Figure 7A", analysis_id=f"Fig7_A_{r.conversion}_{r.outcome}",
        endpoint_or_outcome=r.outcome, comparison="Evolving versus fixed dispersal",
        regime=r.conversion, n_1=r.n_pairs, n_2=r.n_pairs, independent_unit="origin-seed pair",
        test="two-sided exact McNemar test", discordant_1_only=r.discordant_evolving_only, discordant_2_only=r.discordant_fixed_only,
        p_raw=r.p_raw, p_adjusted=r.p_holm_4, adjustment_family="Fig7A four prespecified outcome tests",
        family_size=4, status="tested", source_file=str(f.relative_to(ROOT)), notes="Outcome coded against all other outcomes",
    )
f = f7 / "panel_b_tests.csv"
d = pd.read_csv(f)
for _, r in d.iterrows():
    add(
        figure_panel="Figure 7B", analysis_id=f"Fig7_B_{r.endpoint_group}_{r.conversion}",
        endpoint_or_outcome="adult dispersal change (%)", comparison=r.comparison,
        regime=r.conversion, n_1=r.n, independent_unit="origin-seed pair",
        test="two-sided paired t-test", effect_estimate=r.mean_effect,
        test_statistic=r.t, df=int(r.n)-1, p_raw=r.p_raw, p_adjusted=r.p_holm_family,
        adjustment_family="Fig7B six displayed matched comparisons", family_size=6,
        status="tested", source_file=str(f.relative_to(ROOT)), notes="Final-20-generation adult-population-weighted endpoint",
    )
f = f7 / "panel_c_tests.csv"
d = pd.read_csv(f)
for _, r in d.iterrows():
    add(
        figure_panel="Figure 7C", analysis_id=f"Fig7_C_{r.conversion}",
        endpoint_or_outcome="final relative adult population size", comparison="Evolving minus fixed dispersal",
        regime=r.conversion, n_1=r.paired_n, n_2=r.paired_n, independent_unit="origin-seed pair",
        test="two-sided paired t-test", effect_estimate=r.mean_evolving_minus_fixed,
        test_statistic=r.t, df=int(r.paired_n)-1, p_raw=r.p_raw, p_adjusted=r.p_holm_4,
        adjustment_family="Fig7C four conversion settings", family_size=4,
        status="tested", source_file=str(f.relative_to(ROOT)), notes="Final-20-generation adult population ratio; elimination = 0",
    )


s2 = pd.DataFrame(rows, columns=S2_COLUMNS)
for col in ["n_1", "n_2", "effect_estimate", "test_statistic", "df", "discordant_1_only", "discordant_2_only", "p_raw", "p_adjusted", "family_size"]:
    s2[col] = pd.to_numeric(s2[col], errors="coerce")
s2.insert(0, "row_id", [f"S2-{i:03d}" for i in range(1, len(s2) + 1)])
s2.to_csv(TABLE / "Supplementary_Table_S2_all_P_values.csv", index=False)
print(f"S2 rows: {len(s2)}")
