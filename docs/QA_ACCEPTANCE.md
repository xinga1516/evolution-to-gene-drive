# Three-party acceptance log

No process may be marked accepted unless the implementer and both independent reviewers record an explicit `PASS` for the same candidate revision.

## Roles

- Implementer: primary Codex agent (`root`).
- Reviewer 1: independent data/code-provenance reviewer.
- Reviewer 2: independent statistics/reproducibility reviewer.

Reviewers must not convert `PENDING`, `NOT ASSESSABLE` or a conditional approval into `PASS`.

## Gate log

| Process | Deliverable | Implementer | Reviewer 1 | Reviewer 2 | Accepted |
|---|---|---|---|---|---|
| 1 | Freeze publication scope; create panel-level `config/figure_data_map.csv`; quarantine superseded numbering/window definitions | PASS | PASS | PASS | YES |
| 2 | Resolve one authoritative data and plotting lineage for every mapped row | PENDING | PENDING | PENDING | NO |
| 3 | Build `data/source_data/` and data dictionary with external raw-data provenance | PENDING | PENDING | PENDING | NO |
| 4 | Freeze statistical code and numerical outputs in `results/statistics/` | PENDING | PENDING | PENDING | NO |
| 5 | Freeze final plotting scripts, environment and figure-data mapping | PENDING | PENDING | PENDING | NO |
| 6 | Build parameterized SLiM runner, run manifest and short run guide | PENDING | PENDING | PENDING | NO |
| 7 | End-to-end clean-room reproduction and repository completeness audit | PENDING | PENDING | PENDING | NO |
| 8 | Commit, push and final remote verification | PENDING | PENDING | PENDING | NO |

## Review record format

For each process, reviewers append:

```text
Candidate commit: <hash>
Reviewer: <role/name>
Decision: PASS | FAIL
Evidence checked: <paths and commands>
Blocking findings: <none or numbered list>
```

If any party records `FAIL`, the process remains unaccepted. A repaired candidate requires a new review by all three parties.

## Process 1 accepted review record

Candidate commit: `527acd902c96e07c5fe38fa93ef92c03b101d278`

### Implementer

- Reviewer: primary Codex agent (`root`)
- Decision: `PASS`
- Evidence checked: 45 CSV rows; 45 unique `record_id` values; expected panel/table counts; existence of every non-`PENDING_TRACE` candidate path; `git diff --check`; current user instructions for final-20 windows, panel exclusions and replicate definitions.
- Blocking findings: none after the repairs in `527acd9`.

### Reviewer 1

- Reviewer: independent data/code-provenance reviewer
- Decision: `PASS`
- Evidence checked: full scope, gate and map; all 45 records; all non-pending paths; current S1, S3–S6 and Figure 6 artifacts/scripts/data; historical v174 numbering and wording.
- Blocking findings: none. S1C rebuild, S3 plot-script tracing and remaining `PENDING_TRACE` fields are explicitly deferred to later processes.

### Reviewer 2

- Reviewer: independent statistics/reproducibility reviewer
- Decision: `PASS`
- Evidence checked: all 45 rows; Figure 3 10,000-permutation outputs/scripts; Figure 6A and 6D endpoints; S1, S3, S4/Table S3, S5 and S6 rules; independent-unit and matched-origin definitions.
- Blocking findings: none.

## Process 2 accepted review record

Candidate commit: `18537ac95acee46586372eca3ee34d242b7e5072`

### Implementer

- Reviewer: primary Codex agent (`root`)
- Decision: `PASS`
- Evidence checked: 45 unique map rows; no `PENDING_TRACE`, `TODO` or `UNKNOWN`; existence of every resolved path; 13 unique raw-lineage dataset IDs; F1/F2 panel-specific counts; complete 280-file raw batches for Figure 2E/S1B and Figure 3E/S1C; final-20 source/statistics consistency; `git diff --check` and clean worktree.
- Blocking findings: none after the repairs through `18537ac`.

### Reviewer 1

- Reviewer: independent data/code-provenance reviewer (`github_structure_reviewer`)
- Decision: `PASS`
- Evidence checked: 45/45 map entries; all declared paths; raw batch counts; S1B duplicated-cache quarantine; F1A and F1D lineages; F2A, F2B-C and F2D counts; F6D final-20 statistics rebuild flag; S3 four-panel refactor requirement.
- Blocking findings: none.

### Reviewer 2

- Reviewer: independent statistics/reproducibility reviewer (`local_archive_reviewer`)
- Decision: `PASS`
- Evidence checked: panel-specific final-20 statistics for F1B-C and F2B-C; 800-run F1A source; final-100 isolation for Figure 2E, Figure 3E and S1B-C; Figure 6D test rebuild; complete Table S2 quarantine; descriptive-panel `not applicable` decisions; split F1/F2 lineage manifests and observed replicate counts.
- Blocking findings: none.

### Post-acceptance invalidation

The preceding Process-2 acceptance was invalidated during Process-3 raw parsing. The accepted evidence incorrectly described Figure 3E/S1C as a complete 280-file batch. Independent filesystem and parsed-output checks found three zero-byte 0.99 no-control files (replicates 5, 7 and 9) and no non-empty replacements. The usable lineage is 277 simulations, with `n = 17` in that cell. Process 2 is reopened and requires a new three-party review of a repaired candidate.

## Process 2 re-accepted review record

Candidate commit: `9c514de91a94aa19483fcc08a419f737e814ae2a`

### Implementer

- Reviewer: primary Codex agent (`root`)
- Decision: `PASS`
- Evidence checked: 280 expected non-raw paths; 277 non-empty outputs; zero-byte files limited to h=0.99 no-control replicates 5, 7 and 9; no non-empty replacement in the workspace; actual raw-rebuilt cell counts; true globs retained in the panel map; non-empty filtering and no-imputation rule retained in lineage documentation.
- Blocking findings: none.

### Reviewer 1

- Reviewer: independent data/code-provenance reviewer (`github_structure_reviewer`)
- Decision: `PASS`
- Evidence checked: corrected F3E/S1C globs, `OBSERVED_MISSINGNESS_N17` status, raw-lineage selection rule, 277 usable simulations and the three zero-byte outputs.
- Blocking findings: none after the path-selector repair in `9c514de`.

### Reviewer 2

- Reviewer: independent statistics/reproducibility reviewer (`local_archive_reviewer`)
- Decision: `PASS`
- Evidence checked: same-candidate diff, raw batch and final-20 endpoint counts, n=17 observed missingness, no-imputation rule and `git diff --check`.
- Blocking findings: none.

### Second post-acceptance invalidation

The corrected-n Process-2 acceptance was reopened during Process-3 input
reconciliation.  `config/raw_lineage_manifest.csv` did not enumerate the
actual build inputs for Figure 3D, S2, S3, S4/Table S3, S5/S6 or Table S1 and
used one broad Figure-6 parent directory for Figure 6 and S4-S6.  Because this
fails the requirement for one authoritative lineage per frozen publication
item, the Process-2 gate is `NO` again.  The expanded manifest must receive a
new same-candidate PASS from the implementer and both reviewers.

## Process 2 expanded-lineage failed review record

Candidate commit: `e375e0cbf42088d67ffbac1ab0b11f7deb584f85`

- Reviewer: independent data/code-provenance reviewer (`github_structure_reviewer`)
- Decision: `FAIL`
- Evidence checked: 22 lineage paths and all distinct inputs consumed by
  `scripts/build_source_data.py`; replicate and trajectory counts in the
  declared Figure 6C and 6D sources.
- Blocking findings: Figure 6C was incorrectly described as 20 replicates per
  condition although observed counts are P70_L=14, S70_L=20 and S85_L=20.
  Figure 6D must likewise state P70_L=14 and five other cells at n=20 rather
  than use a vague availability qualifier.

## Process 2 observed-count repair failed review record

Candidate commit: `ce2894f68485e58543bd50913d485f11e99310c1`

- Reviewer: independent data/code-provenance reviewer (`github_structure_reviewer`)
- Decision: `PASS`
- Evidence checked: repaired Figure 6C/D numeric counts and the preceding
  failed-candidate record.
- Blocking findings: none within the requested narrow re-review.

- Reviewer: independent statistics/reproducibility reviewer (`local_archive_reviewer`)
- Decision: `FAIL`
- Evidence checked: every seed-delimited block in the Figure 2E/S1B raw files;
  Figure 6 terminal outcomes; S5/S6 weekly final-window record counts.
- Blocking findings: the 20 h=0.70-neutral files each contain two independent
  simulations but the parser merges them; Figure 6C/D exclusions were wrongly
  called missingness instead of outcome-conditioned inclusion; S5/S6 used an
  inclusive final-window boundary and therefore retained 21 weekly records.
