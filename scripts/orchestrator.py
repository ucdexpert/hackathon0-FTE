#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator - Master process for AI Employee.

The Orchestrator:
1. Monitors /Needs_Action folder for new items
2. Triggers Qwen Code to process pending items
3. Updates Dashboard.md with current status
4. Manages the workflow: Inbox → Needs_Action → Done

Gold Tier Features:
- Odoo accounting integration
- Facebook/Instagram social media monitoring
- CEO Briefing generation
- Ralph Wiggum persistence loop
- Advanced HITL workflow
- Multi-agent coordination

Usage:
    python orchestrator.py /path/to/vault
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import subprocess
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class Orchestrator:
    """Main orchestrator for AI Employee workflow."""

    def __init__(self, vault_path: str, check_interval: int = 30):
        """
        Initialize the orchestrator.

        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks
        """
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval

        # Core folders
        self.inbox = self.vault_path / 'Inbox'
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.plans = self.vault_path / 'Plans'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'
        self.logs = self.vault_path / 'Logs'
        self.dashboard = self.vault_path / 'Dashboard.md'
        
        # Gold Tier folders
        self.briefings = self.vault_path / 'Briefings'
        self.social = self.vault_path / 'Social'
        self.accounting = self.vault_path / 'Accounting'
        self.invoices = self.vault_path / 'Invoices'
        self.in_progress = self.vault_path / 'In_Progress'  # For persistence loop

        for folder in [self.briefings, self.social, self.accounting, self.invoices, self.in_progress]:
            folder.mkdir(parents=True, exist_ok=True)

        # Ensure all core folders exist
        for folder in [self.inbox, self.needs_action, self.done,
                       self.plans, self.pending_approval, self.approved,
                       self.rejected, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.processed_files = set()
        
        # Gold Tier: Briefing schedule
        self.last_briefing = None
        self.briefing_day = 0  # Monday
    
    def count_files(self, folder: Path) -> int:
        """Count .md files in a folder."""
        if not folder.exists():
            return 0
        return len(list(folder.glob('*.md')))
    
    def get_pending_actions(self) -> list:
        """Get list of pending action files."""
        if not self.needs_action.exists():
            return []
        return [f for f in self.needs_action.glob('*.md') 
                if f.name not in self.processed_files]
    
    def get_pending_approvals(self) -> list:
        """Get list of pending approval files."""
        if not self.pending_approval.exists():
            return []
        return list(self.pending_approval.glob('*.md'))
    
    def update_dashboard(self):
        """Update the Dashboard.md with current status."""
        pending_count = self.count_files(self.needs_action)
        approval_count = self.count_files(self.pending_approval)
        done_today = self.count_files_done_today()
        done_week = self.count_files_done_this_week()

        # Count inbox
        inbox_count = self.count_files(self.inbox)

        # Get recent activity from logs
        recent_activity = self.get_recent_activity()
        
        # Gold Tier: Get Odoo revenue data
        revenue_mtd = self.get_revenue_mtd()
        
        # Gold Tier: Get social media stats
        social_stats = self.get_social_stats()

        content = f"""---
last_updated: {datetime.now().isoformat()}
status: active
tier: gold
---

# AI Employee Dashboard

> **Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.**

---

## 📊 Quick Stats

| Metric | Value | Status |
|--------|-------|--------|
| **Pending Actions** | {pending_count} | {'✅ Clear' if pending_count == 0 else '⚠️ Action needed'} |
| **Pending Approvals** | {approval_count} | {'✅ Clear' if approval_count == 0 else '⚠️ Review required'} |
| **Tasks Completed Today** | {done_today} | - |
| **Tasks Completed This Week** | {done_week} | - |
| **Revenue MTD** | ${revenue_mtd:,.2f} | - |

---

## 📥 Inbox Status

| Folder | Count |
|--------|-------|
| /Inbox | {inbox_count} |
| /Needs_Action | {pending_count} |
| /Pending_Approval | {approval_count} |

---

## 🎯 Active Projects

*No active projects*

---

## ⏳ Pending Approvals

{self.format_pending_approvals()}

---

## ✅ Recent Activity

{recent_activity if recent_activity else '*No recent activity*'}

---

## 📈 Business Goals Progress

| Goal | Target | Current | Progress |
|------|--------|---------|----------|
| Monthly Revenue | $10,000 | ${revenue_mtd:,.2f} | {revenue_mtd/100:.1f}% |

---

## 📱 Social Media

| Platform | Posts This Week | Status |
|----------|-----------------|--------|
| LinkedIn | {social_stats.get('linkedin', 0)} | {'✅ Active' if social_stats.get('linkedin', 0) > 0 else '⚪ Inactive'} |
| Facebook | {social_stats.get('facebook', 0)} | {'✅ Active' if social_stats.get('facebook', 0) > 0 else '⚪ Inactive'} |
| Instagram | {social_stats.get('instagram', 0)} | {'✅ Active' if social_stats.get('instagram', 0) > 0 else '⚪ Inactive'} |

---

## 🔔 Alerts

{self.format_alerts(pending_count, approval_count, revenue_mtd)}

---

## 📝 Notes

- Dashboard auto-updates when AI Employee processes files
- Move approved items from `/Pending_Approval` to `/Approved` to trigger actions
- Check `/Briefings` for weekly CEO reports
- Gold Tier: Odoo accounting integration active

---

*Last generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*AI Employee v1.0 (Gold Tier)*
"""

        self.dashboard.write_text(content, encoding='utf-8')
        self.logger.info('Dashboard updated')
    
    def get_revenue_mtd(self) -> float:
        """Get month-to-date revenue from Odoo or logs."""
        try:
            from scripts.mcp.odoo_mcp import OdooMCPServer
            
            odoo = OdooMCPServer(
                vault_path=str(self.vault_path)
            )
            
            if odoo.authenticate():
                result = odoo.get_financial_reports()
                if 'report' in result:
                    return result['report'].get('monthly_revenue', 0)
        except Exception as e:
            self.logger.debug(f'Could not get Odoo revenue: {e}')
        
        # Fallback: parse accounting logs
        today = datetime.now()
        month_start = today.replace(day=1)
        revenue = 0
        
        for log_file in self.accounting_folder.glob('*.md'):
            try:
                content = log_file.read_text()
                if str(month_start.year) in content and str(month_start.month) in content:
                    import re
                    amounts = re.findall(r'\$[\d,]+\.?\d*', content)
                    for amount in amounts:
                        revenue += float(amount.replace('$', '').replace(',', ''))
            except:
                pass
        
        return revenue
    
    def get_social_stats(self) -> Dict:
        """Get social media posting statistics."""
        stats = {'linkedin': 0, 'facebook': 0, 'instagram': 0}
        
        # Get this week's date range
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_start_str = week_start.strftime('%Y-%m-%d')
        
        # Parse social media logs
        for log_file in self.logs.glob('social_*.md'):
            try:
                content = log_file.read_text()
                if week_start_str in content:
                    if 'linkedin' in content.lower():
                        stats['linkedin'] += content.count('success')
                    if 'facebook' in content.lower():
                        stats['facebook'] += content.count('success')
                    if 'instagram' in content.lower():
                        stats['instagram'] += content.count('success')
            except:
                pass
        
        return stats
    
    def count_files_done_today(self) -> int:
        """Count files moved to Done today."""
        if not self.done.exists():
            return 0
        today = datetime.now().strftime('%Y-%m-%d')
        count = 0
        for f in self.done.glob('*.md'):
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d')
                if mtime == today:
                    count += 1
            except:
                pass
        return count
    
    def count_files_done_this_week(self) -> int:
        """Count files moved to Done this week."""
        if not self.done.exists():
            return 0
        return len(list(self.done.glob('*.md')))
    
    def get_recent_activity(self) -> str:
        """Get recent activity from log files."""
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs / f'{today}.md'
        
        if not log_file.exists():
            return ''
        
        content = log_file.read_text()
        lines = content.split('\n')[-5:]  # Last 5 entries
        return '\n'.join(f'- {line}' for line in lines if line.strip())
    
    def format_pending_approvals(self) -> str:
        """Format pending approvals for dashboard."""
        approvals = self.get_pending_approvals()
        if not approvals:
            return '*No pending approvals*'
        
        lines = []
        for approval in approvals[:5]:  # Show max 5
            lines.append(f'- `{approval.name}`')
        
        if len(approvals) > 5:
            lines.append(f'- ... and {len(approvals) - 5} more')
        
        return '\n'.join(lines)
    
    def format_alerts(self, pending_count: int, approval_count: int, revenue_mtd: float = 0) -> str:
        """Format alerts for dashboard."""
        alerts = []

        if pending_count > 10:
            alerts.append('- ⚠️ High volume of pending actions')
        if approval_count > 0:
            alerts.append('- ⏳ Awaiting human approval')
        
        # Gold Tier: Revenue alert
        monthly_target = 10000
        if revenue_mtd < monthly_target * 0.3:
            alerts.append(f'- 🔴 Revenue ${revenue_mtd:,.2f} is below 30% of target')
        elif revenue_mtd < monthly_target * 0.6:
            alerts.append(f'- 🟡 Revenue ${revenue_mtd:,.2f} is below 60% of target')

        if not alerts:
            return '*No alerts*'

        return '\n'.join(alerts)
    
    def log_action(self, action_type: str, details: str, status: str = 'info'):
        """Log an action to the daily log file."""
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs / f'{today}.md'

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        entry = f'[{timestamp}] [{status.upper()}] {action_type}: {details}'

        if log_file.exists():
            content = log_file.read_text(encoding='utf-8')
            content = content.rstrip() + '\n' + entry + '\n'
        else:
            content = f"# Daily Log - {today}\n\n{entry}\n"

        log_file.write_text(content, encoding='utf-8')
    
    def check_and_generate_briefing(self):
        """Check if it's Monday morning and generate CEO briefing."""
        today = datetime.now()
        
        # Generate on Monday (weekday 0) between 6-9 AM
        if today.weekday() == 0 and 6 <= today.hour < 10:
            if self.last_briefing is None or self.last_briefing < today - timedelta(days=7):
                self.generate_ceo_briefing()
                self.last_briefing = today
    
    def generate_ceo_briefing(self):
        """Generate weekly CEO briefing."""
        try:
            self.logger.info('Generating weekly CEO briefing...')
            
            from scripts.ceo_briefing import CEOBriefingGenerator
            
            generator = CEOBriefingGenerator(
                vault_path=str(self.vault_path)
            )
            
            briefing_path = generator.generate_weekly_briefing(week_offset=-1)
            
            self.logger.info(f'CEO briefing generated: {briefing_path}')
            self.log_action('ceo_briefing_generated', str(briefing_path), 'success')
            
        except Exception as e:
            self.logger.error(f'Failed to generate CEO briefing: {e}')
            self.log_action('ceo_briefing_failed', str(e), 'error')
    
    def process_approved_files(self):
        """Process files in /Approved folder."""
        approved_files = list(self.approved.glob('*.md'))

        for approved_file in approved_files:
            self.logger.info(f'Processing approved file: {approved_file.name}')

            # Read the approval
            content = approved_file.read_text()

            # Check if it's an email approval request
            if 'type: approval_request' in content and 'action: send_email' in content:
                self._send_approved_email(approved_file, content)
            else:
                # For non-email approvals, just move to Done
                self._move_to_done(approved_file)

    def _send_approved_email(self, approved_file: Path, content: str):
        """Send email from approved approval request."""
        try:
            # Parse email details from frontmatter
            email_data = self._parse_email_approval(content)

            if not email_data:
                self.logger.error(f'Could not parse email data from {approved_file.name}')
                self._move_to_done(approved_file)
                return

            # Import Email MCP Server
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            
            # Import using absolute path
            import importlib.util
            email_mcp_path = Path(__file__).parent / 'mcp' / 'email_mcp.py'
            spec = importlib.util.spec_from_file_location('email_mcp', email_mcp_path)
            email_mcp_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(email_mcp_module)
            EmailMCPServer = email_mcp_module.EmailMCPServer

            # Create email server and send
            email_server = EmailMCPServer(vault_path=str(self.vault_path))

            if not email_server.authenticate():
                self.logger.error('Failed to authenticate with Gmail API')
                self._move_to_done(approved_file)
                return

            # Send email (skip_approval=True since it's already approved)
            result = email_server.send_email(
                to=email_data['to'],
                subject=email_data['subject'],
                body=email_data['body'],
                html=email_data.get('html', False),
                attachments=email_data.get('attachments', []),
                cc=email_data.get('cc', []),
                bcc=email_data.get('bcc', []),
                skip_approval=True
            )

            if result.get('status') == 'sent':
                self.logger.info(f"Email sent successfully to {email_data['to']}, ID: {result.get('message_id')}")
                self.log_action('email_sent', f"To: {email_data['to']}, Subject: {email_data['subject']}, ID: {result.get('message_id')}", 'success')

                # Add sent info to file before moving
                sent_info = f"\n\n---\n\n**Sent:** {datetime.now().isoformat()}\n**Message ID:** {result.get('message_id')}\n**Status:** Sent successfully\n"
                approved_file.write_text(content + sent_info, encoding='utf-8')

                self._move_to_done(approved_file)
            else:
                self.logger.error(f"Failed to send email: {result}")
                self.log_action('email_send_failed', f"To: {email_data['to']}, Error: {result}", 'error')

        except Exception as e:
            self.logger.error(f'Error sending approved email: {e}')
            self.log_action('email_send_error', f"File: {approved_file.name}, Error: {e}", 'error')

    def _parse_email_approval(self, content: str) -> dict:
        """Parse email details from approval request content."""
        email_data = {
            'to': '',
            'subject': '',
            'body': '',
            'html': False,
            'attachments': [],
            'cc': [],
            'bcc': []
        }

        # Parse frontmatter
        in_frontmatter = False
        in_body = False
        body_lines = []

        for line in content.split('\n'):
            # Check for frontmatter
            if line.strip() == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                else:
                    in_frontmatter = False
                continue

            if in_frontmatter:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()

                    if key == 'to':
                        email_data['to'] = value
                    elif key == 'subject':
                        email_data['subject'] = value
                    elif key == 'attachments':
                        try:
                            email_data['attachments'] = json.loads(value) if value else []
                        except:
                            email_data['attachments'] = []

            # Parse body (after frontmatter, before next section)
            elif line.strip() == '## Email Body':
                in_body = True
                continue
            elif in_body and line.strip().startswith('##'):
                in_body = False
            elif in_body:
                body_lines.append(line)

        email_data['body'] = '\n'.join(body_lines).strip()

        # Parse CC/BCC from body section if present
        body_text = '\n'.join(content.split('## Email Body')[1].split('##')[0]) if '## Email Body' in content else ''
        if '**CC:**' in content:
            cc_line = [l for l in content.split('\n') if '**CC:**' in l]
            if cc_line:
                email_data['cc'] = [x.strip() for x in cc_line[0].replace('**CC:**', '').split(',')]
        if '**BCC:**' in content:
            bcc_line = [l for l in content.split('\n') if '**BCC:**' in l]
            if bcc_line:
                email_data['bcc'] = [x.strip() for x in bcc_line[0].replace('**BCC:**', '').split(',')]

        return email_data

    def _move_to_done(self, approved_file: Path):
        """Move file to Done folder."""
        try:
            dest = self.done / approved_file.name
            approved_file.rename(dest)
            self.logger.info(f'Moved to Done: {dest.name}')
            self.log_action('file_moved_to_done', approved_file.name, 'info')
        except Exception as e:
            self.logger.error(f'Failed to move to Done: {e}')
    
    def check_for_qwen_completion(self):
        """Check if Qwen Code has completed processing using persistence loop."""
        # Check In_Progress folder for active tasks
        in_progress_files = list(self.in_progress.glob('*.md')) if hasattr(self, 'in_progress') else []
        
        if in_progress_files:
            self.logger.info(f'Found {len(in_progress_files)} active task(s) in In_Progress/')
            for task_file in in_progress_files:
                # Check if task is complete
                content = task_file.read_text(encoding='utf-8')
                if 'status: completed' in content:
                    self.logger.info(f'Task complete: {task_file.name}')
                    # Move to Done
                    done_file = self.done / task_file.name
                    task_file.rename(done_file)
                    self.log_action('task_completed', task_file.name, 'success')

    def check_pending_actions(self):
        """Check and log pending action files in Needs_Action folder."""
        pending_files = self.get_pending_actions()
        
        if pending_files:
            self.logger.info(f'Found {len(pending_files)} pending action(s) in Needs_Action/')
            for f in pending_files:
                self.logger.info(f'  - {f.name}')
        else:
            self.logger.debug('No pending actions')
        
        return pending_files

    def run(self):
        """Main orchestrator loop."""
        self.logger.info(f'Starting Orchestrator (Gold Tier)')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Check interval: {self.check_interval}s')
        self.logger.info(f'Features: Odoo, Facebook, Instagram, CEO Briefings')

        # Initial dashboard update
        self.update_dashboard()

        try:
            while True:
                # Check for approved files to process
                self.process_approved_files()

                # Check for pending actions in Needs_Action
                self.check_pending_actions()

                # Update dashboard
                self.update_dashboard()

                # Check for Qwen completion
                self.check_for_qwen_completion()
                
                # Gold Tier: Check if briefing should be generated
                self.check_and_generate_briefing()

                # Log heartbeat
                self.logger.debug('Orchestrator heartbeat')

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info('Orchestrator stopped by user')
        except Exception as e:
            self.logger.error(f'Fatal error: {e}')
            raise


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py <vault_path> [check_interval]")
        print("\nExamples:")
        print("  python orchestrator.py /path/to/vault")
        print("  python orchestrator.py /path/to/vault 60")
        sys.exit(1)
    
    vault_path = sys.argv[1]
    check_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    orchestrator = Orchestrator(vault_path, check_interval)
    orchestrator.run()


if __name__ == "__main__":
    main()
