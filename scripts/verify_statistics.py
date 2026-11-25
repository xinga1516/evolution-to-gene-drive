#!/usr/bin/env python3
"""Fail-fast checks for the frozen statistical archive."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "results" / "statistics"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized_text_sha256(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    data = pd.read_csv(OUT / "all_inferential_tests.csv")
    checks: list[tuple[str, bool]] = []

    def check(name: str, condition) -> None:
        checks.append((name, bool(condition)))

    check("unique record ids", data.record_id.is_unique)
    check("no zero raw P", not data.p_raw.eq(0).any())
    check("no zero adjusted P", not data.p_adjusted.eq(0).any())
    check("raw P in range", data.p_raw.dropna().between(0, 1).all())
    check("adjusted P in range", data.p_adjusted.dropna().between(0, 1).all())
    check("tested rows have raw P", data.loc[data.status.eq("tested"), "p_raw"].notna().all())
    check("tested rows have actual n", data.loc[data.status.eq("tested"), "n_total"].notna().all())
    check("all source hashes recorded", data.source_sha256.notna().all())
    for source, group in data.groupby("source_file"):
        check(f"source exists: {source}", (REPO / source).is_file())
        check(f"source hash matches: {source}", group.source_sha256.eq(sha256(REPO / source)).all())
    for source, group in data.dropna(subset=["source_file_2"]).groupby("source_file_2"):
        check(f"secondary source exists: {source}", (REPO / source).is_file())
        check(f"secondary source hash matches: {source}", group.source_sha256_2.eq(sha256(REPO / source)).all())

    f2e = data[data.test_id.eq("Figure2E_exact_spearman")].iloc[0]
    f3e = data[data.test_id.eq("Figure3E_exact_spearman")].iloc[0]
    check("Figure2E rho", np.isclose(f2e.estimate, -0.8928571428571429))
    check("Figure2E exact P", np.isclose(f2e.p_raw, 62 / 5040))
    check("Figure2E enumeration", f2e.permutations_or_enumerations == 5040)
    check("Figure3E rho", np.isclose(f3e.estimate, 1.0))
    check("Figure3E exact P", np.isclose(f3e.p_raw, 2 / 5040))
    check("Figure3E enumeration", f3e.permutations_or_enumerations == 5040)

    s1c = data[data.test_id.eq("S1C_0.99")].iloc[0]
    check("S1C h=.99 actual n", s1c.n_group1 == 17 and s1c.n_group2 == 20)
    f6d = data[data.test_id.str.startswith("F6D_")].set_index("test_id")
    check("F6D P70 n", f6d.loc["F6D_P70", "n_group1"] == 14 and f6d.loc["F6D_P70", "n_group2"] == 20)
    check("F6D P85 structural NE", f6d.loc["F6D_P85", "status"] == "not estimable")
    check("F6D Holm family size", f6d.loc[["F6D_P70", "F6D_S70", "F6D_S85"], "p_adjusted"].notna().all())

    stability = pd.read_csv(OUT / "Table_S3.csv")
    check("Table S3 eight diagnostics", len(stability) == 8)
    check("Table S3 n=20 per model", stability.n_independent_simulations.eq(20).all())
    check("Table S3 Panmictic 2.5% failures", stability.query("condition_id == 'P70_L'").pass_epsilon_0p025.tolist() == [False, False, True, True])
    check("Table S3 all pass 5%", stability.pass_epsilon_0p05.all())
    check("Table S3 source provenance", stability.source_file.notna().all() and stability.source_sha256.notna().all())
    check("Table S3 script provenance", stability.analysis_script.notna().all() and stability.analysis_script_sha256.notna().all())
    script_path = REPO / stability.analysis_script.iloc[0]
    check("Table S3 normalized script hash", stability.analysis_script_sha256.eq(normalized_text_sha256(script_path)).all())

    figure4_coefficients = pd.read_csv(OUT / "Figure4_model_coefficients_HC3.csv")
    check("Figure4 coefficient P values nonzero", not figure4_coefficients.p_value.eq(0).any())
    figure4 = data[data.publication_item.eq("Figure 4")]
    check("Figure4 all tested rows actual n", figure4.loc[figure4.status.eq("tested"), ["n_group1", "n_group2", "n_total"]].notna().all().all())
    check("Figure4 dual input chain", figure4.source_file_2.notna().all() and figure4.source_sha256_2.notna().all())

    catalog = pd.read_csv(OUT / "statistics_catalog.csv")
    check("S2 descriptive catalog", catalog[catalog.record_id.isin(["S2A", "S2B"])].statistics_file.eq("not applicable").all())
    check("S4 catalog linked to Table S3", catalog[catalog.publication_item.eq("Supplementary Figure S4")].statistics_file.eq("results/statistics/Table_S3.csv").all())

    table_s2 = pd.read_csv(OUT / "Table_S2.csv")
    check("Table S2 is exact generated view", table_s2.equals(data[data.status.isin(["tested", "not estimable"])].reset_index(drop=True)))

    failed = [name for name, passed in checks if not passed]
    report = {"checks": len(checks), "failed": len(failed), "failures": failed}
    (OUT / "verification_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
