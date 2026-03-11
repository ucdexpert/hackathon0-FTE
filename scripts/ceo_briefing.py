#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CEO Briefing Generator - Creates weekly executive reports.

Generates comprehensive "Monday Morning CEO Briefing" reports including:
- Revenue summary from Odoo
- Tasks completed
- Bottlenecks identified
- Social media performance
- Proactive suggestions

Usage:
    python ceo_briefing.py <vault_path> [--week WEEK] [--odoo-config CONFIG]
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class CEOBriefingGenerator:
    """Generates weekly CEO briefing reports."""

    def __init__(self, vault_path: str = '.',
                 odoo_host: str = 'localhost',
                 odoo_port: int = 8069,
                 odoo_db: str = 'odoo',
                 odoo_user: str = 'admin',
                 odoo_password: str = 'admin'):
        """
        Initialize CEO Briefing Generator.

        Args:
            vault_path: Path to Obsidian vault
            odoo_host: Odoo server host
            odoo_port: Odoo server port
            odoo_db: Odoo database name
            odoo_user: Odoo username
            odoo_password: Odoo password
        """
        self.vault_path = Path(vault_path)
        self.briefings_folder = self.vault_path / 'Briefings'
        self.done_folder = self.vault_path / 'Done'
        self.logs_folder = self.vault_path / 'Logs'
        self.accounting_folder = self.vault_path / 'Accounting'
        self.social_folder = self.vault_path / 'Social'

        for folder in [self.briefings_folder, self.done_folder,
                       self.logs_folder, self.accounting_folder, self.social_folder]:
            folder.mkdir(parents=True, exist_ok=True)

        # Odoo configuration
        self.odoo_config = {
            'host': odoo_host,
            'port': odoo_port,
            'db': odoo_db,
            'user': odoo_user,
            'password': odoo_password
        }

        self.logger = logging.getLogger(self.__class__.__name__)

    def generate_weekly_briefing(self, week_offset: int = 0) -> Path:
        """
        Generate weekly CEO briefing.

        Args:
            week_offset: 0 for current week, -1 for last week, etc.

        Returns:
            Path to generated briefing file
        """
        # Calculate week dates
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday(), weeks=-week_offset)
        week_end = week_start + timedelta(days=6, hours=23, minutes=59)

        week_start_str = week_start.strftime('%Y-%m-%d')
        week_end_str = week_end.strftime('%Y-%m-%d')

        self.logger.info(f'Generating briefing for week: {week_start_str} to {week_end_str}')

        # Gather data
        revenue_data = self._get_revenue_data(week_start_str, week_end_str)
        tasks_data = self._get_tasks_data(week_start_str, week_end_str)
        bottlenecks = self._identify_bottlenecks(tasks_data, revenue_data)
        social_data = self._get_social_media_data(week_start_str, week_end_str)
        suggestions = self._generate_suggestions(revenue_data, tasks_data, bottlenecks)

        # Generate briefing content
        briefing_content = self._create_briefing_content(
            week_start=week_start_str,
            week_end=week_end_str,
            revenue_data=revenue_data,
            tasks_data=tasks_data,
            bottlenecks=bottlenecks,
            social_data=social_data,
            suggestions=suggestions
        )

        # Write briefing file
        filename = f"{week_start.strftime('%Y%m%d')}_Week_{week_start.strftime('%W')}_Briefing.md"
        filepath = self.briefings_folder / filename
        filepath.write_text(briefing_content, encoding='utf-8')

        self.logger.info(f'Briefing generated: {filepath}')

        return filepath

    def _get_revenue_data(self, week_start: str, week_end: str) -> Dict:
        """Get revenue data from Odoo or logs."""
        revenue_data = {
            'total_revenue': 0,
            'invoices_count': 0,
            'payments_received': 0,
            'pending_invoices': 0,
            'top_customers': [],
            'revenue_trend': 'stable',
            'weekly_breakdown': []
        }

        try:
            # Try to get data from Odoo
            from scripts.mcp.odoo_mcp import OdooMCPServer

            odoo = OdooMCPServer(
                host=self.odoo_config['host'],
                port=self.odoo_config['port'],
                db=self.odoo_config['db'],
                username=self.odoo_config['user'],
                password=self.odoo_config['password'],
                vault_path=str(self.vault_path)
            )

            if odoo.authenticate():
                # Get invoices for the period
                invoices_result = odoo.get_invoices(
                    limit=100,
                    date_from=week_start,
                    date_to=week_end,
                    state='posted'
                )

                if 'invoices' in invoices_result:
                    invoices = invoices_result['invoices']
                    revenue_data['invoices_count'] = len(invoices)
                    revenue_data['total_revenue'] = sum(
                        inv.get('amount_total', 0) for inv in invoices
                    )

                    # Calculate pending
                    pending_result = odoo.get_invoices(
                        limit=100,
                        date_from=week_start,
                        date_to=week_end,
                        state='posted'
                    )
                    if 'invoices' in pending_result:
                        revenue_data['pending_invoices'] = sum(
                            1 for inv in pending_result.get('invoices', [])
                            if inv.get('payment_state') != 'paid'
                        )

                # Get financial summary
                financial_result = odoo.get_financial_reports()
                if 'report' in financial_result:
                    revenue_data['monthly_revenue'] = financial_result['report'].get('monthly_revenue', 0)

        except Exception as e:
            self.logger.warning(f'Could not get Odoo data: {e}')
            # Fall back to log parsing
            revenue_data = self._parse_revenue_from_logs(week_start, week_end)

        return revenue_data

    def _parse_revenue_from_logs(self, week_start: str, week_end: str) -> Dict:
        """Parse revenue data from log files."""
        revenue_data = {
            'total_revenue': 0,
            'invoices_count': 0,
            'payments_received': 0,
            'pending_invoices': 0
        }

        # Parse accounting logs
        for log_file in self.accounting_folder.glob('*.md'):
            try:
                content = log_file.read_text()
                # Look for revenue entries
                if 'revenue' in content.lower() or 'invoice' in content.lower():
                    # Simple parsing - can be enhanced
                    for line in content.split('\n'):
                        if '$' in line:
                            try:
                                # Extract dollar amount
                                import re
                                amounts = re.findall(r'\$[\d,]+\.?\d*', line)
                                for amount in amounts:
                                    revenue_data['total_revenue'] += float(amount.replace('$', '').replace(',', ''))
                            except:
                                pass
            except Exception as e:
                self.logger.debug(f'Error parsing {log_file}: {e}')

        return revenue_data

    def _get_tasks_data(self, week_start: str, week_end: str) -> Dict:
        """Get tasks completed data from Done folder."""
        tasks_data = {
            'completed_count': 0,
            'pending_count': 0,
            'tasks_by_type': {},
            'average_completion_time': 0,
            'completed_tasks': []
        }

        # Count files in Done folder
        if self.done_folder.exists():
            for file in self.done_folder.glob('*.md'):
                try:
                    mtime = datetime.fromtimestamp(file.stat().st_mtime)
                    if week_start <= mtime.strftime('%Y-%m-%d') <= week_end:
                        tasks_data['completed_count'] += 1

                        # Parse task type from frontmatter
                        content = file.read_text()
                        if 'type:' in content:
                            for line in content.split('\n')[:20]:
                                if 'type:' in line:
                                    task_type = line.split('type:')[1].strip()
                                    tasks_data['tasks_by_type'][task_type] = \
                                        tasks_data['tasks_by_type'].get(task_type, 0) + 1
                                    break

                        tasks_data['completed_tasks'].append({
                            'name': file.stem,
                            'completed_at': mtime.isoformat()
                        })
                except Exception as e:
                    self.logger.debug(f'Error parsing {file}: {e}')

        # Count pending in Needs_Action
        needs_action = self.vault_path / 'Needs_Action'
        if needs_action.exists():
            tasks_data['pending_count'] = len(list(needs_action.glob('*.md')))

        return tasks_data

    def _identify_bottlenecks(self, tasks_data: Dict, revenue_data: Dict) -> List[Dict]:
        """Identify bottlenecks from data."""
        bottlenecks = []

        # Check pending tasks
        if tasks_data.get('pending_count', 0) > 10:
            bottlenecks.append({
                'type': 'high_pending_volume',
                'severity': 'medium',
                'description': f"{tasks_data['pending_count']} tasks pending in Needs_Action",
                'suggestion': 'Review and prioritize pending tasks'
            })

        # Check revenue vs target
        monthly_target = 10000  # From Business_Goals.md
        current_revenue = revenue_data.get('monthly_revenue', 0)
        if current_revenue < monthly_target * 0.5:
            bottlenecks.append({
                'type': 'revenue_below_target',
                'severity': 'high',
                'description': f'Revenue ${current_revenue:,.2f} is below 50% of target ${monthly_target:,.2f}',
                'suggestion': 'Review sales pipeline and marketing activities'
            })

        # Check pending invoices
        if revenue_data.get('pending_invoices', 0) > 5:
            bottlenecks.append({
                'type': 'uncollected_revenue',
                'severity': 'medium',
                'description': f"{revenue_data['pending_invoices']} invoices awaiting payment",
                'suggestion': 'Send payment reminders to customers'
            })

        return bottlenecks

    def _get_social_media_data(self, week_start: str, week_end: str) -> Dict:
        """Get social media performance data."""
        social_data = {
            'posts_count': 0,
            'platforms': {},
            'scheduled_posts': 0
        }

        # Count social media logs
        for log_file in self.logs_folder.glob('social_*.md'):
            try:
                content = log_file.read_text()
                if week_start in content or week_end in content:
                    social_data['posts_count'] += content.count('success')
            except:
                pass

        # Count scheduled posts
        if self.social_folder.exists():
            social_data['scheduled_posts'] = len(
                list(self.social_folder.glob('SCHEDULED_*.md'))
            )

        return social_data

    def _generate_suggestions(self, revenue_data: Dict, tasks_data: Dict,
                               bottlenecks: List[Dict]) -> List[Dict]:
        """Generate proactive suggestions."""
        suggestions = []

        # Revenue-based suggestions
        if revenue_data.get('total_revenue', 0) > 0:
            suggestions.append({
                'category': 'revenue_optimization',
                'suggestion': 'Revenue is coming in. Consider following up with top customers for testimonials.',
                'priority': 'low'
            })

        # Task-based suggestions
        if tasks_data.get('pending_count', 0) > 5:
            suggestions.append({
                'category': 'productivity',
                'suggestion': f"You have {tasks_data['pending_count']} pending tasks. Consider batching similar tasks.",
                'priority': 'medium'
            })

        # Bottleneck-based suggestions
        for bottleneck in bottlenecks:
            if bottleneck.get('suggestion'):
                suggestions.append({
                    'category': 'bottleneck_resolution',
                    'suggestion': bottleneck['suggestion'],
                    'priority': bottleneck.get('severity', 'medium')
                })

        return suggestions

    def _create_briefing_content(self, week_start: str, week_end: str,
                                  revenue_data: Dict, tasks_data: Dict,
                                  bottlenecks: List[Dict],
                                  social_data: Dict,
                                  suggestions: List[Dict]) -> str:
        """Create the full briefing markdown content."""

        # Calculate progress percentage
        monthly_target = 10000
        current_revenue = revenue_data.get('monthly_revenue', revenue_data.get('total_revenue', 0))
        progress_pct = (current_revenue / monthly_target * 100) if monthly_target > 0 else 0

        # Determine status
        if progress_pct >= 80:
            status = "🟢 On Track"
        elif progress_pct >= 50:
            status = "🟡 Needs Attention"
        else:
            status = "🔴 Behind Target"

        content = f"""---
generated: {datetime.now().isoformat()}
period: {week_start} to {week_end}
type: weekly_briefing
status: {status.lower().replace(' ', '_')}
---

# Monday Morning CEO Briefing

**Week of:** {week_start} to {week_end}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Status:** {status}

---

## Executive Summary

{self._generate_executive_summary(revenue_data, tasks_data, bottlenecks)}

---

## 📊 Revenue Report

| Metric | Value | Target | Progress |
|--------|-------|--------|----------|
| **This Week** | ${revenue_data.get('total_revenue', 0):,.2f} | - | - |
| **MTD** | ${current_revenue:,.2f} | ${monthly_target:,.2f} | {progress_pct:.1f}% |
| **Invoices Sent** | {revenue_data.get('invoices_count', 0)} | - | - |
| **Pending Payment** | {revenue_data.get('pending_invoices', 0)} | - | - |

### Revenue Trend

{self._generate_revenue_trend(revenue_data)}

---

## ✅ Completed Tasks

**Total Completed:** {tasks_data.get('completed_count', 0)}

**Pending:** {tasks_data.get('pending_count', 0)}

### Tasks by Type

{self._format_tasks_by_type(tasks_data.get('tasks_by_type', {}))}

### Recent Completions

{self._format_recent_tasks(tasks_data.get('completed_tasks', [])[:5])}

---

## 🚧 Bottlenecks Identified

{self._format_bottlenecks(bottlenecks)}

---

## 📱 Social Media Performance

| Metric | Value |
|--------|-------|
| **Posts This Week** | {social_data.get('posts_count', 0)} |
| **Scheduled Posts** | {social_data.get('scheduled_posts', 0)} |

---

## 💡 Proactive Suggestions

{self._format_suggestions(suggestions)}

---

## 📅 Upcoming Deadlines

{self._generate_upcoming_deadlines()}

---

## 🎯 Action Items for This Week

Based on the analysis above, here are the recommended priorities:

1. {self._generate_action_item(1, suggestions, bottlenecks)}
2. {self._generate_action_item(2, suggestions, bottlenecks)}
3. {self._generate_action_item(3, suggestions, bottlenecks)}

---

*Generated by AI Employee v1.0 (Gold Tier)*
*Next briefing: {(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')}*
"""

        return content

    def _generate_executive_summary(self, revenue_data: Dict, tasks_data: Dict,
                                     bottlenecks: List[Dict]) -> str:
        """Generate executive summary paragraph."""
        summary_parts = []

        # Revenue summary
        revenue = revenue_data.get('total_revenue', 0)
        if revenue > 0:
            summary_parts.append(f"Strong week with ${revenue:,.2f} in revenue.")
        else:
            summary_parts.append("No revenue recorded this week.")

        # Tasks summary
        completed = tasks_data.get('completed_count', 0)
        pending = tasks_data.get('pending_count', 0)
        summary_parts.append(f"{completed} tasks completed, {pending} pending.")

        # Bottlenecks
        high_severity = [b for b in bottlenecks if b.get('severity') == 'high']
        if high_severity:
            summary_parts.append(f"{len(high_severity)} critical bottleneck(s) identified.")

        return ' '.join(summary_parts)

    def _generate_revenue_trend(self, revenue_data: Dict) -> str:
        """Generate revenue trend analysis."""
        total = revenue_data.get('total_revenue', 0)
        monthly = revenue_data.get('monthly_revenue', 0)

        if total == 0 and monthly == 0:
            return "*No revenue data available. Ensure Odoo is configured and invoices are being tracked.*"

        if monthly > 0:
            weekly_avg = monthly / 4
            if total > weekly_avg * 1.2:
                return "📈 **Trend:** Above average week!"
            elif total < weekly_avg * 0.8:
                return "📉 **Trend:** Below average week. Review pipeline."
            else:
                return "➡️ **Trend:** On track with monthly goals."

        return "*Insufficient data for trend analysis.*"

    def _format_tasks_by_type(self, tasks_by_type: Dict) -> str:
        """Format tasks by type table."""
        if not tasks_by_type:
            return "*No task type data available*"

        lines = ["| Type | Count |", "|------|-------|"]
        for task_type, count in sorted(tasks_by_type.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {task_type.replace('_', ' ').title()} | {count} |")

        return '\n'.join(lines)

    def _format_recent_tasks(self, tasks: List[Dict]) -> str:
        """Format recent completed tasks."""
        if not tasks:
            return "*No recent tasks*"

        lines = []
        for task in tasks:
            name = task.get('name', 'Unknown').replace('_', ' ').replace('-', ' ')
            completed = task.get('completed_at', '')[:10]
            lines.append(f"- [x] {name} ({completed})")

        return '\n'.join(lines)

    def _format_bottlenecks(self, bottlenecks: List[Dict]) -> str:
        """Format bottlenecks section."""
        if not bottlenecks:
            return "*No bottlenecks identified. Great job!*"

        lines = []
        for bottleneck in bottlenecks:
            severity_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(
                bottleneck.get('severity', 'medium'), '🟡'
            )
            lines.append(f"- {severity_icon} **{bottleneck.get('type', 'Issue').replace('_', ' ').title()}:** {bottleneck.get('description', '')}")

        return '\n'.join(lines)

    def _format_suggestions(self, suggestions: List[Dict]) -> str:
        """Format suggestions section."""
        if not suggestions:
            return "*No specific suggestions at this time.*"

        lines = []
        for suggestion in suggestions:
            priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(
                suggestion.get('priority', 'medium'), '🟡'
            )
            category = suggestion.get('category', 'General').replace('_', ' ').title()
            lines.append(f"- {priority_icon} **{category}:** {suggestion.get('suggestion', '')}")

        return '\n'.join(lines)

    def _generate_upcoming_deadlines(self) -> str:
        """Generate upcoming deadlines section."""
        # This would integrate with calendar in future
        return """| Deadline | Task | Days Remaining |
|----------|------|----------------|
| Monthly tax prep | Accounting review | 25 |
| Q1 planning | Strategy session | 30 |
| *Add more deadlines in Business_Goals.md* | - | - |"""

    def _generate_action_item(self, index: int, suggestions: List[Dict],
                               bottlenecks: List[Dict]) -> str:
        """Generate numbered action item."""
        # Prioritize high-severity bottlenecks
        high_bottlenecks = [b for b in bottlenecks if b.get('severity') == 'high']
        if index <= len(high_bottlenecks):
            return high_bottlenecks[index - 1].get('suggestion', f'Address bottleneck {index}')

        # Then suggestions
        suggestion_index = index - len(high_bottlenecks) - 1
        if suggestion_index >= 0 and suggestion_index < len(suggestions):
            return suggestions[suggestion_index].get('suggestion', f'Action item {index}')

        return f"Review pending tasks in Needs_Action folder"


def main():
    """Main entry point."""
    import argparse

    # Load environment variables
    load_dotenv()

    parser = argparse.ArgumentParser(
        description='CEO Briefing Generator - Weekly executive reports',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ceo_briefing.py .
  python ceo_briefing.py . --week -1  # Last week's briefing
  python ceo_briefing.py . --odoo-config /path/to/.env
        """
    )
    parser.add_argument('vault_path', nargs='?', default='.', help='Path to Obsidian vault')
    parser.add_argument('--week', '-w', type=int, default=0, help='Week offset (0=current, -1=last week)')
    parser.add_argument('--odoo-host', type=str, default=os.getenv('ODOO_HOST', 'localhost'), help='Odoo host')
    parser.add_argument('--odoo-port', type=int, default=int(os.getenv('ODOO_PORT', '8069')), help='Odoo port')
    parser.add_argument('--odoo-db', type=str, default=os.getenv('ODOO_DB', 'odoo'), help='Odoo database')
    parser.add_argument('--odoo-user', type=str, default=os.getenv('ODOO_USERNAME', 'admin'), help='Odoo username')
    parser.add_argument('--odoo-password', type=str, default=os.getenv('ODOO_PASSWORD', 'admin'), help='Odoo password')

    args = parser.parse_args()

    generator = CEOBriefingGenerator(
        vault_path=args.vault_path,
        odoo_host=args.odoo_host,
        odoo_port=args.odoo_port,
        odoo_db=args.odoo_db,
        odoo_user=args.odoo_user,
        odoo_password=args.odoo_password
    )

    print("\n" + "="*60)
    print("CEO Briefing Generator")
    print("="*60)

    briefing_path = generator.generate_weekly_briefing(week_offset=args.week)

    print(f"\n✓ Briefing generated: {briefing_path}")
    print(f"\nOpen in Obsidian to review:")
    print(f"  obsidian://open?vault=AI_Employee_Vault&path={briefing_path}")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
