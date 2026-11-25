#!/usr/bin/env python3
"""Verify the external Figure 5 / Figure S3 checkpoint archive."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

EXPECTED_MODEL_SHA256 = "94e465ec99eaef5646cdfc1828c8121cb0b7df4b4290a0f7622e04624def8812"
EXPECTED_SEEDS = range(61001, 61101)
MODES = ("evolving", "uniform")
REQUIRED = ("checkpoint.bin", "data_traits.csv", "data_metadata.csv", "status.json")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def metadata_value(raw: bytes, key: str) -> str | None:
    rows = csv.reader(io.StringIO(raw.decode("utf-8-sig")))
    next(rows, None)
    for row in rows:
        if len(row) >= 2 and row[0] == key:
            return row[1].strip()
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    failures: list[str] = []
    model_hashes: set[str] = set()
    with zipfile.ZipFile(args.archive) as archive:
        entries = {item.filename: item for item in archive.infolist()}
        for mode in MODES:
            for seed in EXPECTED_SEEDS:
                prefix = f"checkpoints/{mode}/seed_{seed}/"
                for filename in REQUIRED:
                    name = prefix + filename
                    item = entries.get(name)
                    if item is None or item.file_size == 0:
                        failures.append(f"missing_or_empty:{name}")
                metadata_name = prefix + "data_metadata.csv"
                if metadata_name in entries and entries[metadata_name].file_size:
                    value = metadata_value(archive.read(metadata_name), "source_sha256")
                    if value:
                        model_hashes.add(value)
                    else:
                        failures.append(f"missing_source_sha256:{metadata_name}")
                status_name = prefix + "status.json"
                if status_name in entries and entries[status_name].file_size:
                    try:
                        status = json.loads(archive.read(status_name))
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        failures.append(f"invalid_status_json:{status_name}:{exc}")
                        continue
                    expected_status = {
                        "exit_code": 0,
                        "stage": "checkpoint",
                        "trait_mode": mode,
                        "origin_seed": seed,
                        "k": 1.0,
                        "m": 100,
                        "laplace_b": 0.05,
                        "effective_female_number": 10000,
                        "checkpoint_tick": 100,
                        "checkpoint_complete": True,
                        "outputs_complete": True,
                    }
                    for key, expected in expected_status.items():
                        if status.get(key) != expected:
                            failures.append(
                                f"status_mismatch:{status_name}:{key}:"
                                f"{status.get(key)!r}!={expected!r}"
                            )
                    command = status.get("command") or []
                    if not any(
                        isinstance(item, str)
                        and item.endswith("/reprising.formal_experiment.pinned.slim")
                        for item in command
                    ):
                        failures.append(f"status_model_path_missing:{status_name}")

    if model_hashes != {EXPECTED_MODEL_SHA256}:
        failures.append(f"unexpected_model_hashes:{sorted(model_hashes)}")
    report = {
        "archive_name": args.archive.name,
        "archive_sha256": sha256(args.archive),
        "expected_modes": list(MODES),
        "expected_seed_range": [61001, 61100],
        "expected_checkpoint_directories": 200,
        "required_files_per_directory": list(REQUIRED),
        "observed_model_hashes": sorted(model_hashes),
        "status_contract": {
            "exit_code": 0,
            "stage": "checkpoint",
            "trait_mode_matches_path": True,
            "origin_seed_matches_path": True,
            "k": 1.0,
            "m": 100,
            "laplace_b": 0.05,
            "effective_female_number": 10000,
            "checkpoint_tick": 100,
            "checkpoint_complete": True,
            "outputs_complete": True,
            "pinned_model_path_recorded": True,
        },
        "checks_passed": not failures,
        "failures": failures,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
