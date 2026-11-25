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

The Source Data workbook builder uses Node.js 24.22.3 and OpenAI's
`@oai/artifact-tool`. That dependency is separate from final plotting; all
publication panels can be rendered directly from the checked-in canonical CSV
and CSV.GZ files using only the Python environment above.
