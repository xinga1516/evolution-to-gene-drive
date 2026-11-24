#!/usr/bin/env node
/** Build and visually preview the publication Source Data workbooks. */

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const artifactModule = "C:/Users/jim ma/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";
const { SpreadsheetFile, Workbook } = await import(pathToFileURL(artifactModule));

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(scriptDir, "..");
const sourceDir = path.join(repo, "data", "source_data");
const previewDir = path.join(sourceDir, "workbook_previews");
const manifestPath = path.join(sourceDir, "workbook_manifest.json");
const manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));

const fontFamily = "Arial";
const headerFill = "#1F4E78";
const labelFill = "#E8F0F7";
const borderColor = "#D9E2F3";

function repoRelative(absolutePath) {
  return path.relative(repo, absolutePath).split(path.sep).join("/");
}

function columnName(index) {
  let value = index + 1;
  let result = "";
  while (value > 0) {
    const remainder = (value - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    value = Math.floor((value - 1) / 26);
  }
  return result;
}

function numberFormatFor(header) {
  const key = String(header).toLowerCase();
  if (/(^|_)(rep|replicate|seed|tick|generation|record|index|n|count)($|_)/.test(key)) return "0";
  if (/week|time/.test(key)) return "0.000";
  if (/probability|proportion|relative|fitness|conversion|mean|median|q0|q1|q2|q7|q9|delta|response|load|nni|resistance|viability|copies/.test(key)) return "0.000000";
  return "General";
}

async function csvMatrix(csvPath) {
  const text = await fs.readFile(csvPath, "utf8");
  const csvBook = await Workbook.fromCSV(text.replace(/^\uFEFF/, ""), { sheetName: "Data" });
  const sheet = csvBook.worksheets.getItem("Data");
  return sheet.getUsedRange(true).values;
}

function styleReadme(sheet) {
  sheet.showGridLines = false;
  sheet.getRange("A1:F1").merge();
  sheet.getRange("A1").values = [["Publication Source Data"]];
  sheet.getRange("A1:F1").format = {
    font: { name: fontFamily, size: 14, bold: true, color: "#1F1F1F" },
    verticalAlignment: "center",
  };
  sheet.getRange("A1:F1").format.rowHeight = 26;
  sheet.getRange("A3:A9").format = {
    fill: labelFill,
    font: { name: fontFamily, size: 10, bold: true, color: "#1F1F1F" },
    verticalAlignment: "center",
  };
  for (let row = 3; row <= 9; row += 1) sheet.getRange(`B${row}:F${row}`).merge();
  sheet.getRange("B3:F9").format = {
    font: { name: fontFamily, size: 10, color: "#1F1F1F" },
    verticalAlignment: "center",
    wrapText: true,
  };
  sheet.getRange("A3:F9").format.borders = { preset: "outside", style: "thin", color: borderColor };
  sheet.getRange("A:A").format.columnWidth = 24;
  sheet.getRange("B:F").format.columnWidth = 18;
  sheet.getRange("A3:F9").format.rowHeight = 42;
}

function styleIndex(sheet, rowCount) {
  sheet.showGridLines = false;
  const used = sheet.getRange(`A1:F${rowCount}`);
  used.format.font = { name: fontFamily, size: 10, color: "#1F1F1F" };
  sheet.getRange("A1:F1").format = {
    fill: headerFill,
    font: { name: fontFamily, size: 10, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    borders: { preset: "all", style: "thin", color: "#FFFFFF" },
  };
  sheet.getRange("A1:F1").format.rowHeight = 24;
  sheet.getRange(`A2:F${rowCount}`).format.verticalAlignment = "center";
  sheet.getRange(`A2:F${rowCount}`).format.rowHeight = 22;
  sheet.getRange("A:A").format.columnWidth = 22;
  sheet.getRange("B:B").format.columnWidth = 30;
  sheet.getRange("C:C").format.columnWidth = 70;
  sheet.getRange("D:F").format.columnWidth = 14;
  sheet.freezePanes.freezeRows(1);
}

function styleDataSheet(sheet, matrix) {
  sheet.showGridLines = false;
  const rows = matrix.length;
  const cols = matrix[0]?.length ?? 0;
  if (!rows || !cols) return;
  const lastColumn = columnName(cols - 1);
  const used = sheet.getRange(`A1:${lastColumn}${rows}`);
  used.format.font = { name: fontFamily, size: 10, color: "#1F1F1F" };
  used.format.verticalAlignment = "center";
  sheet.getRange(`A1:${lastColumn}1`).format = {
    fill: headerFill,
    font: { name: fontFamily, size: 10, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    borders: { preset: "all", style: "thin", color: "#FFFFFF" },
    wrapText: true,
  };
  sheet.getRange(`A1:${lastColumn}1`).format.rowHeight = 32;
  for (let col = 0; col < cols; col += 1) {
    const header = matrix[0][col] ?? "";
    const column = columnName(col);
    const dataRange = rows > 1 ? sheet.getRange(`${column}2:${column}${rows}`) : null;
    const numberFormat = numberFormatFor(header);
    if (dataRange && numberFormat !== "General") dataRange.format.numberFormat = numberFormat;
    const maxLength = Math.max(
      String(header).length,
      ...matrix.slice(1, Math.min(rows, 201)).map((row) => String(row[col] ?? "").length),
    );
    sheet.getRange(`${column}:${column}`).format.columnWidth = Math.min(42, Math.max(12, maxLength + 2));
  }
  sheet.freezePanes.freezeRows(1);
  if (cols > 7) sheet.freezePanes.freezeColumns(2);
}

async function buildWorkbook(bookName, entries) {
  const workbook = Workbook.create();
  const readme = workbook.worksheets.add("README");
  const index = workbook.worksheets.add("INDEX");
  readme.getRange("A3:B9").values = [
    ["Workbook", bookName],
    ["Purpose", "Values behind the final accepted publication figure or supplementary table."],
    ["Independent unit", "One stochastic simulation replicate unless the panel map explicitly declares matched origins."],
    ["Exact data authority", "Canonical CSV/CSV.GZ files under data/source_data/files; this workbook is a convenient panel-indexed view."],
    ["Panel map", "config/figure_data_map.csv"],
    ["Raw lineage", "config/raw_lineage_manifest.csv"],
    ["Missingness", bookName === "Figure3" || bookName === "Figure_S1" ? "Figure 3E / S1C: h=0.99 variable group has n=17; zero-byte reps 5, 7 and 9 are not imputed." : "See data/README.md and panel-specific n columns."],
  ];
  styleReadme(readme);

  const indexRows = [["Sheet", "Publication scope", "Canonical/staging path", "Rows", "Columns", "Workbook view"]];
  for (const entry of entries) {
    const csvPath = path.join(repo, ...entry.path.split("/"));
    const matrix = await csvMatrix(csvPath);
    const sheet = workbook.worksheets.add(entry.sheet);
    sheet.getRange("A1").write(matrix);
    styleDataSheet(sheet, matrix);
    indexRows.push([entry.sheet, entry.scope, entry.path, entry.rows, entry.columns, entry.scope.includes("decimated") ? "decimated; exact table in files/" : "exact rows"]);
  }
  index.getRange("A1").write(indexRows);
  styleIndex(index, indexRows.length);
  workbook.recalculate();

  const outputPath = path.join(sourceDir, `${bookName}.xlsx`);
  const exported = await SpreadsheetFile.exportXlsx(workbook);
  await exported.save(outputPath);

  const bookPreviewDir = path.join(previewDir, bookName);
  await fs.mkdir(bookPreviewDir, { recursive: true });
  for (const sheetName of ["README", "INDEX", ...entries.map((entry) => entry.sheet)]) {
    const entry = entries.find((item) => item.sheet === sheetName);
    const renderRange = sheetName === "README"
      ? "A1:F9"
      : sheetName === "INDEX"
        ? `A1:F${indexRows.length}`
        : `A1:${columnName(entry.columns - 1)}${Math.min(entry.rows + 1, 41)}`;
    const preview = await workbook.render({
      sheetName,
      range: renderRange,
      autoCrop: "all",
      scale: 1,
      format: "png",
    });
    await fs.writeFile(path.join(bookPreviewDir, `${sheetName}.png`), new Uint8Array(await preview.arrayBuffer()));
  }
  await fs.rm(`${outputPath}.inspect.ndjson`, { force: true });
  return { workbook: repoRelative(outputPath), sheets: 2 + entries.length };
}

await fs.rm(previewDir, { recursive: true, force: true });
await fs.mkdir(previewDir, { recursive: true });
const report = [];
for (const [bookName, entries] of Object.entries(manifest)) {
  if (!entries.length) continue;
  report.push(await buildWorkbook(bookName, entries));
}
await fs.writeFile(path.join(previewDir, "build_report.json"), `${JSON.stringify(report, null, 2)}\n`, "utf8");
console.log(`Built ${report.length} workbooks with ${report.reduce((sum, item) => sum + item.sheets, 0)} sheets.`);
