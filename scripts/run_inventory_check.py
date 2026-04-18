#!/usr/bin/env python3
"""Wrapper to run Amazon inventory check."""

import sys
import os
import json

# Add the amazon-inventory directory to path
autoads_dir = "/root/.openclaw/workspace/autoads"
inventory_dir = os.path.join(autoads_dir, "amazon-inventory")
sys.path.insert(0, autoads_dir)

# Set env from .env
env_file = os.path.join(autoads_dir, ".env")
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key] = val

# Run the script directly
customer_id = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "3674729801")

# Build command
cmd = f'cd "{autoads_dir}" && python3 amazon-inventory/check_inventory.py --customer-id {customer_id}'
result = os.popen(cmd).read()
print(result)
