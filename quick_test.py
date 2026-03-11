from dotenv import load_dotenv
import os
import requests

# Force reload .env
load_dotenv('.env', override=True)

TOKEN = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
PAGE_ID = os.getenv('FACEBOOK_PAGE_ID')

print("\n" + "="*60)
print("FACEBOOK TOKEN TEST")
print("="*60)

print(f"\nToken starts with: {TOKEN[:20] if TOKEN else 'NOT SET'}...")
print(f"Page ID: {PAGE_ID}")

# Test simple request
url = f'https://graph.facebook.com/v18.0/{PAGE_ID}'
params = {'access_token': TOKEN, 'fields': 'id,name'}

print("\nTesting connection...")
response = requests.get(url, params=params, timeout=30)

if response.status_code == 200:
    data = response.json()
    print(f"✅ SUCCESS! Connected to: {data.get('name', 'Unknown')}")
else:
    print(f"❌ Failed: {response.status_code}")
    print(f"   Error: {response.json().get('error', {}).get('message', 'Unknown')}")

print("\n" + "="*60 + "\n")
