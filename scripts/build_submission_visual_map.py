#!/usr/bin/env python3
"""Freeze the final-deck slide mapping and hashes used for visual QA."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "config" / "submission_visual_map.csv"
DECK_NAME = "Figures _修改提交(1).pptx"
DECK_SHA256 = "87beaa2c79f58bda6889e18b60847a4e217a5d53f2761dbc1f12ecc459a970e1"
MAPPING = [
    ("Figure 1", 1, "Figure1.png"), ("Figure 2", 3, "Figure2.png"),
    ("Figure 3", 5, "Figure3.png"), ("Figure 4", 7, "Figure4.png"),
    ("Figure 5", 9, "Figure5.png"), ("Figure 6", 10, "Figure6.png"),
    ("Supplementary Figure S1", 14, "Figure_S1.png"),
    ("Supplementary Figure S2", 15, "Figure_S2.png"),
    ("Supplementary Figure S3", 16, "Figure_S3.png"),
    ("Supplementary Figure S4", 17, "Figure_S4.png"),
    ("Supplementary Figure S5", 18, "Figure_S5.png"),
    ("Supplementary Figure S6", 19, "Figure_S6.png"),
    ("Supplementary Table S1", 20, "Table_S1_1.png"),
    ("Supplementary Table S1", 21, "Table_S1_2.png"),
    ("Supplementary Table S1", 22, "Table_S1_3.png"),
    ("Supplementary Table S1", 23, "Table_S1_4.png"),
    ("Supplementary Table S3", 24, "Table_S3.png"),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    rows=[]
    for item, slide, filename in MAPPING:
        rel=Path("docs/visual_references/submission_slides") / filename
        rows.append({"publication_item":item,"source_deck_filename":DECK_NAME,
                     "source_deck_sha256":DECK_SHA256,"slide_number":slide,
                     "visual_reference":rel.as_posix(),"visual_reference_sha256":digest(REPO/rel),
                     "status":"LOCKED_FINAL"})
    with OUT.open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]),lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    print(f"wrote {OUT.relative_to(REPO)}: {len(rows)} references")


if __name__ == "__main__":
    main()
