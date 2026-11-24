# Final statistical archive

This directory is generated from the canonical tables under
`data/source_data/files/` by:

```powershell
python scripts/compute_final_statistics.py
```

`all_inferential_tests.csv` is the single long-form source of truth for every
reported hypothesis test. `Table_S2.csv` is generated directly from that file;
it is not maintained independently. `Table_S3.csv` contains operational
pre-release stability diagnostics and deliberately contains no P values.

The panel-specific CSV files are filtered convenience views. Figure 4 also has
separate HC3 coefficient, common-support summary, conditional-contrast,
diagnostic, and full-range sensitivity tables. `statistics_catalog.csv`
registers descriptive panels for which inferential statistics are not
applicable. `qa_summary.json` contains machine-checkable invariants.

Full raw SLiM stdout remains external because it is about 5.1 GB. The exact
selected raw-file inventory and hashes are recorded in
`data/external_raw_file_manifest.csv.gz`. Its public retrieval URI is pending
the external archive deposit and is not fabricated here.

