# Running the frozen simulations

The final launch layer has three parts:

- `scripts/run_slim.py`: one parameterized runner;
- `config/run_manifest.csv`: one row per condition cell, including publication
  scope, effective parameter overrides, replicate count and seed rule;
- this short guide.

The runner never launches SLiM by default.  It validates the complete manifest
and prints commands unless `--execute` is supplied.

## Validate and inspect

From the repository root:

```bash
python scripts/run_slim.py --validate-only
python scripts/run_slim.py --run-id f6_p70_l --replicate 1
```

The second command is a dry run.  It prints the exact `slim -s ... -d ...`
command but does not create files or start a simulation.

## Execute

Install SLiM and either place `slim` on `PATH` or give its executable explicitly:

```bash
python scripts/run_slim.py --run-id f6_p70_l --replicate 1 \
  --slim-bin /path/to/slim --output-root /path/to/runs --execute
```

Omit `--replicate` to run every declared replicate for the selected condition.
Use repeated `--run-id` arguments to select several cells.  `--all --execute`
is intentionally explicit and should normally be submitted through the local
scheduler rather than run on a login node.

Each replicate is isolated in its own directory and produces:

- `slim_stdout.log`;
- `run_receipt.json`, containing the command, seed, parameter overrides, model
  hash, publication scope and exit code;
- any model-generated sidecar files in the same replicate directory.

## Seeds

Most condition cells use `sha256-v1`: the seed is derived from
`seed_namespace | run_id | replicate` and is therefore independent of row
order and platform.  The audited Figure 6 retest uses its historical
`linear-v1` rule (`930000000 + 1000 × condition_index + replicate`).

The manifest records intended replicate counts separately from observed usable
replicates.  Missing or zero-byte historical outputs are not imputed.

## Model provenance and current limitation

The executable rows use the two frozen, hash-checked SLiM 4-compatible models:

- panmictic: `C29CEF8B...3FBBDD8`;
- spatial: `93FB3142...734CB6`.

Figure 5 and Supplementary Figure S3 used a distinct checkpoint-based SLiM 5.0
model, `reprising.formal_experiment.pinned.slim`, with recorded SHA-256
`94E465EC...EF8812`.  Its complete historical commands are preserved in the
manifest, but the model text and pre-release checkpoint files are not present
in the current local archive.  Those nine rows are labelled
`external_model_required` and the runner will not silently substitute another
model.  Exact rerunning of those rows requires recovery of that hash-matched
model and its 100 evolving/uniform checkpoints.

The checked-in Source Data, final statistics and final figures do not depend on
rerunning SLiM; they rebuild from the frozen replicate-level summaries.
