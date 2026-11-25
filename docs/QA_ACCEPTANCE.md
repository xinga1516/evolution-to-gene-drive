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
| 2 | Resolve one authoritative data and plotting lineage for every mapped row | PASS | PASS | PASS | YES |
| 3 | Build `data/source_data/` and data dictionary with external raw-data provenance | PASS | PASS | PASS | YES |
| 4 | Freeze statistical code and numerical outputs in `results/statistics/` | PASS | PASS | PASS | YES |
| 5 | Freeze final plotting scripts, environment and figure-data mapping | PASS | PASS | PASS | YES |
| 6 | Build parameterized SLiM runner, run manifest and short run guide | PASS | PASS | PASS | YES |
| 7 | End-to-end clean-room reproduction and repository completeness audit | PASS | PASS | PASS | YES |
| 8 | Commit, push and final remote verification | PASS | PASS | PASS | YES |

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

## Process 2 final re-accepted review record

Candidate commit: `cd7665e329b97bb2fe990098d8ca7686a6bf9053`

### Implementer

- Reviewer: primary Codex agent (`root`)
- Decision: `PASS`
- Evidence checked: 22 unique existing lineage inputs; 280 Figure-2E/S1B
  endpoints in 14 cells of n=20; last-block selection for all 20 two-block
  neutral-0.70 files; 277 Figure-3E/S1C endpoints with n=17 in the declared
  cell; Figure-6 outcome counts and structural exclusions; no final-100 input
  substituted into a final-20 rebuild; `git diff --check`.
- Blocking findings: none.

## Process 4 accepted review record

Candidate commit: `df1162922907d646808c64d4597dd73efc9daad5`

### Implementer

- Reviewer: primary Codex agent (`root`)
- Decision: `PASS`
- Evidence checked: deterministic rebuild of 111 inferential records and 8
  stability diagnostics; 63/63 statistical checks; 15/15 Source Data workbook
  checks; exact Figure 2E/Figure 3E enumeration; actual-n and missingness rules;
  Figure 4 common-support HC3 outputs and dual-input hashes; Figure 6D
  final-20 outcome-conditioned tests; Table S2 generated view; Table S3
  threshold diagnostics and provenance.
- Blocking findings: none after repairs through `df11629`.

### Reviewer 1

- Reviewer: independent data/code-provenance reviewer
  (`github_structure_reviewer`)
- Decision: `PASS`
- Evidence checked: clean Windows clone; full statistics rebuild and verifier;
  normalized script hash; Table S3 hash match; clean `git status --short` after
  regeneration; retention of all prior statistical/provenance repairs.
- Blocking findings: none.

### Reviewer 2

- Reviewer: independent statistics/reproducibility reviewer
  (`local_archive_reviewer`)
- Decision: `PASS`
- Evidence checked: independent clean clone and numerical recomputation of
  Figure 2E/Figure 3E, S1, Figure 6D, Figure 4 HC3 common-support sample sizes,
  S4/Table S3, S2 family mapping, Table S2 identity, nonzero P values and
  cross-platform normalized hashes; 63/63 checks and clean worktree.
- Blocking findings: none.

### Reviewer 1

- Reviewer: independent data/code-provenance reviewer (`github_structure_reviewer`)
- Decision: `PASS`
- Evidence checked: exact-candidate parser output; unique cell-by-replicate
  rows and retained seeds; block indices/counts; all manifest paths; F6
  terminal outcomes; F3E/S1C observed missingness; panel-map completeness.
- Blocking findings: none.

### Reviewer 2

- Reviewer: independent statistics/reproducibility reviewer (`local_archive_reviewer`)
- Decision: `PASS`
- Evidence checked: all h=0.70-neutral seed blocks and final-window records;
  independent-unit preservation; F6 outcome-conditioned inclusion; F3E/S1C
  n=17 and no imputation; final-20 versus final-100 isolation.
- Blocking findings: none.

## Process 5 accepted review record

Candidate commit: `478b45fbdf5dd0651b70fc39f9efd81f80306e5b`

### Implementer

- Reviewer: primary Codex agent (`root`)
- Decision: `PASS`
- Evidence checked: fresh Windows clone initially and finally clean; 99
  inferential records and 8 stability diagnostics rebuilt; 101/101 Source
  Data checks; 59/59 statistics checks; 15 workbooks with 61 sheets rebuilt
  deterministically; 46-row figure/table manifest and deterministic rerender
  with zero failures; PowerPoint COM export of all 17 mapped pages matched the
  frozen references exactly.
- Blocking findings: none.

### Reviewer 1

- Reviewer: independent data/code-provenance reviewer
  (`github_structure_reviewer`)
- Decision: `PASS`
- Evidence checked: independent fresh Windows clone; initial/final clean
  worktree; S2 targeted-LF checksum; two consecutive workbook builds with
  identical hashes; 101/59/15/46/17 verification gates; fixed gzip headers;
  unchanged decompressed scientific data; unchanged XLSX sheet structure,
  values, data types, styles and number formats.
- Blocking findings: none.

### Reviewer 2

- Reviewer: independent statistics/reproducibility reviewer
  (`local_archive_reviewer`)
- Decision: `PASS`
- Evidence checked: independent fresh Windows clone; full statistical rebuild;
  deterministic 15-workbook sequence; 124 canonical and resolved XLSX
  relationships; exact 17-page PowerPoint comparison; 46-row deterministic
  figure/table rebuild; S2 A--B descriptive-only scope and S3 A--F consistency;
  final clean worktree.
- Blocking findings: none. The pending public external-archive retrieval URI
  remains a Process-3 issue and is outside this Process-5 decision.

## Process 6 incomplete-launch failed review record

Candidate commit: `c542b280789b9d9a6ebafa1200486fe89d41e3d7`

### Implementer

- Reviewer: primary Codex agent (`root`)
- Decision: `FAIL`
- Evidence checked: 120-row manifest validation; clean-clone model hashes;
  Figure 4 architecture-grid identity; Figure 6 historical seed rule; default
  dry-run and explicit incomplete-batch guard; local and remote-repository
  search for the Figure 5 pinned model.
- Blocking findings: the Figure 5/S3 SLiM 5 pinned model and its 100 matched
  checkpoints are absent, so the full publication scope cannot be rerun.

### Reviewer 1

- Reviewer: independent data/code-provenance reviewer
  (`github_structure_reviewer`)
- Decision: `FAIL`
- Evidence checked: fresh clone; manifest identities and lineage IDs; frozen
  model hashes; runner validation and dry runs; derived references and Figure
  6 seeds; incomplete-run refusal.
- Blocking findings: nine Figure 5/S3 rows lack the hash-matched model and
  checkpoints and contain non-executable checkpoint descriptions; Tables S1
  and S2 lacked explicit no-simulation mappings; exact SLiM version was not
  enforced.

### Reviewer 2

- Reviewer: independent statistics/reproducibility reviewer
  (`local_archive_reviewer`)
- Decision: `FAIL`
- Evidence checked: fresh clone; F1/S1 missingness; Figure 2E and Figure 3E
  cell counts; Figure 4's 45 parameter cells; Figure 6 seeds; deterministic
  dry runs and receipts; incomplete-run refusal.
- Blocking findings: the Figure 5/S3 model, checkpoints and per-replicate
  executable checkpoint/branch parameters are absent. The runner therefore
  cannot execute those nine cells even if incomplete runs are acknowledged.

Post-review repairs in `ec71369` separate Figure 2A (100 replicates per cell),
Figure 2B--C (20 per cell) and Figure 2D (100 per spatial cell), add explicit
Table S1 and S2 no-simulation mappings, and enforce SLiM 4.0.1 for executable
rows. The Figure 5/S3 asset blocker remains; Process 6 stays unaccepted.

### Process 6 checkpoint recovery update

Local archive recovery after the failed review found the complete Figure 5/S3
checkpoint tree. `checkpoints.zip` has SHA256
`7684e5c164a8c0fcfe99a4b9d53fc93630e9aa8f12e5cc2e037fefc5390b6811`.
The repository verifier confirms 200/200 complete checkpoint directories,
evolving and uniform seeds 61001--61100, their trait histories, successful
checkpoint status records and the expected pinned-model hash. The previously
reported checkpoint blocker is therefore resolved.

At that earlier strict-scope review, Process 6 remained `NO`: the exact
`reprising.formal_experiment.pinned.slim` (expected SHA256
`94e465ec99eaef5646cdfc1828c8121cb0b7df4b4290a0f7622e04624def8812`)
and `formal_drive_task1.py` had not been recovered. The nine external Figure
5/S3 rows therefore could not be promoted to executable rows. That local-rerun
requirement was subsequently superseded by the final project policy recorded
below.

## Processes 3, 6 and 7 accepted under the final project policy

Candidate commit: `178ea8d94f85059cb8f0c27bee3f3104920db78c`

The project owner clarified that historical cluster simulations do not need
to be locally rerunnable and raw-data retrieval locations are intentionally
omitted for now. The prior stricter requirements remain documented above as
historical review findings but are not acceptance requirements for this
candidate.

### Implementer

- Reviewer: primary Codex agent (`root`)
- Decision: `PASS`
- Evidence checked: fresh clone with clean initial/final worktree; 101/101
  Source Data checks; 59/59 statistics checks; 15/15 workbooks; 46 mapped
  figure/table records and deterministic rerender; 12 locked figures and
  Tables S1--S3; 134-row launch manifest; optional-URI policy and nonlocal
  Figure 5/S3 provenance semantics.
- Blocking findings: none under the final project policy.

### Reviewer 1

- Reviewer: independent data/code-provenance reviewer
  (`github_structure_reviewer`)
- Decision: `PASS`
- Evidence checked: exact candidate; Source Data 101/101; statistics 59/59;
  workbooks 15/15; 134 manifest rows; 46 deterministic figure/table records;
  17 PowerPoint pages matched to frozen references; clean worktree; URI marked
  intentionally omitted and Figure 5/S3 rows transparently provenance-only.
- Blocking findings: none.

### Reviewer 2

- Reviewer: independent statistics/reproducibility reviewer
  (`local_archive_reviewer`)
- Decision: `PASS`
- Evidence checked: independent clean clone; Source Data 101/101; statistics
  59/59 including 99 inferential records and 8 stability diagnostics; 15
  workbooks; all 46 `FINAL_VERIFIED` mappings; 12 figures and Tables S1--S3;
  17-page PowerPoint comparison; environment and launch-layer completeness.
- Blocking findings: none.

## Process 8 accepted review record

Candidate commit: `9de86cc27d05a1fd60149bda74581d8cd372d519`

### Implementer

- Reviewer: primary Codex agent (`root`)
- Decision: `PASS`
- Evidence checked: successful push response updating
  `reproducibility-archive` from `f237c16` to `9de86cc`; local clean HEAD;
  post-push `git ls-remote --heads origin reproducibility-archive` returning
  the exact full candidate SHA.
- Blocking findings: none.

### Reviewer 1

- Reviewer: independent data/code-provenance reviewer
  (`github_structure_reviewer`)
- Decision: `PASS`
- Evidence checked: push acknowledgement, exact remote ref readback, matching
  local clean HEAD, and prior Process-7 clean-room scientific verification.
- Blocking findings: none. A full shallow clone was treated as optional
  strengthening rather than a requirement after exact ref readback succeeded.

### Reviewer 2

- Reviewer: independent statistics/reproducibility reviewer
  (`local_archive_reviewer`)
- Decision: `PASS`
- Evidence checked: exact `ls-remote` SHA, successful push acknowledgement,
  matching local clean HEAD and the accepted scientific candidate.
- Blocking findings: none.
