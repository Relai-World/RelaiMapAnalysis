#!/usr/bin/env python3
"""
Debug coordinates issue in insights data
"""
import requests
import json

def debug_coordinates():
    api_url = 'https://hyderabad-intelligence.onrender.com'
    response = requests.get(f'{api_url}/api/v1/insights', timeout=30)

    if response.status_code == 200:
        data = response.json()
        gachibowli = next((d for d in data if 'gachibowli' in d.get('location', '').lower()), None)
        
        if gachibowli:
            print('🔍 Gachibowli data structure:')
            print('=' * 50)
            for key, value in gachibowli.items():
                print(f'{key}: {value} (type: {type(value).__name__})')
            
            print('\n📍 Coordinate Analysis:')
            print('=' * 50)
            lat = gachibowli.get('latitude')
            lng = gachibowli.get('longitude')
            
            print(f'Latitude: {lat}')
            print(f'Longitude: {lng}')
            print(f'Latitude type: {type(lat)}')
            print(f'Longitude type: {type(lng)}')
            
            # Check if they're valid numbers
            try:
                lat_float = float(lat) if lat is not None else None
                lng_float = float(lng) if lng is not None else None
                print(f'Latitude as float: {lat_float}')
                print(f'Longitude as float: {lng_float}')
                
                if lat_float and lng_float:
                    print('✅ Coordinates are valid numbers')
                else:
                    print('❌ Coordinates are invalid (None or NaN)')
                    
            except (ValueError, TypeError) as e:
                print(f'❌ Error converting coordinates: {e}')
            
            # Test a few more locations
            print('\n🌍 Testing other locations:')
            print('=' * 50)
            for i, location in enumerate(data[:3]):
                name = location.get('location', 'Unknown')
                lat = location.get('latitude')
                lng = location.get('longitude')
                print(f'{name}: lat={lat}, lng={lng}')
                
        else:
            print('❌ Gachibowli not found')
    else:
        print(f'❌ Error: {response.status_code}')

if __name__ == "__main__":
    debug_coordinates()