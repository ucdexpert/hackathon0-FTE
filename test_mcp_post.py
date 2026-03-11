#!/usr/bin/env python3
"""Test MCP server post functionality"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "scripts" / "mcp"))

from linkedin_mcp_server import MCPServer

CONTENT = "MCP Server Test - AI Employee working! #AI #Automation"

print("=" * 60)
print("  TESTING LINKEDIN MCP SERVER POST")
print("=" * 60)
print(f"\nContent: {CONTENT}\n")

server = MCPServer()

# Check auth
is_auth = server.client.is_authenticated()
print(f"Auth: {'✓ YES' if is_auth else '✗ NO'}\n")

if not is_auth:
    print("Run: python scripts/mcp/linkedin_mcp_server.py --authenticate\n")
    sys.exit(1)

print("Posting (browser will open)...\n")
result = server.client.post(CONTENT)

print("\n" + "=" * 60)
print("  RESULT")
print("=" * 60)
if result.get("success"):
    print(f"  ✓ Status: POSTED")
    print(f"  Screenshot: {result.get('screenshot')}")
    print(f"  Timestamp: {result.get('timestamp')}")
else:
    print(f"  ✗ Status: FAILED")
    print(f"  Error: {result.get('message')}")
print("=" * 60 + "\n")
