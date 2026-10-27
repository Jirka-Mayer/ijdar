#!/bin/bash
# Synthesizes a smashcima dataset on the LRC cluster in parallel.
# Run this on the head node, from the repository root (use tmux/screen):
#
#   bash smc/synthesize-on-cluster.sh \
#       datasets/olimpic-synthetic datasets/olimpic-smc-gboth both 4
#
# Arguments: INPUT_DATASET OUTPUT_DATASET GLYPHS COPIES [SLICE_COUNT]
#
# Already rendered images are skipped, so re-running with a higher
# COPIES value only renders the new copies (and also retries failed ones).
# Requires 'smc/.venv/bin/smc install-assets' to have been run before.
# Must be run from the repository root, since MuseScore is taken from
# the 'musescore/' folder in the working directory.

set -e

INPUT_DATASET="$1"
OUTPUT_DATASET="$2"
GLYPHS="$3"
COPIES="$4"
SLICE_COUNT="${5:-300}"

if [ -z "$COPIES" ]; then
    echo "Usage: $0 INPUT_DATASET OUTPUT_DATASET GLYPHS COPIES [SLICE_COUNT]"
    exit 2
fi

mkdir -p logs

CMD="smc/.venv/bin/smc synthesize \
    --input-dataset $INPUT_DATASET \
    --output-dataset $OUTPUT_DATASET \
    --glyphs $GLYPHS \
    --copies $COPIES \
    --slice-count $SLICE_COUNT \
    --slice-index \$SLURM_PROCID"

srun -u -n "$SLICE_COUNT" -p cpu-troja,cpu-ms --mem-per-cpu=4G \
    bash -c "$CMD" > "logs/smc-synthesize-$(basename "$OUTPUT_DATASET").log" 2>&1
