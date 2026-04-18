#!/bin/bash
# CPC Analyzer - Run CPC analysis for Google Ads campaigns

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR/../archer-roi"

# Default: analyze both accounts with 6% commission rate
python3 check_cpc.py --rate 0.06 "$@"
