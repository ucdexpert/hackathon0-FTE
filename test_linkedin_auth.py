#!/usr/bin/env python3
"""Test LinkedIn authentication"""
import sys
from pathlib import Path

# Add scripts/mcp to path
script_dir = Path(__file__).parent / "scripts" / "mcp"
sys.path.insert(0, str(script_dir))

from linkedin_mcp_server import MCPServer

server = MCPServer()
is_auth = server.client.is_authenticated()

print("\n" + "="*60)
print("LINKEDIN AUTHENTICATION STATUS")
print("="*60)
print(f"\nStatus: {'✓ AUTHENTICATED' if is_auth else '✗ NOT AUTHENTICATED'}")
print(f"Session path: {server.client.session_path}")

if not is_auth:
    print("\n→ Run authentication with:")
    print("  python scripts/mcp/linkedin_mcp_server.py --authenticate")
print("="*60 + "\n")
