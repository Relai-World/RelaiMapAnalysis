import requests
import json

print("=" * 60)
print("🧪 TESTING ALL API ENDPOINTS")
print("=" * 60)

BASE_URL = "http://127.0.0.1:8000"

# Test 1: Health Check
print("\n1️⃣  Testing: GET /")
try:
    response = requests.get(f"{BASE_URL}/", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Get All Insights
print("\n2️⃣  Testing: GET /api/v1/insights")
try:
    response = requests.get(f"{BASE_URL}/api/v1/insights", timeout=5)
    print(f"   Status: {response.status_code}")
    data = response.json()
    if isinstance(data, list):
        print(f"   Found {len(data)} locations")
        if len(data) > 0:
            print(f"   Sample: {json.dumps(data[0], indent=2)}")
    else:
        print(f"   Response: {json.dumps(data, indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Get Price Trends
print("\n3️⃣  Testing: GET /api/v1/location/1/trends")
try:
    response = requests.get(f"{BASE_URL}/api/v1/location/1/trends", timeout=5)
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Found {len(data)} data points")
    if len(data) > 0:
        print(f"   Sample: {json.dumps(data[0], indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Get All Location Costs
print("\n4️⃣  Testing: GET /api/v1/location-costs")
try:
    response = requests.get(f"{BASE_URL}/api/v1/location-costs", timeout=5)
    print(f"   Status: {response.status_code}")
    data = response.json()
    if isinstance(data, list):
        print(f"   Found {len(data)} locations with cost data")
        if len(data) > 0:
            print(f"   Sample: {json.dumps(data[0], indent=2)}")
    else:
        print(f"   Response: {json.dumps(data, indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Get Specific Location Cost
print("\n5️⃣  Testing: GET /api/v1/location-costs/Gachibowli")
try:
    response = requests.get(f"{BASE_URL}/api/v1/location-costs/Gachibowli", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 6: Get Infrastructure (slower - uses Overpass API)
print("\n6️⃣  Testing: GET /api/v1/location/1/infra (may take 2-3 seconds)")
try:
    response = requests.get(f"{BASE_URL}/api/v1/location/1/infra", timeout=10)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ API TESTING COMPLETE")
print("=" * 60)
