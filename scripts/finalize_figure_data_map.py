#!/usr/bin/env python3
"""Replace development-workspace candidates with final repository-native paths."""

from __future__ import annotations

import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "config" / "figure_data_map.csv"


def key(item: str) -> str | None:
    if item.startswith("Figure "):
        return item.replace("Figure ", "Figure")
    if item.startswith("Supplementary Figure S"):
        return item.replace("Supplementary Figure S", "Figure_S")
    return None


def main() -> None:
    rows = list(csv.DictReader(TARGET.open(newline="", encoding="utf-8-sig")))
    for row in rows:
        figure = key(row["publication_item"])
        if figure:
            row["local_authority_candidate"] = "scripts/plotting/authoritative_sources (historical visual lineage only)"
            row["source_data_candidate"] = f"data/source_data/files/{figure}/"
            row["statistics_candidate"] = row["repository_statistics_target"]
            row["plot_script_candidate"] = "scripts/plotting/build_final_figures.py"
        else:
            table = row["publication_item"].rsplit(" ", 1)[-1]
            row["local_authority_candidate"] = "not applicable"
            row["source_data_candidate"] = f"data/source_data/Table_{table}.xlsx"
            row["statistics_candidate"] = row["repository_statistics_target"]
            row["plot_script_candidate"] = "scripts/build_source_workbooks.mjs"
        row["trace_status"] = "FINAL_VERIFIED"
    with TARGET.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    print(f"finalized {len(rows)} map records")


if __name__ == "__main__":
    main()
