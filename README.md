# AI Employee Vault - Bronze & Silver Tier

> **Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.**

This is a **Bronze & Silver Tier** implementation of the Personal AI Employee hackathon. It provides the foundational infrastructure for an autonomous AI agent that manages personal and business affairs using **Qwen Code** and Obsidian.

---

## 🏆 Bronze Tier Deliverables

- [x] Obsidian vault with `Dashboard.md` and `Company_Handbook.md`
- [x] One working Watcher script (File System monitoring)
- [x] Qwen Code successfully reading from and writing to the vault
- [x] Basic folder structure: `/Inbox`, `/Needs_Action`, `/Done`
- [x] Orchestrator for workflow management

## 🥈 Silver Tier Deliverables

- [x] All Bronze requirements plus:
- [x] Two or more Watcher scripts (Gmail + WhatsApp)
- [x] One working MCP server for external action (Email MCP)
- [x] Human-in-the-loop approval workflow for sensitive actions
- [x] Basic scheduling via cron or Task Scheduler
- [x] Plan Generator for Qwen reasoning loop
- [x] LinkedIn Poster for business lead generation

---

## 📁 Project Structure

```
AI_Employee_Vault/
├── Dashboard.md              # Real-time status dashboard
├── Company_Handbook.md       # Rules of engagement
├── Business_Goals.md         # Goals and objectives
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── scripts/
│   ├── orchestrator.py       # Master workflow process
│   ├── plan_generator.py     # Creates Plan.md files
│   ├── scheduler.py          # Cron/Task Scheduler integration
│   ├── linkedin_poster.py    # LinkedIn automation
│   ├── verify_bronze.py      # Bronze tier verification
│   ├── verify_silver.py      # Silver tier verification
│   ├── watchers/
│   │   ├── base_watcher.py       # Base class for all watchers
│   │   ├── filesystem_watcher.py # File system monitor (Bronze)
│   │   ├── gmail_watcher.py      # Gmail monitor (Silver)
│   │   └── whatsapp_watcher.py   # WhatsApp monitor (Silver)
│   └── mcp/
│       └── email_mcp.py          # Email MCP server (Silver)
├── Inbox/                    # Drop zone for new items
├── Needs_Action/             # Items requiring processing
├── Done/                     # Completed tasks
├── Plans/                    # AI-generated plans
├── Pending_Approval/         # Awaiting human approval
├── Approved/                 # Approved actions
├── Rejected/                 # Denied actions
├── Logs/                     # Daily activity logs
├── Briefings/                # Weekly CEO reports
├── Accounting/               # Financial records
└── LinkedIn_Posts/           # LinkedIn post drafts
```

---

## 🚀 Quick Start

### Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| [Python](https://www.python.org/downloads/) | 3.13+ | Watcher scripts |
| [Obsidian](https://obsidian.md/download) | v1.10.6+ | Knowledge base |
| [Qwen Code](https://github.com/QwenLM/Qwen) | Latest | Reasoning engine |
| [Node.js](https://nodejs.org/) | v24+ LTS | MCP servers (future) |

### Installation

1. **Clone or download this vault** to your local machine

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Open the vault in Obsidian:**
   - Launch Obsidian
   - Click "Open folder as vault"
   - Select the `AI_Employee_Vault` folder

4. **Verify folder structure:**
   All required folders should exist: `Inbox`, `Needs_Action`, `Done`, etc.

---

## 📖 Usage

### Starting the File System Watcher

The File System Watcher monitors the `/Inbox` folder for new files:

```bash
# From the vault root directory
python scripts/watchers/filesystem_watcher.py .
```

**How it works:**
1. Drop any file into the `/Inbox` folder
2. The watcher detects the new file
3. An action file (`.md`) is created in `/Needs_Action`
4. Qwen Code can then process the action file

### Starting the Orchestrator

The Orchestrator manages the overall workflow:

```bash
# From the vault root directory
python scripts/orchestrator.py . 30
```

**Arguments:**
- `.` - Path to the vault (current directory)
- `30` - Check interval in seconds (optional, default: 30)

### Running Both (Recommended)

Run both processes in separate terminal windows:

```bash
# Terminal 1: File System Watcher
python scripts/watchers/filesystem_watcher.py .

# Terminal 2: Orchestrator
python scripts/orchestrator.py . 30
```

---

## 🔄 Workflow

### Basic Flow (Bronze Tier)

```
1. User drops file → /Inbox/
2. File System Watcher detects → Creates action file in /Needs_Action/
3. User prompts Qwen Code to process /Needs_Action/
4. Qwen creates Plan.md → Processes task → Moves to /Done/
5. Orchestrator updates Dashboard.md
```

### Using Qwen Code

```bash
# Navigate to vault directory
cd /path/to/AI_Employee_Vault

# Start Qwen Code
qwen

# Prompt examples:
# "Check /Needs_Action for new items and process them"
# "Review the Company_Handbook.md and update the Dashboard.md"
# "Create a plan for processing all pending action files"
```

---

## 📝 Example: Processing a File Drop

1. **Drop a file** into `/Inbox/`:
   ```
   /Inbox/client_invoice.pdf
   ```

2. **Watcher creates action file** in `/Needs_Action/`:
   ```
   /Needs_Action/FILE_client_invoice.pdf.md
   ```

3. **Prompt Qwen Code**:
   ```
   Check /Needs_Action for new items. Read the Company_Handbook.md
   for rules. Create a plan to process the invoice file.
   ```

4. **Qwen creates plan** in `/Plans/`:
   ```
   /Plans/PLAN_invoice_client.md
   ```

5. **After processing**, files move to `/Done/`

---

## 🔧 Configuration

### Environment Variables (Optional)

Create a `.env` file for future integrations:

```bash
# .env - NEVER commit to version control
DRY_RUN=true
LOG_LEVEL=INFO
```

### Watcher Configuration

Edit `src/watchers/filesystem_watcher.py` to customize:

- `check_interval`: How often to check for new files
- `watch_folder`: Which folder to monitor (default: `/Inbox`)

---

## 📊 Dashboard

The `Dashboard.md` auto-updates with:

- Pending actions count
- Pending approvals count
- Tasks completed today/this week
- Recent activity from logs
- Alerts for high volumes

---

## 🛠️ Troubleshooting

### Watcher not detecting files

1. Ensure the watcher is running: Check terminal output
2. Verify folder permissions: Watcher needs read/write access
3. Check file extensions: Hidden files (`.xxx`) are skipped

### Orchestrator not updating dashboard

1. Verify vault path is correct
2. Check `Dashboard.md` is not locked by Obsidian
3. Review logs in `/Logs/` for errors

### Python import errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Verify installation
python -c "import watchdog; print(watchdog.__version__)"
```

---

## 📈 Next Steps (Silver Tier)

After mastering Bronze Tier, consider adding:

1. **Gmail Watcher** - Monitor email for important messages
2. **WhatsApp Watcher** - Detect urgent messages via Playwright
3. **MCP Server Integration** - Enable Qwen to send emails
4. **Human-in-the-Loop** - Approval workflow for sensitive actions
5. **Scheduled Tasks** - Cron-based daily briefings

---

## 🥈 Silver Tier Usage

### Install All Dependencies

```bash
pip install -r requirements.txt
playwright install
```

### Start Gmail Watcher

```bash
# First-time authentication
python scripts/watchers/gmail_watcher.py . --authenticate

# Start watching
python scripts/watchers/gmail_watcher.py .
```

### Start WhatsApp Watcher

```bash
# Opens browser for QR code scan (first time only)
python scripts/watchers/whatsapp_watcher.py .
```

### Start Email MCP Server

```bash
python scripts/mcp/email_mcp.py
```

### Install Scheduler

```bash
# Linux/Mac
python scripts/scheduler.py install

# Windows
python scripts/scheduler.py install --platform windows
```

### Create LinkedIn Post

```bash
# Create post for approval
python scripts/linkedin_poster.py . --create "Your post text here"

# List pending posts
python scripts/linkedin_poster.py . --list
```

### Generate Plans

```bash
python scripts/plan_generator.py .
```

---

## 📊 Dashboard

The `Dashboard.md` auto-updates with:

- Pending actions count
- Pending approvals count
- Tasks completed today/this week
- Recent activity from logs
- Alerts for high volumes

---

## 🛠️ Troubleshooting

### Watcher not detecting files

1. Ensure the watcher is running: Check terminal output
2. Verify folder permissions: Watcher needs read/write access
3. Check file extensions: Hidden files (`.xxx`) are skipped

### Orchestrator not updating dashboard

1. Verify vault path is correct
2. Check `Dashboard.md` is not locked by Obsidian
3. Review logs in `/Logs/` for errors

### Python import errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Verify installation
python -c "import watchdog; print(watchdog.__version__)"
```

### Gmail Watcher Authentication Failed

```bash
# Re-authenticate
python scripts/watchers/gmail_watcher.py . --authenticate

# Check credentials.json exists
ls credentials.json
```

### WhatsApp/LinkedIn Browser Issues

```bash
# Reinstall Playwright browsers
playwright install chromium

# Clear session data
rm -rf .whatsapp_session
rm -rf .linkedin_session
```

---

## 📚 Resources

- [Full Hackathon Blueprint](./Personal%20AI%20Employe%20FTEs.md)
- [Company Handbook](./Company_Handbook.md)
- [Business Goals](./Business_Goals.md)
- [Qwen Code Documentation](https://github.com/QwenLM/Qwen)
- [Obsidian Help](https://help.obsidian.md/)
- [Playwright Documentation](https://playwright.dev/python/)
- [Gmail API Reference](https://developers.google.com/gmail/api)

---

## 🤝 Contributing

This is a hackathon project. Feel free to:

1. Fork and customize for your needs
2. Add new watcher implementations
3. Improve the orchestrator logic
4. Share your enhancements with the community

---

## 📄 License

This project is part of the Personal AI Employee Hackathon 2026.

---

*AI Employee v0.2 (Bronze & Silver Tier)*
*Built with ❤️ for autonomous productivity*
