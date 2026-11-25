#!/usr/bin/env python3
"""Build canonical, repository-sized Source Data files.

The full SLiM stdout archives remain external.  This script copies already
validated processed sources, rebuilds the final-20-week S1/F2E/F3E endpoints
from the frozen raw lineages, and writes compact plot-level or replicate-level
tables.  It deliberately does not calculate inferential statistics; that is a
separate gated process.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import re
import shutil
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parents[1]
WORKSPACE = REPO.parent
FINAL = Path(r"D:/champer实验室工作/文章figure终版")
OUT = REPO / "data" / "source_data"
FILES = OUT / "files"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def nrows(path: Path) -> int:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8-sig", errors="replace") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def copy_source(source: Path, relative_target: str, *, gzip_csv: bool = False) -> Path:
    target = FILES / relative_target
    target.parent.mkdir(parents=True, exist_ok=True)
    if gzip_csv and source.suffix != ".gz":
        # ``gzip.open(path, "wb")`` embeds both the current time and the
        # output filename in the member header.  That made an otherwise
        # identical Source Data rebuild differ byte-for-byte on every run.
        # Use an explicitly anonymous member with a fixed timestamp so the
        # repository checksum is reproducible across machines and dates.
        with source.open("rb") as src, target.open("wb") as raw_target:
            with gzip.GzipFile(
                filename="",
                mode="wb",
                compresslevel=9,
                fileobj=raw_target,
                mtime=0,
            ) as dst:
                shutil.copyfileobj(src, dst)
    else:
        shutil.copy2(source, target)
    return target


def write_frame(
    frame: pd.DataFrame,
    relative_target: str,
    *,
    encoding: str = "utf-8-sig",
    lineterminator: str | None = None,
) -> Path:
    target = FILES / relative_target
    target.parent.mkdir(parents=True, exist_ok=True)
    compression = {"method": "gzip", "mtime": 0} if target.suffix == ".gz" else None
    frame.to_csv(
        target,
        index=False,
        encoding=encoding,
        compression=compression,
        lineterminator=lineterminator,
    )
    return target


def quantile_summary(data: pd.DataFrame, groups: list[str], metrics: list[str]) -> pd.DataFrame:
    records: list[dict] = []
    for keys, group in data.groupby(groups, sort=True, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        base = dict(zip(groups, keys))
        for metric in metrics:
            values = pd.to_numeric(group[metric], errors="coerce").dropna().to_numpy(float)
            if not len(values):
                continue
            records.append({
                **base,
                "metric": metric,
                "n": int(len(values)),
                "median": float(np.median(values)),
                "q05": float(np.quantile(values, 0.05)),
                "q25": float(np.quantile(values, 0.25)),
                "q75": float(np.quantile(values, 0.75)),
                "q95": float(np.quantile(values, 0.95)),
            })
    return pd.DataFrame.from_records(records)


def _finish_run(meta: dict, nni: list[tuple[float, float]], attrs: list[tuple[float, float, float]]) -> dict | None:
    if not nni and not attrs:
        return None
    row = dict(meta)
    if nni:
        end = max(x[0] for x in nni)
        values = [x[1] for x in nni if x[0] >= end - 20.0]
        row["final20_nni"] = float(np.mean(values)) if values else np.nan
        row["n_final20_nni_records"] = len(values)
        row["last_nni_week"] = end
    else:
        row.update(final20_nni=np.nan, n_final20_nni_records=0, last_nni_week=np.nan)
    if attrs:
        end = max(x[0] for x in attrs)
        kept = [(value, pop) for week, value, pop in attrs if week >= end - 20.0]
        values = np.asarray([x[0] for x in kept], float)
        weights = np.asarray([x[1] for x in kept], float)
        valid = np.isfinite(values) & np.isfinite(weights) & (weights >= 0)
        if valid.any() and weights[valid].sum() > 0:
            endpoint = float(np.average(values[valid], weights=weights[valid]))
        elif valid.any():
            endpoint = float(np.mean(values[valid]))
        else:
            endpoint = np.nan
        row["final20_attribute_weighted"] = endpoint
        row["n_final20_attribute_records"] = int(valid.sum())
        row["last_attribute_week"] = end
    else:
        row.update(
            final20_attribute_weighted=np.nan,
            n_final20_attribute_records=0,
            last_attribute_week=np.nan,
        )
    return row


def parse_spatial_raw(path: Path, *, setting: float, cohort: str, concatenated: bool) -> list[dict]:
    """Parse complete seed-delimited simulations and retain the declared blocks.

    Concatenated aggregate files use every complete seed block as a replicate.
    Files nominally representing one replicate use the last complete block.
    The latter rule is required for the 20 h=0.70 neutral Figure-2E files,
    where a superseded run was followed by an appended rerun in the same file.
    """
    rows: list[dict] = []
    nni: list[tuple[float, float]] = []
    attrs: list[tuple[float, float, float]] = []
    generation_time = 3.167
    area = 1.0
    current_pop = np.nan
    pending_attr: tuple[float, float] | None = None
    replicate_match = re.search(r"_(\d+)\.out$", path.name)
    file_replicate = int(replicate_match.group(1)) if replicate_match else 1
    replicate = 0
    block_index = 0
    seed = ""
    expecting_seed = False
    started = False

    def finish() -> None:
        nonlocal nni, attrs, pending_attr, replicate
        if not started:
            return
        row = _finish_run(
            {
                "setting": setting,
                "cohort": cohort,
                "replicate": replicate,
                "seed": seed,
                "source_file": path.name,
                "source_block_index": block_index,
            },
            nni,
            attrs,
        )
        if row is not None:
            rows.append(row)
        nni = []
        attrs = []
        pending_attr = None

    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for raw in handle:
            line = raw.strip()
            if line.startswith("// Initial random seed:"):
                if started:
                    finish()
                started = True
                block_index += 1
                replicate = block_index if concatenated else file_replicate
                generation_time = 3.167
                area = 1.0
                current_pop = np.nan
                seed = line.split(":", 1)[1].strip()
                expecting_seed = not bool(seed)
                continue
            if expecting_seed and re.fullmatch(r"\d+", line):
                seed = line
                expecting_seed = False
                continue
            if not started:
                continue
            if line.startswith("GENERATION TIME:"):
                generation_time = float(line.split(":", 1)[1])
            elif line.startswith("SIM BOUND:"):
                area = float(line.split(":", 1)[1])
            elif line.startswith("POPULATION_SIZE:"):
                current_pop = float(line.split(":", 1)[1])
            elif line.startswith("average attribute:"):
                pending_attr = (float(line.split(":", 1)[1]), current_pop)
            elif line.startswith("WT_ALLELES::"):
                parts = line.split()
                generation = int(parts[2])
                population = int(parts[3])
                ann = float(parts[6])
                if generation >= 21 and population > 0 and ann > 0:
                    week = (generation - 21) / generation_time
                    expected_ann = 0.5 * area / np.sqrt(population)
                    nni.append((week, ann / expected_ann))
                    if pending_attr is not None:
                        attrs.append((week, pending_attr[0], pending_attr[1]))
                pending_attr = None
    finish()
    for row in rows:
        row["source_block_count"] = len(rows)
        row["block_selection_rule"] = "all_seed_blocks" if concatenated else "last_complete_seed_block"
    return rows if concatenated else rows[-1:]


def build_raw_endpoints() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    s1_dir = FINAL / "figure1+2  (可靠）"
    s1_specs = [
        ("first drive without mutations.out", 0.70, "Neutral mutations"),
        ("first dirve with mutations.out", 0.70, "Variable mutations"),
        ("second drive without mutations.out", 0.85, "Neutral mutations"),
        ("second drive with mutations.out", 0.85, "Variable mutations"),
    ]
    s1_rows: list[dict] = []
    for name, setting, cohort in s1_specs:
        s1_rows.extend(parse_spatial_raw(s1_dir / name, setting=setting, cohort=cohort, concatenated=True))

    f2_dir = FINAL / "figure3 (待补充erMut）" / "rerun_logs" / "panelE_logs14" / "logs14"
    f2_rows: list[dict] = []
    for cohort, pattern in [
        ("Neutral mutations", "raw_fig3F_er_spt_control_h*.out"),
        ("Variable mutations", "raw_fig3F_er_spt_functional_h*.out"),
    ]:
        for path in sorted(f2_dir.glob(pattern)):
            match = re.search(r"_h(0\.\d+)", path.name)
            if match:
                f2_rows.extend(parse_spatial_raw(path, setting=float(match.group(1)), cohort=cohort, concatenated=False))

    f3_dir = FINAL / "figure4（全部缺失）" / "rerun_logs" / "logs4"
    f3_rows: list[dict] = []
    for cohort, pattern in [
        ("Neutral mutations", "spatial_control_h*.out"),
        ("Variable mutations", "spatial_nocontrol_h*.out"),
    ]:
        for path in sorted(f3_dir.glob(pattern)):
            if path.name.startswith("raw_"):
                continue
            match = re.search(r"_h(0\.\d+)", path.name)
            if match:
                f3_rows.extend(parse_spatial_raw(path, setting=float(match.group(1)), cohort=cohort, concatenated=False))

    return pd.DataFrame(s1_rows), pd.DataFrame(f2_rows), pd.DataFrame(f3_rows)


def build() -> list[dict]:
    OUT.mkdir(parents=True, exist_ok=True)
    FILES.mkdir(parents=True, exist_ok=True)
    created: list[tuple[Path, str, str]] = []

    def add(path: Path, panels: str, table_type: str) -> None:
        created.append((path, panels, table_type))

    direct = [
        ("Figure1/endpoint_replicates.csv", "Figure 1A", "replicate", WORKSPACE / "文章终稿数据/Figure2/processed_source/Figure2_source_endpoint_simulation_level.csv", False),
        ("Figure1/final20_replicates.csv", "Figure 1B-C", "replicate", WORKSPACE / "new_main_figure_task/final20_attribute_panels_20261024/Figure2_final20_source.csv", False),
        ("Figure1/nni_plot_summary.csv", "Figure 1D", "plot-summary", WORKSPACE / "文章终稿数据/Figure2/processed_source/Figure2_source_panelB_NNI_summary.csv", False),
        ("Figure2/endpoint_replicates.csv", "Figure 2A", "replicate", WORKSPACE / "文章终稿数据/Figure3/processed_source/Figure3_source_endpoint_simulation_level.csv", False),
        ("Figure2/final20_replicates.csv", "Figure 2B-C", "replicate", WORKSPACE / "new_main_figure_task/final20_attribute_panels_20261024/Figure3_final20_source.csv", False),
        ("Figure2/nni_replicate_trajectories.csv.gz", "Figure 2D", "replicate-trajectory", WORKSPACE / "文章终稿数据/Figure3/processed_source/Figure3_source_panelC_trajectory_simulation_level.csv.gz", False),
        ("Figure3/final20_replicates.csv", "Figure 3A-C", "replicate", WORKSPACE / "new_main_figure_task/final20_attribute_panels_20261024/Figure4_final20_source_100rep.csv", False),
        ("Figure3/nni_replicate_trajectories.csv.gz", "Figure 3D", "replicate-trajectory", WORKSPACE / "文章终稿数据/Figure4/processed_source_final/Figure4_source_panelC_trajectory_simulation_level.csv.gz", False),
        ("Figure4/simulation_level_source.csv", "Figure 4A-C", "replicate", WORKSPACE / "文章终稿数据/Figure5/processed_source_final/Figure5_simulation_level_source.csv", False),
        ("Figure5/source_data_per_run.csv", "Figure 5A-B", "replicate", WORKSPACE / "new_main_figure_task/figure7_final20_all_outcomes_warmB_20261024_v5/source_data_per_run.csv", False),
        ("Figure6/panelA_replicates.csv", "Figure 6A", "replicate", WORKSPACE / "文章终稿数据/Figure6/retest_20rep_20260914_final/processed/Figure6_panelA_source_data.csv", False),
        ("Figure6/panelB_outcome_summary.csv", "Figure 6B", "plot-summary", WORKSPACE / "文章终稿数据/Figure6/retest_20rep_20260914_final/processed/Figure6_panelB_source_data.csv", False),
        ("Figure6/panelC_replicate_trajectories.csv.gz", "Figure 6C", "replicate-trajectory", WORKSPACE / "文章终稿数据/Figure6/retest_20rep_20260914_final/processed/Figure6_panelC_trajectory_source_data.csv", True),
        ("Figure6/panelD_final20_replicates.csv", "Figure 6D", "replicate", WORKSPACE / "文章终稿数据/Figure6/retest_20rep_20260914_final/processed/Figure6_panelD_source_data.csv", False),
        ("Figure4/architecture_parameter_metadata.csv", "Figure 4A-C", "parameter-metadata", WORKSPACE / "文章终稿数据/Supplementary/Figure S2/data/Figure_S2_simulation_level_source.csv", False),
        ("Figure_S4/pre_release_block_replicates.csv", "Supplementary Figure S4A-D; Supplementary Table S3", "replicate-block", WORKSPACE / "single_panel_outputs/S4_recreated/S4_pre_release_blocks_revised.csv", False),
        ("Table_S1/parameter_definitions.csv", "Supplementary Table S1", "parameter", WORKSPACE / "supplementary_final/Supplementary_Table_S1.csv", False),
    ]
    for target, panels, table_type, source, compress in direct:
        path = copy_source(source, target, gzip_csv=compress)
        add(path, panels, table_type)

    s1a, f2e, f3e = build_raw_endpoints()
    for frame, target, panels in [
        (s1a, "Figure_S1/panelA_final20_replicates.csv", "Supplementary Figure S1A"),
        (f2e, "Figure2/panelE_final20_replicates.csv", "Figure 2E"),
        (f2e, "Figure_S1/panelB_final20_replicates.csv", "Supplementary Figure S1B"),
        (f3e, "Figure3/panelE_final20_replicates.csv", "Figure 3E"),
        (f3e, "Figure_S1/panelC_final20_replicates.csv", "Supplementary Figure S1C"),
    ]:
        path = write_frame(frame, target)
        add(path, panels, "replicate")

    s2_outcomes = pd.DataFrame([
        {"figure": figure, "setting": setting, "cohort": cohort,
         "long_term_persistence": 20, "population_elimination": 0}
        for figure in ["Figure 2E", "Figure 3E"]
        for setting in ["0.70", "0.75", "0.80", "0.85", "0.90", "0.95", "Emp"]
        for cohort in ["Neutral mutations", "Variable mutations"]
    ])
    # This small table is byte-locked as UTF-8 without BOM and LF line endings
    # so its catalog checksum is identical on Windows, macOS and Linux.
    path = write_frame(
        s2_outcomes,
        "Figure_S2/outcome_composition.csv",
        encoding="utf-8",
        lineterminator="\n",
    )
    add(path, "Supplementary Figure S2A-B", "outcome-count")

    s3_source = WORKSPACE / "supplementary_final/source_data/S3_reference_per_run.csv"
    s3 = pd.read_csv(s3_source, usecols=[
        "arch", "run", "tick", "dispersal_change_pct", "dispersal_sd_ratio",
        "he_over_initial", "segregating_over_initial", "adult_N_ratio",
        "fertile_female_N_ratio", "n_age_gt0", "n_fertile_females",
    ])
    s3 = s3[s3["tick"].between(1, 1600)].copy()
    path = write_frame(s3, "Figure_S3/replicate_trajectories.csv.gz")
    add(path, "Supplementary Figure S3A-F", "replicate-trajectory")
    s3_summary = quantile_summary(
        s3,
        ["arch", "tick"],
        ["dispersal_change_pct", "dispersal_sd_ratio", "he_over_initial", "segregating_over_initial", "adult_N_ratio", "fertile_female_N_ratio"],
    )
    path = write_frame(s3_summary, "Figure_S3/plot_summary.csv")
    add(path, "Supplementary Figure S3A-F", "plot-summary")

    trajectory_source = WORKSPACE / "supplementary_final/source_data/S3_S4_S5_trajectory_values.csv"
    usecols = [
        "condition_id", "model", "drive_conversion", "load", "replicate", "seed",
        "week_relative_release", "N_total", "B", "mean_Wload", "mutation_copies_per_individual",
    ]
    trajectories = pd.read_csv(trajectory_source, usecols=usecols)
    trajectories = trajectories[trajectories["week_relative_release"].between(0, 1500)].copy()

    s5 = trajectories[trajectories["condition_id"].isin(["P70_L", "S70_L", "S85_L"])].copy()
    s5_summary = quantile_summary(
        s5,
        ["condition_id", "week_relative_release"],
        ["B", "mutation_copies_per_individual", "mean_Wload"],
    )
    path = write_frame(s5_summary, "Figure_S5/plot_summary.csv.gz")
    add(path, "Supplementary Figure S5A-C", "plot-summary")
    final20 = []
    for keys, group in s5.groupby(["condition_id", "replicate", "seed"], sort=True):
        end = group["week_relative_release"].max()
        tail = group.sort_values("week_relative_release").tail(20)
        final20.append({
            "condition_id": keys[0], "replicate": keys[1], "seed": keys[2],
            "final20_B": tail["B"].mean(),
            "final20_mutation_copies_per_individual": tail["mutation_copies_per_individual"].mean(),
            "final20_mean_Wload": tail["mean_Wload"].mean(),
            "n_final20_records": len(tail),
        })
    path = write_frame(pd.DataFrame(final20), "Figure_S5/replicate_final20_summary.csv")
    add(path, "Supplementary Figure S5A-C", "replicate")

    s6_conditions = ["P70_L", "P70_N", "S70_L", "S70_N", "S85_L", "S85_N"]
    s6 = trajectories[trajectories["condition_id"].isin(s6_conditions)][
        ["condition_id", "model", "drive_conversion", "load", "replicate", "seed", "week_relative_release", "N_total"]
    ].copy()
    path = write_frame(s6, "Figure_S6/replicate_trajectories.csv.gz")
    add(path, "Supplementary Figure S6A-B", "replicate-trajectory")

    catalog: list[dict] = []
    for path, panels, table_type in created:
        with (gzip.open(path, "rt", encoding="utf-8-sig") if path.suffix == ".gz" else path.open("r", encoding="utf-8-sig")) as handle:
            header = next(csv.reader(handle), [])
        catalog.append({
            "repository_path": path.relative_to(REPO).as_posix(),
            "publication_scope": panels,
            "table_type": table_type,
            "row_count": nrows(path),
            "column_count": len(header),
            "sha256": sha256(path),
        })
    catalog_path = OUT / "source_data_catalog.csv"
    pd.DataFrame(catalog).sort_values(["publication_scope", "repository_path"]).to_csv(
        catalog_path, index=False, encoding="utf-8-sig"
    )
    return catalog


if __name__ == "__main__":
    result = build()
    print(f"wrote {len(result)} canonical Source Data tables under {FILES}")
