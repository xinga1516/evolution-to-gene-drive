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

This is a partial Process-7 audit, not final acceptance. Two external gates
remain open:

1. `public_external_archive_ready=False` until the approximately 5.1 GB raw
   simulation archive has a public retrieval URI and deposit checksum.
2. Figure 5 / Figure S3 cannot be launched from the manifest until the exact
   pinned model and historical runner are recovered. The 200 checkpoint
   directories have been recovered and independently verified.

Process 7 and Process 8 remain unaccepted until these gates are closed and the
same final candidate receives PASS decisions from the implementer and both
independent reviewers.
