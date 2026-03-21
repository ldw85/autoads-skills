#!/bin/bash
# Wrapper script for daily trends - runs the trends script and outputs message

WORKDIR="/root/.openclaw/workspace"
LOG_FILE="$WORKDIR/logs/daily-trends.log"
OUTPUT_FILE="$WORKDIR/logs/trends_to_send.txt"

cd "$WORKDIR"

# Ensure directories exist
mkdir -p "$WORKDIR/logs"

# Run the trends script and capture output
OUTPUT=$(node scripts/daily-trends.mjs 2>&1)

# Extract message between MESSAGE_START and MESSAGE_END
MESSAGE=$(echo "$OUTPUT" | sed -n '/MESSAGE_START/,/MESSAGE_END/p' | sed '1d;$d')

# Save the message to file for pickup
if [ -n "$MESSAGE" ]; then
    echo "$MESSAGE" > "$OUTPUT_FILE"
    echo "[$(date)] Trends message saved to $OUTPUT_FILE" >> "$LOG_FILE"
else
    echo "[$(date)] Failed to generate trends message" >> "$LOG_FILE"
    echo "$OUTPUT" >> "$LOG_FILE"
fi
