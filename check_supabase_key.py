import os
import base64
import json
from dotenv import load_dotenv

load_dotenv()

key = os.getenv('SUPABASE_KEY')
if not key:
    print("No SUPABASE_KEY found in .env")
    exit()

# JWT tokens have 3 parts separated by dots
parts = key.split('.')
if len(parts) != 3:
    print("Invalid JWT format")
    exit()

# Decode the payload (second part)
payload = parts[1]
# Add padding if needed
padding = 4 - len(payload) % 4
if padding != 4:
    payload += '=' * padding

try:
    decoded = base64.urlsafe_b64decode(payload)
    data = json.loads(decoded)
    
    print("=" * 60)
    print("SUPABASE KEY INFORMATION")
    print("=" * 60)
    print(f"Role: {data.get('role', 'unknown')}")
    print(f"Issuer: {data.get('iss', 'unknown')}")
    print(f"Reference: {data.get('ref', 'unknown')}")
    
    if data.get('role') == 'anon':
        print("\n⚠️  WARNING: This is an ANON key (public, limited permissions)")
        print("   You need the SERVICE_ROLE key for full database access")
    elif data.get('role') == 'service_role':
        print("\n✅ This is a SERVICE_ROLE key (full permissions)")
    else:
        print(f"\n❓ Unknown role: {data.get('role')}")
        
except Exception as e:
    print(f"Error decoding: {e}")
