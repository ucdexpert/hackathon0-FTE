#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plan Generator - Creates Plan.md files for items in Needs_Action.

This script analyzes action files and generates structured plans
for Qwen Code to execute.

Usage:
    python plan_generator.py <vault_path>
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class PlanGenerator:
    """Generates Plan.md files for action items."""
    
    # Plan templates by action type
    TEMPLATES = {
        'email': {
            'objective': 'Process email and respond if needed',
            'steps': [
                'Read email content and identify sender intent',
                'Check Company_Handbook.md for response rules',
                'Draft appropriate response',
                'Send response (REQUIRES APPROVAL)',
                'Archive email after processing'
            ]
        },
        'whatsapp_message': {
            'objective': 'Process WhatsApp message and respond',
            'steps': [
                'Read message and identify keywords',
                'Determine urgency level',
                'Draft response following Company_Handbook.md',
                'Send response on WhatsApp (REQUIRES APPROVAL)',
                'Mark message as processed'
            ]
        },
        'file_drop': {
            'objective': 'Process dropped file',
            'steps': [
                'Read file metadata and content',
                'Determine required action',
                'Execute action or create sub-plan',
                'Move file to appropriate folder'
            ]
        },
        'invoice_request': {
            'objective': 'Generate and send invoice',
            'steps': [
                'Identify client details from request',
                'Look up client rate/project details',
                'Generate invoice PDF',
                'Send invoice via email (REQUIRES APPROVAL)',
                'Log transaction in /Accounting/',
                'Update Dashboard.md'
            ]
        },
        'payment_request': {
            'objective': 'Process payment request',
            'steps': [
                'Verify payment details and amount',
                'Check against Company_Handbook.md thresholds',
                'Create payment approval request',
                'Wait for human approval',
                'Execute payment (after approval)',
                'Log transaction'
            ]
        }
    }
    
    def __init__(self, vault_path: str):
        """
        Initialize Plan Generator.
        
        Args:
            vault_path: Path to Obsidian vault
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.plans = self.vault_path / 'Plans'
        self.company_handbook = self.vault_path / 'Company_Handbook.md'
        
        self.plans.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _detect_action_type(self, content: str, filename: str) -> str:
        """Detect action type from file content and name."""
        content_lower = content.lower()
        
        # Check frontmatter for type
        if 'type:' in content_lower:
            for line in content.split('\n')[:10]:
                if 'type:' in line.lower():
                    type_value = line.split(':')[1].strip().lower()
                    if 'email' in type_value:
                        return 'email'
                    elif 'whatsapp' in type_value:
                        return 'whatsapp_message'
                    elif 'file' in type_value:
                        return 'file_drop'
        
        # Check filename patterns
        if filename.upper().startswith('EMAIL_'):
            return 'email'
        elif filename.upper().startswith('WHATSAPP_'):
            return 'whatsapp_message'
        elif filename.upper().startswith('FILE_'):
            return 'file_drop'
        
        # Check content keywords
        if 'invoice' in content_lower and ('request' in content_lower or 'send' in content_lower):
            return 'invoice_request'
        elif 'payment' in content_lower:
            return 'payment_request'
        elif 'whatsapp' in content_lower:
            return 'whatsapp_message'
        elif 'email' in content_lower:
            return 'email'
        
        return 'file_drop'  # Default
    
    def _extract_metadata(self, content: str) -> Dict:
        """Extract metadata from action file."""
        metadata = {
            'from': 'Unknown',
            'subject': 'No Subject',
            'priority': 'normal'
        }
        
        # Simple frontmatter parsing
        in_frontmatter = False
        for line in content.split('\n'):
            if line.strip() == '---':
                if not in_frontmatter:
                    in_frontmatter = True
                else:
                    break
                continue
            
            if in_frontmatter and ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key in ['from', 'from_email', 'chat_name']:
                    metadata['from'] = value
                elif key in ['subject']:
                    metadata['subject'] = value
                elif key in ['priority']:
                    metadata['priority'] = value
        
        return metadata
    
    def _get_template(self, action_type: str, metadata: Dict) -> Dict:
        """Get plan template for action type."""
        base_template = self.TEMPLATES.get(action_type, self.TEMPLATES['file_drop'])
        
        return {
            'objective': base_template['objective'],
            'steps': base_template['steps'].copy(),
            'priority': metadata.get('priority', 'normal')
        }
    
    def create_plan(self, action_file: Path) -> Optional[Path]:
        """
        Create a Plan.md file for an action file.
        
        Args:
            action_file: Path to action file in Needs_Action
            
        Returns:
            Path to created plan file, or None if failed
        """
        try:
            # Read action file
            content = action_file.read_text(encoding='utf-8')
            
            # Detect type and extract metadata
            action_type = self._detect_action_type(content, action_file.name)
            metadata = self._extract_metadata(content)
            template = self._get_template(action_type, metadata)
            
            # Generate timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_type = action_type.replace('_', '-')
            
            # Create plan filename
            plan_filename = f"PLAN_{safe_type}_{timestamp}.md"
            plan_path = self.plans / plan_filename
            
            # Generate steps markdown
            steps_md = '\n'.join(f'- [ ] {step}' for step in template['steps'])
            
            # Create plan content
            plan_content = f"""---
type: plan
objective: {template['objective']}
created: {datetime.now().isoformat()}
status: pending
source_file: {action_file.name}
priority: {template['priority']}
estimated_steps: {len(template['steps'])}
completed_steps: 0
---

# Plan: {template['objective'].title()}

## Objective

{template['objective']}

## Source

- **From:** /Needs_Action/{action_file.name}
- **Type:** {action_type.replace('_', ' ').title()}
- **From:** {metadata['from']}
- **Subject:** {metadata['subject']}

## Steps

{steps_md}

## Notes

- Follow Company_Handbook.md rules
- Request approval for sensitive actions
- Log all completed actions

## Completion Criteria

Plan is complete when:
1. All steps executed or marked N/A
2. Required approvals obtained
3. Files moved to appropriate folders
4. Dashboard.md updated

---

*Created by Plan Generator*
"""
            
            # Write plan file
            plan_path.write_text(plan_content, encoding='utf-8')
            
            self.logger.info(f'Created plan: {plan_path.name}')
            return plan_path
            
        except Exception as e:
            self.logger.error(f'Failed to create plan: {e}')
            return None
    
    def process_all_pending(self) -> List[Path]:
        """
        Process all action files without plans.
        
        Returns:
            List of created plan files
        """
        created_plans = []
        
        # Get existing plan source files
        existing_plans = set()
        for plan_file in self.plans.glob('*.md'):
            content = plan_file.read_text(encoding='utf-8')
            for line in content.split('\n')[:15]:
                if 'source_file:' in line:
                    source = line.split(':')[1].strip()
                    existing_plans.add(source)
        
        # Check each action file
        for action_file in self.needs_action.glob('*.md'):
            if action_file.name not in existing_plans:
                plan_path = self.create_plan(action_file)
                if plan_path:
                    created_plans.append(plan_path)
        
        if created_plans:
            self.logger.info(f'Created {len(created_plans)} new plans')
        else:
            self.logger.debug('No new plans needed')
        
        return created_plans


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python plan_generator.py <vault_path>")
        print("\nExample:")
        print("  python plan_generator.py /path/to/vault")
        sys.exit(1)
    
    vault_path = sys.argv[1]
    
    if not Path(vault_path).exists():
        print(f"Vault path not found: {vault_path}")
        sys.exit(1)
    
    generator = PlanGenerator(vault_path)
    plans = generator.process_all_pending()
    
    if plans:
        print(f"\nCreated {len(plans)} plan(s):")
        for plan in plans:
            print(f"  - {plan.name}")
    else:
        print("\nNo new plans needed")


if __name__ == "__main__":
    main()
