# Reproducibility archive scope

Status: process 1 candidate, awaiting two independent reviewer approvals  
Prepared: 2026-11-24  
Working branch: `reproducibility-archive`

## Purpose

This archive will contain the material needed to reproduce every published main-figure panel, supplementary-figure panel and supplementary table without uploading the full raw SLiM output to GitHub.

The target publication scope is:

- Main Figures 1–6.
- Supplementary Figures S1–S6.
- Supplementary Tables S1–S3.

The panel inventory frozen for the first-pass map is:

| Item | Panels / table units |
|---|---|
| Figure 1 | A–D |
| Figure 2 | A–E |
| Figure 3 | A–E |
| Figure 4 | A–C |
| Figure 5 | A–B |
| Figure 6 | A–D |
| Supplementary Figure S1 | A–C |
| Supplementary Figure S2 | A–C |
| Supplementary Figure S3 | A–D |
| Supplementary Figure S4 | A–D, including mean genetic viability (`W_load`) |
| Supplementary Figure S5 | A–C; Panmictic 0.85 excluded |
| Supplementary Figure S6 | A–B |
| Supplementary Tables | S1, S2 and S3 |

## Authority rule

Historical Word legends and the earlier combined PowerPoint are not treated as a single authoritative source because they still contain superseded numbering and endpoint definitions, including deck Figure 2–7 numbering and final-100-week wording.

The historical combined deck is retained only as visual provenance. Its old-to-current mapping is:

| Current item | Historical v174 item | Slide |
|---|---:|---:|
| Figure 1 | Figure 2 | 1 |
| Figure 2 | Figure 3 | 3 |
| Figure 3 | Figure 4 | 5 |
| Figure 4 | Figure 5 | 7 |
| Figure 5 | Figure 7 | 10 |
| Figure 6 | Figure 6 | 9 |
| Supplementary Figures S1–S5 | same historical label | 13–17 |

It must not be entered as a current visual authority candidate in the panel map.

For archive construction, authority is resolved in this order:

1. The user's latest explicit figure-by-figure instruction.
2. The latest locked single-panel or combined-figure artifact produced after that instruction.
3. The exact plotting script and data files used to create that artifact.
4. Current processed-source validation tables and statistical outputs.
5. Matching raw simulation outputs or an external immutable raw-data archive.
6. Historical decks, Word legends and old workbench maps for provenance only.

No file is considered authoritative merely because its filename contains `final`.

## Current endpoint rules to preserve

- Simulation replicate is the independent unit unless a documented matched-origin analysis is used.
- Final trait values are adult-population-size-weighted means over the final 20 weeks/records where specified.
- Final population size is the arithmetic mean over the final 20 weeks/records, with elimination handled according to the panel's analysis script.
- Figure 3 two-sided permutation analyses use 10,000 permutations.
- Figure 6 Panel D reports relative population size over the final 20 weekly records.
- Supplementary Figure S1 uses final-20-week NNI and includes both neutral and variable groups in Panel A.
- Supplementary Figure S4 stability diagnostics evaluate 2.5%, 5% and 10% thresholds and include `W_load`.
- Supplementary Figure S5 excludes Panmictic 0.85.
- Supplementary Figure S6 displays replicate-level trajectories rather than only 20-replicate means.

## Required repository destinations

The completed archive will use these destinations:

```text
scripts/                      final launch, processing, statistics and plotting code
config/                       run manifest, parameter table and figure-to-data map
data/README.md                data dictionary, provenance and external raw-data links
data/source_data/             replicate-level or panel-level values behind every panel/table
results/statistics/           final numerical statistical results
docs/                         run instructions, environment and review records
```

The launch layer will contain only:

1. one parameterized SLiM runner;
2. one configuration table listing figure/test, parameters, replicate count and seed or deterministic seed rule;
3. one short run guide.

## Explicit exclusions from GitHub

- Full raw SLiM output files and large raw archives are not copied into `data/source_data/`.
- Superseded drawings, temporary render directories, patch graphics and historical candidate decks are not publication source data.
- A summary table is not accepted as Source Data if the plotted independent-replicate values are recoverable.

Raw simulation data is represented by checksummed provenance records. A retrieval path is intentionally omitted under the current archive policy.

## Process-1 acceptance condition

Process 1 freezes scope only. It is accepted when all three reviewers agree that:

- every current figure and table is represented;
- current numbering and panel inventory are correct;
- superseded numbering and endpoint definitions are clearly quarantined;
- the initial panel-level mapping has a stable key and does not claim unverified provenance as final.

Provenance, statistical and rerun fields marked `PENDING_TRACE` are resolved in later gated processes.
