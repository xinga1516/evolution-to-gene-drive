# Reproducible rendering environment

The frozen Python environment is recorded in `environment.yml` and
`requirements-lock.txt`. The accepted renderer was verified with CPython
3.12.5 and Matplotlib 3.10.1 using the non-interactive Agg backend.

Arial is an external publication-font dependency and is not redistributed by
this repository. The renderer calls `findfont("Arial",
fallback_to_default=False)` and fails before rendering if Arial is unavailable,
instead of silently changing text metrics. On the accepted Windows build the
font resolved to `C:\Windows\Fonts\arial.ttf`.

Figures are emitted as deterministic SVG and 300-dpi PNG. Figure dimensions,
font family, output hashes, script hash, environment hash, source-data hashes,
and statistics hashes are frozen in `config/figure_plot_manifest.csv`.

Pixel-exact verification of the manually composed submission pages additionally
requires Microsoft PowerPoint on Windows. `scripts/verify_submission_deck.ps1`
opens the archived deck read-only, exports the mapped slides at 1920×1080 and
compares SHA-256 values with the frozen references. This dependency is only for
submission-layout QA; it is not used to calculate scientific values.

The Source Data workbook builder uses Node.js 24.22.3 and OpenAI's
`@oai/artifact-tool`. That dependency is separate from final plotting; all
publication panels can be rendered directly from the checked-in canonical CSV
and CSV.GZ files using only the Python environment above.

Supplementary Tables S1–S3 are built deterministically with openpyxl 3.1.5;
ZIP member timestamps and workbook core timestamps are normalized before hash
comparison.

SLiM is an external simulation dependency and is not installed by the Conda
environment.  The parameterized launch layer is documented in
`docs/RUNNING_SLIM.md`.  Its executable rows hash-check the frozen panmictic
and spatial model files before planning or running commands.  Figure 5/S3 used
a separate SLiM 5.0 checkpoint model; the manifest preserves its expected hash
and commands and marks the rows non-executable until the exact model and
checkpoints are recovered.
