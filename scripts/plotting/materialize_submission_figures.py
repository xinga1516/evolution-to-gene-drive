#!/usr/bin/env python3
"""Materialize the pixel-exact final-deck figure pages from frozen references."""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MAP = REPO / "config" / "submission_visual_map.csv"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",type=Path,default=REPO/"results/figures/submission")
    args=parser.parse_args(); output=args.output_dir.resolve(); output.mkdir(parents=True,exist_ok=True)
    rows=list(csv.DictReader(MAP.open(newline="",encoding="utf-8-sig")))
    copied=0
    for row in rows:
        if not row["publication_item"].startswith(("Figure ","Supplementary Figure ")):
            continue
        source=REPO/row["visual_reference"]
        if digest(source) != row["visual_reference_sha256"]:
            raise RuntimeError(f"visual reference hash mismatch: {source}")
        target=output/source.name
        shutil.copyfile(source,target)
        copied += 1
    print(f"materialized {copied} locked submission figures")


if __name__ == "__main__":
    main()
