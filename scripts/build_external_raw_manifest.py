#!/usr/bin/env python3
"""Hash the exact external inputs selected by the frozen lineage manifest."""

from __future__ import annotations

import csv
import gzip
import hashlib
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[1]
WORKSPACE = REPO.parent
LINEAGE = REPO / "config" / "raw_lineage_manifest.csv"
OUTPUT = REPO / "data" / "external_raw_file_manifest.csv.gz"


def sha256_and_seed_blocks(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    marker = b"// Initial random seed:"
    seed_blocks = 0
    carry = b""
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
            seed_blocks += (carry + block).count(marker)
            carry = block[-(len(marker) - 1):]
    return digest.hexdigest(), seed_blocks


def resolve(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else WORKSPACE / path


def selected_files(dataset_id: str, root: Path) -> list[tuple[Path, str]]:
    if root.is_file():
        return [(root, "included")]
    if dataset_id == "F2E_S1B":
        files = [
            *root.glob("raw_fig3F_er_spt_control_h*.out"),
            *root.glob("raw_fig3F_er_spt_functional_h*.out"),
        ]
        return [(path, "included") for path in sorted(files)]
    if dataset_id == "F3E_S1C":
        files = [
            *root.glob("spatial_control_h*.out"),
            *root.glob("spatial_nocontrol_h*.out"),
        ]
        files = [path for path in files if not path.name.startswith("raw_")]
        return [
            (path, "included" if path.stat().st_size else "excluded_zero_byte")
            for path in sorted(files)
        ]
    if dataset_id == "S1A":
        names = [
            "first drive without mutations.out",
            "first dirve with mutations.out",
            "second drive without mutations.out",
            "second drive with mutations.out",
        ]
        return [(root / name, "included") for name in names]
    raise ValueError(f"No explicit selection rule implemented for directory dataset {dataset_id}: {root}")


def build() -> pd.DataFrame:
    with LINEAGE.open("r", encoding="utf-8-sig", newline="") as handle:
        lineage = list(csv.DictReader(handle))

    records: list[dict] = []
    for row in lineage:
        root = resolve(row["external_or_workspace_path"])
        if not root.exists():
            raise FileNotFoundError(f"{row['dataset_id']}: {root}")
        for path, selection_status in selected_files(row["dataset_id"], root):
            if not path.exists():
                raise FileNotFoundError(f"{row['dataset_id']}: {path}")
            size = path.stat().st_size
            file_sha256, seed_blocks = sha256_and_seed_blocks(path) if size else (hashlib.sha256(b"").hexdigest(), 0)
            if row["dataset_id"] == "F2E_S1B":
                retained_blocks = 1
                block_selection_rule = "last_complete_seed_block"
            elif row["dataset_id"] == "F3E_S1C":
                retained_blocks = 1 if selection_status == "included" else 0
                block_selection_rule = "only_complete_seed_block"
            elif row["dataset_id"] == "S1A":
                retained_blocks = seed_blocks
                block_selection_rule = "all_seed_blocks"
            else:
                retained_blocks = ""
                block_selection_rule = "entire_file"
            records.append({
                "dataset_id": row["dataset_id"],
                "publication_scope": row["publication_scope"],
                "declared_root": row["external_or_workspace_path"],
                "selected_file": path.name,
                "selection_status": selection_status,
                "size_bytes": size,
                "sha256": file_sha256,
                "seed_blocks_detected": seed_blocks if path.suffix.lower() == ".out" else "",
                "retained_seed_blocks": retained_blocks,
                "block_selection_rule": block_selection_rule,
                "retrieval_uri": "",
                "availability_status": "local_verified_external_deposit_pending",
            })

    frame = pd.DataFrame.from_records(records).sort_values(
        ["dataset_id", "selected_file"], kind="stable"
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUTPUT, "wt", encoding="utf-8-sig", newline="") as handle:
        frame.to_csv(handle, index=False)
    print(
        f"wrote {len(frame)} rows; included={(frame.selection_status == 'included').sum()}; "
        f"excluded_zero_byte={(frame.selection_status == 'excluded_zero_byte').sum()}"
    )
    return frame


if __name__ == "__main__":
    build()
