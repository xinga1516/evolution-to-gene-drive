# Frozen submission visuals

The PNG files in `submission_slides/` are read-only exports from the user's
locked final deck, `Figures _修改提交(1).pptx` (SHA-256
`87beaa2c79f58bda6889e18b60847a4e217a5d53f2761dbc1f12ecc459a970e1`).
The exact binary is archived as `Figures_final_submission.pptx`.
They are the sole authority for final layout, panel size, typography, legend
placement and manual PowerPoint composition.

The source deck contains both an obsolete final-100-week S1 page (slide 13)
and the accepted final-20-week S1 page (slide 14). Only slide 14 is frozen as
`Figure_S1.png`. Main Figures 1–6 are slides 1, 3, 5, 7, 9 and 10;
Supplementary Figures S1–S6 are slides 14–19; Table S1 spans slides 20–23;
Table S3 is slide 24. Table S2 is generated from the accepted exact-test
results and has no page in this deck.

These images are visual references, not numerical data sources. Canonical
values remain under `data/source_data/files/`, accepted numerical tests remain
under `results/statistics/`, and repository-native redraws are produced by
`scripts/plotting/render_final_figures.py`. A figure cannot pass QA unless its
panel variables, data values, labels and statistics agree with the frozen
visual reference.

Run `scripts/verify_submission_deck.ps1` on Windows with Microsoft PowerPoint.
It checks the archived deck hash, exports every mapped slide at 1920×1080 and
requires each export to be byte-identical to its frozen reference.
