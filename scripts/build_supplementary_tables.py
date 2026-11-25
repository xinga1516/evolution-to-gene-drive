#!/usr/bin/env python3
"""Build the three supplementary workbooks from canonical CSV inputs."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import tempfile
import zipfile
import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "data" / "source_data" / "workbook_tables"
TABLES = {
    "Table_S1.xlsx": [("Parameters", SOURCE / "Table_S1" / "Parameters.csv")],
    "Table_S2.xlsx": [("All_P_values", SOURCE / "Table_S2" / "All_P_values.csv")],
    "Table_S3.xlsx": [
        ("Stability_inputs", SOURCE / "Table_S3" / "Stability_inputs.csv"),
        ("Stability_diagnostics", SOURCE / "Table_S3" / "Stability_diagnostics.csv"),
    ],
}


def normalize_xlsx(source: Path, target: Path) -> None:
    with zipfile.ZipFile(source) as zin, zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zout:
        for name in sorted(zin.namelist()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = zin.getinfo(name).external_attr
            payload = zin.read(name)
            if name == "docProps/core.xml":
                payload = re.sub(
                    rb"<dcterms:modified[^>]*>.*?</dcterms:modified>",
                    b'<dcterms:modified xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="dcterms:W3CDTF">2000-01-01T00:00:00Z</dcterms:modified>',
                    payload,
                )
            zout.writestr(info, payload)


def build_workbook(sheets: list[tuple[str, Path]], target: Path) -> None:
    wb = Workbook()
    wb.remove(wb.active)
    wb.properties.creator = "evolution-to-gene-drive reproducibility archive"
    wb.properties.created = wb.properties.modified = dt.datetime(2000, 1, 1)
    readme = wb.create_sheet("README")
    readme.append(["Publication Source Data"])
    readme.append(["Workbook", target.name])
    readme.append(["Provenance", "Built deterministically from the canonical CSV files listed in INDEX."])
    readme.append(["Builder", "scripts/build_supplementary_tables.py"])
    readme["A1"].font = Font(name="Arial", size=14, bold=True)
    readme.column_dimensions["A"].width = 22
    readme.column_dimensions["B"].width = 78
    index = wb.create_sheet("INDEX")
    index.append(["sheet", "canonical_csv", "rows", "columns"])
    for title, csv_path in sheets:
        ws = wb.create_sheet(title=title[:31])
        row_count = 0
        column_count = 0
        with csv_path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.reader(handle):
                ws.append(row)
                row_count += 1
                column_count = max(column_count, len(row))
        index.append([title[:31], csv_path.relative_to(REPO).as_posix(), max(0, row_count - 1), column_count])
        for cell in ws[1]:
            cell.font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="2F6B8A")
            cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for column in ws.columns:
            letter = column[0].column_letter
            width = min(45, max(10, max(len(str(c.value or "")) for c in column) + 2))
            ws.column_dimensions[letter].width = width
            for cell in column[1:]:
                cell.font = Font(name="Arial", size=9)
                cell.alignment = Alignment(vertical="top", wrap_text=width >= 35)
    for cell in index[1]:
        cell.font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2F6B8A")
    index.freeze_panes = "A2"
    index.column_dimensions["A"].width = 24
    index.column_dimensions["B"].width = 72
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="table-build-") as tmp:
        raw = Path(tmp) / target.name
        wb.save(raw)
        normalized = Path(tmp) / ("normalized-" + target.name)
        normalize_xlsx(raw, normalized)
        target.write_bytes(normalized.read_bytes())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=REPO / "data" / "source_data")
    args = parser.parse_args()
    for name, sheets in TABLES.items():
        build_workbook(sheets, args.output_dir / name)
        print(args.output_dir / name)


if __name__ == "__main__":
    main()
