# Final figure rendering

`build_final_figures.py` is the authoritative build entry point. It produces
two deliberately separate artifacts:

- `results/figures/rebuilt/`: repository-native, data-driven redraws made by
  `render_final_figures.py` from canonical Source Data and accepted statistics;
- `results/figures/submission/`: pixel-exact pages materialized from the frozen
  final-deck visual references.

The separation is intentional. The final PowerPoint contains manual page
composition and late-stage placement that no single historical plotting script
reproduces. Numerical reproducibility is therefore verified against the
data-driven redraw, while exact appearance is verified against the locked deck
export. Neither artifact substitutes for the other.

The data-driven renderer reads the canonical panel-level files under
`data/source_data/files/` and accepted numerical results under
`results/statistics/`; it does not read a PowerPoint file, a local cache, or
the unreleased simulation archive.

Render every figure from the repository root:

```powershell
python scripts/plotting/build_final_figures.py
```

Render one figure by passing one of `Figure1` ... `Figure6` or
`Figure_S1` ... `Figure_S6` to `--figure`.

The files in `authoritative_sources/` are frozen, non-executable visual-lineage
snapshots recovered from the figure-development workspace. They document how
late-stage panels were drawn, but some contain historical absolute paths and
must not be used as reproducible entry points. They are deliberately excluded
from the final figure manifest and verification command.

The renderer uses the non-interactive Matplotlib Agg backend, requires Arial,
fixes random jitter seeds and SVG hash salts, and writes deterministic SVG plus
300-dpi PNG outputs.
