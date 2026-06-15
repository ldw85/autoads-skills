#!/usr/bin/env python3
"""ZAFRO 8000 BTU top10 seed keywords GKP query - batch 1 (top 5 core)"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace/skills/keyword-planner')

if __name__ == "__main__":
    from run_skill import main
    sys.argv = [
        "run_skill.py",
        "--keywords",
        "zafro 8000 btu portable air conditioner, zafro portable air conditioner, 8000 btu portable air conditioner, 8000 btu air conditioner, portable air conditioner",
        "--ads-account", "6660356395",
        "--output", "file",
    ]
    main()
