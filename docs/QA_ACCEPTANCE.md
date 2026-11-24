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
| 1 | Freeze publication scope; create panel-level `config/figure_data_map.csv`; quarantine superseded numbering/window definitions | READY_FOR_REVIEW | PENDING | PENDING | NO |
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
