#!/bin/bash
# PartnerBoost Product Selector Runner

cd "$(dirname "$0")"

# Default parameters
TOKEN="${PARTNERBOOST_TOKEN:-}"
UID="${PARTNERBOOST_UID:-}"
COUNTRY="US"
MIN_PRICE="100"
MIN_REVIEWS="20"
MIN_RATING="4.0"
OUTPUT="/root/.openclaw/workspace/logs/partnerboost_selected_products.csv"

echo "=== PartnerBoost Product Selector ==="
echo ""

# Check if token provided
if [ -z "$TOKEN" ]; then
    echo "Error: No token provided"
    echo "Usage: PARTNERBOOST_TOKEN=xxx PARTNERBOOST_UID=yyy $0 [options]"
    echo ""
    echo "Options:"
    echo "  --country US          Country code (default: US)"
    echo "  --min-price 100       Minimum price"
    echo "  --min-reviews 20     Minimum reviews"  
    echo "  --min-rating 4.0     Minimum rating"
    exit 1
fi

# Build command
CMD="python3 main.py -t '$TOKEN' -u '$UID' --country '$COUNTRY' --min-price '$MIN_PRICE' --min-reviews '$MIN_REVIEWS' --min-rating '$MIN_RATING' -o '$OUTPUT'"

echo "Running: $CMD"
eval $CMD

echo ""
echo "Output: $OUTPUT"