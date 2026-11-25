#!/usr/bin/env bash
# Recover the exact historical runtime assets used for Figure 5 / Figure S3.
# Run this on the cluster. The resulting archive belongs in the external raw
# data deposit, not in Git.

set -euo pipefail

SOURCE_ROOT="${1:-/lustre2/jchamper_pkuhpc/xinyue/mutation/migration/final}"
OUTPUT_DIR="${2:-$PWD/figure5_s3_runtime_assets}"
MODEL_NAME="reprising.formal_experiment.pinned.slim"
RUNNER_NAME="formal_drive_task1.py"
EXPECTED_MODEL_SHA256="94e465ec99eaef5646cdfc1828c8121cb0b7df4b4290a0f7622e04624def8812"

MODEL="$SOURCE_ROOT/$MODEL_NAME"
RUNNER="$SOURCE_ROOT/$RUNNER_NAME"
CHECKPOINT_ROOT="$SOURCE_ROOT/formal_100/checkpoints"
STAGE="$OUTPUT_DIR/stage"
ARCHIVE="$OUTPUT_DIR/figure5_s3_runtime_assets.tar.gz"

command -v sha256sum >/dev/null 2>&1 || { echo "ERROR: sha256sum unavailable" >&2; exit 1; }
command -v tar >/dev/null 2>&1 || { echo "ERROR: tar unavailable" >&2; exit 1; }

[[ -f "$MODEL" ]] || { echo "ERROR: model not found: $MODEL" >&2; exit 1; }
[[ -f "$RUNNER" ]] || { echo "ERROR: runner not found: $RUNNER" >&2; exit 1; }

actual_hash="$(sha256sum "$MODEL" | awk '{print $1}')"
[[ "$actual_hash" == "$EXPECTED_MODEL_SHA256" ]] || {
    echo "ERROR: model hash mismatch: $actual_hash" >&2
    exit 1
}

[[ ! -e "$STAGE" ]] || {
    echo "ERROR: staging path already exists; choose a new output directory: $STAGE" >&2
    exit 1
}
mkdir -p -- "$STAGE/model" "$STAGE/checkpoints/evolving" "$STAGE/checkpoints/uniform"
cp -- "$MODEL" "$STAGE/model/$MODEL_NAME"
cp -- "$RUNNER" "$STAGE/model/$RUNNER_NAME"

for mode in evolving uniform; do
    for seed in $(seq 61001 61100); do
        src="$CHECKPOINT_ROOT/$mode/seed_$seed/checkpoint.bin"
        dst="$STAGE/checkpoints/$mode/seed_$seed"
        [[ -s "$src" ]] || { echo "ERROR: missing/non-empty checkpoint required: $src" >&2; exit 1; }
        mkdir -p -- "$dst"
        cp -- "$src" "$dst/checkpoint.bin"
    done
done

checkpoint_count="$(find "$STAGE/checkpoints" -type f -name checkpoint.bin | wc -l | tr -d ' ')"
[[ "$checkpoint_count" == "200" ]] || {
    echo "ERROR: expected 200 checkpoints, found $checkpoint_count" >&2
    exit 1
}

(
    cd -- "$STAGE"
    find . -type f -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt
)
tar -czf "$ARCHIVE" -C "$STAGE" .
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"

echo "PASS: recovered hash-matched model, runner and 200 checkpoints"
echo "Archive: $ARCHIVE"
echo "Checksum: $ARCHIVE.sha256"
