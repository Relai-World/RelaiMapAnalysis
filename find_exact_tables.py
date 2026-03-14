import os
import requests
from dotenv import load_dotenv

def find_exact_table_names():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}"
    }
    
    try:
        response = requests.get(f"{url}/rest/v1/", headers=headers, timeout=10)
        if response.status_code == 200:
            definitions = response.json().get('definitions', {})
            print("Exact Table Names Found:")
            for table in definitions.keys():
                print(f" - {table}")
        else:
            print(f"Failed: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_exact_table_names()
