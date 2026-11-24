# Process 2: authoritative lineage audit

Status: candidate for three-party review  
Prepared: 2026-11-24  
Scope: every row in `config/figure_data_map.csv`

## Acceptance rule

Process 2 resolves which visual artifact, simulation-level values, statistical output and plotting implementation belong to each frozen publication row. It does not yet copy the values into repository Source Data workbooks or rerun the statistical analyses; those are Processes 3 and 4.

Acceptance requires all of the following:

- all 45 frozen rows have a non-placeholder lineage entry;
- descriptive panels explicitly say `not applicable` instead of inventing a statistical test;
- final-20 and final-100 material is not silently mixed;
- known stale products are quarantined and linked to the raw inputs needed for correction;
- the main agent and two independent reviewers agree with the lineage decisions.

## Resolution summary

- 37 rows have a directly resolved visual, source, statistics and code lineage.
- four Supplementary Figure S3 rows have resolved data and plotting logic, but the six-panel workbench function must be refactored to emit only the accepted four-panel publication figure in Process 5.
- Supplementary Figure S1B has a complete raw trajectory lineage; its displayed significance values must be recomputed from final-20 values in Process 4.
- Figure 2E, Figure 3E and Supplementary Figure S1C have complete raw trajectory lineages but their existing association products use the wrong final-100 NNI window. They are explicitly marked for rebuild and are not accepted as final-20 Source Data.

There are no remaining `PENDING_TRACE` values in the panel map.

## Material finding: association-window mismatch

The current axis labels for Figure 2E and Figure 3E say final 20 weeks. However, the CSV files consumed by the current redraw scripts identify their control metric as `arithmetic mean NNI over final 100 weeks per simulation`.

The affected stale files are:

- `文章终稿数据/Figure3/processed_source/Figure3_source_panelE_association.csv`;
- `文章终稿数据/Figure3/processed_source/Figure3_panelE_exact_spearman.csv`;
- `new_main_figure_task/.endpoint20_raw/Figure4/unique/11/11d1e8b802dc31b4f9dccc5c1f735f97b52e3a0f139fa91b1d0bf57ba3b05b0a_Figure4_source_panelE_association.csv`;
- `文章终稿数据/Figure4/processed_source_final/Figure4_panelE_exact_spearman.csv`;
- the current S1C loader in `code/redraw_s1_figure3e_refined.py`.

These files remain historical provenance only. Changing their labels would not correct the values.

## Correct raw lineages for the rebuild

### Figure 2E and Supplementary Figure S1B

Use:

`文章终稿数据/Figure3/raw_or_authoritative_source/source_tables/Figure3_panelE_logs14_trajectory_tidy.csv.gz`

The table contains `file`, `h`, `treatment`, `rep`, `week`, `nni`, `pop_size` and `zbar`. The approved 20 filenames per setting and cohort are the filenames recorded in `Figure3_source_panelE_replicate_level.csv`; this resolves the duplicated neutral 0.70 batch without selecting by row order.

For every retained simulation:

- NNI is the arithmetic mean over its final 20 recorded weeks;
- the variable-mutation trait is the population-size-weighted mean of `zbar` over its final 20 recorded weeks;
- setting summaries and confidence intervals are recomputed from the independent simulations;
- the two-sided exact Spearman test is recomputed from the seven setting summaries.

### Figure 3E and Supplementary Figure S1C

Use the complete non-raw rerun batch in:

`D:/champer实验室工作/文章figure终版/figure4（全部缺失）/rerun_logs/logs4`

Selection is restricted to filenames beginning with `spatial_control_` or `spatial_nocontrol_` and containing the `308231` seed stem. This gives exactly 20 outputs for each cohort at each of seven settings: 0.70, 0.75, 0.80, 0.85, 0.90, 0.95 and 0.99 (280 files total). The older `raw_spatial_` batch is not used because its 0.99 no-control cell has only 17 outputs.

The same final-20 rules above are applied after parsing `WT_ALLELES::`, `POPULATION_SIZE:` and `average attribute:` records. The NNI normalization follows the existing parser: observed mean NNI divided by `0.5 / sqrt(population) * area`.

## Visual authority decisions

Later single-panel SVGs are used where the user explicitly requested a panel-only redraw. For unchanged panels that were locked before the panel-only workflow, `Figures _修改提交.pptx` is the current visual authority, with slides 1, 3, 5 and 7 mapped in `figure_data_map.csv`. The earlier v174 deck remains historical provenance only and is not restored as current authority.

## Descriptive panels

Trajectory-only and reference-diagnostic panels without a prespecified inferential test are marked `not applicable` in the statistics column. This applies to Figure 1D, Figure 2D, Figure 3D, Figure 6C-D, Supplementary Figure S1A, Supplementary Figure S3 and Supplementary Figures S5-S6. Summary values and uncertainty bands will still be deposited as Source Data.

## Required downstream work

Process 3 will create the panel/table Source Data workbooks and data dictionary, including the rebuilt final-20 replicate values. Process 4 will recompute final statistics and replace all `DERIVE_FROM_FINAL20_SOURCE_IN_PROCESS4` markers. Process 5 will package self-contained plotting scripts and refactor S3 to the accepted four-panel output.
