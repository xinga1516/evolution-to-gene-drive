# evolution-to-gene-drive

Minimal reproducibility files for the final figures, supplementary figures and
supplementary tables.

## Repository contents

```text
scripts/              final SLiM launch, Source Data processing, statistics and plotting code
config/               effective run manifest and figure-to-data map
data/README.md         data dictionary, provenance and data-availability notes
data/source_data/      one Source Data workbook per published figure or table
results/statistics/    final statistical results and statistical methods
environment.yml       software environment
文件结构说明.md          Chinese guide to the deposited files
```

Generated figures, PowerPoint exports, expanded CSV copies, QA reports and
historical one-off plotting scripts are intentionally not deposited.

## Environment

```bash
conda env create -f environment.yml
conda activate evolution-to-gene-drive-archive
```

## SLiM launch

`scripts/run_slim.py` reads `config/run_manifest.csv`, expands each selected
condition to its declared replicates, creates reproducible seeds and passes the
row's `defines_json` values to SLiM with `-d`.

```bash
python scripts/run_slim.py --validate-only
python scripts/run_slim.py --run-id f1_panmictic_0p7_neutral
python scripts/run_slim.py --run-id f1_panmictic_0p7_neutral --execute
```

See `scripts/README.md` for the short launch description. Historical Figure 5
and Supplementary Figure S3 cluster jobs are retained as provenance-only rows
in the manifest and are not locally executable from this deposit.

## Statistics and figures

```bash
python scripts/compute_final_statistics.py
python scripts/plot_final_figures.py --figure all --output-dir output/figures
```

The Excel workbooks are the deposited Source Data. Full raw SLiM outputs are
not included, and a public raw-data retrieval location has not yet been
specified. See `data/README.md` for definitions and known missingness.

Because the cluster-level raw outputs are not deposited, obsolete raw-output
parsers with machine-specific paths are intentionally excluded. The supported
processing chain starts from the deposited replicate-summary workbooks and is
implemented by `compute_final_statistics.py` and `plot_final_figures.py`.
