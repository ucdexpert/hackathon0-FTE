# .env Setup Guide - Quick Reference

## Quick Setup (Copy & Paste)

Copy these lines and fill in your values:

```bash
# Facebook Graph API (Get from developers.facebook.com)
FACEBOOK_PAGE_ACCESS_TOKEN=EAA...
FACEBOOK_PAGE_ID=123456789012345
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841400000000000

# Odoo (Default Docker setup)
ODOO_HOST=localhost
ODOO_PORT=8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=admin
```

---

## Facebook Graph API Setup

### Step 1: Get Page Access Token

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app (or create one)
3. Click **Get Token** → **Get Page Access Token**
4. Select your Facebook Page
5. Copy the token (starts with `EAA...`)

**Paste here:**
```
FACEBOOK_PAGE_ACCESS_TOKEN=
```

### Step 2: Get Page ID

**Method 1: From Page Settings**
1. Go to your Facebook Page
2. Click **About** in left menu
3. Scroll to **Facebook Page ID**

**Method 2: From Graph API**
```
https://graph.facebook.com/me/accounts?access_token=YOUR_TOKEN
```

**Paste here:**
```
FACEBOOK_PAGE_ID=
```

### Step 3: Instagram Business ID (Optional)

1. Make sure Instagram is connected to your Facebook Page
2. Use Graph API:
```
https://graph.facebook.com/v18.0/me?fields=instagram_business_account&access_token=YOUR_TOKEN
```

**Paste here:**
```
INSTAGRAM_BUSINESS_ACCOUNT_ID=
```

---

## Odoo Setup (Docker)

### Default Configuration

If you're running Odoo via Docker Compose (recommended):

```bash
ODOO_HOST=localhost
ODOO_PORT=8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=admin
```

### Start Odoo

```bash
cd odoo
python setup_odoo.py start
```

Wait 2-3 minutes, then access at http://localhost:8069

---

## Gmail API Setup (Optional)

### Get Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable Gmail API
4. Go to **Credentials** → **Create Credentials** → **OAuth Client ID**
5. Application type: **Web application**
6. Authorized redirect URIs: `http://localhost:8080`
7. Copy Client ID and Client Secret

**Paste here:**
```
GMAIL_CLIENT_ID=
GMAIL_CLIENT_SECRET=
GMAIL_REDIRECT_URI=http://localhost:8080
```

---

## Verify Configuration

### Test Facebook Connection

```bash
curl "https://graph.facebook.com/v18.0/YOUR_PAGE_ID?access_token=YOUR_TOKEN"
```

Should return your Page information.

### Test Odoo Connection

```bash
curl http://localhost:8069
```

Should return HTML (Odoo homepage).

### Run Verification

```bash
python scripts/verify_gold.py .
```

---

## Security Checklist

- [ ] `.env` file is in `.gitignore`
- [ ] Using long-lived Facebook token (60 days)
- [ ] Odoo password changed from default
- [ ] API keys not shared publicly
- [ ] Tokens stored securely

---

## Troubleshooting

### Facebook: "Invalid OAuth access token"

- Token expired → Generate new long-lived token
- Wrong token type → Must be Page token, not User token

### Odoo: Connection refused

- Odoo not running → `python odoo/setup_odoo.py start`
- Wrong port → Check `ODOO_PORT` (default 8069)

### Instagram: "Account not found"

- Instagram not connected to Facebook Page
- Not a Business/Creator account
- Wrong account ID

---

## Full .env Example

```bash
# Facebook Graph API
FACEBOOK_PAGE_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FACEBOOK_PAGE_ID=123456789012345
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841400000000000

# Odoo
ODOO_HOST=localhost
ODOO_PORT=8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=admin

# Gmail
GMAIL_CLIENT_ID=123456789-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxxxx
GMAIL_REDIRECT_URI=http://localhost:8080

# General
VAULT_PATH=.
LOG_LEVEL=INFO
DRY_RUN=false
```

---

## Next Steps

After configuring `.env`:

1. **Start Odoo** (if using):
   ```bash
   python odoo/setup_odoo.py start
   ```

2. **Test Facebook Watcher**:
   ```bash
   python scripts/watchers/facebook_watcher.py .
   ```

3. **Start Orchestrator**:
   ```bash
   python scripts/orchestrator.py . 30
   ```

4. **Run Verification**:
   ```bash
   python scripts/verify_gold.py .
   ```

---

**Need Help?** See [`FACEBOOK_SETUP.md`](./FACEBOOK_SETUP.md) for detailed Facebook API setup.
