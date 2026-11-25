#!/usr/bin/env python3
"""Build data-driven redraws and pixel-exact final-deck figure pages."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO=Path(__file__).resolve().parents[2]


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--rebuilt-dir",type=Path,default=REPO/"results/figures/rebuilt")
    parser.add_argument("--submission-dir",type=Path,default=REPO/"results/figures/submission")
    args=parser.parse_args()
    subprocess.run([sys.executable,str(REPO/"scripts/plotting/render_final_figures.py"),"--figure","all",
                    "--output-dir",str(args.rebuilt_dir)],cwd=REPO,check=True)
    subprocess.run([sys.executable,str(REPO/"scripts/plotting/materialize_submission_figures.py"),
                    "--output-dir",str(args.submission_dir)],cwd=REPO,check=True)


if __name__ == "__main__":
    main()
