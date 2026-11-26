# Data dictionary and provenance

`source_data/` contains the values behind Main Figures 1–6, Supplementary
Figures S1–S6 and Supplementary Tables S1–S3. Each published item has one Excel
workbook. The panel-indexed worksheets contain replicate-level endpoints,
replicate trajectories or across-replicate plot summaries as appropriate.

Full SLiM stdout and other raw simulator outputs are not deposited. A public
retrieval URI for the raw outputs has not yet been specified.

## Independent unit

One stochastic simulation replicate is the independent unit unless
`config/figure_data_map.csv` explicitly identifies matched simulation origins.
Rows from different weeks of one simulation are not independent replicates.

## Key definitions

- `final20_attribute_weighted`: adult-population-size-weighted mean of the
  evolving attribute over the final 20 records.
- `final20_population` / `final20_population_mean`: mean population size over
  the final 20 records.
- `final20_nni`: mean normalized nearest-neighbour index over the final 20 records.
- `Nmin_relative`: minimum post-release population size divided by the
  condition-specific population normalizer.
- `B`: virtual haploid load.
- `mean_Wload`: recorded mean genetic viability under recessive load.
- `mutation_copies_per_individual`: mean deleterious-mutation copies carried by
  an individual.

## Common columns

| Column | Meaning |
| --- | --- |
| `model` / `model_std` | Panmictic or spatial architecture. |
| `setting`, `h`, `drive_conversion` | Drive-conversion setting. |
| `treatment` / `cohort` | Neutral/control or variable/functional modifier group. |
| `replicate` / `rep` | Independent simulation identifier. |
| `seed`, `origin_seed`, `branch_seed` | Random seed or matched-origin identifiers. |
| `week`, `week_relative_release` | Time, with zero at release where specified. |
| `outcome` | Mutually exclusive terminal classification. |
| `q05`, `q25`, `median`, `q75`, `q95` | Across-replicate plot summaries. |

## Known missingness and selection rules

- Figure 3E and Supplementary Figure S1C have 17 usable simulations in the
  0.99 variable-mutation cell; three zero-byte runs were not imputed.
- Figure 2E/S1B duplicate seed blocks retain the last complete block for each
  named replicate; the blocks are never averaged together.
- Figure 6C/D use outcome-conditioned inclusion. P70 with load contributes 14
  persistent trajectories; P85 has no persistent endpoint because all runs
  eliminated.

The exact panel-to-workbook, statistics and code mapping is recorded in
`config/figure_data_map.csv`.
