#!/bin/bash
export DECODO_AUTH_TOKEN="VTAwMDAzODA1MDQ6UFdfMWI3MjgzMzRmOTE4NjdlMmU3ZDY4ZWVmNzE4ZDEwMzY1"
cd /root/.openclaw/workspace/skills/amazon-inventory-monitor
python3 check_inventory.py --customer-id 3674729801
