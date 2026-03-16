#!/usr/bin/env python3
"""
Location Data Backup Script
===========================

This script creates a backup of all location-related data before running fixes.
Run this BEFORE using the Google Places fixer.
"""

import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def backup_table(table_name, select_fields="*"):
    """Backup a specific table"""
    print(f"📦 Backing up {table_name}...")
    
    try:
        # Get total count first
        count_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table_name}?select=count",
            headers={**headers, "Prefer": "count=exact"}
        )
        
        if count_response.status_code == 200:
            total_count = int(count_response.headers.get('Content-Range', '0').split('/')[-1])
            print(f"   📊 Found {total_count} records")
        else:
            total_count = "unknown"
        
        # Fetch all data
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table_name}?select={select_fields}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Backed up {len(data)} records")
            return data
        else:
            print(f"   ❌ Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None

def main():
    timestamp = int(time.time())
    backup_data = {
        'timestamp': timestamp,
        'backup_date': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp)),
        'tables': {}
    }
    
    print("🚀 Creating Location Data Backup")
    print("=" * 40)
    
    # Backup key tables
    tables_to_backup = [
        ('locations', 'id,name,geom'),
        ('news_balanced_corpus_1', 'id,location_id,location_name'),
        ('price_trends', 'location,year_2020,year_2021,year_2022,year_2023,year_2024,year_2025,year_2026'),
        ('unified_data_DataType_Raghu', 'id,projectname,areaname,buildername')
    ]
    
    for table_name, fields in tables_to_backup:
        data = backup_table(table_name, fields)
        if data is not None:
            backup_data['tables'][table_name] = data
    
    # Save backup
    backup_filename = f"location_backup_{timestamp}.json"
    
    try:
        with open(backup_filename, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        print(f"\n💾 Backup saved to: {backup_filename}")
        print(f"📊 Total tables backed up: {len(backup_data['tables'])}")
        
        # Show summary
        print("\n📋 Backup Summary:")
        for table_name, data in backup_data['tables'].items():
            print(f"   {table_name}: {len(data)} records")
            
    except Exception as e:
        print(f"❌ Error saving backup: {e}")

if __name__ == "__main__":
    main()