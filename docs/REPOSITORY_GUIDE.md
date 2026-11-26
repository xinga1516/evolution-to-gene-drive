# Repository guide: where to look first

This repository is an archive for the locked final figures and supplementary
material. It contains both the files needed to inspect the submission and the
files needed to reproduce the numerical results. You normally do **not** need
to open every directory.

## Quick route

| If you want to... | Open this first | What it contains |
| --- | --- | --- |
| See the final submitted appearance | `docs/visual_references/Figures_final_submission.pptx` | Canonical final PowerPoint deck. |
| See a particular figure as an image | `results/figures/submission/` | Frozen PNG exports of the 12 main/supplementary figures. |
| Inspect numbers behind a figure or table | `data/source_data/Figure*.xlsx` or `Table_S*.xlsx` | One readable Source Data workbook per published item. |
| Inspect reported statistical tests | `results/statistics/` | Final test values and the statistics catalogue. |
| Find the data and code used for a panel | `config/figure_data_map.csv` | The 46-row figure/table-to-data lineage map. |
| Rebuild or verify the archive | `README.md` | Short, ordered command sequence. |

## Directory map

```text
README.md                         Start here: build and verification commands

docs/
  REPOSITORY_GUIDE.md             This short navigation guide
  QA_ACCEPTANCE.md                Final three-party QA record
  ARCHIVE_SCOPE.md                What is and is not included in the archive
  ENVIRONMENT.md                  Software environment and reproducibility notes
  visual_references/              Final PowerPoint and frozen reference slides

data/
  README.md                       Data dictionary and provenance overview
  source_data/                    Published Source Data workbooks (15 files)
    files/                        Machine-readable values used by the workbooks

results/
  figures/submission/             PNGs exported from the locked final deck
  figures/rebuilt/                Script-generated data-driven redraws (PNG/SVG)
  statistics/                     Final numerical tests and statistics methods

config/
  figure_data_map.csv             46 published panel/table records: data, tests, code
  figure_plot_manifest.csv        Render environment and output hashes for the 46 records
  submission_visual_map.csv       Final-deck slide to frozen-PNG map (17 slides)
  run_manifest.csv                134 simulation/run configurations
  raw_lineage_manifest.csv        Historical raw-data provenance (not a raw-data archive)

scripts/
  plotting/                       Final figure-rendering entry point and inputs
  build_*.py / verify_*.py        Source Data, tables, mappings, and validation
  run_slim.py                     Parameterized SLiM launch/manifest validator

population model/final/           Final SLiM model files
data process/                     Legacy/raw processing scripts retained for provenance
```

## What is authoritative?

- **Visual submission:** the PowerPoint deck in `docs/visual_references/` and
  `results/figures/submission/`.
- **Published numerical values:** the Excel workbooks in `data/source_data/`.
- **Reported statistics:** `results/statistics/`.
- **Panel-level provenance:** `config/figure_data_map.csv`.

The `results/figures/rebuilt/` files are reproducible data-driven redraws.
They demonstrate numerical reconstruction, but the PowerPoint deck remains the
authoritative record of the final manual page composition.

## Intentional limits

- Raw SLiM outputs are not stored here; the archive provides replicate-level
  summaries rather than full raw outputs.
- The raw-simulation retrieval URI is intentionally blank at present.
- Figure 5 and Supplementary Figure S3 retain provenance and final summaries;
  their historical cluster model is not required to run locally for this
  archive's acceptance.
