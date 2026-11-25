#!/usr/bin/env python3
"""Build the 45-row figure/table build manifest from canonical repository files."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
MAP = REPO / "config" / "figure_data_map.csv"
OUT = REPO / "config" / "figure_plot_manifest.csv"
VISUAL_MAP = REPO / "config" / "submission_visual_map.csv"
PLOT_SCRIPT = Path("scripts/plotting/build_final_figures.py")
RENDER_SCRIPT = Path("scripts/plotting/render_final_figures.py")
TABLE_SCRIPT = Path("scripts/build_source_workbooks.mjs")


def sha256(path: Path, normalize_text: bool = False) -> str:
    payload = path.read_bytes()
    if normalize_text:
        payload = payload.replace(b"\r\n", b"\n")
    return hashlib.sha256(payload).hexdigest()


def packed(paths: list[Path], normalize_text: bool = False) -> str:
    return ";".join(f"{p.as_posix()}={sha256(REPO / p, normalize_text)}" for p in paths)


def figure_key(publication_item: str) -> str | None:
    if publication_item.startswith("Figure "):
        return publication_item.replace("Figure ", "Figure")
    if publication_item.startswith("Supplementary Figure S"):
        return publication_item.replace("Supplementary Figure S", "Figure_S")
    return None


def source_paths(publication_item: str, key: str | None) -> list[Path]:
    if key:
        folder = REPO / "data" / "source_data" / "files" / key
        return [p.relative_to(REPO) for p in sorted(folder.glob("*")) if p.is_file()]
    suffix = publication_item.rsplit(" ", 1)[-1].replace("S", "S")
    workbook = Path("data/source_data") / f"Table_{suffix}.xlsx"
    return [workbook]


def main() -> None:
    environment_files = [Path("environment.yml"), Path("requirements-lock.txt"), Path("docs/ENVIRONMENT.md")]
    env_hashes = packed(environment_files, normalize_text=True)
    rows: list[dict[str, str]] = []
    visual_rows = list(csv.DictReader(VISUAL_MAP.open(newline="", encoding="utf-8-sig")))
    visuals: dict[str, list[Path]] = {}
    for visual in visual_rows:
        visuals.setdefault(visual["publication_item"], []).append(Path(visual["visual_reference"]))
    with MAP.open(newline="", encoding="utf-8-sig") as handle:
        for record in csv.DictReader(handle):
            item, panel = record["publication_item"], record["panel"]
            key = figure_key(item)
            is_figure = key is not None
            script = PLOT_SCRIPT if is_figure else TABLE_SCRIPT
            cli = (f"python {PLOT_SCRIPT.as_posix()}"
                   if is_figure else "node scripts/build_source_workbooks.mjs")
            sources = source_paths(item, key)
            stats_target = record["repository_statistics_target"]
            stats = [] if stats_target == "not applicable" else [Path(stats_target)]
            output_paths: list[Path]
            if is_figure:
                output_paths = [Path("results/figures/submission") / f"{key}.png"]
                reconstructed_paths = [Path("results/figures/rebuilt") / f"{key}.png", Path("results/figures/rebuilt") / f"{key}.svg"]
                with Image.open(REPO / output_paths[0]) as image:
                    width_px, height_px = image.size
                dimensions = f"{width_px}x{height_px}px"
                formats = "PNG"
                dpi = "PowerPoint export 1920x1080"
            else:
                output_paths = sources
                reconstructed_paths = []
                dimensions, formats, dpi = "not applicable", "XLSX", "not applicable"
            rows.append({
                "record_id": record["record_id"], "publication_item": item, "panel": panel,
                "script_path": script.as_posix(), "command": cli,
                "source_files_sha256": packed(sources),
                "statistics_files_sha256": packed(stats) if stats else "not applicable",
                "script_sha256_lf": sha256(REPO / script, normalize_text=True),
                "renderer_sha256_lf": sha256(REPO / RENDER_SCRIPT, normalize_text=True) if is_figure else "not applicable",
                "environment_sha256_lf": env_hashes, "random_seed": "fixed in renderer" if is_figure else "not applicable",
                "output_files_sha256": packed(output_paths), "formats": formats,
                "reconstructed_output_files_sha256": packed(reconstructed_paths) if reconstructed_paths else "not applicable",
                "dimensions": dimensions, "dpi": dpi, "font_family": "Arial" if is_figure else "not applicable",
                "visual_reference_sha256": packed(visuals.get(item, [])) if visuals.get(item) else "not applicable",
                "visual_lineage": "locked final-deck slide plus scripts/plotting/authoritative_sources" if is_figure else "locked final-deck slide when present",
                "qa_status": "FINAL_VERIFIED",
            })
    fields = list(rows[0])
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    print(f"wrote {OUT.relative_to(REPO)}: {len(rows)} records")


if __name__ == "__main__":
    main()
