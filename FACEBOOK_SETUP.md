# Facebook Graph API Setup Guide

## Overview

This AI Employee integration uses the **Facebook Graph API** (not Playwright automation) for:
- Monitoring Facebook Page notifications
- Reading Page messages
- Tracking post comments and engagement
- Posting to Facebook Page
- Posting to Instagram Business Account
- Getting Page insights

---

## Prerequisites

1. **Facebook Page** - You must own or manage a Facebook Page
2. **Facebook Developer Account** - Access to [developers.facebook.com](https://developers.facebook.com)
3. **Instagram Business Account** (optional) - Connected to your Facebook Page

---

## Step 1: Create Facebook App

### 1.1 Go to Facebook Developers

1. Visit [https://developers.facebook.com](https://developers.facebook.com)
2. Click **My Apps** → **Create App**

### 1.2 Select App Type

Choose **Business** as the app type (recommended for Pages)

### 1.3 Configure App

- **App Name**: `AI Employee Social Media`
- **App Contact Email**: your-email@example.com
- Click **Create App**

---

## Step 2: Add Facebook Graph API

### 2.1 Add Graph API Product

1. In your App Dashboard, scroll to **Add Products to Your App**
2. Click **Add Product** next to **Graph API**

### 2.2 Configure Permissions

Your app needs these permissions:
- `pages_read_engagement` - Read Page content and engagement
- `pages_read_user_content` - Read Page messages and comments
- `pages_manage_posts` - Create posts on Page
- `pages_manage_engagement` - Engage with content
- `instagram_basic` - Basic Instagram data
- `instagram_content_publish` - Publish to Instagram
- `instagram_manage_insights` - Get Instagram insights

---

## Step 3: Get Page Access Token

### 3.1 Use Graph API Explorer

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app from the **Application** dropdown
3. Click **Get Token** → **Get Page Access Token**
4. Select your Facebook Page
5. Check the required permissions
6. Click **Generate Access Token**

### 3.2 Copy Token

Copy the generated **Page Access Token** - you'll need this for configuration.

**Important:** For production use, you should generate a **Long-Lived Page Access Token** that doesn't expire.

---

## Step 4: Get Page ID

### 4.1 Find Your Page ID

**Method 1: From Page Settings**
1. Go to your Facebook Page
2. Click **About** in the left menu
3. Scroll down to find **Facebook Page ID**

**Method 2: Using Graph API**
```
GET https://graph.facebook.com/me/accounts?access_token=YOUR_ACCESS_TOKEN
```

Copy the **Page ID**.

---

## Step 5: Configure Instagram (Optional)

### 5.1 Requirements

- Instagram **Business** or **Creator** account
- Instagram account must be **connected to your Facebook Page**

### 5.2 Connect Instagram to Facebook

1. Go to your Facebook Page
2. Click **Settings** → **Instagram**
3. Click **Connect Account**
4. Log in to Instagram and authorize

### 5.3 Get Instagram Business Account ID

Use Graph API Explorer:
```
GET https://graph.facebook.com/v18.0/me?fields=instagram_business_account&access_token=YOUR_ACCESS_TOKEN
```

Copy the **instagram_business_account.id** value.

---

## Step 6: Configure Environment Variables

Create or update `.env` file in your vault root:

```bash
# Facebook Graph API Configuration
FACEBOOK_PAGE_ACCESS_TOKEN=EAA...your_long_access_token_here
FACEBOOK_PAGE_ID=123456789012345

# Instagram Business Account (optional)
INSTAGRAM_BUSINESS_ACCOUNT_ID=17841400000000000
```

---

## Step 7: Test Configuration

### 7.1 Test Facebook Connection

```bash
# Test Graph API connection
curl "https://graph.facebook.com/v18.0/YOUR_PAGE_ID?access_token=YOUR_ACCESS_TOKEN"
```

Should return your Page information.

### 7.2 Test Facebook Watcher

```bash
# Run Facebook Watcher
python scripts/watchers/facebook_watcher.py .
```

Should start monitoring without errors.

### 7.3 Test Social MCP Server

```bash
# Test Social MCP Server
python scripts/mcp/social_mcp.py
```

Should start and show configured Page ID.

---

## Facebook Graph API Endpoints Used

### Monitoring

| Endpoint | Purpose |
|----------|---------|
| `/{page-id}/conversations` | Get Page messages |
| `/{page-id}/posts` | Get Page posts |
| `/{post-id}/comments` | Get post comments |
| `/{page-id}/insights` | Get Page analytics |

### Posting

| Endpoint | Purpose |
|----------|---------|
| `/{page-id}/feed` | Post text/link to Page |
| `/{page-id}/photos` | Post photo to Page |
| `/{comment-id}/comments` | Reply to comment |

### Instagram

| Endpoint | Purpose |
|----------|---------|
| `/{ig-account-id}/media` | Create media container |
| `/{ig-account-id}/media_publish` | Publish media |
| `/{ig-account-id}/insights` | Get Instagram analytics |

---

## Access Token Types

### Short-Lived Token
- **Validity:** 1-2 hours
- **Use:** Testing only

### Long-Lived Token (Recommended)
- **Validity:** 60 days
- **How to get:** Exchange short-lived token
- **Refresh:** Can be refreshed before expiry

### Never-Expiring Token
- **Validity:** Does not expire
- **Use:** Production systems
- **How to get:** Requires app review and business verification

---

## Getting Long-Lived Token

1. Go to [Access Token Debugger](https://developers.facebook.com/tools/debug/access_token/)
2. Enter your short-lived token
3. Click **Debug**
4. Click **Extend Access Token**
5. Copy the new long-lived token

---

## App Review (For Production)

To use your app with real users (not just test accounts):

1. Go to **App Review** in your dashboard
2. Submit each permission for review
3. Provide detailed use case descriptions
4. Wait for approval (typically 3-7 days)

**Required for production:**
- `pages_read_engagement`
- `pages_manage_posts`
- `instagram_basic`
- `instagram_content_publish`

---

## Rate Limits

Facebook Graph API has rate limits:

- **Page-level rate limit:** 200 calls per hour per Page
- **User-level rate limit:** 200 calls per hour per user

The Facebook Watcher is configured to check every 5 minutes (300 seconds) to stay well within limits.

---

## Troubleshooting

### Error: "Page Access Token is required"

**Solution:**
- Ensure `FACEBOOK_PAGE_ACCESS_TOKEN` is set in `.env`
- Token must be a **Page** token, not a **User** token

### Error: "Unsupported get request"

**Solution:**
- Check that Page ID is correct
- Ensure token has required permissions
- Verify app is in development mode (for testing)

### Error: "Invalid OAuth access token"

**Solution:**
- Token may have expired
- Generate a new long-lived token
- Update `.env` file

### No messages/comments appearing

**Solution:**
- Check Page has messages/comments
- Verify `pages_read_user_content` permission
- Check token hasn't expired

---

## Security Best Practices

1. **Never commit tokens** - Add `.env` to `.gitignore`
2. **Use long-lived tokens** - More secure than short-lived
3. **Rotate tokens regularly** - Especially if compromised
4. **Limit permissions** - Only request what you need
5. **Monitor app activity** - Check for unusual API usage

---

## Testing with Graph API Explorer

### Test Reading Messages

```
GET /v18.0/{page-id}/conversations?fields=messages{from,message,created_time}
```

### Test Reading Posts

```
GET /v18.0/{page-id}/posts?fields=message,created_time
```

### Test Creating Post

```
POST /v18.0/{page-id}/feed
message=Hello from AI Employee!
```

---

## Resources

- [Graph API Documentation](https://developers.facebook.com/docs/graph-api)
- [Facebook Login Review](https://developers.facebook.com/docs/facebook-login/review/)
- [Page Access Token Documentation](https://developers.facebook.com/docs/pages/access-tokens)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api)

---

## Support

For issues with Facebook API:
- [Facebook Developer Support](https://developers.facebook.com/support/)
- [Stack Overflow - facebook-graph-api](https://stackoverflow.com/questions/tagged/facebook-graph-api)

---

**Next:** After setup, run `python scripts/watchers/facebook_watcher.py .` to start monitoring!
