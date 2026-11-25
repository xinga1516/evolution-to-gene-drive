#!/usr/bin/env python3
"""Verify manifest hashes and deterministic clean-path figure rendering."""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "config" / "figure_plot_manifest.csv"
WINDOWS_ABSOLUTE = re.compile(r"(?:^|[;= ])(?:[A-Za-z]:[/\\])")


def sha256(path: Path, normalize_text: bool = False) -> str:
    payload = path.read_bytes()
    if normalize_text:
        payload = payload.replace(b"\r\n", b"\n")
    return hashlib.sha256(payload).hexdigest()


def check_pack(value: str, normalize_text: bool = False) -> list[str]:
    failures: list[str] = []
    if value == "not applicable":
        return failures
    for pair in value.split(";"):
        path_text, expected = pair.rsplit("=", 1)
        path = REPO / path_text
        if not path.is_file():
            failures.append(f"missing {path_text}")
        elif sha256(path, normalize_text) != expected:
            failures.append(f"hash mismatch {path_text}")
    return failures


def pack_hashes(value: str) -> set[str]:
    if value == "not applicable":
        return set()
    return {pair.rsplit("=", 1)[1] for pair in value.split(";")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-rerender", action="store_true")
    args = parser.parse_args()
    rows = list(csv.DictReader(MANIFEST.open(newline="", encoding="utf-8-sig")))
    failures: list[str] = []
    if len(rows) != 45:
        failures.append(f"manifest row count {len(rows)} != 45")
    if len({row["record_id"] for row in rows}) != len(rows):
        failures.append("duplicate record_id")
    for row in rows:
        joined = " ".join(row.values())
        if WINDOWS_ABSOLUTE.search(joined):
            failures.append(f"{row['record_id']}: absolute path in manifest")
        failures.extend(f"{row['record_id']}: {item}" for item in check_pack(row["source_files_sha256"]))
        failures.extend(f"{row['record_id']}: {item}" for item in check_pack(row["statistics_files_sha256"]))
        failures.extend(f"{row['record_id']}: {item}" for item in check_pack(row["output_files_sha256"]))
        failures.extend(f"{row['record_id']}: {item}" for item in check_pack(row["reconstructed_output_files_sha256"]))
        script = REPO / row["script_path"]
        if not script.is_file() or sha256(script, True) != row["script_sha256_lf"]:
            failures.append(f"{row['record_id']}: script hash mismatch")
        failures.extend(f"{row['record_id']}: {item}" for item in check_pack(row["visual_reference_sha256"]))
        if row["formats"] == "PNG" and pack_hashes(row["output_files_sha256"]) != pack_hashes(row["visual_reference_sha256"]):
            failures.append(f"{row['record_id']}: submission output is not byte-identical to locked visual")
        if row["qa_status"] != "FINAL_VERIFIED":
            failures.append(f"{row['record_id']}: qa_status is not FINAL_VERIFIED")
    figures = sorted({row["publication_item"] for row in rows if row["formats"] == "PNG"})
    if len(figures) != 12:
        failures.append(f"figure count {len(figures)} != 12")
    if not args.skip_rerender and not failures:
        with tempfile.TemporaryDirectory(prefix="figure-render-") as temp:
            temp_root=Path(temp); rebuilt=temp_root/"rebuilt"; submission=temp_root/"submission"
            subprocess.run([sys.executable, str(REPO / "scripts/plotting/build_final_figures.py"),
                            "--rebuilt-dir", str(rebuilt), "--submission-dir", str(submission)], cwd=REPO, check=True)
            for subdir in ("rebuilt","submission"):
                accepted_outputs = sorted((REPO / "results/figures" / subdir).glob("*.png")) + sorted((REPO / "results/figures" / subdir).glob("*.svg"))
                for accepted in accepted_outputs:
                    candidate = temp_root / subdir / accepted.name
                    if not candidate.is_file() or sha256(candidate) != sha256(accepted):
                        failures.append(f"rerender mismatch {subdir}/{accepted.name}")
    report = REPO / "results" / "figures" / "verification_report.txt"
    report.write_text("\n".join([f"checks={len(rows)} records + deterministic rerender", f"failures={len(failures)}", *failures]) + "\n", encoding="utf-8")
    print(report.read_text(encoding="utf-8"), end="")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
