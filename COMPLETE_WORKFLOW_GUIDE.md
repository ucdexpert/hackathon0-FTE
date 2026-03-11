# AI Employee - Complete Workflow Guide

## 🎯 Real-World Example: Customer Inquiry to Invoice

This guide shows how your AI Employee handles a complete business workflow:

1. **Customer comments** on Facebook post
2. **AI detects** the comment
3. **AI responds** to customer
4. **AI creates** invoice in Odoo
5. **AI tracks** payment
6. **AI reports** in CEO Briefing

---

## Scenario: Customer Wants to Buy Your Service

### Step 1: Customer Sees Facebook Post

**Your Post:** (Already published)
```
Excited to share our AI Employee Gold Tier! 🤖 
Automated Facebook posting with Graph API integration. 
#AI #Automation #Tech
```

**Customer (John Doe) comments:**
```
Hi! I'm interested in your AI Employee service. What are your prices? 
This looks urgent for my business!
```

---

### Step 2: Facebook Watcher Detects Comment

**Time:** 09:00 AM - Customer comments  
**Time:** 09:05 AM - Facebook Watcher checks API

**What happens:**
```
Facebook Graph API
    ↓
facebook_watcher.py polls every 5 minutes
    ↓
Detects comment with keywords: "interested", "prices", "urgent"
    ↓
Creates action file
```

**File Created:** `Needs_Action/FACEBOOK_fb_comment_12345.md`

```markdown
---
type: facebook_comment
from_source: Facebook
from_name: John Doe
subject: Hi! I'm interested in your AI Employee service...
received: 2026-03-10T09:05:00
priority: high
status: pending
notification_id: fb_comment_12345
---

# Facebook Comment

**From:** John Doe

**Content:**

Hi! I'm interested in your AI Employee service. What are your prices? 
This looks urgent for my business!

---

## Suggested Actions

- [ ] Review comment
- [ ] Respond to customer inquiry
- [ ] Create invoice in Odoo
- [ ] Mark as processed
```

---

### Step 3: Claude Code Processes the Comment

**Orchestrator detects** new file in `Needs_Action/`

**Claude Code reads** the comment and:
1. Understands: Customer wants pricing information
2. Identifies: This is a sales lead (keyword: "interested")
3. Priority: HIGH (keyword: "urgent")
4. Action needed: Reply with pricing + create invoice

**Claude creates plan:** `Plans/Plan_reply_john_doe_12345.md`

```markdown
# Plan: Respond to John Doe

## Understanding
- Customer is interested in AI Employee service
- Asking for pricing
- Marked as urgent

## Steps
1. [ ] Prepare pricing information
2. [ ] Create friendly response
3. [ ] Create approval file for reply
4. [ ] After approval, post reply
5. [ ] Create customer in Odoo
6. [ ] Create invoice for AI Employee service
```

---

### Step 4: AI Creates Reply (With Approval)

**Claude drafts response:**
```
Hi John! Thanks for your interest in AI Employee Gold Tier! 

Our pricing:
- Gold Tier Setup: $500 (one-time)
- Monthly Support: $100/month

This includes:
✅ Facebook Integration
✅ Odoo ERP Integration  
✅ Auto-posting & Monitoring
✅ Weekly CEO Briefings

I'll send you an invoice. When would you like to start?

Best regards,
AI Employee Team
```

**Creates approval file:** `Pending_Approval/FACEBOOK_REPLY_12345.md`

```markdown
---
type: approval_request
action: facebook_reply_comment
comment_id: 12345
message: Hi John! Thanks for your interest...
created: 2026-03-10T09:06:00
status: pending
---

# Facebook Reply Approval Request

**To:** John Doe

**Message:**

Hi John! Thanks for your interest in AI Employee Gold Tier! 

Our pricing:
- Gold Tier Setup: $500 (one-time)
- Monthly Support: $100/month
...

---

## To Approve
Move this file to /Approved folder.
```

---

### Step 5: Human Approves Reply

**You review** the response and:
1. Move file from `Pending_Approval/` → `Approved/`
2. Orchestrator detects the approval
3. Social MCP executes the reply

**MCP calls Facebook API:**
```python
POST /v18.0/12345/comments
{
  "message": "Hi John! Thanks for your interest...",
  "access_token": "EAA..."
}
```

**Result:** Reply posted to Facebook!

---

### Step 6: AI Creates Customer in Odoo

**Claude Code creates** customer in Odoo via MCP:

```python
# Call Odoo MCP Server
/mcp call odoo-mcp create_customer {
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1-555-0123",
  "city": "New York"
}
```

**Odoo creates customer:**
- Customer ID: 42
- Name: John Doe
- Email: john@example.com

---

### Step 7: AI Creates Invoice in Odoo

**Claude creates invoice** via Odoo MCP:

```python
# Create invoice
/mcp call odoo-mcp create_invoice {
  "partner_id": 42,
  "invoice_type": "out_invoice",
  "lines": [
    {
      "product_id": 1,
      "name": "AI Employee Gold Tier Setup",
      "quantity": 1,
      "price_unit": 500
    },
    {
      "product_id": 2,
      "name": "Monthly Support (March)",
      "quantity": 1,
      "price_unit": 100
    }
  ],
  "narrative": "AI Employee Gold Tier - John Doe"
}
```

**Odoo creates invoice:**
- Invoice ID: INV/2026/0001
- Total: $600
- Status: Posted
- Payment Terms: 30 days

---

### Step 8: AI Sends Invoice via Email

**Creates approval file:** `Pending_Approval/EMAIL_SEND_Invoice_John_Doe.md`

```markdown
---
type: approval_request
action: send_email
to: john@example.com
subject: Invoice INV/2026/0001 - AI Employee Gold Tier
amount: 600.00
---

# Email Approval Request

**To:** john@example.com

**Subject:** Invoice INV/2026/0001 - AI Employee Gold Tier

**Body:**

Dear John,

Thank you for choosing AI Employee Gold Tier!

Please find attached your invoice:
- Invoice #: INV/2026/0001
- Amount: $600.00
- Due Date: April 9, 2026

We're excited to work with you!

Best regards,
AI Employee Team

---

## To Approve
Move to /Approved folder.
```

**You approve** → Email sent with invoice PDF!

---

### Step 9: Customer Pays Invoice

**Time:** March 15, 2026  
**Action:** John pays $600 via bank transfer

**You record payment in Odoo:**
1. Open Odoo → Invoicing → Invoices
2. Find INV/2026/0001
3. Click "Register Payment"
4. Amount: $600
5. Status: Paid ✅

---

### Step 10: Facebook Watcher Continues Monitoring

Meanwhile, Facebook Watcher:
- ✅ Still monitoring every 5 minutes
- ✅ Detecting new comments
- ✅ Creating action files
- ✅ AI processing inquiries

---

### Step 11: Monday Morning - CEO Briefing Generated

**Time:** Monday, March 17, 2026 at 7:00 AM

**Orchestrator triggers:** CEO Briefing Generator

**Briefing created:** `Briefings/20260317_Week_12_Briefing.md`

```markdown
---
generated: 2026-03-17T07:00:00
period: 2026-03-10 to 2026-03-16
status: on_track
---

# Monday Morning CEO Briefing

## Executive Summary

Great week! New customer acquired via Facebook. Revenue on track.

## Revenue Report

| Metric | Value | Target | Progress |
|--------|-------|--------|----------|
| This Week | $600.00 | - | - |
| MTD | $600.00 | $10,000 | 6.0% |
| Invoices Sent | 1 | - | - |
| Pending Payment | 0 | - | - |

## Completed Tasks

- [x] Responded to John Doe inquiry (Facebook)
- [x] Created customer in Odoo
- [x] Generated and sent invoice
- [x] Payment received

## Social Media Performance

| Platform | Posts | Engagement |
|----------|-------|------------|
| Facebook | 1 | 1 comment, 1 lead |
| Instagram | 0 | - |

## Proactive Suggestions

- 🟢 Follow up with John for testimonial
- 🟡 Post more frequently on Facebook
- 🟢 Consider Instagram for more reach

## Action Items

1. Post customer success story
2. Create testimonial request for John
3. Schedule social media posts for next week
```

---

## 📊 Complete System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CUSTOMER JOURNEY                         │
└─────────────────────────────────────────────────────────────┘

Facebook Post Published
         ↓
Customer Comments "Interested, what's price?"
         ↓
Facebook Watcher Detects (5 min)
         ↓
Creates: Needs_Action/FACEBOOK_fb_comment_*.md
         ↓
Claude Code Reads & Analyzes
         ↓
Creates Plan: Plans/Plan_reply_*.md
         ↓
Creates Approval: Pending_Approval/FACEBOOK_REPLY_*.md
         ↓
Human Approves (Move to /Approved/)
         ↓
Social MCP Posts Reply to Facebook
         ↓
Odoo MCP Creates Customer
         ↓
Odoo MCP Creates Invoice
         ↓
Email MCP Sends Invoice (After Approval)
         ↓
Customer Pays
         ↓
Payment Recorded in Odoo
         ↓
Monday: CEO Briefing Generated
         ↓
Dashboard Updated
         ↓
Task Moved to Done/
```

---

## 🎯 Your Daily Workflow

### Morning (9:00 AM)

1. **Check Dashboard.md**
   ```bash
   type Dashboard.md
   ```
   
2. **Review Pending Approvals**
   ```bash
   dir Pending_Approval
   ```

3. **Approve files** (move to `/Approved/`)

### During Day

- Facebook Watcher monitors automatically
- New comments → Action files created
- Claude processes and suggests responses
- You approve → AI executes

### Evening (5:00 PM)

1. **Check what was completed**
   ```bash
   dir Done
   ```

2. **Review logs**
   ```bash
   type Logs\social_2026-03-10.md
   ```

3. **Plan tomorrow's posts**

---

## 📁 Folder Workflow

```
Inbox/
  ↓ (New items arrive here)
Needs_Action/
  ↓ (AI processes)
Plans/
  ↓ (Creates approval)
Pending_Approval/
  ↓ (You approve)
Approved/
  ↓ (AI executes)
Done/
```

---

## 🔧 Commands You'll Use Daily

### Facebook Posting:
```bash
# Quick post
python auto_post_facebook.py "Your message"

# Check status
python test_facebook.py
```

### Odoo Operations:
```bash
# Check Odoo status
docker compose -f odoo/docker-compose.yml ps

# Test Odoo connection
python scripts/mcp/odoo_mcp.py --authenticate
```

### System Management:
```bash
# Start all watchers
python scripts/orchestrator.py . 30

# Check what's pending
dir Pending_Approval

# View completed tasks
dir Done
```

---

## ✅ What Happens Automatically

| Task | Frequency | Status |
|------|-----------|--------|
| Facebook Monitoring | Every 5 min | ✅ Auto |
| Comment Detection | Real-time (5 min delay) | ✅ Auto |
| Action File Creation | On new comment | ✅ Auto |
| Dashboard Updates | Every 30 sec | ✅ Auto |
| Log Writing | Every action | ✅ Auto |
| CEO Briefing | Mondays 7 AM | ✅ Auto |

---

## 🎯 What Requires Your Approval

| Action | Approval Needed | Why |
|--------|----------------|-----|
| Facebook Replies | ✅ Yes | Safety |
| Facebook Posts | ✅ Yes | Quality control |
| Email Sending | ✅ Yes | Prevent mistakes |
| Invoice Creation | ⚠️ Optional | Can be auto |
| Payment Recording | ✅ Yes | Financial control |

---

## 🚀 Next Level Automation

Once comfortable, you can:

1. **Auto-approve small invoices** (< $100)
2. **Auto-reply to common questions**
3. **Schedule posts in advance**
4. **Auto-generate invoices from comments**
5. **Connect more platforms** (WhatsApp, LinkedIn)

---

## 📞 Support & Resources

- **Facebook Guide:** `FACEBOOK_WORKFLOW_GUIDE.md`
- **Odoo Setup:** `odoo/README.md`
- **MCP Servers:** `scripts/mcp/README.md`
- **Architecture:** `FACEBOOK_ARCHITECTURE.md`

---

**Your AI Employee is now fully operational!** 🎉

Start by:
1. Posting to Facebook regularly
2. Responding to comments via approval workflow
3. Creating customers and invoices in Odoo
4. Reviewing Monday CEO briefings

The system will handle the rest automatically! 🤖
