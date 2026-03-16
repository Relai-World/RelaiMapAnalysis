#!/usr/bin/env python3
"""
Google Places API Location Fixer
================================

This script:
1. Fetches all locations from Supabase
2. Uses Google Places API to get accurate coordinates and correct spelling
3. Updates coordinates in locations table
4. Updates spelling across all tables that reference location names

Tables that will be updated:
- locations (coordinates + name)
- news_balanced_corpus_1 (location_name)
- price_trends (location)
- unified_data_DataType_Raghu (areaname)

Usage:
    python fix_locations_with_google_places.py
"""

import os
import requests
import time
import json
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_PLACES_API_KEY = input("Enter your Google Places API Key: ").strip()

if not all([SUPABASE_URL, SUPABASE_KEY, GOOGLE_PLACES_API_KEY]):
    print("❌ Missing required environment variables or API key")
    exit(1)

# Supabase headers
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

class LocationFixer:
    def __init__(self):
        self.processed_locations = []
        self.failed_locations = []
        self.spelling_corrections = {}
        
    def get_all_locations(self) -> List[Dict]:
        """Fetch all locations from Supabase"""
        print("📍 Fetching all locations from Supabase...")
        
        try:
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/locations?select=id,name,geom",
                headers=headers
            )
            
            if response.status_code == 200:
                locations = response.json()
                print(f"✅ Found {len(locations)} locations")
                return locations
            else:
                print(f"❌ Error fetching locations: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Exception fetching locations: {e}")
            return []
    
    def search_google_places(self, location_name: str) -> Optional[Dict]:
        """Search Google Places API for location"""
        # Add Hyderabad context for better results
        query = f"{location_name}, Hyderabad, Telangana, India"
        
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            'query': query,
            'key': GOOGLE_PLACES_API_KEY,
            'fields': 'place_id,name,geometry,formatted_address'
        }
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('results') and len(data['results']) > 0:
                    result = data['results'][0]  # Take the first result
                    
                    return {
                        'place_id': result.get('place_id'),
                        'name': result.get('name'),
                        'formatted_address': result.get('formatted_address'),
                        'lat': result['geometry']['location']['lat'],
                        'lng': result['geometry']['location']['lng']
                    }
                else:
                    print(f"   ⚠️  No results found for: {location_name}")
                    return None
            else:
                print(f"   ❌ Google Places API error: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Exception searching Google Places: {e}")
            return None
    
    def extract_current_coordinates(self, geom_str: str) -> Tuple[Optional[float], Optional[float]]:
        """Extract coordinates from POINT(lng lat) format"""
        if not geom_str or not geom_str.startswith('POINT('):
            return None, None
            
        try:
            coords = geom_str.replace('POINT(', '').replace(')', '').split()
            if len(coords) == 2:
                return float(coords[0]), float(coords[1])  # lng, lat
        except:
            pass
            
        return None, None
    
    def update_location_coordinates(self, location_id: int, new_lng: float, new_lat: float, corrected_name: str = None) -> bool:
        """Update location coordinates in Supabase"""
        new_geom = f"POINT({new_lng} {new_lat})"
        
        update_data = {"geom": new_geom}
        if corrected_name:
            update_data["name"] = corrected_name
        
        try:
            response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/locations?id=eq.{location_id}",
                headers=headers,
                json=update_data
            )
            
            if response.status_code == 204:
                return True
            else:
                print(f"   ❌ Error updating location {location_id}: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception updating location {location_id}: {e}")
            return False
    
    def update_spelling_in_tables(self, old_name: str, new_name: str):
        """Update spelling across all tables that reference location names"""
        if old_name == new_name:
            return
            
        print(f"   📝 Updating spelling: '{old_name}' → '{new_name}'")
        
        # 1. Update news_balanced_corpus_1.location_name
        try:
            response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/news_balanced_corpus_1?location_name=eq.{old_name}",
                headers=headers,
                json={"location_name": new_name}
            )
            if response.status_code == 204:
                print(f"      ✅ Updated news_balanced_corpus_1")
            else:
                print(f"      ⚠️  news_balanced_corpus_1 update: {response.status_code}")
        except Exception as e:
            print(f"      ❌ Error updating news_balanced_corpus_1: {e}")
        
        # 2. Update price_trends.location
        try:
            response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/price_trends?location=eq.{old_name}",
                headers=headers,
                json={"location": new_name}
            )
            if response.status_code == 204:
                print(f"      ✅ Updated price_trends")
            else:
                print(f"      ⚠️  price_trends update: {response.status_code}")
        except Exception as e:
            print(f"      ❌ Error updating price_trends: {e}")
        
        # 3. Update unified_data_DataType_Raghu.areaname (exact matches only)
        try:
            response = requests.patch(
                f"{SUPABASE_URL}/rest/v1/unified_data_DataType_Raghu?areaname=eq.{old_name}",
                headers=headers,
                json={"areaname": new_name}
            )
            if response.status_code == 204:
                print(f"      ✅ Updated unified_data_DataType_Raghu")
            else:
                print(f"      ⚠️  unified_data_DataType_Raghu update: {response.status_code}")
        except Exception as e:
            print(f"      ❌ Error updating unified_data_DataType_Raghu: {e}")
    
    def is_coordinate_significantly_different(self, old_lng: float, old_lat: float, new_lng: float, new_lat: float) -> bool:
        """Check if coordinates are significantly different (>100m)"""
        if old_lng is None or old_lat is None:
            return True
            
        # Simple distance check (approximate)
        lng_diff = abs(old_lng - new_lng)
        lat_diff = abs(old_lat - new_lat)
        
        # ~0.001 degrees ≈ 100 meters
        return lng_diff > 0.001 or lat_diff > 0.001
    
    def process_location(self, location: Dict) -> bool:
        """Process a single location"""
        location_id = location['id']
        current_name = location['name']
        current_geom = location.get('geom')
        
        print(f"\n🔍 Processing: {current_name} (ID: {location_id})")
        
        # Get current coordinates
        current_lng, current_lat = self.extract_current_coordinates(current_geom)
        if current_lng and current_lat:
            print(f"   📍 Current: {current_lng:.6f}, {current_lat:.6f}")
        else:
            print(f"   📍 Current: No valid coordinates")
        
        # Search Google Places
        places_result = self.search_google_places(current_name)
        
        if not places_result:
            self.failed_locations.append({
                'id': location_id,
                'name': current_name,
                'reason': 'No Google Places result'
            })
            return False
        
        new_lng = places_result['lng']
        new_lat = places_result['lat']
        google_name = places_result['name']
        
        print(f"   🎯 Google: {new_lng:.6f}, {new_lat:.6f}")
        print(f"   📝 Google name: {google_name}")
        
        # Check if coordinates need updating
        coords_need_update = self.is_coordinate_significantly_different(
            current_lng, current_lat, new_lng, new_lat
        )
        
        # Check if name needs correction
        name_needs_correction = current_name.lower().strip() != google_name.lower().strip()
        
        if coords_need_update or name_needs_correction:
            # Update coordinates (and name if needed)
            corrected_name = google_name if name_needs_correction else None
            
            if self.update_location_coordinates(location_id, new_lng, new_lat, corrected_name):
                print(f"   ✅ Updated coordinates")
                
                # Update spelling across tables if name changed
                if name_needs_correction:
                    self.update_spelling_in_tables(current_name, google_name)
                    self.spelling_corrections[current_name] = google_name
                
                self.processed_locations.append({
                    'id': location_id,
                    'old_name': current_name,
                    'new_name': google_name if name_needs_correction else current_name,
                    'old_coords': (current_lng, current_lat),
                    'new_coords': (new_lng, new_lat),
                    'coords_updated': coords_need_update,
                    'name_updated': name_needs_correction
                })
                
                return True
            else:
                self.failed_locations.append({
                    'id': location_id,
                    'name': current_name,
                    'reason': 'Database update failed'
                })
                return False
        else:
            print(f"   ✅ No updates needed")
            return True
    
    def run(self):
        """Main execution function"""
        print("🚀 Starting Google Places Location Fixer")
        print("=" * 50)
        
        # Get all locations
        locations = self.get_all_locations()
        if not locations:
            print("❌ No locations found. Exiting.")
            return
        
        # Process each location
        total = len(locations)
        for i, location in enumerate(locations, 1):
            print(f"\n[{i}/{total}] ", end="")
            self.process_location(location)
            
            # Rate limiting - Google Places API has limits
            time.sleep(0.1)  # 100ms delay between requests
        
        # Summary
        self.print_summary()
        
        # Save results
        self.save_results()
    
    def print_summary(self):
        """Print processing summary"""
        print("\n" + "=" * 50)
        print("📊 PROCESSING SUMMARY")
        print("=" * 50)
        
        print(f"✅ Successfully processed: {len(self.processed_locations)}")
        print(f"❌ Failed: {len(self.failed_locations)}")
        print(f"📝 Spelling corrections: {len(self.spelling_corrections)}")
        
        if self.spelling_corrections:
            print("\n📝 Spelling Corrections Made:")
            for old, new in self.spelling_corrections.items():
                print(f"   '{old}' → '{new}'")
        
        if self.failed_locations:
            print("\n❌ Failed Locations:")
            for failed in self.failed_locations:
                print(f"   {failed['name']} (ID: {failed['id']}) - {failed['reason']}")
    
    def save_results(self):
        """Save results to JSON files"""
        timestamp = int(time.time())
        
        # Save successful updates
        with open(f"location_fixes_{timestamp}.json", "w") as f:
            json.dump({
                'processed_locations': self.processed_locations,
                'spelling_corrections': self.spelling_corrections,
                'failed_locations': self.failed_locations,
                'timestamp': timestamp
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: location_fixes_{timestamp}.json")

if __name__ == "__main__":
    fixer = LocationFixer()
    fixer.run()