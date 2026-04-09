#!/bin/bash
# Amazon URL Suffix Monitor - Wrapper Script
# Checks all Amazon ads for missing final_url_suffix and reports to Feishu

SCRIPT_DIR="/root/.openclaw/workspace/autoads/scripts"
LOG_FILE="/root/.openclaw/workspace/logs/amazon_suffix_check.log"
OUTPUT_FILE="/root/.openclaw/workspace/logs/amazon_suffix_report.txt"

cd "$SCRIPT_DIR"

# Run the check and save output (with --pause to auto-pause problematic campaigns)
python3 check_suffix.py --pause 2>&1 | tee "$LOG_FILE" > "$OUTPUT_FILE"

EXIT_CODE=${PIPESTATUS[0]}

echo "---" >> "$LOG_FILE"
echo "Check completed at $(date)" >> "$LOG_FILE"
echo "Exit code: $EXIT_CODE" >> "$LOG_FILE"

exit 0
