#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bronze Tier Verification Script

Verifies that all Bronze tier requirements are met:
- [x] Obsidian vault with Dashboard.md and Company_Handbook.md
- [x] One working Watcher script (File System monitoring)
- [x] Basic folder structure: /Inbox, /Needs_Action, /Done
- [x] Python scripts compile without errors
"""

import sys
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


def verify_python_syntax(filepath: Path) -> bool:
    """Verify Python file has valid syntax."""
    import py_compile
    try:
        py_compile.compile(filepath, doraise=True)
        print(f"  [OK] Syntax: {filepath.name}")
        return True
    except py_compile.PyCompileError as e:
        print(f"  [ERROR] Syntax: {filepath.name} - {e}")
        return False


def main():
    if len(sys.argv) < 2:
        vault_path = Path('.')
    else:
        vault_path = Path(sys.argv[1])
    
    print("=" * 60)
    print("AI Employee Vault - Bronze Tier Verification")
    print("=" * 60)
    print(f"\nVault Path: {vault_path.absolute()}\n")
    
    checks = []
    
    # Check required files
    print("Required Files:")
    checks.append(check_file(vault_path / 'Dashboard.md', 'Dashboard'))
    checks.append(check_file(vault_path / 'Company_Handbook.md', 'Company Handbook'))
    checks.append(check_file(vault_path / 'Business_Goals.md', 'Business Goals'))
    checks.append(check_file(vault_path / 'README.md', 'README'))
    checks.append(check_file(vault_path / 'requirements.txt', 'Requirements'))
    print()
    
    # Check required folders
    print("Required Folders:")
    required_folders = [
        'Inbox', 'Needs_Action', 'Done', 'Plans',
        'Pending_Approval', 'Approved', 'Rejected',
        'Logs', 'Briefings', 'Accounting'
    ]
    for folder in required_folders:
        checks.append(check_folder(vault_path / folder, folder))
    print()
    
    # Check Python scripts
    print("Python Scripts:")
    scripts_path = vault_path / 'scripts'
    if scripts_path.exists():
        checks.append(check_file(scripts_path / 'orchestrator.py', 'Orchestrator'))
        checks.append(check_file(scripts_path / 'watchers' / 'base_watcher.py', 'Base Watcher'))
        checks.append(check_file(scripts_path / 'watchers' / 'filesystem_watcher.py', 'Filesystem Watcher'))
        print()
        
        # Verify syntax
        print("Syntax Verification:")
        checks.append(verify_python_syntax(scripts_path / 'orchestrator.py'))
        checks.append(verify_python_syntax(scripts_path / 'watchers' / 'base_watcher.py'))
        checks.append(verify_python_syntax(scripts_path / 'watchers' / 'filesystem_watcher.py'))
    else:
        print("[MISSING] scripts/ folder not found")
        checks.append(False)
    print()
    
    # Summary
    print("=" * 60)
    passed = sum(checks)
    total = len(checks)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"Results: {passed}/{total} checks passed ({percentage:.1f}%)")
    
    if all(checks):
        print("\nBRONZE TIER COMPLETE!")
        print("\nNext steps:")
        print("1. pip install -r requirements.txt")
        print("2. python scripts/watchers/filesystem_watcher.py .")
        print("3. python scripts/orchestrator.py . 30")
        print("4. Drop a file in /Inbox to test")
        return 0
    else:
        print("\nBRONZE TIER INCOMPLETE")
        print("\nPlease create the missing files/folders listed above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
