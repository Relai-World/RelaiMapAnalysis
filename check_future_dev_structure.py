#!/usr/bin/env python3

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def check_table_structure():
    """Check the actual data structure and quality in future_development_scrap table"""
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get a few records to see actual structure
        response = supabase.table('future_development_scrap').select('*').limit(3).execute()
        records = response.data
        
        print(f"🔍 ACTUAL TABLE STRUCTURE & DATA")
        print(f"=" * 60)
        
        if records:
            # Show all columns and their values
            first_record = records[0]
            print(f"Available columns: {list(first_record.keys())}")
            print(f"\n📋 DETAILED RECORD ANALYSIS:")
            print(f"-" * 60)
            
            for i, record in enumerate(records, 1):
                print(f"\nRecord {i}:")
                for key, value in record.items():
                    if value is not None and value != '':
                        print(f"  {key}: {value}")
                    else:
                        print(f"  {key}: [EMPTY/NULL]")
                print("-" * 40)
                
        # Check data quality statistics
        print(f"\n📊 DATA QUALITY ANALYSIS:")
        print(f"-" * 60)
        
        # Count non-null values for key fields
        all_response = supabase.table('future_development_scrap').select('*').execute()
        all_records = all_response.data
        
        total_records = len(all_records)
        
        quality_stats = {}
        if all_records:
            sample_record = all_records[0]
            for field in sample_record.keys():
                non_null_count = sum(1 for record in all_records 
                                   if record.get(field) is not None and record.get(field) != '')
                quality_stats[field] = {
                    'non_null': non_null_count,
                    'percentage': (non_null_count / total_records) * 100
                }
        
        for field, stats in quality_stats.items():
            print(f"  {field}: {stats['non_null']}/{total_records} ({stats['percentage']:.1f}%) populated")
            
    except Exception as e:
        print(f"❌ Error checking table structure: {e}")

if __name__ == "__main__":
    check_table_structure()