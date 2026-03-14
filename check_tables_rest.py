import os
import requests
from dotenv import load_dotenv

def check_tables_rest():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("Missing SUPABASE_URL or SUPABASE_KEY")
        return

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}"
    }
    
    # Supabase REST API exposes the schema at the root /
    try:
        response = requests.get(f"{url}/rest/v1/", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            definitions = data.get('definitions', {})
            print("Tables found via REST API:")
            for table in definitions.keys():
                print(f" - {table}")
        else:
            print(f"Failed to fetch schema: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_tables_rest()
