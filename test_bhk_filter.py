"""
Test the new BHK filtering functionality
"""

import requests

# Test the API endpoint
base_url = "http://localhost:8000"

print("Testing BHK filtering API...")

# Test 1: All properties in Hitec City
print("\n1. All properties in Hitec City:")
response = requests.get(f"{base_url}/api/v1/properties?area=Hitec City")
if response.status_code == 200:
    properties = response.json()
    print(f"   Total properties: {len(properties)}")
    
    # Count BHK distribution
    bhk_counts = {}
    for prop in properties:
        bhk = prop.get('bhk', 'Unknown')
        bhk_counts[bhk] = bhk_counts.get(bhk, 0) + 1
    
    print("   BHK distribution:")
    for bhk, count in sorted(bhk_counts.items()):
        print(f"     {bhk} BHK: {count} units")
else:
    print(f"   Error: {response.status_code}")

# Test 2: Only 2 BHK properties
print("\n2. Only 2 BHK properties in Hitec City:")
response = requests.get(f"{base_url}/api/v1/properties?area=Hitec City&bhk=2")
if response.status_code == 200:
    properties = response.json()
    print(f"   Total 2 BHK properties: {len(properties)}")
    
    # Verify all are 2 BHK
    non_2bhk = [prop for prop in properties if str(float(prop.get('bhk', 0))) != '2.0']
    if non_2bhk:
        print(f"   WARNING: Found {len(non_2bhk)} non-2BHK properties!")
    else:
        print("   ✅ All properties are 2 BHK")
else:
    print(f"   Error: {response.status_code}")

# Test 3: Only 3 BHK properties
print("\n3. Only 3 BHK properties in Hitec City:")
response = requests.get(f"{base_url}/api/v1/properties?area=Hitec City&bhk=3")
if response.status_code == 200:
    properties = response.json()
    print(f"   Total 3 BHK properties: {len(properties)}")
    
    # Verify all are 3 BHK
    non_3bhk = [prop for prop in properties if str(prop.get('bhk', '')) != '3']
    if non_3bhk:
        print(f"   WARNING: Found {len(non_3bhk)} non-3BHK properties!")
    else:
        print("   ✅ All properties are 3 BHK")
else:
    print(f"   Error: {response.status_code}")

print("\nBHK filtering test complete!")