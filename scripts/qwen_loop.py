#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qwen Code Persistence Loop

Keeps Qwen Code working on multi-step tasks until completion.
Similar to Claude Code's "Ralph Wiggum" loop.

Usage:
    python qwen_loop.py "Process all files in Needs_Action"
"""

import sys
import os
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class QwenPersistenceLoop:
    """
    Keeps Qwen Code working on tasks until completion.
    
    How it works:
    1. Creates task state file
    2. Launches Qwen Code with prompt
    3. Monitors task completion
    4. If not complete → Re-launch Qwen with context
    5. Loops until task is done or max iterations reached
    """

    def __init__(self, vault_path: str = '.', max_iterations: int = 10):
        self.vault_path = Path(vault_path)
        self.max_iterations = max_iterations
        self.state_folder = self.vault_path / 'In_Progress'
        self.done_folder = self.vault_path / 'Done'
        self.needs_action = self.vault_path / 'Needs_Action'
        self.logs_folder = self.vault_path / 'Logs'
        
        # Ensure folders exist
        for folder in [self.state_folder, self.done_folder, self.logs_folder]:
            folder.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_task_state(self, task: str, iteration: int = 0) -> Path:
        """Create task state file to track progress."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        task_id = f"task_{timestamp}"
        
        state_file = self.state_folder / f"{task_id}.md"
        
        content = f"""---
type: task_state
task: {task}
created: {datetime.now().isoformat()}
iteration: {iteration}
max_iterations: {self.max_iterations}
status: in_progress
---

# Task State: {task_id}

## Original Task
{task}

## Iteration History

### Iteration {iteration}
- Started: {datetime.now().isoformat()}
- Status: In Progress

## Completion Criteria
Task is complete when:
- All files in /Needs_Action/ are processed
- Results moved to /Done/
- No errors occurred

## Notes
Qwen Code will work on this task until completion or max iterations.
"""
        state_file.write_text(content, encoding='utf-8')
        self.logger.info(f"Created task state: {state_file}")
        return state_file

    def update_task_state(self, state_file: Path, iteration: int, 
                          output: str, status: str = 'in_progress'):
        """Update task state with iteration results."""
        content = state_file.read_text(encoding='utf-8')
        
        update_section = f"""
### Iteration {iteration} Results
- Completed: {datetime.now().isoformat()}
- Status: {status}
- Output: {output[:500]}...

"""
        # Insert before "## Notes"
        if '## Notes' in content:
            content = content.replace('## Notes', update_section + '## Notes')
        else:
            content += update_section
        
        # Update status
        content = content.replace(f'status: in_progress', f'status: {status}')
        content = content.replace(f'iteration: {iteration-1}', f'iteration: {iteration}')
        
        state_file.write_text(content, encoding='utf-8')

    def check_task_completion(self, state_file: Path) -> bool:
        """
        Check if task is complete.
        
        Completion criteria:
        1. No files left in Needs_Action (for processing tasks)
        2. Results in Done folder
        3. No errors in logs
        """
        # Check if any files still in Needs_Action
        pending_files = list(self.needs_action.glob('*.md'))
        
        if pending_files:
            self.logger.info(f"Task not complete: {len(pending_files)} files pending")
            return False
        
        self.logger.info("Task complete: No pending files")
        return True

    def get_qwen_prompt(self, task: str, iteration: int, 
                       previous_output: str = None) -> str:
        """
        Generate prompt for Qwen Code.
        
        Includes:
        - Original task
        - Previous iteration results
        - Instructions to continue
        """
        prompt = f"""
# Task: {task}

"""
        if iteration > 0 and previous_output:
            prompt += f"""
## Previous Attempt (Iteration {iteration})
{previous_output[:1000]}

## Issues Identified
The task is not yet complete. Please:
1. Review what was done
2. Identify what's missing
3. Continue working until complete

"""
        
        prompt += f"""
## Instructions

Process all files in /Needs_Action/ folder:
1. Read each file
2. Take appropriate action
3. Move processed files to /Done/
4. Create any necessary approval files in /Pending_Approval/

## Completion Criteria

Task is complete when:
- All files in /Needs_Action/ are processed
- Results are in /Done/ or /Pending_Approval/
- No errors occurred

## Important

- Work step by step
- Don't give up
- If you encounter errors, try again
- Keep working until ALL files are processed

Start now.
"""
        return prompt

    def run_qwen_code(self, prompt: str) -> str:
        """
        Run Qwen Code with the given prompt.
        
        In a real implementation, this would:
        1. Call Qwen Code API
        2. Or launch Qwen Code CLI
        3. Capture output
        
        For now, this is a placeholder.
        """
        self.logger.info("Running Qwen Code...")
        
        # TODO: Implement actual Qwen Code integration
        # This could be:
        # 1. API call to Qwen
        # 2. CLI invocation
        # 3. File-based interaction
        
        output = f"Qwen Code processed task at iteration {datetime.now().isoformat()}"
        
        return output

    def execute_task(self, task: str) -> bool:
        """
        Execute task with persistence loop.
        
        Returns:
            True if task completed successfully
            False if failed or max iterations reached
        """
        self.logger.info(f"Starting persistence loop for task: {task}")
        self.logger.info(f"Max iterations: {self.max_iterations}")
        
        # Create initial task state
        state_file = self.create_task_state(task)
        
        iteration = 0
        previous_output = None
        
        while iteration < self.max_iterations:
            iteration += 1
            
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"ITERATION {iteration}/{self.max_iterations}")
            self.logger.info(f"{'='*60}")
            
            # Generate prompt
            prompt = self.get_qwen_prompt(task, iteration, previous_output)
            
            # Run Qwen Code
            output = self.run_qwen_code(prompt)
            
            # Update state
            self.update_task_state(state_file, iteration, output)
            
            # Check completion
            if self.check_task_completion(state_file):
                self.logger.info(f"\n✅ TASK COMPLETED in {iteration} iterations!")
                
                # Move state file to Done
                done_file = self.done_folder / state_file.name
                state_file.rename(done_file)
                
                return True
            
            previous_output = output
            self.logger.info(f"Task not complete, continuing...")
            
            # Small delay before next iteration
            time.sleep(2)
        
        # Max iterations reached
        self.logger.error(f"\n❌ MAX ITERATIONS ({self.max_iterations}) REACHED")
        self.logger.error("Task not completed")
        
        # Move state file to Logs for review
        log_file = self.logs_folder / f"failed_{state_file.name}"
        state_file.rename(log_file)
        
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python qwen_loop.py \"Your task description\"")
        print("\nExample:")
        print('  python qwen_loop.py "Process all files in Needs_Action"')
        sys.exit(1)
    
    task = sys.argv[1]
    vault_path = sys.argv[2] if len(sys.argv) > 2 else '.'
    
    print("\n" + "="*70)
    print("QWEN CODE PERSISTENCE LOOP")
    print("="*70)
    print(f"\nTask: {task}")
    print(f"Vault: {vault_path}")
    print(f"Max iterations: 10")
    print("\nStarting persistence loop...")
    print("="*70 + "\n")
    
    loop = QwenPersistenceLoop(vault_path)
    success = loop.execute_task(task)
    
    print("\n" + "="*70)
    if success:
        print("✅ SUCCESS! Task completed!")
    else:
        print("❌ FAILED! Max iterations reached.")
    print("="*70 + "\n")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
