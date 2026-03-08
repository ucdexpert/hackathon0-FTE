#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test to show orchestrator detecting files in Needs_Action folder.
"""

import sys
from pathlib import Path

# Add scripts folder to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from orchestrator import Orchestrator

# Create orchestrator instance
orchestrator = Orchestrator('.', check_interval=5)

print("=" * 60)
print("Testing Orchestrator File Detection")
print("=" * 60)

# Check pending actions
pending = orchestrator.check_pending_actions()

print()
if pending:
    print(f"SUCCESS: Found {len(pending)} file(s) in Needs_Action/")
    print("\nFiles detected:")
    for f in pending:
        print(f"  - {f.name}")
else:
    print("No pending files in Needs_Action/")

print()
print("Dashboard stats:")
print(f"  Needs_Action count: {orchestrator.count_files(orchestrator.needs_action)}")
print(f"  Pending_Approval count: {orchestrator.count_files(orchestrator.pending_approval)}")
print(f"  Inbox count: {orchestrator.count_files(orchestrator.inbox)}")
