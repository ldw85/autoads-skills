#!/bin/bash
# Wrapper script for Amazon opportunities analysis

WORKDIR="/root/.openclaw/workspace"
LOG_FILE="$WORKDIR/logs/amazon-opportunities.log"
OUTPUT_FILE="$WORKDIR/logs/amazon_to_send.txt"

cd "$WORKDIR"

# Ensure directories exist
mkdir -p "$WORKDIR/logs"

# Run the analysis script
OUTPUT=$(node scripts/amazon-opportunities.mjs 2>&1)

# Extract message between MESSAGE_START and MESSAGE_END
MESSAGE=$(echo "$OUTPUT" | sed -n '/MESSAGE_START/,/MESSAGE_END/p' | sed '1d;$d')

# Save the message to file
if [ -n "$MESSAGE" ]; then
    echo "$MESSAGE" > "$OUTPUT_FILE"
    echo "[$(date)] Amazon opportunities saved to $OUTPUT_FILE" >> "$LOG_FILE"
else
    echo "[$(date)] Failed to generate message" >> "$LOG_FILE"
    echo "$OUTPUT" >> "$LOG_FILE"
fi
