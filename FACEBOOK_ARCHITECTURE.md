# Facebook Integration - Visual Architecture

## Complete System Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FACEBOOK GRAPH API                              │
│  (Comments, Messages, Posts, Insights)                                  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ HTTPS Requests
                                 │ (Every 5 minutes)
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      facebook_watcher.py                                │
│                                                                         │
│  1. Polls Graph API:                                                    │
│     - GET /{page-id}/posts                                              │
│     - GET /{post-id}/comments                                           │
│     - GET /{page-id}/conversations                                      │
│                                                                         │
│  2. Filters by keywords:                                                │
│     ['urgent', 'message', 'inquiry', 'buy', 'price']                    │
│                                                                         │
│  3. Tracks processed IDs (avoids duplicates)                            │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 │ New comment/message detected
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    /Needs_Action/ Folder                                │
│                                                                         │
│  Creates: FACEBOOK_fb_comment_12345.md                                  │
│                                                                         │
│  ```markdown                                                            │
│  ---                                                                    │
│  type: facebook_comment                                                 │
│  from: John Doe                                                         │
│  subject: What are your prices?                                         │
│  priority: high                                                         │
│  ---                                                                    │
│                                                                         │
│  # Facebook Comment                                                     │
│  **From:** John Doe                                                     │
│  **Content:** What are your prices?                                     │
│                                                                         │
│  ## Suggested Actions                                                   │
│  - [ ] Respond to customer inquiry                                      │
│  ```                                                                    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 │ Orchestrator detects new file
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLAUDE CODE                                     │
│                                                                         │
│  Reads the action file and:                                             │
│  1. Analyzes the comment                                                │
│  2. Creates plan: Plans/Plan_reply_12345.md                             │
│  3. Drafts response: "Thank you for your inquiry..."                    │
│  4. Creates approval request                                            │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 │ Creates approval file
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   /Pending_Approval/ Folder                             │
│                                                                         │
│  Creates: FACEBOOK_REPLY_20260308_210000.md                             │
│                                                                         │
│  ```markdown                                                            │
│  ---                                                                    │
│  type: approval_request                                                 │
│  action: facebook_reply_comment                                         │
│  comment_id: 12345                                                      │
│  message: Thank you for your inquiry! Our pricing...                    │
│  ---                                                                    │
│                                                                         │
│  ## To Approve                                                          │
│  Move this file to /Approved folder.                                    │
│  ```                                                                    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 │ Human reviews and moves to /Approved/
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      /Approved/ Folder                                  │
│                                                                         │
│  Orchestrator detects approved file and triggers:                       │
│  social_mcp.py → execute_facebook_reply()                               │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 │ Calls Facebook Graph API
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      FACEBOOK GRAPH API (POST)                          │
│                                                                         │
│  POST /v18.0/{comment-id}/comments                                      │
│  {                                                                      │
│    "message": "Thank you for your inquiry!...",                         │
│    "access_token": "EAA..."                                             │
│  }                                                                      │
│                                                                         │
│  Response: { "id": "12345_67890" }                                      │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 │ Success!
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Logging & Cleanup                               │
│                                                                         │
│  1. Log action: Logs/social_2026-03-08.md                               │
│     [2026-03-08 21:05:00] [SUCCESS] facebook_reply_comment: {...}       │
│                                                                         │
│  2. Move file to: Done/FACEBOOK_REPLY_20260308_210000.md                │
│                                                                         │
│  3. Update Dashboard.md                                                 │
│     - Increment tasks completed                                         │
│     - Add to recent activity                                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Auto-Posting Flow (Creating New Posts)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER / CLAUDE CODE                              │
│                                                                         │
│  User request: "Post about our new service"                             │
│                                                                         │
│  Claude creates plan and calls MCP:                                     │
│  /mcp call social-mcp facebook_post {                                   │
│    "content": "Excited to announce..."                                  │
│  }                                                                      │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      social_mcp.py                                      │
│                                                                         │
│  facebook_post() function:                                              │
│  1. Validates content                                                   │
│  2. Creates HITL approval file (safety first!)                          │
│  3. Returns: { "status": "pending_approval", ... }                      │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   /Pending_Approval/ Folder                             │
│                                                                         │
│  Creates: SOCIAL_FACEBOOK_POST_20260308_210000.md                       │
│                                                                         │
│  Content includes:                                                      │
│  - Post text                                                            │
│  - Privacy setting                                                      │
│  - Approval instructions                                                │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 │ Human reviews content
                                 │ Moves to /Approved/
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      /Approved/ Folder                                  │
│                                                                         │
│  Orchestrator detects and calls:                                        │
│  social_mcp.py → execute_facebook_post()                                │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 │ POST to Graph API
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      FACEBOOK GRAPH API                                 │
│                                                                         │
│  POST /v18.0/{page-id}/feed                                             │
│  {                                                                      │
│    "message": "Excited to announce...",                                 │
│    "access_token": "EAA..."                                             │
│  }                                                                      │
│                                                                         │
│  Returns: { "id": "164209393453546_1234567890" }                        │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SUCCESS!                                        │
│                                                                         │
│  Post published to: https://facebook.com/164209393453546                │
│                                                                         │
│  Logged to: Logs/social_2026-03-08.md                                   │
│  File moved to: Done/                                                   │
│  Dashboard updated                                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Facebook   │────▶│   Watcher    │────▶│ Needs_Action │
│  Graph API   │     │  (Python)    │     │   Folder     │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                    │
                            │                    │
                            ▼                    ▼
                     ┌──────────────┐     ┌──────────────┐
                     │  social_mcp  │◀────│  Claude Code │
                     │    (MCP)     │     │  (Reasoning) │
                     └──────────────┘     └──────────────┘
                            │                    │
                            │                    │
                            ▼                    ▼
                     ┌──────────────┐     ┌──────────────┐
                     │Pending_Appro │◀────│  Plan Files  │
                     │    val       │     │              │
                     └──────────────┘     └──────────────┘
                            │
                            │ (Human approves)
                            ▼
                     ┌──────────────┐
                     │   Approved   │
                     │    Folder    │
                     └──────────────┘
                            │
                            │ (Auto-executes)
                            ▼
                     ┌──────────────┐     ┌──────────────┐
                     │  Facebook    │     │     Logs     │
                     │   Posted!    │     │   Done/      │
                     └──────────────┘     └──────────────┘
```

---

## Folder Structure

```
AI_Employee_Vault/
│
├── .env                          # Facebook credentials
├── facebook/.env                 # Alternative Facebook config
│
├── scripts/
│   ├── watchers/
│   │   └── facebook_watcher.py   # Monitors Facebook API
│   └── mcp/
│       └── social_mcp.py         # Posts to Facebook
│
├── Needs_Action/                 # New comments/messages
│   ├── FACEBOOK_fb_comment_*.md
│   └── FACEBOOK_fb_message_*.md
│
├── Plans/                        # Claude's response plans
│   └── Plan_reply_comment_*.md
│
├── Pending_Approval/             # Awaiting human approval
│   ├── SOCIAL_FACEBOOK_POST_*.md
│   └── FACEBOOK_REPLY_*.md
│
├── Approved/                     # Ready to execute
│   └── (files moved here trigger execution)
│
├── Done/                         # Completed actions
│   ├── FACEBOOK_REPLY_*.md
│   └── SOCIAL_FACEBOOK_POST_*.md
│
├── Logs/                         # Activity logs
│   └── social_2026-03-08.md
│
└── Social/                       # Scheduled posts
    └── SCHEDULED_*.md
```

---

## Timeline Example

```
09:00:00  Facebook Watcher starts
09:00:05  First API poll (no new comments)
09:05:00  Second API poll
09:05:03  📢 NEW COMMENT detected!
          - From: John Doe
          - "What are your prices?"
09:05:04  Creates: Needs_Action/FACEBOOK_fb_comment_78901.md
09:05:05  Orchestrator detects new file
09:05:10  Claude Code reads and analyzes
09:05:15  Creates: Plans/Plan_reply_78901.md
09:05:20  Creates: Pending_Approval/FACEBOOK_REPLY_090520.md
          "Thank you for your inquiry! Our pricing starts at..."
09:10:00  👤 Human reviews approval file
09:10:05  👤 Moves file to /Approved/
09:10:06  Orchestrator detects approved file
09:10:10  social_mcp.py executes reply
09:10:12  ✅ Reply posted to Facebook
09:10:13  Logs action to Logs/social_2026-03-08.md
09:10:14  Moves file to Done/
09:10:15  Updates Dashboard.md
09:15:00  Next API poll (continues monitoring)
```

---

## Permissions Required

### Facebook Page Access Token Permissions

| Permission | Purpose |
|------------|---------|
| `pages_read_engagement` | Read comments, likes, shares |
| `pages_read_user_content` | Read messages, conversations |
| `pages_manage_posts` | Create posts |
| `pages_manage_engagement` | Reply to comments |
| `instagram_basic` | Basic Instagram data |
| `instagram_content_publish` | Post to Instagram |

### How to Get Permissions

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app
3. Click **Get Token** → **Get Page Access Token**
4. Check all required permissions
5. Click **Generate**
6. Copy token to `.env`

---

## API Rate Limits

```
┌─────────────────────────────────────────┐
│  Facebook Graph API Rate Limits         │
├─────────────────────────────────────────┤
│  Page-level: 200 calls/hour/page        │
│  User-level: 200 calls/hour/user        │
│                                         │
│  Our watcher: 12 calls/hour             │
│  (every 5 minutes = 12 per hour)        │
│                                         │
│  ✅ Well within limits!                 │
└─────────────────────────────────────────┘
```

---

## Quick Start Commands

```bash
# 1. Start Facebook Watcher
python scripts/watchers/facebook_watcher.py .

# 2. Post to Facebook (via MCP)
python scripts/mcp/social_mcp.py

# 3. Run full system
python scripts/orchestrator.py . 30

# 4. Check what's in Needs_Action
dir Needs_Action\FACEBOOK_*.md

# 5. View logs
type Logs\social_2026-03-08.md
```

---

**For detailed instructions, see:**
- [`FACEBOOK_WORKFLOW_GUIDE.md`](./FACEBOOK_WORKFLOW_GUIDE.md) - Complete workflow guide
- [`FACEBOOK_SETUP.md`](./FACEBOOK_SETUP.md) - Setup instructions
- [`ENV_SETUP_GUIDE.md`](./ENV_SETUP_GUIDE.md) - Environment configuration
