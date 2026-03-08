# Gmail Watcher - Quick Start Guide

## Overview

The Gmail Watcher monitors your Gmail inbox for important emails and creates action files in the `/Needs_Action` folder for Qwen Code to process.

**Uses:** Your existing `credentials.json` (Gmail API OAuth)

---

## Step 1: Install Dependencies

```bash
pip install google-auth google-auth-oauthlib google-api-python-client
```

---

## Step 2: First-Time Authentication

Run the authentication command:

```bash
python scripts/watchers/gmail_watcher.py . --authenticate
```

**What happens:**
1. Browser opens automatically
2. Google login page appears
3. Grant Gmail API permissions
4. `token.json` is created automatically
5. Authentication complete!

---

## Step 3: Start Gmail Watcher

```bash
python scripts/watchers/gmail_watcher.py .
```

**Optional settings:**

```bash
# Check every 60 seconds instead of 120
python scripts/watchers/gmail_watcher.py . --interval 60

# Custom keywords
python scripts/watchers/gmail_watcher.py . --keywords "urgent,invoice,payment,client"

# Both options
python scripts/watchers/gmail_watcher.py . --interval 60 --keywords "urgent,invoice"
```

---

## How It Works

1. **Connects to Gmail API** using your `credentials.json`
2. **Checks every 2 minutes** (by default) for:
   - Unread emails
   - Emails containing your keywords (urgent, invoice, payment, etc.)
3. **Creates action files** in `/Needs_Action/` for each new email
4. **Remembers processed emails** - won't create duplicate action files

---

## Action File Format

Each email creates a file like: `Needs_Action/EMAIL_abc123.md`

```markdown
---
type: email
from: client@example.com
subject: Urgent: Invoice Request
received: 2026-03-01T17:00:00
priority: high
status: pending
---

# Email Received

**From:** client@example.com
**Subject:** Urgent: Invoice Request

---

## Preview

Hi, can you send me the invoice for...

---

## Suggested Actions

- [ ] Read full email in Gmail
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
```

---

## Files Created

| File | Purpose |
|------|---------|
| `token.json` | OAuth token (auto-created, keep private) |
| `.gmail_cache.json` | Processed email cache (prevents duplicates) |
| `Needs_Action/EMAIL_*.md` | Action files for new emails |

---

## Troubleshooting

### "Credentials file not found"
```bash
# Make sure credentials.json is in vault root
dir credentials.json

# Or specify path
python scripts/watchers/gmail_watcher.py . --credentials path/to/credentials.json
```

### "Google libraries not installed"
```bash
pip install google-auth google-auth-oauthlib google-api-python-client
```

### "Token expired"
```bash
# Just re-authenticate
python scripts/watchers/gmail_watcher.py . --authenticate
```

### "No emails detected"
- Check if emails match your keywords
- Try with broader keywords: `--keywords "test"`
- Verify Gmail API is enabled in Google Cloud Console

---

## Security Notes

- ✅ `credentials.json` - Safe to keep (OAuth client info)
- 🔒 `token.json` - **NEVER share** (your access token)
- 🔒 `.gmail_cache.json` - Local cache only
- ✅ Add to `.gitignore`:
  ```
  token.json
  .gmail_cache.json
  ```

---

## Example Output

```
2026-03-01 17:00:00 - GmailWatcher - INFO - ============================================================
2026-03-01 17:00:00 - GmailWatcher - INFO - Starting GmailWatcher
2026-03-01 17:00:00 - GmailWatcher - INFO - ============================================================
2026-03-01 17:00:00 - GmailWatcher - INFO - Credentials file: D:\vault\credentials.json
2026-03-01 17:00:00 - GmailWatcher - INFO - Loaded existing OAuth token
2026-03-01 17:00:01 - GmailWatcher - INFO - Successfully authenticated with Gmail API
2026-03-01 17:00:01 - GmailWatcher - INFO - ============================================================
2026-03-01 17:00:01 - GmailWatcher - INFO - Gmail Watcher is now running...
2026-03-01 17:00:01 - GmailWatcher - INFO - Press Ctrl+C to stop
2026-03-01 17:00:01 - GmailWatcher - INFO - ============================================================
2026-03-01 17:02:15 - GmailWatcher - INFO - Found 2 new emails
2026-03-01 17:02:15 - GmailWatcher - INFO - Created action file: EMAIL_abc123.md
2026-03-01 17:02:15 - GmailWatcher - INFO - Created action file: EMAIL_def456.md
```

---

## Integration with Qwen Code

After Gmail Watcher creates action files, prompt Qwen Code:

```
Check /Needs_Action for new email files. Read the Company_Handbook.md 
for response rules. Create a plan to process each email and draft 
appropriate responses.
```

---

*For more details, see: .qwen/skills/gmail-watcher/SKILL.md*
