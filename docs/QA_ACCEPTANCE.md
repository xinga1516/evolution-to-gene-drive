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
