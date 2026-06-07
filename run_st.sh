#!/bin/bash
cd /root/.openclaw/workspace
export PYTHONPATH=/root/.openclaw/workspace/autoads/src
python3 scripts/search_term_analyzer.py --all-spending --verbose "$@"

