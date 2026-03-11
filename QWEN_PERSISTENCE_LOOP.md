# Qwen Code Persistence Loop

## What is This?

Similar to Claude Code's **"Ralph Wiggum" loop**, this keeps **Qwen Code** working on multi-step tasks until they're **actually complete**, not just giving up after one try.

---

## The Problem

Without persistence:
```
You: "Process all files in Needs_Action"
Qwen: Tries once, encounters error, gives up
Result: Task incomplete ❌
```

With Persistence Loop:
```
You: "Process all files in Needs_Action"
Qwen: Tries once, encounters error
Loop: "Not done, try again"
Qwen: Tries again, partial success
Loop: "Still not done, continue"
Qwen: Keeps working...
Result: Task COMPLETE ✅
```

---

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│              QWEN CODE PERSISTENCE LOOP                 │
└─────────────────────────────────────────────────────────┘

Start Task
    ↓
Create Task State File (In_Progress/)
    ↓
┌──────────────────────────────────────┐
│  ITERATION 1                         │
│  → Qwen works on task                │
│  → Check: Is it done?                │
│  → NO → Continue                     │
└──────────────────────────────────────┘
    ↓
┌──────────────────────────────────────┐
│  ITERATION 2                         │
│  → Qwen reviews previous attempt     │
│  → Fixes issues                      │
│  → Check: Is it done?                │
│  → NO → Continue                     │
└──────────────────────────────────────┘
    ↓
... continues looping ...
    ↓
┌──────────────────────────────────────┐
│  ITERATION N                         │
│  → Qwen completes task               │
│  → Check: Is it done?                │
│  → YES → Success!                    │
└──────────────────────────────────────┘
    ↓
Move State File to Done/
    ↓
Task Complete! ✅
```

---

## Usage

### Basic Usage

```bash
python scripts/qwen_loop.py "Process all files in Needs_Action"
```

### With Custom Vault Path

```bash
python scripts/qwen_loop.py "Process all files" /path/to/vault
```

### With Max Iterations

Edit the script or create wrapper:
```python
loop = QwenPersistenceLoop(vault_path, max_iterations=20)
```

---

## Example: Processing Facebook Comments

### Step 1: Facebook Watcher Detects Comments

Files created in `Needs_Action/`:
```
Needs_Action/
├── FACEBOOK_fb_comment_12345.md
├── FACEBOOK_fb_comment_12346.md
└── FACEBOOK_fb_comment_12347.md
```

### Step 2: Start Persistence Loop

```bash
python scripts/qwen_loop.py "Process all Facebook comments in Needs_Action"
```

### Step 3: Watch It Work

```
======================================================================
QWEN CODE PERSISTENCE LOOP
======================================================================

Task: Process all Facebook comments in Needs_Action
Vault: .
Max iterations: 10

Starting persistence loop...
======================================================================

============================================================
ITERATION 1/10
============================================================
- Reading Facebook comments...
- Created 3 approval files
- Moved 0 files (waiting for approval)
- Task not complete, continuing...

============================================================
ITERATION 2/10
============================================================
- Reviewing previous iteration...
- Approval files still pending
- Checking for new comments...
- Task not complete, continuing...

============================================================
ITERATION 3/10
============================================================
- All comments processed
- Approval files created in Pending_Approval/
- Needs_Action is now empty
- Task complete!

✅ TASK COMPLETED in 3 iterations!
```

---

## Task State Files

Each task creates a state file in `In_Progress/`:

```markdown
---
type: task_state
task: Process all Facebook comments
created: 2026-03-10T22:45:00
iteration: 3
max_iterations: 10
status: completed
---

# Task State: task_20260310_224500

## Original Task
Process all Facebook comments in Needs_Action

## Iteration History

### Iteration 1
- Started: 2026-03-10T22:45:00
- Status: In Progress
- Processed 3 comments
- Created 3 approval files

### Iteration 2
- Started: 2026-03-10T22:45:30
- Status: In Progress
- Reviewing approval status
- 2 files approved, 1 pending

### Iteration 3
- Started: 2026-03-10T22:46:00
- Status: Completed
- All files processed
- Task complete!

## Completion Criteria
Task is complete when:
- All files in /Needs_Action/ are processed ✓
- Results moved to /Done/ ✓
- No errors occurred ✓
```

---

## Integration with Orchestrator

The orchestrator can use the persistence loop:

```python
# In orchestrator.py

def process_needs_action(self):
    """Process all files in Needs_Action using persistence loop."""
    
    pending_files = list(self.needs_action.glob('*.md'))
    
    if not pending_files:
        return
    
    # Use persistence loop for multi-step processing
    loop = QwenPersistenceLoop(str(self.vault_path))
    
    task = f"Process {len(pending_files)} files in Needs_Action"
    success = loop.execute_task(task)
    
    if success:
        self.log_action('persistence_loop_complete', task, 'success')
    else:
        self.log_action('persistence_loop_failed', task, 'error')
```

---

## Completion Detection

The loop checks if task is complete by:

1. **Needs_Action Empty** - No files left to process
2. **Done Folder Updated** - Results are there
3. **No Errors** - Logs show success

You can customize the `check_task_completion()` method for your use case.

---

## Max Iterations

Default: **10 iterations**

Why limit?
- Prevents infinite loops
- Allows human review if stuck
- Saves resources

If task needs more iterations:
1. Check logs for what's blocking
2. Fix the issue
3. Re-run loop

---

## Error Handling

If loop fails:

1. **State file moved to Logs/**
   - For human review
   - Contains all iteration history

2. **Error logged**
   - What was attempted
   - Where it failed

3. **Task can be retried**
   - Just run loop again
   - It will pick up where it left off

---

## Real-World Example: Customer Inquiry Workflow

### Scenario

Customer comments on Facebook: "I want to buy your service!"

### Without Persistence Loop

```
Qwen: Reads comment
Qwen: Tries to create reply
Qwen: MCP server not responding
Qwen: Gives up ❌
Result: Customer never gets response
```

### With Persistence Loop

```
Iteration 1:
Qwen: Reads comment
Qwen: Tries to create reply
Qwen: MCP server not responding
Loop: Not done, retry...

Iteration 2:
Qwen: Retries MCP server
Qwen: Server responds!
Qwen: Creates reply
Qwen: Creates approval file
Qwen: Waits for approval
Loop: Checking approval...

Iteration 3:
Qwen: Approval still pending
Qwen: Logs status
Loop: Waiting...

Iteration 4:
Qwen: Approval received!
Qwen: Executes reply
Qwen: Posts to Facebook
Qwen: Creates customer in Odoo
Loop: Checking completion...
Loop: Needs_Action is empty!
Loop: Task complete! ✅

Result: Customer gets response, invoice created
```

---

## Benefits

| Benefit | Description |
|---------|-------------|
| **Persistence** | Doesn't give up after first error |
| **Context** | Each iteration learns from previous |
| **Tracking** | Full audit trail in state files |
| **Flexibility** | Works for any multi-step task |
| **Safety** | Max iterations prevents infinite loops |

---

## Best Practices

### 1. Clear Task Descriptions

```bash
# Good
python qwen_loop.py "Process all Facebook comments and create replies"

# Bad
python qwen_loop.py "Do stuff"
```

### 2. Monitor Progress

Check `In_Progress/` folder:
```bash
dir In_Progress
type In_Progress\task_*.md
```

### 3. Review Logs

```bash
type Logs\qwen_loop_*.md
```

### 4. Set Reasonable Max Iterations

- Simple tasks: 3-5 iterations
- Complex tasks: 10-20 iterations
- Research tasks: 20+ iterations

---

## Advanced: Custom Completion Criteria

Override `check_task_completion()` for your use case:

```python
class CustomLoop(QwenPersistenceLoop):
    def check_task_completion(self, state_file):
        # Custom logic
        if self.custom_condition():
            return True
        return False
```

---

## Comparison: Ralph Wiggum vs Qwen Loop

| Feature | Ralph Wiggum (Claude) | Qwen Loop |
|---------|----------------------|-----------|
| **Platform** | Claude Code | Qwen Code |
| **Implementation** | Plugin | Python Script |
| **Detection** | File movement | State files |
| **Max Iterations** | Configurable | Configurable |
| **Context** | Previous output | Full state tracking |

---

## Future Enhancements

1. **Qwen Code Integration**
   - Direct API calls
   - CLI invocation
   - File-based interaction

2. **Smart Retry**
   - Learn from failures
   - Adjust strategy

3. **Parallel Processing**
   - Multiple tasks at once
   - Batch processing

4. **Human-in-the-Loop**
   - Request help when stuck
   - Escalate after N failures

---

## Quick Reference

```bash
# Start persistence loop
python scripts/qwen_loop.py "Your task"

# Check task status
dir In_Progress

# View completed tasks
dir Done\task_*.md

# View failed tasks
dir Logs\failed_task_*.md
```

---

**Your AI Employee now has persistence!** 🎉

Multi-step tasks will now complete reliably, even if errors occur along the way!
