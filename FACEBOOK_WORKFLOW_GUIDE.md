# Facebook Integration - Complete Workflow Guide

## Overview

Your AI Employee uses **Facebook Graph API** to:
1. **Detect** new comments, messages, and engagement
2. **Create** action files for Claude Code to process
3. **Post** to Facebook (with human approval)
4. **Monitor** Page insights

---

## Configuration Files

### 1. Facebook Credentials

You've added credentials to `facebook/.env`. The system reads from **TWO** locations:

**Primary:** Root `.env` file
```bash
FACEBOOK_APP_ID=1119283080300264
FACEBOOK_APP_SECRET=933d8bbbb82c1d91cf69f26b06b22be5
FACEBOOK_PAGE_ACCESS_TOKEN=EAA...
FACEBOOK_PAGE_ID=164209393453546
FACEBOOK_ACCESS_TOKEN=EAAP5ZB2...
```

**Alternative:** `facebook/.env` (if you want separate Facebook config)
```bash
# Create this file if needed
FACEBOOK_PAGE_ACCESS_TOKEN=EAA...
FACEBOOK_PAGE_ID=164209393453546
```

---

## Part 1: How Facebook Watcher Detects Comments

### Architecture

```
Facebook Graph API
       ↓
facebook_watcher.py (checks every 5 minutes)
       ↓
Detects: Comments, Messages, Engagement
       ↓
Creates .md file in /Needs_Action/
       ↓
Claude Code processes the file
       ↓
Suggests actions (reply, ignore, etc.)
```

### Step-by-Step Flow

#### Step 1: Watcher Polls Facebook API

Every 5 minutes (300 seconds), the watcher calls:

```python
# Get recent posts
GET /v18.0/{page-id}/posts?limit=5

# For each post, get comments
GET /v18.0/{post-id}/comments?fields=from,message,created_time&limit=10

# Get messages
GET /v18.0/{page-id}/conversations?fields=messages{from,message,created_time}
```

#### Step 2: Filter by Keywords

Comments/messages are filtered for important keywords:
```python
KEYWORDS = ['urgent', 'message', 'inquiry', 'question', 
            'order', 'buy', 'price', 'interested']
```

#### Step 3: Create Action File

When a new comment is detected, creates:
`/Needs_Action/FACEBOOK_fb_comment_12345.md`

```markdown
---
type: facebook_comment
from_source: Facebook
from_name: John Doe
subject: What are your prices?
received: 2026-03-08T21:00:00
priority: high
status: pending
notification_id: fb_comment_12345
---

# Facebook Comment

**Source:** Facebook Comments

**From:** John Doe

**Received:** 2026-03-08 21:00:00

---

## Content

What are your prices for the AI Employee package?

---

## Suggested Actions

- [ ] Review comment
- [ ] Respond to customer inquiry
- [ ] Mark as processed
```

#### Step 4: Claude Code Processes

The Orchestrator triggers Claude Code to:
1. Read the action file
2. Understand the inquiry
3. Create a response plan
4. Suggest reply (requires approval)

---

## Part 2: How Auto-Posting Works

### Architecture

```
User/Claude Code
       ↓
Creates post content
       ↓
social_mcp.py → facebook_post()
       ↓
Creates approval file in /Pending_Approval/
       ↓
Human reviews and moves to /Approved/
       ↓
MCP executes post via Graph API
       ↓
Post published to Facebook Page
```

### Step-by-Step Flow

#### Step 1: Create Post Request

**Via Claude Code:**
```bash
/mcp call social-mcp facebook_post {
  "content": "Excited to announce our Gold Tier AI Employee! 
              Features include Facebook integration, Odoo ERP, 
              and automated CEO briefings. #AI #Automation"
}
```

#### Step 2: MCP Creates Approval File

Creates: `/Pending_Approval/SOCIAL_FACEBOOK_POST_20260308_210000.md`

```markdown
---
type: approval_request
action: social_media_post
platform: facebook
post_action: post
created: 2026-03-08T21:00:00
status: pending
privacy: EVERYONE
---

# Social Media Post Approval Request

**Platform:** Facebook

**Action:** Post

---

## Post Content

Excited to announce our Gold Tier AI Employee!
Features include Facebook integration, Odoo ERP, 
and automated CEO briefings. #AI #Automation

---

## To Approve
Move this file to /Approved folder.

## To Reject
Move this file to /Rejected folder.
```

#### Step 3: Human Approval

**You review and:**
- Move to `/Approved/` → Post will be published
- Move to `/Rejected/` → Post is cancelled

#### Step 4: MCP Executes Post

When file is in `/Approved/`, the Orchestrator calls:

```python
# Post to Facebook
POST /v18.0/{page-id}/feed
{
  "message": "Excited to announce our Gold Tier AI Employee!...",
  "access_token": "EAA..."
}

# Returns post_id
{
  "id": "164209393453546_1234567890"
}
```

#### Step 5: Log and Move to Done

- Logs action to `/Logs/social_2026-03-08.md`
- Moves approval file to `/Done/`

---

## Running the Facebook Integration

### Option 1: Run Facebook Watcher Only

```bash
cd "D:\hackathons-Q-4\hackathon 0 new-2\AI_Employee_Vault"
python scripts/watchers/facebook_watcher.py .
```

**What happens:**
- Connects to Facebook Graph API
- Checks for new comments/messages every 5 minutes
- Creates action files in `/Needs_Action/`
- Runs continuously until you press Ctrl+C

### Option 2: Run Full Orchestrator (Recommended)

```bash
python scripts/orchestrator.py . 30
```

**What happens:**
- Runs Facebook Watcher in background
- Monitors all folders
- Processes approved posts
- Updates Dashboard
- Generates CEO briefings (on Mondays)

### Option 3: Run as Background Service (Windows)

Create `start_facebook_watcher.bat`:

```batch
@echo off
cd /d "D:\hackathons-Q-4\hackathon 0 new-2\AI_Employee_Vault"
python scripts/watchers/facebook_watcher.py .
pause
```

Double-click to start, or use Task Scheduler for auto-start.

---

## Testing Your Setup

### Test 1: Check Facebook Connection

```bash
# Test via command line
curl "https://graph.facebook.com/v18.0/164209393453546?access_token=YOUR_PAGE_TOKEN"
```

**Expected response:**
```json
{
  "id": "164209393453546",
  "name": "Your Page Name"
}
```

### Test 2: Run Facebook Watcher (Dry Run)

```bash
python scripts/watchers/facebook_watcher.py . --interval 60
```

Watch for output:
```
============================================================
Starting FacebookWatcher
============================================================
Vault path: D:\hackathons-Q-4\hackathon 0 new-2\AI_Employee_Vault
Check interval: 60s
Keywords to filter: ['urgent', 'message', 'inquiry', ...]
============================================================
Facebook Watcher is now running...
Press Ctrl+C to stop
============================================================
```

### Test 3: Post to Facebook (Test Post)

**Step 1:** Create post via MCP
```bash
python scripts/mcp/social_mcp.py
```

**Step 2:** In another terminal, call MCP:
```bash
# Use the MCP client
python .qwen/skills/browsing-with-playwright/scripts/mcp-client.py call \
  -u http://localhost:8811 \
  -t facebook_post \
  -p '{"content": "Test post from AI Employee!"}'
```

**Step 3:** Check `/Pending_Approval/` for approval file

**Step 4:** Move to `/Approved/` to publish

---

## Monitoring Facebook Activity

### View Recent Comments Detected

```bash
# List all Facebook action files
dir Needs_Action\FACEBOOK_*.md
```

### View Posted Content

```bash
# List all social media logs
dir Logs\social_*.md

# View today's log
type Logs\social_2026-03-08.md
```

### View Scheduled Posts

```bash
# List scheduled posts
dir Social\SCHEDULED_*.md
```

---

## Common Workflows

### Workflow 1: Respond to Customer Comment

1. **Comment arrives** on Facebook post
2. **Watcher detects** it (within 5 minutes)
3. **Creates file:** `Needs_Action/FACEBOOK_fb_comment_12345.md`
4. **Claude Code reads** the comment
5. **Creates plan:** Plan_reply_comment_12345.md
6. **Suggests reply:** "Thank you for your inquiry..."
7. **Creates approval:** Pending_Approval/FACEBOOK_REPLY_12345.md
8. **You approve:** Move to /Approved/
9. **MCP posts reply** to Facebook
10. **File moved to:** Done/

### Workflow 2: Auto-Post Business Update

1. **You tell Claude:** "Post about our new service"
2. **Claude creates:** Plan_social_post_20260308.md
3. **Calls MCP:** facebook_post with content
4. **Creates approval:** Pending_Approval/SOCIAL_FACEBOOK_POST_*.md
5. **You review** the post content
6. **You approve:** Move to /Approved/
7. **MCP publishes** to Facebook
8. **Logs result:** Logs/social_2026-03-08.md

### Workflow 3: Monitor for Urgent Messages

1. **Watcher runs** every 5 minutes
2. **Filters messages** for keywords: "urgent", "asap", "help"
3. **High priority** messages create action files immediately
4. **Claude processes** and alerts you
5. **You respond** via approved reply workflow

---

## Configuration Options

### Change Check Interval

Edit `facebook_watcher.py` or pass as argument:

```bash
# Check every 2 minutes (120 seconds)
python scripts/watchers/facebook_watcher.py . --interval 120

# Check every minute
python scripts/watchers/facebook_watcher.py . --interval 60
```

### Add Custom Keywords

```bash
# Monitor for specific keywords
python scripts/watchers/facebook_watcher.py . \
  --keywords "urgent,invoice,payment,buy,price,demo"
```

Or edit in `facebook_watcher.py`:
```python
DEFAULT_KEYWORDS = ['urgent', 'message', 'inquiry', 
                    'question', 'order', 'buy', 'price', 
                    'interested', 'demo', 'pricing']
```

---

## Troubleshooting

### Issue: "Page Access Token not configured"

**Solution:**
```bash
# Check .env file has correct token
cat .env | grep FACEBOOK_PAGE_ACCESS_TOKEN

# Token should start with EAA...
# Make sure no spaces or quotes
```

### Issue: "Invalid OAuth access token"

**Solution:**
1. Token expired → Get new long-lived token
2. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
3. Generate new Page Access Token
4. Update `.env` file

### Issue: No comments detected

**Solution:**
```bash
# Check if Page has comments
curl "https://graph.facebook.com/v18.0/164209393453546/posts?access_token=YOUR_TOKEN"

# Check watcher logs
python scripts/watchers/facebook_watcher.py . --interval 30
```

### Issue: Post not publishing

**Solution:**
1. Check approval file is in `/Approved/` (not `/Pending_Approval/`)
2. Check token has `pages_manage_posts` permission
3. Check logs: `type Logs\social_2026-03-08.md`

---

## API Endpoints Used

### Reading Data

| Endpoint | Purpose |
|----------|---------|
| `GET /{page-id}/posts` | Get Page posts |
| `GET /{post-id}/comments` | Get post comments |
| `GET /{page-id}/conversations` | Get messages |
| `GET /{page-id}/insights` | Get analytics |

### Posting Data

| Endpoint | Purpose |
|----------|---------|
| `POST /{page-id}/feed` | Create post |
| `POST /{page-id}/photos` | Post photo |
| `POST /{comment-id}/comments` | Reply to comment |

---

## Security Best Practices

1. **Never commit .env** - Already in .gitignore ✅
2. **Use long-lived tokens** - 60 days validity ✅
3. **Rotate tokens monthly** - Reset in Facebook Developers
4. **Limit permissions** - Only request what you need
5. **Monitor API usage** - Check Graph API Explorer

---

## Quick Reference Commands

```bash
# Start Facebook Watcher
python scripts/watchers/facebook_watcher.py .

# Start with custom interval
python scripts/watchers/facebook_watcher.py . --interval 60

# Start with custom keywords
python scripts/watchers/facebook_watcher.py . --keywords "urgent,invoice"

# Test Facebook connection
curl "https://graph.facebook.com/v18.0/164209393453546?access_token=YOUR_TOKEN"

# Start Social MCP Server
python scripts/mcp/social_mcp.py

# Start full Orchestrator
python scripts/orchestrator.py . 30

# Verify Gold Tier
python scripts/verify_gold.py .
```

---

## Next Steps

1. **Start Facebook Watcher:**
   ```bash
   python scripts/watchers/facebook_watcher.py .
   ```

2. **Post a test message** on your Facebook Page

3. **Watch for action file** in `/Needs_Action/`

4. **Review and respond** via Claude Code

---

**Need Help?** 
- [Facebook Graph API Docs](https://developers.facebook.com/docs/graph-api)
- [FACEBOOK_SETUP.md](./FACEBOOK_SETUP.md) - Detailed setup guide
- [ENV_SETUP_GUIDE.md](./ENV_SETUP_GUIDE.md) - Environment configuration
