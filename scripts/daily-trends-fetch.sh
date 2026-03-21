#!/bin/bash
# Daily Google Trends Briefing Script
# Fetches, filters, and sends trending topics to David via Feishu

WORKDIR="/root/.openclaw/workspace"
SCRIPT_DIR="$WORKDIR/scripts"
LOG_FILE="$WORKDIR/logs/daily-trends.log"

# Ensure directories exist
mkdir -p "$SCRIPT_DIR" "$WORKDIR/logs"

# Fetch Google Trends RSS (US)
TRENDS=$(curl -s --max-time 30 "https://trends.google.com/trending/rss?geo=US" 2>&1)

if [ $? -ne 0 ]; then
    echo "[$(date)] Failed to fetch trends RSS" >> "$LOG_FILE"
    exit 1
fi

# Parse titles and descriptions from RSS
echo "$TRENDS" | grep -E '<title>|<description>' | sed 's/<[^>]*>//g' | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//' > "$SCRIPT_DIR/trends_raw.txt"

# Read the raw trends for AI filtering
TRENDS_CONTENT=$(cat "$SCRIPT_DIR/trends_raw.txt")

# If file is small or empty, log and exit
if [ -z "$TRENDS_CONTENT" ] || [ $(wc -c < "$SCRIPT_DIR/trends_raw.txt") -lt 100 ]; then
    echo "[$(date)] Trends content too short, skipping" >> "$LOG_FILE"
    exit 0
fi

echo "[$(date)] Fetched trends, length: $(wc -c < "$SCRIPT_DIR/trends_raw.txt")" >> "$LOG_FILE"

# The actual filtering and formatting will be done by the AI in the next step
# We'll output the raw trends to a temp file that will be processed
echo "$TRENDS_CONTENT" > "$SCRIPT_DIR/trends_for_filter.txt"

echo "[$(date)] Trends saved for AI filtering" >> "$LOG_FILE"
exit 0
