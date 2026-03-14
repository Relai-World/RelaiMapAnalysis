import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

print("Checking table names in Supabase...")
print("=" * 80)

# Try to query the table with different case variations
variations = [
    "unified_data_DataType_Raghu",
    "unified_data_datatype_raghu",
    "UNIFIED_DATA_DATATYPE_RAGHU",
    "Unified_Data_DataType_Raghu"
]

for table_name in variations:
    try:
        # Try to get just 1 row to test if table exists
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table_name}?limit=1",
            headers=headers
        )
        print(f"\nTable: {table_name}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ FOUND! This is the correct table name")
            data = response.json()
            if len(data) > 0:
                print(f"Sample columns: {list(data[0].keys())[:10]}")
            break
        else:
            print(f"❌ Not found - {response.json().get('message', 'Unknown error')[:80]}")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 80)
