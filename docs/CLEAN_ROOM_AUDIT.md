# Clean-room audit

Candidate scientific revision: `db7c4b4`

The candidate was cloned into a new temporary directory and checked without
using generated files from the working checkout. Results:

- Source Data verification: 101 checks, 0 failures;
- statistics verification: 59 checks, 0 failures;
- Source Data workbooks: 15 verified, 0 failures;
- publication artifact map: 46 records plus deterministic rerender, 0 failures;
- all 12 locked figures and Tables S1--S3 were materialized successfully;
- initial and final clean-clone worktrees were clean.

Under the current acceptance policy, a raw-data retrieval URI is intentionally
omitted and historical Figure 5/S3 cluster rerunning is not required. Their
absence is therefore informational rather than a clean-room failure. Final
acceptance still requires the same final candidate to receive PASS decisions
from the implementer and both independent reviewers.
