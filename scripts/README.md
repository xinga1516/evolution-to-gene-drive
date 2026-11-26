# Running the deposited code

## SLiM

`run_slim.py` is the single parameterized launcher. It reads
`../config/run_manifest.csv`; each row specifies the publication scope, model,
parameter overrides, replicate count and deterministic seed rule. The default
is a dry run. Add `--execute` only when the declared SLiM version is installed.

```bash
python scripts/run_slim.py --validate-only
python scripts/run_slim.py --run-id <run_id>
python scripts/run_slim.py --run-id <run_id> --execute
```

## Source Data processing, statistics and plotting

```bash
python scripts/compute_final_statistics.py
python scripts/plot_final_figures.py --figure all --output-dir output/figures
```

Both scripts read the deposited Excel workbooks in `data/source_data/`.
Generated outputs are not tracked by Git.

The historical cluster raw-output parsers are not included because their raw
inputs and machine-specific paths are outside this deposit. Here, "processing"
therefore means the supported transformation from the deposited replicate-
summary workbooks to final statistics and figures.
