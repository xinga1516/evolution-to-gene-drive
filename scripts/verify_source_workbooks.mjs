#!/usr/bin/env node
/** Verify workbook sheet structure, dimensions, headers and formula-error text. */

import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const artifactModule = "C:/Users/jim ma/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";
const { FileBlob, SpreadsheetFile, Workbook } = await import(pathToFileURL(artifactModule));

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourceDir = path.join(repo, "data", "source_data");
const manifest = JSON.parse(await fs.readFile(path.join(sourceDir, "workbook_manifest.json"), "utf8"));
const errorTokens = new Set(["#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A"]);
const report = [];
let failed = false;

async function csvHeader(csvPath) {
  const text = await fs.readFile(csvPath, "utf8");
  const csvBook = await Workbook.fromCSV(text.replace(/^\uFEFF/, ""), { sheetName: "Data" });
  return csvBook.worksheets.getItem("Data").getUsedRange(true).values[0].map(String);
}

for (const [bookName, entries] of Object.entries(manifest)) {
  if (!entries.length) continue;
  const workbookPath = path.join(sourceDir, `${bookName}.xlsx`);
  const blob = await FileBlob.load(workbookPath);
  const workbook = await SpreadsheetFile.importXlsx(blob);
  const expectedSheets = ["README", "INDEX", ...entries.map((entry) => entry.sheet)];
  const actualSheets = workbook.worksheets.items.map((sheet) => sheet.name);
  const workbookResult = {
    workbook: path.relative(repo, workbookPath).split(path.sep).join("/"),
    expected_sheets: expectedSheets,
    actual_sheets: actualSheets,
    sheets: [],
    pass: JSON.stringify(expectedSheets) === JSON.stringify(actualSheets),
  };

  for (const entry of entries) {
    const sheet = workbook.worksheets.getItem(entry.sheet);
    const matrix = sheet.getUsedRange(true).values;
    const actualRows = matrix.length - 1;
    const actualColumns = matrix[0]?.length ?? 0;
    const expectedHeader = await csvHeader(path.join(repo, ...entry.path.split("/")));
    const actualHeader = (matrix[0] ?? []).map(String);
    let formulaErrors = 0;
    for (const row of matrix) {
      for (const value of row) if (errorTokens.has(String(value))) formulaErrors += 1;
    }
    const sheetPass = actualRows === entry.rows
      && actualColumns === entry.columns
      && JSON.stringify(actualHeader) === JSON.stringify(expectedHeader)
      && formulaErrors === 0;
    workbookResult.sheets.push({
      sheet: entry.sheet,
      expected_rows: entry.rows,
      actual_rows: actualRows,
      expected_columns: entry.columns,
      actual_columns: actualColumns,
      header_match: JSON.stringify(actualHeader) === JSON.stringify(expectedHeader),
      formula_error_tokens: formulaErrors,
      pass: sheetPass,
    });
    workbookResult.pass = workbookResult.pass && sheetPass;
  }
  failed = failed || !workbookResult.pass;
  report.push(workbookResult);
}

const output = path.join(sourceDir, "workbook_qa.json");
await fs.writeFile(output, `${JSON.stringify(report, null, 2)}\n`, "utf8");
console.log(`Verified ${report.length} workbooks; failures=${report.filter((item) => !item.pass).length}`);
if (failed) process.exitCode = 1;
