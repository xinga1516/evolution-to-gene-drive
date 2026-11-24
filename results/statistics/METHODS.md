# Statistical methods frozen for the final figures

## General rules

- The independent unit is one simulation unless a row explicitly identifies a
  matched origin seed or a parameter-setting mean.
- All tests are two-sided. Monte-Carlo permutation P values use the plus-one
  definition `(extreme + 1) / (B + 1)` and therefore are never zero.
- Figure 1–3 and S1 continuous comparisons use 10,000 permutations. Figure 6
  uses 200,000 permutations, matching its prespecified higher-resolution
  analysis. The actual seed and extreme-count are stored on every row.
- Exact Spearman tests enumerate all permutations and record the enumeration
  count. Figure 2E and Figure 3E use seven parameter-setting means (`7! =
  5,040`), not 140 simulation replicates as independent observations.
- Actual included sample sizes are computed from Source Data. Missing runs are
  not imputed. In Figure 3E/S1C, the 0.99 variable-mutation group has n=17
  because three archived files are zero bytes.
- P values, effect directions and sample sizes are machine-readable in
  `all_inferential_tests.csv`; symbols are convenience fields only.

## Prespecified multiplicity families

- Figure 1A, 2A and 3A: Holm across four condition-specific outcome tests in
  each panel.
- Figure 1B–C, 2B–C and 3B–C: Holm across four condition-specific contrasts
  within each panel.
- Figure 4: separate Holm families across three traits for the joint realized
  SD effect, architecture effect, and interaction. Low/mid/high same-SD path
  contrasts form a three-test Holm family within each trait.
- Figure 5A: Holm across four prespecified exact McNemar tests. Figure 5B:
  Holm across six estimable primary paired t tests. The n=7 comparison also
  has a separately labelled exact sign-flip sensitivity analysis.
- Figure 6A: Holm across four comparisons. Figure 6B is one prespecified P70
  elimination contrast. Figure 6D: Holm across the three estimable comparisons;
  P85 is structurally not estimable because both conditions eliminated.
- S1B and S1C: Holm across seven setting comparisons within each panel.
- S2: Holm across the three estimable lower-SD strata within each trait. A
  one-setting stratum is labelled not estimable.

## Panel-specific methods

- Figure 1A and 2A use two-sided Fisher–Freeman–Halton fixed-margin exact tests
  of terminal outcome distributions.
- Figure 3A and Figure 6B use two-sided Fisher exact tests.
- Figure 4 fits `endpoint ~ SD_0.01 * Path` within empirical common support.
  Inference uses HC3 covariance. Joint Wald tests assess realized-SD and
  architecture effects; conditional path contrasts are evaluated at the
  lower quartile, median and upper quartile of common-support realized SD.
  The shared `m=50, b=b_min` setting cannot identify a path effect and is
  excluded from both comparison arms. Full-range fits are sensitivity analyses.
- Figure 5 uses matched `origin_seed` as the paired unit. Panel A uses exact
  McNemar tests. Panel B uses paired t tests and an exact sign-flip sensitivity
  test for the n=7 contrast.
- Figure 6D estimates load differences conditional on long-term persistence
  using arithmetic mean relative population size over the final 20 weekly
  records.
- S4/Table S3 is not a null-hypothesis test. Four 250-week block means from the
  last 1,000 pre-release weeks are first averaged across 20 simulations per
  model. `R_trend` is the fitted absolute change from week 5,000 to 5,999
  divided by the fourth block mean; `R_last` is the absolute M4–M3 change
  divided by M4. Operational stability requires both values to be strictly
  below 2.5%, 5%, or 10%.

Descriptive trajectory panels (Figure 1D, 2D, 3D, 6C, S3, S5 and S6), S1A,
and Table S1 do not receive inferential P values.
