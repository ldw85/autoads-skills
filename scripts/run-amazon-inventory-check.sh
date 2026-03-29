#!/bin/bash
# Amazon Inventory Monitor - Wrapper Script
# Runs the inventory check and sends results to Feishu

CUSTOMER_ID="3674729801"
LOG_FILE="/root/.openclaw/workspace/logs/inventory_check.log"
OUTPUT_FILE="/root/.openclaw/workspace/logs/inventory_report.txt"

cd /root/.openclaw/workspace/skills/amazon-inventory-monitor

# Run the check and save output
python3 check_inventory.py --customer-id "$CUSTOMER_ID" 2>&1 | tee "$LOG_FILE" > "$OUTPUT_FILE"

# Check if there are out of stock items
OUT_OF_STOCK=$(grep -c "❌" "$OUTPUT_FILE" 2>/dev/null || echo "0")

echo "---" >> "$LOG_FILE"
echo "Check completed at $(date)" >> "$LOG_FILE"
echo "Out of stock items found: $OUT_OF_STOCK" >> "$LOG_FILE"

exit 0
