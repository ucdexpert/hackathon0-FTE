import requests

try:
    r = requests.get('http://localhost:8069', timeout=10)
    if r.status_code == 200:
        print("\n✅ SUCCESS! Odoo is accessible!\n")
        print("   URL: http://localhost:8069")
        print("   Status: Running\n")
    else:
        print(f"\n⚠️ Status: {r.status_code}\n")
except Exception as e:
    print(f"\n⚠️ Error: {e}\n")
