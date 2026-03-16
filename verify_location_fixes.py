#!/usr/bin/env python3
"""
Location Fix Verification Script
===============================

This script verifies the location fixes made by the Google Places API fixer.
It checks coordinates and shows before/after comparisons.
"""

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

def get_sample_locations(limit=10):
    """Get a sample of locations to verify"""
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/locations?select=id,name,geom&limit={limit}",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return []

def extract_coordinates(geom_str):
    """Extract coordinates from POINT format"""
    if not geom_str or not geom_str.startswith('POINT('):
        return None, None
        
    try:
        coords = geom_str.replace('POINT(', '').replace(')', '').split()
        if len(coords) == 2:
            return float(coords[0]), float(coords[1])  # lng, lat
    except:
        pass
        
    return None, None

def verify_coordinates(lng, lat, location_name):
    """Check if coordinates are reasonable for Hyderabad area"""
    # Hyderabad bounds (approximate)
    # Longitude: 78.0 to 78.8
    # Latitude: 17.0 to 17.8
    
    if lng is None or lat is None:
        return False, "No coordinates"
    
    if not (78.0 <= lng <= 78.8):
        return False, f"Longitude {lng} outside Hyderabad bounds"
    
    if not (17.0 <= lat <= 17.8):
        return False, f"Latitude {lat} outside Hyderabad bounds"
    
    return True, "Coordinates look good"

def main():
    print("🔍 Verifying Location Fixes")
    print("=" * 40)
    
    locations = get_sample_locations(20)
    
    if not locations:
        print("❌ No locations found")
        return
    
    print(f"📍 Checking {len(locations)} locations...\n")
    
    good_count = 0
    bad_count = 0
    
    for location in locations:
        name = location['name']
        geom = location.get('geom')
        location_id = location['id']
        
        lng, lat = extract_coordinates(geom)
        is_valid, message = verify_coordinates(lng, lat, name)
        
        status = "✅" if is_valid else "❌"
        coords_str = f"{lng:.6f}, {lat:.6f}" if lng and lat else "No coordinates"
        
        print(f"{status} {name} (ID: {location_id})")
        print(f"   📍 {coords_str}")
        print(f"   💬 {message}")
        print()
        
        if is_valid:
            good_count += 1
        else:
            bad_count += 1
    
    print("=" * 40)
    print(f"📊 Summary: {good_count} good, {bad_count} need attention")

if __name__ == "__main__":
    main()