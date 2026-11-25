# Data archive and Source Data dictionary

This directory contains the repository-sized values behind Main Figures 1--6,
Supplementary Figures S1--S6 and Supplementary Tables S1--S3. Full SLiM stdout
is not duplicated here. Raw-output provenance is frozen separately by dataset,
selection rule and checksum so that the large external archive can be verified.

## Layout

- `source_data/Figure*.xlsx` and `source_data/Figure_S*.xlsx`: convenient
  panel-indexed workbooks containing simulation-level endpoints or exact
  plot-summary values.
- `source_data/Table_S*.xlsx`: spreadsheet forms of the supplementary tables.
- `source_data/files/`: canonical CSV/CSV.GZ tables. Compressed files retain
  exact replicate trajectories when they are too large or unwieldy for a
  workbook.
- `source_data/source_data_catalog.csv`: path, scope, table type, dimensions and
  SHA-256 for every canonical table.
- `source_data/workbook_manifest.json`: the sheet-to-canonical-table map used to
  build the workbooks.
- `external_raw_file_manifest.csv.gz`: file-level provenance for the external
  upstream archive (created by the provenance builder). Each selected file has
  a size, SHA-256, seed-block count and inclusion/exclusion status. The manifest includes both
  raw SLiM outputs and authoritative processed inputs; it does not pretend that
  a processed table is a raw simulation log.

## Authority and independent unit

One stochastic simulation replicate is the independent unit unless the panel
map explicitly identifies a matched simulation origin. Summary ribbons and
bars are derived from those independent replicates; rows at different weeks
within one simulation are not independent replicates.

The authoritative definition for every panel is in
`../config/figure_data_map.csv`. The raw or processed lineage that supplies it
is in `../config/raw_lineage_manifest.csv`.

## Endpoint definitions

- `final20_attribute_weighted`: adult-population-size-weighted mean of the
  relevant evolving trait over the final 20 weeks/records specified by the
  panel map.
- `final20_population` or `final20_population_mean`: arithmetic population-size
  mean over the final 20 weeks/records. Eliminated populations are assigned
  zero only where the panel analysis explicitly requires it.
- `final20_nni`: arithmetic mean normalized nearest-neighbour index over the
  replicate's final 20 weeks.
- `Nmin_relative`: minimum or first-valley population size divided by the
  condition-specific normalizer used by Figure 6A.
- `B`: virtual haploid load.
- `mean_Wload`: recorded mean genetic viability under recessive load.
- `mutation_copies_per_individual`: mean number of deleterious-mutation copies
  carried by an individual.

## Common columns

| Column | Meaning |
|---|---|
| `model` / `model_std` | Panmictic or spatial simulation architecture. |
| `setting`, `h`, `drive_conversion` | Drive-conversion efficiency setting. |
| `treatment` / `cohort` | Neutral/control versus variable/functional modifier cohort. |
| `replicate` / `rep` | Independent simulation identifier within the declared condition. |
| `seed`, `origin_seed`, `branch_seed` | Random seed or matched-origin identifiers. |
| `week`, `week_relative_release` | Time in weeks, with zero at release where specified. |
| `outcome` | Mutually exclusive terminal classification used by the panel. |
| `n` / `n_active` | Actual number of finite independent simulations contributing to the row. |
| `q05`, `q25`, `median`, `q75`, `q95` | Across-replicate plot summaries. |
| `source_file`, `resolved_source`, `source_record_id` | Provenance key back to the frozen lineage. |

## Observed missingness

Figure 3E and Supplementary Figure S1C use 277 non-empty raw outputs. Every
setting-by-cohort cell has 20 simulations except the 0.99 no-control/variable
cell, which has 17. Replicates 5, 7 and 9 exist only as zero-byte files and no
non-empty replacement was found. They are not imputed or copied from another
batch. Downstream sample-size reporting and tests must use `n = 17`.

The 20 Figure 2E/S1B neutral-0.70 files each contain two seed-delimited blocks:
a superseded run followed by an appended rerun. The retained simulation is the
last complete block in each named replicate file. The Source Data explicitly
records `source_block_index = 2`, `source_block_count = 2` and the retained
seed; the two independent blocks are never averaged together.

Figure 6C and 6D use outcome-conditioned inclusion, not missing-run
imputation. P70_L contains 14 persistent outcomes and six eliminations. The 14
persistent trajectories/endpoints enter the applicable rows. P85_L and P85_N
are structurally absent from Figure 6D because all runs eliminated.

## External availability

`external_raw_file_manifest.csv.gz` currently records 580 included files and
three explicitly excluded zero-byte files. Its `retrieval_uri` values remain
blank and `availability_status` is
`local_verified_external_deposit_pending` until a public archival deposit is
provided. Local checksums make the selected inputs auditable, but Process 3
cannot be accepted as a public reproducibility archive while those retrieval
URIs are absent.

## Large trajectory tables

The exact weekly replicate values behind Figure 2D, Figure 3D, Figure 6C,
Supplementary Figure S3 and Supplementary Figure S6 are stored as compressed
CSV. Their workbooks contain plot summaries or replicate final-20 summaries
for convenient inspection and point back to the exact compressed table through
the workbook index and catalog. Supplementary Figure S5 workbooks contain the
plotted quantile summaries and a simulation-level final-20 table.

## Supplementary Table S2 dependency

The previous final-100-week Table S2 is quarantined. The current
`Table_S2.xlsx` is generated only from
`results/statistics/all_inferential_tests.csv`, which is rebuilt from the
canonical final-20 Source Data by `scripts/compute_final_statistics.py`.
`results/statistics/Table_S2.csv` and the workbook are generated views rather
than independently edited statistical records.

## Regeneration

Run, in order:

```text
python scripts/build_source_data.py
python scripts/compute_final_statistics.py
python scripts/build_workbook_tables.py
python scripts/build_external_raw_manifest.py
node scripts/build_source_workbooks.mjs
python scripts/build_supplementary_tables.py
node scripts/verify_source_workbooks.mjs
python scripts/verify_source_data.py
python scripts/verify_statistics.py
```

Figure workbooks use the spreadsheet-artifact workflow; Supplementary Tables
S1–S3 are then rebuilt deterministically from their canonical CSV staging
tables by `build_supplementary_tables.py`. All
canonical file hashes and dimensions must match `source_data_catalog.csv` after
regeneration.

After the external raw-data deposit is public, rebuild its provenance rows with
the immutable DOI or archive URL rather than editing the compressed CSV by
hand:

```text
python scripts/build_external_raw_manifest.py --retrieval-uri <DOI-or-archive-URL>
```

The builder then changes `availability_status` to
`public_external_archive`; the verification gate still checks that every
included row has a non-empty retrieval URI.
