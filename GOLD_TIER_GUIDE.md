# Gold Tier Implementation Guide

## AI Employee - Gold Tier: Autonomous Employee

**Tagline:** *Full business automation with accounting, social media, and executive reporting.*

---

## Table of Contents

1. [Overview](#overview)
2. [Gold Tier Features](#gold-tier-features)
3. [Prerequisites](#prerequisites)
4. [Quick Start](#quick-start)
5. [Odoo Setup](#odoo-setup)
6. [Facebook Integration](#facebook-integration)
7. [Instagram Integration](#instagram-integration)
8. [CEO Briefing](#ceo-briefing)
9. [Architecture](#architecture)
10. [Verification](#verification)
11. [Troubleshooting](#troubleshooting)

---

## Overview

Gold Tier transforms your AI Employee from a functional assistant into a **fully autonomous business partner**. It includes:

- **Odoo ERP Integration** - Self-hosted accounting and invoicing
- **Facebook Monitoring & Posting** - Track notifications and engage with customers
- **Instagram Integration** - Post and monitor Instagram business account
- **Weekly CEO Briefings** - Automated executive reports with revenue analysis
- **Multi-MCP Server Architecture** - Specialized servers for different domains
- **Comprehensive Audit Logging** - Full traceability of all AI actions

---

## Gold Tier Features

### 1. Odoo Accounting Integration

**Self-hosted Odoo 19 Community Edition** via Docker Compose:

- Create and track invoices
- Manage customers and products
- Register payments (with HITL approval)
- Generate financial reports
- Track accounts receivable/payable

**Files:**
- `odoo/docker-compose.yml` - Odoo + PostgreSQL configuration
- `odoo/setup_odoo.py` - Odoo management script
- `scripts/mcp/odoo_mcp.py` - Odoo MCP server

### 2. Facebook Integration

**Monitor and post to Facebook:**

- Watch for important notifications
- Track messages with keyword filtering
- Post to timeline and business pages
- Schedule posts for later

**Files:**
- `scripts/watchers/facebook_watcher.py` - Facebook monitoring
- `scripts/mcp/social_mcp.py` - Social media MCP server

### 3. Instagram Integration

**Post and monitor Instagram:**

- Post images with captions and hashtags
- Auto-upload with Playwright automation
- Track engagement (requires Graph API for full insights)

**Files:**
- `scripts/mcp/social_mcp.py` - Instagram posting functions

### 4. Weekly CEO Briefing

**Automated executive reports every Monday morning:**

- Revenue summary from Odoo
- Tasks completed analysis
- Bottleneck identification
- Social media performance
- Proactive suggestions

**Files:**
- `scripts/ceo_briefing.py` - Briefing generator

### 5. Enhanced Orchestrator

**Gold Tier orchestrator includes:**

- Odoo revenue tracking
- Social media statistics
- Automatic briefing generation
- Enhanced dashboard with Gold metrics

---

## Prerequisites

### Hardware Requirements

- **RAM:** 16GB recommended (Odoo requires ~2GB)
- **CPU:** 8 cores recommended
- **Disk:** 50GB free space (Odoo + PostgreSQL + data)
- **OS:** Windows 10/11, macOS, or Linux

### Software Requirements

| Component | Version | Purpose |
|-----------|---------|---------|
| Docker Desktop | Latest | Odoo containerization |
| Python | 3.13+ | Core automation |
| Node.js | v24+ LTS | MCP servers |
| Claude Code | Active | Reasoning engine |
| Obsidian | v1.10.6+ | Dashboard |

### Required Python Packages

```bash
pip install -r requirements.txt
playwright install
```

---

## Quick Start

### Step 1: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Step 2: Start Odoo

```bash
# Navigate to odoo folder
cd odoo

# Start Odoo containers
python setup_odoo.py start

# Or use docker compose directly
docker compose up -d
```

**Wait 2-3 minutes** for Odoo to initialize.

### Step 3: Configure Odoo

1. Open http://localhost:8069
2. Create database:
   - Database name: `odoo`
   - Email: `admin`
   - Password: `admin`
3. Install modules:
   - **Invoicing** (required)
   - **Accounting** (recommended)
   - **Sales** (optional)

### Step 4: Create Test Data in Odoo

```python
# Create a test customer
- Go to Invoicing → Customers → Create
- Name: "Test Customer"
- Email: customer@example.com

# Create a test product
- Go to Invoicing → Products → Create
- Name: "Consulting Service"
- Price: $100

# Create a test invoice
- Go to Invoicing → Customers → Create Invoice
- Select customer and product
- Confirm and post
```

### Step 5: Configure Environment

Create `.env` file in vault root:

```bash
# Odoo Configuration
ODOO_HOST=localhost
ODOO_PORT=8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=admin
```

### Step 6: Start Orchestrator

```bash
# Start the Gold Tier orchestrator
python scripts/orchestrator.py . 30
```

### Step 7: Verify Gold Tier

```bash
# Run verification script
python scripts/verify_gold.py .
```

---

## Odoo Setup

### Docker Compose Configuration

The `odoo/docker-compose.yml` includes:

```yaml
services:
  db:       # PostgreSQL database
  odoo:     # Odoo 19 Community
```

### Management Commands

```bash
# Start Odoo
python odoo/setup_odoo.py start

# Stop Odoo
python odoo/setup_odoo.py stop

# Restart Odoo
python odoo/setup_odoo.py restart

# Check status
python odoo/setup_odoo.py status

# View logs
python odoo/setup_odoo.py logs

# Initialize demo data
python odoo/setup_odoo.py init
```

### Odoo MCP Server Tools

Available via Claude Code:

| Tool | Description |
|------|-------------|
| `create_invoice` | Create customer invoice |
| `get_invoices` | List invoices with filters |
| `get_invoice` | Get specific invoice details |
| `create_customer` | Create new customer |
| `get_customers` | List customers |
| `create_product` | Create product/service |
| `get_products` | List products |
| `register_payment` | Register payment (HITL) |
| `get_account_moves` | Get accounting entries |
| `get_financial_reports` | Get financial summary |

### Usage Example

```python
# In Claude Code, use Odoo MCP tools:
/mcp call odoo-mcp get_financial_reports

# Create invoice
/mcp call odoo-mcp create_invoice {
  "partner_id": 1,
  "lines": [
    {"product_id": 1, "quantity": 1, "price_unit": 100}
  ]
}
```

---

## Facebook Integration

### Setup Facebook Watcher

```bash
# First run: Manual login required
python scripts/watchers/facebook_watcher.py .

# Browser will open
# Login to Facebook manually
# Session saved for future runs
```

### Configuration

Edit watcher keywords in `facebook_watcher.py`:

```python
DEFAULT_KEYWORDS = ['urgent', 'message', 'inquiry', 'order', 'buy', 'price']
```

### Facebook MCP Tools

| Tool | Description |
|------|-------------|
| `facebook_post` | Post to timeline (HITL) |
| `facebook_post_to_page` | Post to business page |
| `get_facebook_insights` | Get page insights |
| `schedule_post` | Schedule post for later |

### Usage Example

```bash
# Post to Facebook (requires approval)
/mcp call social-mcp facebook_post {
  "content": "Exciting business update!",
  "privacy": "public"
}
```

---

## Instagram Integration

### Setup Instagram Session

```bash
# First run: Manual login required
# Session saved to .instagram_session/
```

### Instagram MCP Tools

| Tool | Description |
|------|-------------|
| `instagram_post` | Post image with caption (HITL) |
| `get_instagram_insights` | Get account insights |

### Usage Example

```bash
# Post to Instagram (requires image and approval)
/mcp call social-mcp instagram_post {
  "content": "Check out our new product!",
  "image_path": "/path/to/image.jpg",
  "hashtags": ["tech", "innovation", "AI"]
}
```

---

## CEO Briefing

### Automatic Generation

Briefings are automatically generated on **Monday mornings (6-9 AM)** by the orchestrator.

### Manual Generation

```bash
# Generate briefing for current week
python scripts/ceo_briefing.py .

# Generate briefing for last week
python scripts/ceo_briefing.py . --week -1
```

### Briefing Contents

Each briefing includes:

1. **Executive Summary** - Quick overview
2. **Revenue Report** - Odoo financial data
3. **Completed Tasks** - Productivity analysis
4. **Bottlenecks** - Issues identified
5. **Social Media** - Performance metrics
6. **Proactive Suggestions** - AI recommendations
7. **Action Items** - Prioritized tasks

### Example Briefing Output

```markdown
# Monday Morning CEO Briefing

**Week of:** 2026-03-03 to 2026-03-09

**Status:** 🟢 On Track

## Revenue Report
| Metric | Value | Target | Progress |
|--------|-------|--------|----------|
| This Week | $1,500.00 | - | - |
| MTD | $4,500.00 | $10,000 | 45.0% |

## Bottlenecks
- 🟡 High pending volume: 15 tasks in Needs_Action

## Proactive Suggestions
- 🟢 Revenue Optimization: Follow up with top customers
```

---

## Architecture

### Gold Tier Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL SOURCES                         │
├─────────────┬─────────────┬──────────────┬──────────────────┤
│    Gmail    │  Facebook   │   Instagram  │     Odoo ERP     │
│  WhatsApp   │  Messenger  │   LinkedIn   │  (Docker)        │
└──────┬──────┴──────┬──────┴───────┬──────┴────────┬─────────┘
       │             │              │               │
       ▼             ▼              ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                    WATCHERS (Python)                        │
│  gmail_watcher  facebook_watcher  linkedin_watcher          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    OBSIDIAN VAULT                           │
│  /Needs_Action  /Pending_Approval  /Briefings  /Accounting  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    CLAUDE CODE                              │
│         Reasoning + Planning + Decision Making              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP SERVERS                              │
│  email_mcp  odoo_mcp  social_mcp  browser_mcp              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL ACTIONS                         │
│  Send Email  Create Invoice  Post Social  Make Payment     │
└─────────────────────────────────────────────────────────────┘
```

### Folder Structure

```
AI_Employee_Vault/
├── odoo/
│   ├── docker-compose.yml
│   ├── setup_odoo.py
│   └── .env.example
├── scripts/
│   ├── watchers/
│   │   ├── gmail_watcher.py
│   │   ├── whatsapp_watcher.py
│   │   ├── facebook_watcher.py
│   │   └── linkedin_watcher.py
│   ├── mcp/
│   │   ├── email_mcp.py
│   │   ├── odoo_mcp.py
│   │   └── social_mcp.py
│   ├── orchestrator.py
│   ├── ceo_briefing.py
│   └── verify_gold.py
├── Briefings/          # Weekly CEO reports
├── Accounting/         # Financial records
├── Invoices/           # Invoice PDFs
├── Social/             # Scheduled posts
└── Logs/               # Audit logs
```

---

## Verification

### Run Gold Tier Verification

```bash
python scripts/verify_gold.py .
```

### Verification Checks

The script verifies:

**Bronze Tier (8 checks):**
- Dashboard.md, Company_Handbook.md, Business_Goals.md
- At least 1 watcher script
- Basic folder structure (Inbox, Needs_Action, Done)
- Orchestrator

**Silver Tier (8 checks):**
- 2+ watcher scripts
- LinkedIn auto-posting
- Email MCP server
- HITL folders (Pending_Approval, Approved, Rejected)
- Scheduler
- Plans folder

**Gold Tier (20+ checks):**
- Odoo Docker Compose configuration
- Odoo MCP server with all functions
- Facebook Watcher
- Social Media MCP (Facebook + Instagram)
- CEO Briefing generator
- 3+ MCP servers
- Accounting, Invoices, Social, Briefings folders
- Error handling and audit logging

### Verification Report

A detailed markdown report is saved to `Logs/gold_verification_YYYYMMDD_HHMMSS.md`

---

## Troubleshooting

### Odoo Issues

**Problem:** Odoo won't start

```bash
# Check Docker status
docker ps

# View Odoo logs
python odoo/setup_odoo.py logs

# Restart containers
docker compose down
docker compose up -d
```

**Problem:** Can't connect to Odoo

```bash
# Check if Odoo is running
curl http://localhost:8069

# Should return HTML
```

**Problem:** Authentication fails

```bash
# Verify credentials in .env
cat .env

# Test authentication
python scripts/mcp/odoo_mcp.py --authenticate
```

### Facebook/Instagram Issues

**Problem:** Not logged in

- Browser opens but shows login page
- **Solution:** Manually login, session is saved
- Next runs will auto-login

**Problem:** Post fails

- Check if session is valid
- Re-login to social media
- Verify image path exists (for Instagram)

### CEO Briefing Issues

**Problem:** No revenue data in briefing

- Ensure Odoo is running
- Check Odoo has invoices created
- Verify .env credentials

**Problem:** Briefing not auto-generating

- Check orchestrator is running
- Verify it's Monday between 6-9 AM
- Manually generate: `python scripts/ceo_briefing.py .`

### General Issues

**Problem:** MCP server not found

```bash
# Install MCP library
pip install mcp

# Verify installation
python -c "from mcp.server import Server; print('OK')"
```

**Problem:** Playwright errors

```bash
# Reinstall Playwright
pip install playwright
playwright install chromium
```

---

## Next Steps: Platinum Tier

After completing Gold Tier, consider upgrading to **Platinum Tier**:

1. **Cloud Deployment** - Run 24/7 on Oracle/AWS free tier
2. **Domain Specialization** - Cloud vs Local separation
3. **A2A Communication** - Agent-to-agent protocols
4. **Enhanced Security** - Vault sync with secret isolation

---

## Support & Resources

### Documentation

- [Personal AI Employee FTEs.md](./Personal%20AI%20Employe%20FTEs.md) - Complete blueprint
- [Odoo Documentation](https://www.odoo.com/documentation)
- [Playwright Documentation](https://playwright.dev/python)

### Community

- Wednesday Research Meetings: Wed 10:00 PM PKT
- [Zoom Link](https://us06web.zoom.us/j/87188707642?pwd=a9XloCsinvn1JzICbPc2YGUvWTbOTr.1)
- [YouTube Archive](https://www.youtube.com/@panaversity)

### Hackathon Submission

- [Submission Form](https://forms.gle/JR9T1SJq5rmQyGkGA)
- Include verification report
- Demo video (5-10 minutes)

---

**Gold Tier Complete! 🎉**

Your AI Employee is now a fully autonomous business partner with:
- ✅ Self-hosted Odoo ERP
- ✅ Facebook & Instagram integration
- ✅ Weekly CEO briefings
- ✅ Comprehensive audit logging

**Next:** Run `python scripts/verify_gold.py .` to confirm completion.
