import os
import requests
from dotenv import load_dotenv

def get_detailed_schema():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}"
    }
    
    tables_to_check = [
        "news_balanced_corpus_1",
        "location_insights",
        "price_trends",
        "locations",
        "unified_data_DataType_Raghu",
        "location_costs"
    ]
    
    print("--- Detailed Schema Info ---")
    
    try:
        response = requests.get(f"{url}/rest/v1/", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            definitions = data.get('definitions', {})
            
            for table in tables_to_check:
                if table in definitions:
                    print(f"\nTable: {table}")
                    properties = definitions[table].get('properties', {})
                    for prop, details in properties.items():
                        print(f"  - {prop}: {details.get('format', details.get('type'))}")
                else:
                    print(f"\nTable: {table} - ❌ NOT FOUND in REST definition")
        else:
            print(f"Failed to fetch schema: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_detailed_schema()
