#!/usr/bin/env python3
"""Machine-check canonical Source Data, key sample counts and provenance."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
SOURCE = DATA / "source_data"
FILES = SOURCE / "files"


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


def counts(frame: pd.DataFrame, groups: list[str], unit: str) -> dict[str, int]:
    grouped = frame.groupby(groups, dropna=False)[unit].nunique()
    return {"|".join(map(str, key if isinstance(key, tuple) else (key,))): int(value) for key, value in grouped.items()}


checks: list[dict] = []


def check(name: str, observed, expected) -> None:
    checks.append({"check": name, "observed": observed, "expected": expected, "pass": observed == expected})


catalog = pd.read_csv(SOURCE / "source_data_catalog.csv")
for row in catalog.itertuples(index=False):
    path = REPO / row.repository_path
    check(f"exists:{row.repository_path}", path.exists(), True)
    if path.exists():
        check(f"rows:{row.repository_path}", nrows(path), int(row.row_count))
        check(f"sha256:{row.repository_path}", sha256(path), row.sha256)

f2e = pd.read_csv(FILES / "Figure2/panelE_final20_replicates.csv")
check(
    "Figure2E setting/cohort counts",
    counts(f2e, ["setting", "cohort"], "source_file"),
    {f"{setting}|{cohort}": 20 for setting in [0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99] for cohort in ["Neutral mutations", "Variable mutations"]},
)
f2e_double = f2e[f2e["setting"].eq(0.70) & f2e["cohort"].eq("Neutral mutations")]
f2e_single = f2e.drop(f2e_double.index)
check("Figure2E h0.70 neutral source block count", sorted(f2e_double.source_block_count.unique().tolist()), [2])
check("Figure2E h0.70 neutral selected block", sorted(f2e_double.source_block_index.unique().tolist()), [2])
check("Figure2E other source block count", sorted(f2e_single.source_block_count.unique().tolist()), [1])
check("Figure2E final20 NNI records", sorted(f2e.n_final20_nni_records.unique().tolist()), [64])
check("Figure2E final20 attribute records", sorted(f2e.n_final20_attribute_records.unique().tolist()), [64])

f3e = pd.read_csv(FILES / "Figure3/panelE_final20_replicates.csv")
expected_f3e = {f"{setting}|{cohort}": 20 for setting in [0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99] for cohort in ["Neutral mutations", "Variable mutations"]}
expected_f3e["0.99|Variable mutations"] = 17
check("Figure3E setting/cohort counts", counts(f3e, ["setting", "cohort"], "source_file"), expected_f3e)

s1a = pd.read_csv(FILES / "Figure_S1/panelA_final20_replicates.csv")
check(
    "FigureS1A setting/cohort counts",
    counts(s1a, ["setting", "cohort"], "replicate"),
    {
        "0.7|Neutral mutations": 99,
        "0.7|Variable mutations": 100,
        "0.85|Neutral mutations": 93,
        "0.85|Variable mutations": 100,
    },
)

f6c = pd.read_csv(FILES / "Figure6/panelC_replicate_trajectories.csv.gz")
check(
    "Figure6C replicate counts",
    counts(f6c, ["condition_id"], "replicate"),
    {"P70_L": 14, "S70_L": 20, "S85_L": 20},
)
f6d = pd.read_csv(FILES / "Figure6/panelD_final20_replicates.csv")
check(
    "Figure6D replicate counts",
    counts(f6d, ["condition_id"], "replicate"),
    {"P70_L": 14, "P70_N": 20, "S70_L": 20, "S70_N": 20, "S85_L": 20, "S85_N": 20},
)

s5 = pd.read_csv(FILES / "Figure_S5/replicate_final20_summary.csv")
check("FigureS5 replicate counts", counts(s5, ["condition_id"], "replicate"), {"P70_L": 20, "S70_L": 20, "S85_L": 20})
check("FigureS5 final20 record counts", sorted(s5.n_final20_records.unique().tolist()), [20])
s6 = pd.read_csv(FILES / "Figure_S6/replicate_trajectories.csv.gz")
check(
    "FigureS6 replicate counts",
    counts(s6, ["condition_id"], "replicate"),
    {"P70_L": 20, "P70_N": 20, "S70_L": 20, "S70_N": 20, "S85_L": 20, "S85_N": 20},
)
s6_final20 = pd.read_csv(SOURCE / "workbook_tables/Figure_S6/Replicate_final20.csv")
check("FigureS6 final20 record counts", sorted(s6_final20.n_final20_records.unique().tolist()), [20])

provenance = pd.read_csv(DATA / "external_raw_file_manifest.csv.gz")
check("provenance included files", int((provenance.selection_status == "included").sum()), 580)
check("provenance excluded zero-byte files", int((provenance.selection_status == "excluded_zero_byte").sum()), 3)
check("provenance excluded files are zero bytes", bool((provenance.loc[provenance.selection_status == "excluded_zero_byte", "size_bytes"] == 0).all()), True)

public_ready = bool(provenance.retrieval_uri.notna().all() and provenance.retrieval_uri.astype(str).str.strip().ne("").all())
report = {
    "checks": checks,
    "failed_checks": [item["check"] for item in checks if not item["pass"]],
    "public_external_archive_ready": public_ready,
    "retrieval_uri_policy": (
        "public_uri_recorded" if public_ready else "intentionally_omitted"
    ),
    "retrieval_uri_required_for_acceptance": False,
    "public_archive_blocker": None,
}
(SOURCE / "source_data_qa.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"checks={len(checks)} failed={len(report['failed_checks'])} public_external_archive_ready={public_ready}")
if report["failed_checks"]:
    raise SystemExit(1)
