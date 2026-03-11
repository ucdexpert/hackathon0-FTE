# LinkedIn MCP Server - Complete Usage Guide

## 🔧 Setup for Qwen Code

### Step 1: Add MCP Server Configuration

Add this to your Qwen Code MCP settings (`.qwen/settings.json` or MCP config):

```json
{
  "mcpServers": {
    "linkedin": {
      "command": "python",
      "args": ["scripts/mcp/linkedin_mcp_server.py", "--stdio"],
      "cwd": "D:\\hackathons-Q-4\\hackathon 0 new-2\\AI_Employee_Vault"
    }
  }
}
```

### Step 2: Verify Installation

```bash
# Check if MCP server runs
python scripts/mcp/linkedin_mcp_server.py --stdio
```

You should see: `LinkedIn MCP Server starting (stdio mode)...`

---

## 🛠️ Available MCP Tools

### 1. `linkedin_authenticate`

**Purpose:** Open browser for manual LinkedIn login.

**Parameters:** None

**Example Response:**
```json
{
  "success": true,
  "message": "Authentication successful. Session saved.",
  "session_path": "D:/hackathons-Q-4/.../.linkedin_session"
}
```

**Usage:**
```bash
python scripts/mcp/linkedin_mcp_server.py --authenticate
```

---

### 2. `linkedin_check_auth`

**Purpose:** Check if LinkedIn session is authenticated.

**Parameters:** None

**Example Response:**
```
LinkedIn authentication: ✓ AUTHENTICATED
Session path: D:/.../.linkedin_session
Ready to post!
```

**Usage:**
```bash
python scripts/mcp/linkedin_mcp_server.py --check-auth
```

---

### 3. `linkedin_post` ⭐ Main Tool

**Purpose:** Post content to LinkedIn.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `content` | string | ✅ Yes | Post text (max 3000 chars) |
| `dry_run` | boolean | ❌ No | If true, log but don't post |

**Example MCP Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "linkedin_post",
    "arguments": {
      "content": "Excited to share my AI Employee project! #AI #Automation",
      "dry_run": false
    }
  }
}
```

**Example Response:**
```json
{
  "success": true,
  "message": "Post submitted successfully",
  "screenshot": "D:/.../Logs/linkedin_post_1773226376.png",
  "timestamp": "2026-03-11T15:46:16",
  "content_length": 58
}
```

**Usage:**
```bash
# Post directly
python scripts/mcp/linkedin_mcp_server.py --post "Your post text here"

# Dry run (test)
python scripts/mcp/linkedin_mcp_server.py --post "Test post" --dry-run
```

---

### 4. `linkedin_create_approval_request`

**Purpose:** Create HITL (Human-in-the-Loop) approval file.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `content` | string | ✅ Yes | Post content to approve |
| `reason` | string | ❌ No | Reason for this post |

**Example MCP Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "linkedin_create_approval_request",
    "arguments": {
      "content": "Big announcement coming soon!",
      "reason": "Marketing campaign launch"
    }
  }
}
```

**Creates File:** `Pending_Approval/LINKEDIN_POST_20260311_120000.md`

**File Content:**
```markdown
---
type: linkedin_post_approval
action: post_to_linkedin
content_length: 28
created: 2026-03-11T12:00:00
status: pending
reason: Marketing campaign launch
---

## LinkedIn Post Content

Big announcement coming soon!

## To Approve
Move this file to: /Approved/

## To Reject
Move this file to: /Rejected/

## Auto-Posted By
LinkedIn MCP Server will post when approved.
```

**Response:**
```
✓ Approval request created: D:/.../Pending_Approval/LINKEDIN_POST_20260311_120000.md
Move to /Approved/ to execute the post.
```

---

### 5. `linkedin_check_approvals`

**Purpose:** Check for approved LinkedIn post requests.

**Parameters:** None

**Example Response:**
```
Found 2 approved post(s):
  - LINKEDIN_POST_20260311_103000.md
  - LINKEDIN_POST_20260311_104500.md
```

---

## 📝 Complete Workflow Examples

### Workflow 1: Direct Post via MCP

```python
# Example MCP client code
import requests

response = requests.post("http://localhost:8808", json={
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "linkedin_post",
        "arguments": {
            "content": "Hello LinkedIn from MCP! #AI",
            "dry_run": False
        }
    }
})

print(response.json())
```

### Workflow 2: HITL Approval Flow

```
1. Qwen Code calls: linkedin_create_approval_request
   ↓
2. File created in: Pending_Approval/
   ↓
3. Human reviews in Obsidian
   ↓
4. Human moves file to: Approved/
   ↓
5. Orchestrator calls: linkedin_post
   ↓
6. Post published + screenshot saved
   ↓
7. File moved to: Done/
```

### Workflow 3: Check Auth Before Posting

```python
# Pseudocode for Qwen Code
auth_status = mcp.call("linkedin_check_auth", {})

if "AUTHENTICATED" in auth_status:
    result = mcp.call("linkedin_post", {
        "content": "My post text",
        "dry_run": False
    })
    print(f"Posted! {result}")
else:
    print("Not authenticated! Run authentication first.")
    mcp.call("linkedin_authenticate", {})
```

---

## 🚀 Command Line Usage

### Quick Reference

```bash
# Authenticate (one-time)
python scripts/mcp/linkedin_mcp_server.py --authenticate

# Check auth status
python scripts/mcp/linkedin_mcp_server.py --check-auth

# Post directly
python scripts/mcp/linkedin_mcp_server.py --post "Your post text"

# Dry run test
python scripts/mcp/linkedin_mcp_server.py --post "Test" --dry-run

# Run as MCP server (for Qwen Code)
python scripts/mcp/linkedin_mcp_server.py --stdio
```

---

## 🔗 Integration with Qwen Code

### Example Prompt for Qwen Code

```
I want to post to LinkedIn about my hackathon progress.

1. First, check if we're authenticated with LinkedIn
2. If not authenticated, run the authentication flow
3. Create an approval request with this content:
   "Just completed Silver Tier! Features: Gmail Watcher, 
    WhatsApp Watcher, LinkedIn Auto-posting. #Hackathon #AI"
4. Wait for me to approve in the Approved folder
5. Once approved, execute the post
```

### Qwen Code Will:

1. Call `linkedin_check_auth` → Check authentication
2. Call `linkedin_create_approval_request` → Create approval file
3. Wait for you to move file to `/Approved/`
4. Call `linkedin_post` → Execute the post
5. Report success with screenshot path

---

## 📁 File Locations

| File/Folder | Purpose |
|-------------|---------|
| `.linkedin_session/` | Browser session cookies |
| `Logs/linkedin_post_*.png` | Post screenshots |
| `Pending_Approval/` | Awaiting human approval |
| `Approved/` | Ready to execute |
| `Done/` | Completed posts |
| `Rejected/` | Denied posts |

---

## ⚠️ Troubleshooting

### "Not authenticated"
```bash
python scripts/mcp/linkedin_mcp_server.py --authenticate
```

### "Content exceeds 3000 characters"
LinkedIn has a 3000 character limit. Shorten your post.

### "Editor not found"
LinkedIn UI changed. Check debug files in `Logs/` folder:
- `linkedin_debug_*.png` - Screenshot
- `linkedin_debug_*.html` - Page HTML

### MCP Server not responding
```bash
# Test stdio mode
python scripts/mcp/linkedin_mcp_server.py --stdio
```

---

## 📊 MCP Tool Summary

| Tool | Auth | Post | HITL | Check |
|------|------|------|------|-------|
| `linkedin_authenticate` | ✅ | | | |
| `linkedin_check_auth` | | | | ✅ |
| `linkedin_post` | ✅ | ✅ | | |
| `linkedin_create_approval_request` | | | ✅ | |
| `linkedin_check_approvals` | | | | ✅ |

---

## 🎯 Best Practices

1. **Always test with dry_run first**
   ```bash
   python scripts/mcp/linkedin_mcp_server.py --post "Test" --dry-run
   ```

2. **Use HITL for important posts**
   - Business announcements
   - Client testimonials
   - Marketing campaigns

3. **Check auth before posting**
   - Avoid failed posts
   - Better user experience

4. **Review screenshots**
   - Verify post appearance
   - Audit trail for compliance

---

## 📚 Related Documentation

- [SKILL.md](skills/linkedin-auto-poster/SKILL.md) - Agent skill documentation
- [LINKEDIN_AUTOPOST_GUIDE.md](LINKEDIN_AUTOPOST_GUIDE.md) - Complete workflow guide
- [Personal AI Employee FTEs.md](Personal%20AI%20Employe%20FTEs.md) - Architecture blueprint

---

*Generated for AI Employee Hackathon 2026 - Silver/Gold Tier*
