# AI Employee Vault - Project Context

## Project Overview

This is a **hackathon project** for building a **"Digital FTE" (Full-Time Equivalent)** — an autonomous AI employee powered by **Claude Code** and **Obsidian**. The system proactively manages personal and business affairs 24/7 using a local-first, agent-driven architecture.

**Core Concept:** Transform AI from a reactive chatbot into a proactive business partner that:
- Monitors communications (Gmail, WhatsApp, LinkedIn)
- Tracks finances and bank transactions
- Manages tasks and projects
- Generates "Monday Morning CEO Briefings" with revenue reports and bottleneck analysis
- Posts to social media autonomously

## Architecture

### The Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **The Brain** | Claude Code | Reasoning engine, task execution |
| **The Memory/GUI** | Obsidian | Local Markdown dashboard, long-term memory |
| **The Senses** | Python Watchers | Monitor Gmail, WhatsApp, filesystem for triggers |
| **The Hands** | MCP Servers | Model Context Protocol for external actions |

### Key Patterns

1. **Watcher Architecture** — Lightweight Python scripts run continuously, monitoring inputs and creating `.md` files in `/Needs_Action` folder
2. **Ralph Wiggum Loop** — A Stop hook pattern that keeps Claude iterating until multi-step tasks are complete
3. **Human-in-the-Loop (HITL)** — Sensitive actions require approval via file movement (`/Pending_Approval` → `/Approved`)
4. **Claim-by-Move Rule** — Prevents double-work in multi-agent scenarios

## Directory Structure

```
AI_Employee_Vault/
├── Personal AI Employe FTEs.md    # Main hackathon blueprint (1201 lines)
├── skills-lock.json               # Skill version tracking
├── QWEN.md                        # This context file
└── .qwen/
    └── skills/
        └── browsing-with-playwright/
            ├── SKILL.md           # Browser automation skill documentation
            ├── references/
            │   └── playwright-tools.md  # MCP tool reference (22 tools)
            └── scripts/
                ├── mcp-client.py  # Universal MCP client (HTTP + stdio)
                ├── start-server.sh
                ├── stop-server.sh
                └── verify.py
```

## Available Skills

### browsing-with-playwright

Browser automation via Playwright MCP server for web scraping, form submission, UI testing, and any browser interaction.

**Server Management:**
```bash
# Start server (port 8808)
bash .qwen/skills/browsing-with-playwright/scripts/start-server.sh

# Stop server
bash .qwen/skills/browsing-with-playwright/scripts/stop-server.sh

# Verify running
python .qwen/skills/browsing-with-playwright/scripts/verify.py
```

**Key Tools Available:**
- `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`
- `browser_fill_form`, `browser_select_option`, `browser_take_screenshot`
- `browser_evaluate`, `browser_run_code`, `browser_wait_for`
- `browser_console_messages`, `browser_network_requests`

**Usage Example:**
```bash
# Call via mcp-client.py
python scripts/mcp-client.py call -u http://localhost:8808 \
  -t browser_navigate -p '{"url": "https://example.com"}'
```

## Building & Running

### Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Claude Code | Active subscription | Primary reasoning engine |
| Obsidian | v1.10.6+ | Knowledge base & dashboard |
| Python | 3.13+ | Watcher scripts, orchestration |
| Node.js | v24+ LTS | MCP servers, automation |

### Hardware Requirements

- **Minimum:** 8GB RAM, 4-core CPU, 20GB free disk
- **Recommended:** 16GB RAM, 8-core CPU, SSD storage
- **For always-on:** Dedicated mini-PC or cloud VM

### Hackathon Tiers

| Tier | Time | Deliverables |
|------|------|--------------|
| **Bronze** | 8-12 hrs | Obsidian vault, 1 Watcher, basic folder structure |
| **Silver** | 20-30 hrs | 2+ Watchers, MCP server, HITL workflow, scheduling |
| **Gold** | 40+ hrs | Full integration, Odoo accounting, social media, audit logging |
| **Platinum** | 60+ hrs | Cloud deployment, domain specialization, A2A upgrade |

## Folder Conventions

```
/Vault/
├── Inbox/              # Raw incoming items
├── Needs_Action/       # Items requiring processing
├── In_Progress/<agent>/ # Claimed by specific agent
├── Pending_Approval/   # Awaiting human approval
├── Approved/           # Approved actions (triggers execution)
├── Rejected/           # Denied actions
├── Done/               # Completed tasks
├── Plans/              # Generated plan files
├── Briefings/          # CEO briefing reports
├── Accounting/         # Financial records
└── Updates/            # Cross-agent sync (Platinum tier)
```

## Development Practices

1. **All AI functionality as Agent Skills** — Modular, reusable skill definitions
2. **Local-first data** — Obsidian Markdown keeps data accessible and portable
3. **Graceful degradation** — Error recovery and audit logging
4. **Security** — Secrets never sync (`.env`, tokens, banking credentials)

## Key Files

| File | Description |
|------|-------------|
| `Personal AI Employe FTEs.md` | Complete hackathon blueprint with architecture, templates, and implementation guides |
| `skills-lock.json` | Tracks skill versions and sources for reproducibility |
| `mcp-client.py` | Universal MCP client supporting HTTP and stdio transports |

## Weekly Meetings

**Research & Showcase:** Wednesdays at 10:00 PM PKT on Zoom
- First meeting: Wednesday, Jan 7th, 2026
- [Zoom Link](https://us06web.zoom.us/j/87188707642?pwd=a9XloCsinvn1JzICbPc2YGUvWTbOTr.1)
- [YouTube Archive](https://www.youtube.com/@panaversity)
