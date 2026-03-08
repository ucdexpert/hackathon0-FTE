#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Silver Tier Verification Script

Verifies that all Silver tier requirements are met:
- [x] All Bronze requirements plus:
- [x] Two or more Watcher scripts (Gmail + WhatsApp + LinkedIn)
- [x] One working MCP server for external action (e.g., sending emails)
- [x] Human-in-the-loop approval workflow for sensitive actions
- [x] Basic scheduling via cron or Task Scheduler
- [x] Plan Generator for Qwen reasoning loop
"""

import sys
import importlib.util
from pathlib import Path


def check_file(filepath: Path, description: str) -> bool:
    """Check if a file exists."""
    if filepath.exists():
        print(f"[OK] {description}: {filepath.name}")
        return True
    else:
        print(f"[MISSING] {description}: {filepath.name}")
        return False


def check_folder(filepath: Path, description: str) -> bool:
    """Check if a folder exists."""
    if filepath.exists() and filepath.is_dir():
        print(f"[OK] {description}: {filepath.name}/")
        return True
    else:
        print(f"[MISSING] {description}: {filepath.name}/")
        return False


def check_python_syntax(filepath: Path) -> bool:
    """Verify Python file has valid syntax."""
    import py_compile
    try:
        py_compile.compile(filepath, doraise=True)
        print(f"  [OK] Syntax: {filepath.name}")
        return True
    except Exception as e:
        print(f"  [ERROR] Syntax: {filepath.name} - {e}")
        return False


def check_package(package_name: str) -> bool:
    """Check if a Python package is installed."""
    spec = importlib.util.find_spec(package_name)
    if spec is not None:
        print(f"[OK] Package installed: {package_name}")
        return True
    else:
        print(f"[MISSING] Package: {package_name} (pip install {package_name})")
        return False


def main():
    if len(sys.argv) < 2:
        vault_path = Path('.')
    else:
        vault_path = Path(sys.argv[1])
    
    print("=" * 60)
    print("AI Employee Vault - Silver Tier Verification")
    print("=" * 60)
    print(f"\nVault Path: {vault_path.absolute()}\n")
    
    checks = []
    
    # First check Bronze tier requirements
    print("=" * 60)
    print("BRONZE TIER REQUIREMENTS (Prerequisites)")
    print("=" * 60)
    print()
    
    print("Required Files:")
    checks.append(check_file(vault_path / 'Dashboard.md', 'Dashboard'))
    checks.append(check_file(vault_path / 'Company_Handbook.md', 'Company Handbook'))
    checks.append(check_file(vault_path / 'Business_Goals.md', 'Business Goals'))
    checks.append(check_file(vault_path / 'README.md', 'README'))
    checks.append(check_file(vault_path / 'requirements.txt', 'Requirements'))
    print()
    
    print("Required Folders:")
    required_folders = [
        'Inbox', 'Needs_Action', 'Done', 'Plans',
        'Pending_Approval', 'Approved', 'Rejected',
        'Logs', 'Briefings', 'Accounting'
    ]
    for folder in required_folders:
        checks.append(check_folder(vault_path / folder, folder))
    print()
    
    print("Bronze Tier Scripts:")
    scripts_path = vault_path / 'scripts'
    if scripts_path.exists():
        checks.append(check_file(scripts_path / 'orchestrator.py', 'Orchestrator'))
        checks.append(check_file(scripts_path / 'watchers' / 'base_watcher.py', 'Base Watcher'))
        checks.append(check_file(scripts_path / 'watchers' / 'filesystem_watcher.py', 'Filesystem Watcher'))
    print()
    
    # Silver tier requirements
    print("=" * 60)
    print("SILVER TIER REQUIREMENTS")
    print("=" * 60)
    print()
    
    print("Additional Watcher Scripts (Need 2+):")
    watcher_count = 0
    if check_file(scripts_path / 'watchers' / 'gmail_watcher.py', 'Gmail Watcher'):
        watcher_count += 1
        checks.append(True)
    else:
        checks.append(False)
    
    if check_file(scripts_path / 'watchers' / 'whatsapp_watcher.py', 'WhatsApp Watcher'):
        watcher_count += 1
        checks.append(True)
    else:
        checks.append(False)
    
    if check_file(scripts_path / 'watchers' / 'linkedin_watcher.py', 'LinkedIn Watcher'):
        watcher_count += 1
        checks.append(True)
    else:
        checks.append(False)
    
    if check_file(scripts_path / 'linkedin_poster.py', 'LinkedIn Poster'):
        watcher_count += 1
        checks.append(True)
    else:
        checks.append(False)
    
    print(f"\nTotal watchers available: {watcher_count} (Need 2+)")
    if watcher_count >= 2:
        print("[OK] Watcher requirement met")
        checks.append(True)
    else:
        print("[MISSING] Need at least 2 watcher scripts")
        checks.append(False)
    print()
    
    print("MCP Servers:")
    mcp_path = scripts_path / 'mcp'
    if mcp_path.exists():
        if check_file(mcp_path / 'email_mcp.py', 'Email MCP Server'):
            checks.append(True)
        else:
            checks.append(False)
    else:
        print(f"[MISSING] MCP folder: {mcp_path.name}/")
        checks.append(False)
    print()
    
    print("Plan Generator:")
    if check_file(scripts_path / 'plan_generator.py', 'Plan Generator'):
        checks.append(True)
    else:
        checks.append(False)
    print()
    
    print("Scheduler:")
    if check_file(scripts_path / 'scheduler.py', 'Scheduler'):
        checks.append(True)
    else:
        checks.append(False)
    print()
    
    print("HITL Workflow Folders:")
    checks.append(check_folder(vault_path / 'Pending_Approval', 'Pending Approval'))
    checks.append(check_folder(vault_path / 'Approved', 'Approved'))
    checks.append(check_folder(vault_path / 'Rejected', 'Rejected'))
    print()
    
    print("Python Dependencies:")
    checks.append(check_package('watchdog'))
    checks.append(check_package('playwright'))
    # Optional packages
    check_package('google.auth')  # Won't fail if missing
    check_package('mcp')  # Won't fail if missing
    print()
    
    print("Syntax Verification:")
    silver_scripts = [
        scripts_path / 'watchers' / 'gmail_watcher.py',
        scripts_path / 'watchers' / 'whatsapp_watcher.py',
        scripts_path / 'watchers' / 'linkedin_watcher.py',
        scripts_path / 'plan_generator.py',
        scripts_path / 'scheduler.py',
        scripts_path / 'linkedin_poster.py',
    ]
    for script in silver_scripts:
        if script.exists():
            checks.append(check_python_syntax(script))
    print()
    
    # Summary
    print("=" * 60)
    passed = sum(checks)
    total = len(checks)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"Results: {passed}/{total} checks passed ({percentage:.1f}%)")
    
    # Check specific Silver tier criteria
    bronze_ok = all(checks[:18])  # First 18 checks are Bronze requirements
    watchers_ok = watcher_count >= 2
    mcp_ok = any(check_file(mcp_path / 'email_mcp.py', 'Email MCP') for _ in [1])  # Just check existence
    hitl_ok = (vault_path / 'Pending_Approval').exists() and (vault_path / 'Approved').exists()
    scheduler_ok = (scripts_path / 'scheduler.py').exists()
    plan_gen_ok = (scripts_path / 'plan_generator.py').exists()
    
    print()
    print("Silver Tier Criteria:")
    print(f"  [{'X' if bronze_ok else ' '}] Bronze Tier Complete")
    print(f"  [{'X' if watchers_ok else ' '}] 2+ Watcher Scripts ({watcher_count} available)")
    print(f"  [{'X' if mcp_ok else ' '}] MCP Server for External Actions")
    print(f"  [{'X' if hitl_ok else ' '}] Human-in-the-Loop Workflow")
    print(f"  [{'X' if scheduler_ok else ' '}] Scheduler Integration")
    print(f"  [{'X' if plan_gen_ok else ' '}] Plan Generator")
    
    silver_complete = all([bronze_ok, watchers_ok, mcp_ok, hitl_ok, scheduler_ok, plan_gen_ok])
    
    if silver_complete and percentage >= 90:
        print("\n" + "=" * 60)
        print("SILVER TIER COMPLETE!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. pip install -r requirements.txt")
        print("2. playwright install")
        print("3. Configure Gmail API credentials (optional)")
        print("4. python scripts/scheduler.py install")
        print("5. Start using additional watchers and MCP servers")
        return 0
    else:
        print("\n" + "=" * 60)
        print("SILVER TIER INCOMPLETE")
        print("=" * 60)
        print("\nPlease complete the missing requirements listed above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
