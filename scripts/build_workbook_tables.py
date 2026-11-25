#!/usr/bin/env python3
"""Create compact CSV tables that are embedded in Source Data workbooks.

Large exact replicate trajectories stay in ``data/source_data/files`` as
compressed CSV.  Workbooks contain the simulation-level endpoints and the
plot-level summaries needed for convenient inspection, plus an index pointing
to every exact trajectory table.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "data" / "source_data"
FILES = SOURCE / "files"
STAGING = SOURCE / "workbook_tables"


def quantiles(data: pd.DataFrame, groups: list[str], value: str) -> pd.DataFrame:
    grouped = data.groupby(groups, sort=True, dropna=False)[value]
    return grouped.agg(
        n="count",
        median="median",
        q05=lambda x: x.quantile(0.05),
        q25=lambda x: x.quantile(0.25),
        q75=lambda x: x.quantile(0.75),
        q95=lambda x: x.quantile(0.95),
    ).reset_index()


def write(book: str, sheet: str, frame: pd.DataFrame) -> str:
    folder = STAGING / book
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{sheet}.csv"
    frame.to_csv(path, index=False, encoding="utf-8-sig")
    return path.relative_to(REPO).as_posix()


def compact_figure2_endpoint() -> pd.DataFrame:
    data = pd.read_csv(FILES / "Figure2/endpoint_replicates.csv")
    data["replicate"] = data.groupby(["model_std", "h", "treatment"]).cumcount() + 1
    columns = [
        "model_std", "h", "treatment", "replicate", "outcome", "elimination",
        "persistence", "final_embryo_resistance", "n_over_k", "source_record_id",
    ]
    return data[columns]


def trajectory_summary(path: Path, extra_groups: list[str]) -> pd.DataFrame:
    data = pd.read_csv(path, usecols=[*extra_groups, "week", "nni"])
    summary = quantiles(data, [*extra_groups, "week"], "nni")
    # The exact every-week table remains in files/*.csv.gz.  The workbook is a
    # convenient decimated inspection table, retaining the first, last and
    # every tenth plotted time record within each curve.
    kept = []
    for _, group in summary.groupby(extra_groups, sort=False):
        group = group.sort_values("week")
        index = sorted(set([0, len(group) - 1, *range(0, len(group), 10)]))
        kept.append(group.iloc[index])
    return pd.concat(kept, ignore_index=True)


def final20_population_summary() -> pd.DataFrame:
    data = pd.read_csv(
        FILES / "Figure_S6/replicate_trajectories.csv.gz",
        usecols=["condition_id", "replicate", "seed", "week_relative_release", "N_total"],
    )
    records = []
    for keys, group in data.groupby(["condition_id", "replicate", "seed"], sort=True):
        end = group["week_relative_release"].max()
        tail = group.sort_values("week_relative_release").tail(20)
        records.append({
            "condition_id": keys[0],
            "replicate": keys[1],
            "seed": keys[2],
            "final20_population_mean": tail["N_total"].mean(),
            "n_final20_records": len(tail),
            "last_week": end,
        })
    return pd.DataFrame(records)


def build() -> dict:
    STAGING.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, list[dict]] = {}

    def add(book: str, sheet: str, frame: pd.DataFrame, scope: str) -> None:
        path = write(book, sheet, frame)
        manifest.setdefault(book, []).append({
            "sheet": sheet,
            "path": path,
            "rows": len(frame),
            "columns": len(frame.columns),
            "scope": scope,
        })

    f1a = pd.read_csv(FILES / "Figure1/endpoint_replicates.csv")
    add("Figure1", "Panel_A", f1a[[
        "model", "conversion", "treatment", "record_index_in_source", "elimination",
        "drive_loss", "persistence", "source_record_id",
    ]], "Figure 1A")
    add("Figure1", "Panels_B_C", pd.read_csv(FILES / "Figure1/final20_replicates.csv"), "Figure 1B-C")
    f1d = pd.read_csv(FILES / "Figure1/nni_plot_summary.csv")
    f1d_kept = []
    for _, group in f1d.groupby(["conversion", "treatment"], sort=False):
        group = group.sort_values("week")
        index = sorted(set([0, len(group) - 1, *range(0, len(group), 10)]))
        f1d_kept.append(group.iloc[index])
    add("Figure1", "Panel_D", pd.concat(f1d_kept, ignore_index=True), "Figure 1D (decimated workbook view; exact table in files/)")

    add("Figure2", "Panel_A", compact_figure2_endpoint(), "Figure 2A")
    add("Figure2", "Panels_B_C", pd.read_csv(FILES / "Figure2/final20_replicates.csv"), "Figure 2B-C")
    add("Figure2", "Panel_D", trajectory_summary(
        FILES / "Figure2/nni_replicate_trajectories.csv.gz", ["model", "h", "treatment"]
    ), "Figure 2D")
    add("Figure2", "Panel_E", pd.read_csv(FILES / "Figure2/panelE_final20_replicates.csv"), "Figure 2E")

    add("Figure3", "Panels_A_C", pd.read_csv(FILES / "Figure3/final20_replicates.csv"), "Figure 3A-C")
    add("Figure3", "Panel_D", trajectory_summary(
        FILES / "Figure3/nni_replicate_trajectories.csv.gz", ["model", "h", "treatment"]
    ), "Figure 3D")
    add("Figure3", "Panel_E", pd.read_csv(FILES / "Figure3/panelE_final20_replicates.csv"), "Figure 3E")

    add("Figure4", "Panels_A_C", pd.read_csv(FILES / "Figure4/simulation_level_source.csv"), "Figure 4A-C")
    add("Figure5", "Panels_A_B", pd.read_csv(FILES / "Figure5/source_data_per_run.csv"), "Figure 5A-B")

    add("Figure6", "Panel_A", pd.read_csv(FILES / "Figure6/panelA_replicates.csv"), "Figure 6A")
    add("Figure6", "Panel_B", pd.read_csv(FILES / "Figure6/panelB_outcome_summary.csv"), "Figure 6B")
    f6c = pd.read_csv(
        FILES / "Figure6/panelC_replicate_trajectories.csv.gz",
        usecols=["condition_id", "week_relative_release", "B"],
    )
    f6c = f6c[f6c["week_relative_release"].between(0, 1500)]
    f6c = f6c[(f6c["week_relative_release"] % 10).eq(0)]
    add("Figure6", "Panel_C", quantiles(f6c, ["condition_id", "week_relative_release"], "B"), "Figure 6C")
    add("Figure6", "Panel_D", pd.read_csv(FILES / "Figure6/panelD_final20_replicates.csv"), "Figure 6D")

    for sheet, name in [("Panel_A", "panelA"), ("Panel_B", "panelB"), ("Panel_C", "panelC")]:
        add("Figure_S1", sheet, pd.read_csv(FILES / f"Figure_S1/{name}_final20_replicates.csv"), f"Supplementary Figure S1{sheet[-1]}")
    s2 = pd.read_csv(FILES / "Figure_S2/outcome_composition.csv")
    add("Figure_S2", "Panels_A_B", s2, "Supplementary Figure S2A-B")
    s3 = pd.read_csv(FILES / "Figure_S3/plot_summary.csv")
    add("Figure_S3", "Panels_A_F", s3[(s3["tick"] % 10).eq(0)], "Supplementary Figure S3A-F (decimated workbook view; exact table in files/)")
    add("Figure_S4", "Panels_A_D", pd.read_csv(FILES / "Figure_S4/pre_release_block_replicates.csv"), "Supplementary Figure S4A-D")

    s5 = pd.read_csv(FILES / "Figure_S5/plot_summary.csv.gz")
    for metric, sheet in [
        ("B", "Panel_A"),
        ("mutation_copies_per_individual", "Panel_B"),
        ("mean_Wload", "Panel_C"),
    ]:
        view = s5[s5["metric"].eq(metric)].copy()
        view = view[(view["week_relative_release"] % 10).eq(0)]
        add("Figure_S5", sheet, view, f"Supplementary Figure S5{sheet[-1]} (decimated workbook view; exact table in files/)")
    add("Figure_S5", "Replicate_final20", pd.read_csv(FILES / "Figure_S5/replicate_final20_summary.csv"), "Supplementary Figure S5A-C")

    add("Figure_S6", "Replicate_final20", final20_population_summary(), "Supplementary Figure S6A-B")
    add("Table_S1", "Parameters", pd.read_csv(FILES / "Table_S1/parameter_definitions.csv"), "Supplementary Table S1")
    add("Table_S3", "Stability_inputs", pd.read_csv(FILES / "Figure_S4/pre_release_block_replicates.csv"), "Supplementary Table S3")
    statistics = REPO / "results" / "statistics"
    table_s2 = statistics / "Table_S2.csv"
    table_s3 = statistics / "Table_S3.csv"
    if not table_s2.is_file() or not table_s3.is_file():
        raise FileNotFoundError(
            "Run scripts/compute_final_statistics.py before building Table S2/S3 workbooks"
        )
    add("Table_S2", "All_P_values", pd.read_csv(table_s2), "Supplementary Table S2")
    add("Table_S3", "Stability_diagnostics", pd.read_csv(table_s3), "Supplementary Table S3")

    path = SOURCE / "workbook_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote workbook staging tables for {len(manifest)} workbooks")
    return manifest


if __name__ == "__main__":
    build()
