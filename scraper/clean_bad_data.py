"""
Clean bad/irrelevant data from future_dev table
Removes articles that mention other locations more than the target location
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
import re

load_dotenv()

def clean_future_dev_table():
    """Remove articles that are not actually about the target location"""
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
    
    print("Fetching all articles from future_dev table...")
    result = supabase.table('future_dev').select('*').execute()
    
    if not result.data:
        print("No data found")
        return
    
    print(f"Found {len(result.data)} articles. Analyzing...")
    
    # List of common Hyderabad locations
    common_locations = [
        "gachibowli", "kondapur", "hitec city", "madhapur", "financial district",
        "nanakramguda", "kukatpally", "miyapur", "bachupally", "kompally",
        "secunderabad", "banjara hills", "jubilee hills", "begumpet",
        "lb nagar", "uppal", "nagole", "mehdipatnam", "manikonda", "kokapet",
        "attapur", "rajendra nagar", "shamshabad", "hayathnagar", "abids"
    ]
    
    to_delete = []
    
    for article in result.data:
        location_name = article['location_name'].lower()
        content = article['content'].lower()
        
        # Count target location mentions
        target_count = content.count(location_name)
        
        # Count other location mentions
        other_count = 0
        other_locs = []
        for loc in common_locations:
            if loc != location_name:
                count = content.count(loc)
                if count > 0:
                    other_count += count
                    other_locs.append(f"{loc}({count})")
        
        # If other locations mentioned more, mark for deletion
        if other_count > target_count:
            to_delete.append({
                'id': article['id'],
                'location': article['location_name'],
                'url': article['url'],
                'target_count': target_count,
                'other_count': other_count,
                'other_locs': other_locs
            })
    
    print(f"\nFound {len(to_delete)} articles to delete:")
    print("="*100)
    
    for item in to_delete:
        print(f"ID: {item['id']} | Location: {item['location']} | "
              f"Target mentions: {item['target_count']} | Other mentions: {item['other_count']}")
        print(f"  Other locations: {', '.join(item['other_locs'][:5])}")
        print(f"  URL: {item['url'][:80]}...")
        print()
    
    if to_delete:
        confirm = input(f"\nDelete these {len(to_delete)} articles? (yes/no): ")
        if confirm.lower() == 'yes':
            for item in to_delete:
                supabase.table('future_dev').delete().eq('id', item['id']).execute()
                print(f"Deleted ID: {item['id']}")
            print(f"\n✅ Deleted {len(to_delete)} irrelevant articles")
        else:
            print("Cancelled")
    else:
        print("✅ No bad data found!")

if __name__ == "__main__":
    clean_future_dev_table()
