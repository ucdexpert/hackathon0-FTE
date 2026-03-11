#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gold Tier Verification Script

Verifies all Gold Tier requirements are met:
1. All Silver requirements (Bronze + 2+ Watchers + MCP + HITL + Scheduling)
2. Odoo accounting integration
3. Facebook integration
4. Instagram integration
5. Twitter (X) integration (optional)
6. Multiple MCP servers
7. Weekly CEO Briefing generation
8. Error recovery and graceful degradation
9. Comprehensive audit logging
10. Ralph Wiggum loop

Usage:
    python verify_gold.py <vault_path>
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class GoldTierVerifier:
    """Verifies Gold Tier completion."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.scripts_path = self.vault_path / 'scripts'
        self.watchers_path = self.scripts_path / 'watchers'
        self.mcp_path = self.scripts_path / 'mcp'
        
        self.results = {
            'bronze_requirements': [],
            'silver_requirements': [],
            'gold_requirements': [],
            'overall_status': 'pending'
        }

    def check_file_exists(self, path: Path, description: str) -> Dict:
        """Check if a file exists."""
        exists = path.exists()
        return {
            'check': description,
            'path': str(path),
            'status': 'pass' if exists else 'fail',
            'details': 'Found' if exists else 'Not found'
        }

    def check_folder_exists(self, path: Path, description: str) -> Dict:
        """Check if a folder exists."""
        exists = path.exists() and path.is_dir()
        return {
            'check': description,
            'path': str(path),
            'status': 'pass' if exists else 'fail',
            'details': 'Found' if exists else 'Not found'
        }

    def check_file_content(self, path: Path, keyword: str, description: str) -> Dict:
        """Check if file contains specific keyword."""
        if not path.exists():
            return {
                'check': description,
                'path': str(path),
                'status': 'fail',
                'details': 'File not found'
            }
        
        try:
            # Try reading with utf-8 first, then fallback to latin-1
            try:
                content = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                content = path.read_text(encoding='latin-1')
            
            contains = keyword.lower() in content.lower()
            return {
                'check': description,
                'path': str(path),
                'status': 'pass' if contains else 'fail',
                'details': f'Contains "{keyword}"' if contains else f'Missing "{keyword}"'
            }
        except Exception as e:
            return {
                'check': description,
                'path': str(path),
                'status': 'fail',
                'details': str(e)
            }

    def verify_bronze_requirements(self) -> List[Dict]:
        """Verify Bronze tier requirements."""
        checks = []
        
        # 1. Obsidian vault with Dashboard.md and Company_Handbook.md
        checks.append(self.check_file_exists(
            self.vault_path / 'Dashboard.md',
            'Dashboard.md exists'
        ))
        checks.append(self.check_file_exists(
            self.vault_path / 'Company_Handbook.md',
            'Company_Handbook.md exists'
        ))
        checks.append(self.check_file_exists(
            self.vault_path / 'Business_Goals.md',
            'Business_Goals.md exists'
        ))

        # 2. One working Watcher script
        watcher_files = list(self.watchers_path.glob('*_watcher.py')) if self.watchers_path.exists() else []
        checks.append({
            'check': 'At least one Watcher script',
            'path': str(self.watchers_path),
            'status': 'pass' if len(watcher_files) >= 1 else 'fail',
            'details': f'{len(watcher_files)} watcher(s) found'
        })

        # 3. Basic folder structure
        for folder in ['Inbox', 'Needs_Action', 'Done']:
            checks.append(self.check_folder_exists(
                self.vault_path / folder,
                f'/{folder} folder exists'
            ))

        # 4. Orchestrator
        checks.append(self.check_file_exists(
            self.scripts_path / 'orchestrator.py',
            'orchestrator.py exists'
        ))

        self.results['bronze_requirements'] = checks
        return checks

    def verify_silver_requirements(self) -> List[Dict]:
        """Verify Silver tier requirements."""
        checks = []
        
        # 1. Two or more Watcher scripts
        watcher_files = list(self.watchers_path.glob('*_watcher.py')) if self.watchers_path.exists() else []
        checks.append({
            'check': 'Two or more Watcher scripts',
            'path': str(self.watchers_path),
            'status': 'pass' if len(watcher_files) >= 2 else 'fail',
            'details': f'{len(watcher_files)} watcher(s) found'
        })

        # 2. LinkedIn auto-posting
        linkedin_post_exists = (self.scripts_path / 'linkedin_post.py').exists()
        linkedin_auto_exists = (self.scripts_path / 'linkedin_auto_post.py').exists()
        autopost_exists = (self.scripts_path / 'autopost.py').exists()
        
        checks.append({
            'check': 'LinkedIn posting script exists',
            'path': str(self.scripts_path / 'linkedin_post.py'),
            'status': 'pass' if (linkedin_post_exists or linkedin_auto_exists or autopost_exists) else 'fail',
            'details': 'Found' if (linkedin_post_exists or linkedin_auto_exists or autopost_exists) else 'Not found'
        })
        
        checks.append({
            'check': 'LinkedIn auto-post script exists',
            'path': str(self.scripts_path / 'autopost.py'),
            'status': 'pass' if (linkedin_auto_exists or autopost_exists) else 'fail',
            'details': 'Found' if (linkedin_auto_exists or autopost_exists) else 'Use linkedin_auto_post.py'
        })

        # 3. MCP server for email
        checks.append(self.check_file_exists(
            self.mcp_path / 'email_mcp.py',
            'Email MCP server exists'
        ))

        # 4. HITL approval workflow
        checks.append(self.check_folder_exists(
            self.vault_path / 'Pending_Approval',
            '/Pending_Approval folder exists'
        ))
        checks.append(self.check_folder_exists(
            self.vault_path / 'Approved',
            '/Approved folder exists'
        ))
        checks.append(self.check_folder_exists(
            self.vault_path / 'Rejected',
            '/Rejected folder exists'
        ))

        # 5. Scheduler
        checks.append(self.check_file_exists(
            self.scripts_path / 'scheduler.py',
            'scheduler.py exists'
        ))

        # 6. Plans folder
        checks.append(self.check_folder_exists(
            self.vault_path / 'Plans',
            '/Plans folder exists'
        ))

        self.results['silver_requirements'] = checks
        return checks

    def verify_gold_requirements(self) -> List[Dict]:
        """Verify Gold tier requirements."""
        checks = []
        
        # 1. Odoo accounting integration
        checks.append(self.check_file_exists(
            self.vault_path / 'odoo' / 'docker-compose.yml',
            'Odoo Docker Compose configuration'
        ))
        checks.append(self.check_file_exists(
            self.vault_path / 'odoo' / 'setup_odoo.py',
            'Odoo setup script'
        ))
        checks.append(self.check_file_exists(
            self.mcp_path / 'odoo_mcp.py',
            'Odoo MCP server'
        ))
        
        # Check Odoo MCP has required functions
        odoo_mcp_path = self.mcp_path / 'odoo_mcp.py'
        checks.append(self.check_file_content(
            odoo_mcp_path, 'create_invoice',
            'Odoo MCP: create_invoice function'
        ))
        checks.append(self.check_file_content(
            odoo_mcp_path, 'get_financial_reports',
            'Odoo MCP: get_financial_reports function'
        ))
        checks.append(self.check_file_content(
            odoo_mcp_path, 'register_payment',
            'Odoo MCP: register_payment function'
        ))

        # 2. Facebook integration (Graph API)
        checks.append(self.check_file_exists(
            self.watchers_path / 'facebook_watcher.py',
            'Facebook Watcher (Graph API)'
        ))
        checks.append(self.check_file_content(
            self.watchers_path / 'facebook_watcher.py',
            'graph.facebook.com',
            'Facebook Watcher: Graph API usage'
        ))
        checks.append(self.check_file_content(
            self.watchers_path / 'facebook_watcher.py',
            'page_access_token',
            'Facebook Watcher: API token support'
        ))

        # 3. Instagram integration (via social MCP - Graph API)
        checks.append(self.check_file_exists(
            self.mcp_path / 'social_mcp.py',
            'Social Media MCP server'
        ))
        checks.append(self.check_file_content(
            self.mcp_path / 'social_mcp.py',
            'instagram_post',
            'Instagram post function'
        ))
        checks.append(self.check_file_content(
            self.mcp_path / 'social_mcp.py',
            'facebook_post',
            'Facebook post function'
        ))
        checks.append(self.check_file_content(
            self.mcp_path / 'social_mcp.py',
            'graph.facebook.com',
            'Social MCP: Graph API usage'
        ))

        # 4. Facebook Setup documentation
        checks.append(self.check_file_exists(
            self.vault_path / 'FACEBOOK_SETUP.md',
            'Facebook API setup documentation'
        ))

        # 5. CEO Briefing generation
        checks.append(self.check_file_exists(
            self.scripts_path / 'ceo_briefing.py',
            'CEO Briefing generator'
        ))
        checks.append(self.check_folder_exists(
            self.vault_path / 'Briefings',
            '/Briefings folder exists'
        ))
        checks.append(self.check_file_content(
            self.scripts_path / 'ceo_briefing.py',
            'generate_weekly_briefing',
            'CEO Briefing: generate_weekly_briefing function'
        ))

        # 6. Multiple MCP servers
        mcp_files = list(self.mcp_path.glob('*_mcp.py')) if self.mcp_path.exists() else []
        checks.append({
            'check': 'Multiple MCP servers (3+)',
            'path': str(self.mcp_path),
            'status': 'pass' if len(mcp_files) >= 3 else 'fail',
            'details': f'{len(mcp_files)} MCP server(s) found'
        })

        # 7. Accounting folder
        checks.append(self.check_folder_exists(
            self.vault_path / 'Accounting',
            '/Accounting folder exists'
        ))
        checks.append(self.check_folder_exists(
            self.vault_path / 'Invoices',
            '/Invoices folder exists'
        ))

        # 8. Social folder
        checks.append(self.check_folder_exists(
            self.vault_path / 'Social',
            '/Social folder exists'
        ))

        # 9. Error recovery and audit logging
        checks.append(self.check_file_content(
            self.scripts_path / 'orchestrator.py',
            'log_action',
            'Orchestrator: audit logging'
        ))
        checks.append(self.check_file_content(
            self.scripts_path / 'orchestrator.py',
            'try:',
            'Orchestrator: error handling'
        ))

        # 10. Ralph Wiggum loop reference
        checks.append(self.check_file_content(
            self.vault_path / 'Personal AI Employe FTEs.md',
            'Ralph Wiggum',
            'Ralph Wiggum loop documentation'
        ))

        # 11. Gold tier folder structure
        for folder in ['Briefings', 'Accounting', 'Invoices', 'Social']:
            checks.append(self.check_folder_exists(
                self.vault_path / folder,
                f'/{folder} folder exists'
            ))

        self.results['gold_requirements'] = checks
        return checks

    def calculate_score(self) -> Dict:
        """Calculate overall score."""
        all_checks = (
            self.results.get('bronze_requirements', []) +
            self.results.get('silver_requirements', []) +
            self.results.get('gold_requirements', [])
        )
        
        total = len(all_checks)
        passed = sum(1 for c in all_checks if c['status'] == 'pass')
        failed = total - passed
        
        return {
            'total_checks': total,
            'passed': passed,
            'failed': failed,
            'percentage': (passed / total * 100) if total > 0 else 0
        }

    def verify(self) -> bool:
        """Run all verifications."""
        print("\n" + "="*70)
        print("GOLD TIER VERIFICATION")
        print("="*70)
        
        # Verify all tiers
        print("\n[1/3] Verifying Bronze Tier requirements...")
        self.verify_bronze_requirements()
        
        print("[2/3] Verifying Silver Tier requirements...")
        self.verify_silver_requirements()
        
        print("[3/3] Verifying Gold Tier requirements...")
        self.verify_gold_requirements()
        
        # Calculate score
        score = self.calculate_score()
        
        # Print results
        print("\n" + "="*70)
        print("VERIFICATION RESULTS")
        print("="*70)
        
        print(f"\n📊 Overall Score: {score['percentage']:.1f}%")
        print(f"   Passed: {score['passed']}/{score['total_checks']}")
        print(f"   Failed: {score['failed']}/{score['total_checks']}")
        
        # Bronze results
        bronze_passed = sum(1 for c in self.results['bronze_requirements'] if c['status'] == 'pass')
        bronze_total = len(self.results['bronze_requirements'])
        bronze_status = '✅ PASS' if bronze_passed == bronze_total else '❌ FAIL'
        print(f"\n🥉 Bronze Tier: {bronze_status} ({bronze_passed}/{bronze_total})")
        
        # Silver results
        silver_passed = sum(1 for c in self.results['silver_requirements'] if c['status'] == 'pass')
        silver_total = len(self.results['silver_requirements'])
        silver_status = '✅ PASS' if silver_passed == silver_total else '❌ FAIL'
        print(f"\n🥈 Silver Tier: {silver_status} ({silver_passed}/{silver_total})")
        
        # Gold results
        gold_passed = sum(1 for c in self.results['gold_requirements'] if c['status'] == 'pass')
        gold_total = len(self.results['gold_requirements'])
        gold_status = '✅ PASS' if gold_passed == gold_total else '❌ FAIL'
        print(f"\n🥇 Gold Tier: {gold_status} ({gold_passed}/{gold_total})")
        
        # Overall status
        if gold_passed == gold_total and silver_passed == silver_total and bronze_passed == bronze_total:
            self.results['overall_status'] = 'pass'
            print("\n" + "="*70)
            print("🎉 CONGRATULATIONS! GOLD TIER COMPLETE! 🎉")
            print("="*70)
            print("\nYour AI Employee has all Gold Tier features:")
            print("  ✓ Odoo accounting integration")
            print("  ✓ Facebook monitoring and posting")
            print("  ✓ Instagram monitoring and posting")
            print("  ✓ Weekly CEO Briefing generation")
            print("  ✓ Multiple MCP servers")
            print("  ✓ Comprehensive audit logging")
            print("="*70 + "\n")
            return True
        else:
            self.results['overall_status'] = 'fail'
            print("\n" + "="*70)
            print("⚠️  GOLD TIER INCOMPLETE")
            print("="*70)
            
            # Show failed checks
            all_checks = (
                self.results['bronze_requirements'] +
                self.results['silver_requirements'] +
                self.results['gold_requirements']
            )
            
            failed_checks = [c for c in all_checks if c['status'] == 'fail']
            
            if failed_checks:
                print("\nFailed checks:")
                for check in failed_checks[:10]:  # Show first 10
                    print(f"  ❌ {check['check']}")
                    print(f"     → {check['details']}")
            
            print("\n" + "="*70 + "\n")
            return False

    def save_report(self):
        """Save verification report to file."""
        report_path = self.vault_path / 'Logs' / f'gold_verification_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        score = self.calculate_score()
        
        content = f"""---
generated: {datetime.now().isoformat()}
tier: gold
status: {self.results['overall_status']}
score: {score['percentage']:.1f}%
---

# Gold Tier Verification Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Overall Status:** {'✅ PASS' if self.results['overall_status'] == 'pass' else '❌ FAIL'}

**Score:** {score['percentage']:.1f}% ({score['passed']}/{score['total_checks']})

---

## Bronze Tier ({sum(1 for c in self.results['bronze_requirements'] if c['status'] == 'pass')}/{len(self.results['bronze_requirements'])})

{self._format_checks(self.results['bronze_requirements'])}

## Silver Tier ({sum(1 for c in self.results['silver_requirements'] if c['status'] == 'pass')}/{len(self.results['silver_requirements'])})

{self._format_checks(self.results['silver_requirements'])}

## Gold Tier ({sum(1 for c in self.results['gold_requirements'] if c['status'] == 'pass')}/{len(self.results['gold_requirements'])})

{self._format_checks(self.results['gold_requirements'])}

---

*AI Employee Gold Tier Verification*
"""
        report_path.write_text(content, encoding='utf-8')
        print(f"\n📄 Verification report saved to: {report_path}")
    
    def _format_checks(self, checks: List[Dict]) -> str:
        """Format checks as markdown table."""
        lines = ["| Check | Status | Details |", "|-------|--------|---------|"]
        
        for check in checks:
            icon = '✅' if check['status'] == 'pass' else '❌'
            lines.append(f"| {check['check']} | {icon} | {check['details']} |")
        
        return '\n'.join(lines)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python verify_gold.py <vault_path>")
        print("\nExample:")
        print("  python verify_gold.py .")
        sys.exit(1)
    
    vault_path = sys.argv[1]
    
    verifier = GoldTierVerifier(vault_path)
    success = verifier.verify()
    verifier.save_report()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
