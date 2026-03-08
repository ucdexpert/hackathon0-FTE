#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scheduler - Creates cron jobs (Linux/Mac) or Task Scheduler tasks (Windows).

Manages scheduled tasks for AI Employee operations like daily briefings,
periodic checks, and automated Qwen Code prompts.

Usage:
    python scheduler.py [install|uninstall|status|run] [--task TASK_NAME]
"""

import sys
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Default tasks configuration
DEFAULT_TASKS = [
    {
        'name': 'check_pending',
        'schedule': '*/30 * * * *',  # Every 30 minutes
        'command': 'python scripts/plan_generator.py .',
        'description': 'Check for pending actions and generate plans',
        'enabled': True
    },
    {
        'name': 'daily_briefing',
        'schedule': '0 8 * * *',  # 8:00 AM daily
        'command': 'python scripts/orchestrator.py . 30',
        'description': 'Generate daily briefing and update dashboard',
        'enabled': True
    },
    {
        'name': 'weekly_audit',
        'schedule': '0 20 * * 0',  # Sunday 8:00 PM
        'command': 'python scripts/weekly_audit.py .',
        'description': 'Weekly business and accounting audit',
        'enabled': True
    }
]


class Scheduler:
    """Manages scheduled tasks for AI Employee."""
    
    def __init__(self, vault_path: str):
        """
        Initialize Scheduler.
        
        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path).resolve()
        self.config_file = self.vault_path / 'scheduler_config.json'
        self.log_file = self.vault_path / 'Logs' / 'scheduler.log'
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Ensure Logs folder exists
        (self.vault_path / 'Logs').mkdir(parents=True, exist_ok=True)
        
        # Detect platform
        self.platform = sys.platform
        self.is_windows = self.platform.startswith('win')
        
        self.logger.info(f'Platform: {"Windows" if self.is_windows else "Linux/Mac"}')
    
    def load_config(self) -> dict:
        """Load scheduler configuration."""
        if self.config_file.exists():
            return json.loads(self.config_file.read_text())
        return {'tasks': DEFAULT_TASKS}
    
    def save_config(self, config: dict):
        """Save scheduler configuration."""
        self.config_file.write_text(json.dumps(config, indent=2))
    
    def _get_python_executable(self) -> str:
        """Get Python executable path."""
        return sys.executable
    
    def _get_script_path(self, script: str) -> str:
        """Get absolute path to script."""
        return str(self.vault_path / script)
    
    def install_cron(self, task: dict = None):
        """Install cron jobs on Linux/Mac."""
        try:
            # Get current crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            current_cron = result.stdout if result.returncode == 0 else ''
            
            # Remove existing AI_Employee cron jobs
            lines = current_cron.split('\n')
            new_lines = [l for l in lines if 'AI_Employee' not in l and l.strip()]
            
            # Add new cron jobs
            config = self.load_config()
            tasks = [task] if task else config['tasks']
            
            for t in tasks:
                if not t.get('enabled', True):
                    continue
                
                # Build cron entry
                script_path = self._get_script_path(t['command'].split()[1])
                args = t['command'].split()[2:] if len(t['command'].split()) > 2 else []
                
                cron_cmd = f"{self._get_python_executable()} {script_path} {' '.join(args)}"
                cron_entry = f"# AI_Employee_{t['name']}\n{t['schedule']} cd {self.vault_path} && {cron_cmd} >> {self.log_file} 2>&1\n"
                
                new_lines.append(cron_entry)
                self.logger.info(f"Adding cron job: {t['name']} ({t['schedule']})")
            
            # Install new crontab
            new_cron = '\n'.join(new_lines)
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_cron)
            
            self.logger.info('Cron jobs installed successfully')
            print(f"Cron jobs installed. View with: crontab -l")
            
        except Exception as e:
            self.logger.error(f'Failed to install cron: {e}')
            print(f"Error: {e}")
    
    def uninstall_cron(self):
        """Remove AI_Employee cron jobs."""
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                new_lines = [l for l in lines if 'AI_Employee' not in l and l.strip()]
                
                if len(new_lines) < lines.count(''):
                    new_cron = '\n'.join(new_lines)
                    process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
                    process.communicate(input=new_cron)
                
                self.logger.info('AI_Employee cron jobs removed')
                print('AI_Employee cron jobs removed')
            else:
                print('No cron jobs found')
                
        except Exception as e:
            self.logger.error(f'Failed to uninstall cron: {e}')
    
    def install_windows_task(self, task: dict = None):
        """Install tasks in Windows Task Scheduler."""
        config = self.load_config()
        tasks = [task] if task else config['tasks']
        
        for t in tasks:
            if not t.get('enabled', True):
                continue
            
            task_name = f"AI_Employee_{t['name']}"
            script_path = self._get_script_path(t['command'].split()[1])
            args = t['command'].split()[2:] if len(t['command'].split()) > 2 else []
            
            # Parse cron schedule for Windows
            trigger = self._cron_to_schtasks(t['schedule'])
            
            # Build schtasks command
            cmd = [
                'schtasks', '/Create',
                '/TN', task_name,
                '/TR', f'"{self._get_python_executable()} {script_path} {" ".join(args)}"',
                '/SC', trigger['frequency'],
                '/SD', '01/01/2026',  # Start date
                '/ST', trigger.get('time', '00:00'),  # Start time
                '/RL', 'HIGHEST',  # Run level
                '/F'  # Force create
            ]
            
            if trigger.get('modifier'):
                cmd.extend(['/MO', str(trigger['modifier'])])
            
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
                self.logger.info(f"Windows task installed: {task_name}")
                print(f"Task installed: {task_name}")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to install {task_name}: {e.stderr}")
                print(f"Error installing {task_name}: {e.stderr}")
    
    def _cron_to_schtasks(self, cron_expr: str) -> dict:
        """Convert cron expression to schtasks parameters."""
        parts = cron_expr.split()
        
        if len(parts) != 5:
            return {'frequency': 'ONCE', 'time': '00:00'}
        
        minute, hour, day, month, weekday = parts
        
        # Handle common patterns
        if minute.startswith('*/'):
            # Every N minutes
            return {
                'frequency': 'MINUTE',
                'modifier': int(minute[2:])
            }
        elif hour == '*' and minute != '*':
            # Every hour at specific minute
            return {
                'frequency': 'HOURLY',
                'modifier': 1
            }
        elif day == '*' and month == '*' and weekday == '*':
            # Daily at specific time
            return {
                'frequency': 'DAILY',
                'time': f"{hour.zfill(2)}:{minute.zfill(2)}"
            }
        elif weekday != '*':
            # Weekly on specific day
            day_map = {'0': 'SUN', '1': 'MON', '2': 'TUE', '3': 'WED', 
                       '4': 'THU', '5': 'FRI', '6': 'SAT', '7': 'SUN'}
            return {
                'frequency': 'WEEKLY',
                'day': day_map.get(weekday, 'SUN'),
                'time': f"{hour.zfill(2)}:{minute.zfill(2)}"
            }
        
        return {'frequency': 'ONCE', 'time': '00:00'}
    
    def uninstall_windows_task(self):
        """Remove AI_Employee tasks from Windows Task Scheduler."""
        for task in DEFAULT_TASKS:
            task_name = f"AI_Employee_{task['name']}"
            try:
                subprocess.run(
                    ['schtasks', '/Delete', '/TN', task_name, '/F'],
                    capture_output=True
                )
                self.logger.info(f"Removed task: {task_name}")
            except Exception as e:
                self.logger.debug(f"Could not remove {task_name}: {e}")
        
        print('AI_Employee tasks removed from Task Scheduler')
    
    def status(self):
        """Show status of scheduled tasks."""
        print(f"\n{'='*60}")
        print("AI Employee Scheduler Status")
        print(f"{'='*60}\n")
        
        config = self.load_config()
        
        print(f"Platform: {'Windows' if self.is_windows else 'Linux/Mac'}")
        print(f"Config file: {self.config_file}")
        print(f"Log file: {self.log_file}")
        print(f"\nScheduled Tasks ({len(config['tasks'])} configured):\n")
        
        for task in config['tasks']:
            status = "✓" if task.get('enabled', True) else "✗"
            print(f"  [{status}] {task['name']}")
            print(f"      Schedule: {task['schedule']}")
            print(f"      Command: {task['command']}")
            print(f"      Description: {task.get('description', 'N/A')}")
            print()
    
    def run_task(self, task_name: str):
        """Run a specific task manually."""
        config = self.load_config()
        
        task = next((t for t in config['tasks'] if t['name'] == task_name), None)
        
        if not task:
            print(f"Task not found: {task_name}")
            return
        
        if not task.get('enabled', True):
            print(f"Task is disabled: {task_name}")
            return
        
        self.logger.info(f"Running task: {task_name}")
        print(f"Running: {task['command']}")
        
        try:
            result = subprocess.run(
                task['command'],
                shell=True,
                cwd=str(self.vault_path),
                capture_output=True,
                text=True
            )
            
            print(result.stdout)
            if result.stderr:
                print(f"Errors: {result.stderr}")
            
            self.logger.info(f"Task completed: {task_name}")
            
        except Exception as e:
            self.logger.error(f"Task failed: {e}")
            print(f"Error: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Employee Scheduler')
    parser.add_argument('action', nargs='?', default='status',
                        choices=['install', 'uninstall', 'status', 'run'],
                        help='Action to perform')
    parser.add_argument('--task', '-t', type=str, help='Specific task name')
    parser.add_argument('--platform', '-p', choices=['auto', 'windows', 'linux'],
                        default='auto', help='Force platform type')
    
    args = parser.parse_args()
    
    if len(sys.argv) < 2:
        args.action = 'status'
    
    # Determine vault path (current directory or parent)
    vault_path = Path('.')
    if not (vault_path / 'Dashboard.md').exists():
        # Try parent directory
        if (vault_path.parent / 'Dashboard.md').exists():
            vault_path = vault_path.parent
    
    scheduler = Scheduler(str(vault_path))
    
    if args.action == 'install':
        if scheduler.is_windows:
            scheduler.install_windows_task()
        else:
            scheduler.install_cron()
    
    elif args.action == 'uninstall':
        if scheduler.is_windows:
            scheduler.uninstall_windows_task()
        else:
            scheduler.uninstall_cron()
    
    elif args.action == 'status':
        scheduler.status()
    
    elif args.action == 'run':
        if not args.task:
            print("Error: --task required for run action")
            sys.exit(1)
        scheduler.run_task(args.task)


if __name__ == "__main__":
    main()
