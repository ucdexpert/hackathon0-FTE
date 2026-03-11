#!/usr/bin/env python3
"""
Auto Post to Facebook

Posts to Facebook Page using Graph API.
Reads credentials from .env file.

Usage:
    python auto_post_facebook.py "Your post message here"
"""

import sys
import os
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv('.env', override=True)

# Get credentials
TOKEN = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
PAGE_ID = os.getenv('FACEBOOK_PAGE_ID')

print("\n" + "="*70)
print("AUTO POST TO FACEBOOK")
print("="*70)

# Check credentials
if not TOKEN or not PAGE_ID:
    print("\n❌ ERROR: Missing credentials in .env file")
    print("   Please add FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID")
    sys.exit(1)

print(f"\n✅ Page ID: {PAGE_ID}")
print(f"✅ Token loaded (starts with: {TOKEN[:20]}...)")

# Get message from command line
if len(sys.argv) < 2:
    message = "Hello from AI Employee Gold Tier! 🤖\n\nThis is an automated test post using Facebook Graph API."
    print(f"\n📝 Using default message:")
    print(f"   {message[:50]}...")
else:
    message = " ".join(sys.argv[1:])
    print(f"\n📝 Your message:")
    print(f"   {message[:100]}...")

# Post to Facebook
url = f'https://graph.facebook.com/v18.0/{PAGE_ID}/feed'
params = {
    'message': message,
    'access_token': TOKEN
}

print("\n🔄 Posting to Facebook...")
response = requests.post(url, params=params, timeout=30)

if response.status_code == 200:
    result = response.json()
    post_id = result.get('id', '')
    print("\n" + "="*70)
    print("✅ SUCCESS! POST PUBLISHED!")
    print("="*70)
    print(f"\n   Post ID: {post_id}")
    print(f"   View at: https://facebook.com/{post_id.replace('_', '/posts/')}")
    print("\n" + "="*70 + "\n")
else:
    error_data = response.json()
    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
    print("\n" + "="*70)
    print("❌ FAILED!")
    print("="*70)
    print(f"\n   Status: {response.status_code}")
    print(f"   Error: {error_msg}")
    print("\n   Possible solutions:")
    print("   1. Token expired - Get new token from Graph API Explorer")
    print("   2. Check permissions: pages_manage_posts")
    print("   3. Verify Page ID is correct")
    print("\n" + "="*70 + "\n")
    sys.exit(1)
