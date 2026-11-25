#!/usr/bin/env python3
"""Validate, plan, or execute the frozen SLiM run manifest.

The checked-in CSV is the only launch configuration.  A row represents one
condition cell, not one replicate.  This runner expands the requested rows to
replicates, creates deterministic seeds, passes every declared override to
SLiM with ``-d``, and records a machine-readable receipt beside each raw log.

The default is deliberately a dry run.  Supplying ``--execute`` is required
before SLiM is invoked.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "config" / "run_manifest.csv"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "runs"
MAX_SLIM_SEED = 2**62 - 1
MODEL_HASHES = {
    "panmictic": "c29cef8b22d9d64c98748ea0daf64f4f6e65c19db5130d8536a4d2a9e3fbbdd8",
    "spatial": "93fb31425a541163446db88662f4ece8e2273a414121d5e86a73a5bf85734cb6",
}
REQUIRED_COLUMNS = {
    "run_id",
    "publication_scope",
    "lineage_dataset_ids",
    "execution_role",
    "reuse_run_ids",
    "model",
    "slim_script",
    "slim_sha256",
    "parameter_profile",
    "condition_label",
    "replicate_count",
    "observed_usable_replicates",
    "seed_namespace",
    "seed_rule",
    "seed_base",
    "defines_json",
    "expected_output_subdir",
    "provenance_note",
}


class ManifestError(ValueError):
    """Raised when the launch manifest is internally inconsistent."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS.difference(reader.fieldnames or [])
        if missing:
            raise ManifestError(f"manifest missing columns: {sorted(missing)}")
        rows = list(reader)
    if not rows:
        raise ManifestError("manifest has no rows")
    return rows


def model_parameter_names(script: Path) -> set[str]:
    source = script.read_text(encoding="utf-8-sig")
    return set(re.findall(r'defineCfgParam\(\s*"([A-Za-z0-9_]+)"', source))


def parse_defines(row: dict[str, str]) -> dict[str, Any]:
    try:
        value = json.loads(row["defines_json"] or "{}")
    except json.JSONDecodeError as exc:
        raise ManifestError(f"{row['run_id']}: invalid defines_json: {exc}") from exc
    if not isinstance(value, dict):
        raise ManifestError(f"{row['run_id']}: defines_json must be a JSON object")
    return value


def validate_manifest(rows: list[dict[str, str]], repo_root: Path) -> list[str]:
    errors: list[str] = []
    ids = [row["run_id"] for row in rows]
    duplicate_ids = sorted({run_id for run_id in ids if ids.count(run_id) > 1})
    if duplicate_ids:
        errors.append(f"duplicate run_id values: {duplicate_ids}")
    known_ids = set(ids)
    parameter_names: dict[Path, set[str]] = {}

    for row in rows:
        run_id = row["run_id"] or "<blank>"
        role = row["execution_role"]
        if role not in {"simulation", "derived_reuse", "external_model_required"}:
            errors.append(f"{run_id}: invalid execution_role {role!r}")
            continue
        try:
            replicates = int(row["replicate_count"])
        except ValueError:
            errors.append(f"{run_id}: replicate_count is not an integer")
            continue
        if role == "simulation" and replicates <= 0:
            errors.append(f"{run_id}: simulation row needs replicate_count > 0")
        if role == "derived_reuse":
            if replicates != 0:
                errors.append(f"{run_id}: derived_reuse row must have replicate_count 0")
            refs = [item for item in row["reuse_run_ids"].split(";") if item]
            unknown = sorted(set(refs).difference(known_ids))
            if not refs:
                errors.append(f"{run_id}: derived_reuse row has no reuse_run_ids")
            if unknown:
                errors.append(f"{run_id}: unknown reuse_run_ids {unknown}")
            continue
        if role == "external_model_required":
            if replicates <= 0:
                errors.append(f"{run_id}: external-model row needs replicate_count > 0")
            try:
                parse_defines(row)
            except ManifestError as exc:
                errors.append(str(exc))
            if not row["slim_sha256"] or not row["provenance_note"]:
                errors.append(
                    f"{run_id}: external-model row needs the expected hash and provenance note"
                )
            continue

        model = row["model"]
        if model not in MODEL_HASHES:
            errors.append(f"{run_id}: unknown model {model!r}")
            continue
        script = (repo_root / row["slim_script"]).resolve()
        if not script.is_file():
            errors.append(f"{run_id}: missing SLiM script {row['slim_script']}")
            continue
        actual_hash = sha256_file(script)
        if actual_hash != row["slim_sha256"].lower():
            errors.append(f"{run_id}: manifest SLiM hash mismatch")
        if actual_hash != MODEL_HASHES[model]:
            errors.append(f"{run_id}: frozen {model} model hash mismatch")
        if row["seed_rule"] not in {"sha256-v1", "linear-v1"}:
            errors.append(f"{run_id}: unsupported seed_rule {row['seed_rule']!r}")
        if row["seed_rule"] == "linear-v1":
            try:
                base = int(row["seed_base"])
                if not 0 <= base < MAX_SLIM_SEED - replicates:
                    raise ValueError
            except ValueError:
                errors.append(f"{run_id}: invalid seed_base for linear-v1")
        try:
            defines = parse_defines(row)
        except ManifestError as exc:
            errors.append(str(exc))
            continue
        names = parameter_names.setdefault(script, model_parameter_names(script))
        unknown_defines = sorted(set(defines).difference(names))
        if unknown_defines:
            errors.append(f"{run_id}: defines absent from model: {unknown_defines}")
    return errors


def seed_for(row: dict[str, str], replicate: int) -> int:
    if row["seed_rule"] == "linear-v1":
        return int(row["seed_base"]) + replicate
    material = f"{row['seed_namespace']}|{row['run_id']}|{replicate}".encode("utf-8")
    value = int.from_bytes(hashlib.sha256(material).digest()[:8], "big")
    return value % MAX_SLIM_SEED + 1


def eidos_literal(value: Any) -> str:
    if isinstance(value, bool):
        return "T" if value else "F"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ManifestError("SLiM define values must be finite")
        return format(value, ".15g")
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    raise ManifestError(f"unsupported define value type: {type(value).__name__}")


def command_for(row: dict[str, str], replicate: int, slim_bin: str) -> list[str]:
    seed = seed_for(row, replicate)
    script = (REPO_ROOT / row["slim_script"]).resolve()
    command = [slim_bin, "-s", str(seed)]
    for name, value in sorted(parse_defines(row).items()):
        command.extend(["-d", f"{name}={eidos_literal(value)}"])
    command.append(str(script))
    return command


def selected_rows(
    rows: list[dict[str, str]], run_ids: list[str], run_all: bool
) -> list[dict[str, str]]:
    simulations = [row for row in rows if row["execution_role"] == "simulation"]
    if run_all:
        return simulations
    wanted = set(run_ids)
    selected = [row for row in simulations if row["run_id"] in wanted]
    missing = sorted(wanted.difference(row["run_id"] for row in selected))
    if missing:
        raise ManifestError(f"unknown or non-simulation run IDs: {missing}")
    if not selected:
        raise ManifestError("select --run-id at least once, or use --all")
    return selected


def replicate_numbers(count: int, requested: list[int]) -> Iterable[int]:
    if not requested:
        return range(1, count + 1)
    invalid = sorted({rep for rep in requested if rep < 1 or rep > count})
    if invalid:
        raise ManifestError(f"replicate number outside 1..{count}: {invalid}")
    return sorted(set(requested))


def shell_join(command: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(command)
    return shlex.join(command)


def receipt(
    row: dict[str, str], replicate: int, command: list[str], exit_code: int | None
) -> dict[str, Any]:
    script = (REPO_ROOT / row["slim_script"]).resolve()
    return {
        "run_id": row["run_id"],
        "publication_scope": row["publication_scope"],
        "lineage_dataset_ids": row["lineage_dataset_ids"].split(";"),
        "condition_label": row["condition_label"],
        "replicate": replicate,
        "seed": seed_for(row, replicate),
        "seed_rule": row["seed_rule"],
        "command": command,
        "defines": parse_defines(row),
        "slim_script": str(script),
        "slim_sha256": sha256_file(script),
        "exit_code": exit_code,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--run-id", action="append", default=[])
    parser.add_argument("--all", action="store_true", help="select all simulation rows")
    parser.add_argument("--replicate", type=int, action="append", default=[])
    parser.add_argument("--slim-bin", default=os.environ.get("SLIM_BIN", "slim"))
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="actually run SLiM; without this option only commands are printed",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = args.manifest.resolve()
    rows = load_manifest(manifest)
    errors = validate_manifest(rows, REPO_ROOT)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    derived = sum(row["execution_role"] == "derived_reuse" for row in rows)
    external = sum(row["execution_role"] == "external_model_required" for row in rows)
    print(
        f"Validated {len(rows)} manifest rows "
        f"({derived} derived-reuse; {external} external-model-required)."
    )
    if args.validate_only:
        return 0
    try:
        selected = selected_rows(rows, args.run_id, args.all)
    except ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.execute:
        try:
            subprocess.run(
                [args.slim_bin, "-v"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            print(f"ERROR: cannot execute {args.slim_bin!r}: {exc}", file=sys.stderr)
            return 2

    total = 0
    for row in selected:
        count = int(row["replicate_count"])
        try:
            replicates = replicate_numbers(count, args.replicate)
        except ManifestError as exc:
            print(f"ERROR: {row['run_id']}: {exc}", file=sys.stderr)
            return 2
        for replicate in replicates:
            total += 1
            command = command_for(row, replicate, args.slim_bin)
            run_dir = args.output_root / row["expected_output_subdir"] / f"replicate_{replicate:03d}"
            log_path = run_dir / "slim_stdout.log"
            receipt_path = run_dir / "run_receipt.json"
            print(shell_join(command))
            if not args.execute:
                continue
            run_dir.mkdir(parents=True, exist_ok=True)
            pending = receipt(row, replicate, command, None)
            receipt_path.write_text(
                json.dumps(pending, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            with log_path.open("w", encoding="utf-8", newline="\n") as log:
                result = subprocess.run(
                    command,
                    cwd=run_dir,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    check=False,
                    text=True,
                )
            completed = receipt(row, replicate, command, result.returncode)
            receipt_path.write_text(
                json.dumps(completed, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            if result.returncode:
                print(
                    f"ERROR: {row['run_id']} replicate {replicate} exited "
                    f"{result.returncode}; see {log_path}",
                    file=sys.stderr,
                )
                return result.returncode
    print(f"{'Executed' if args.execute else 'Planned'} {total} replicate commands.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
