"""
Fetch sample property and location data to visualize what's available for comparison
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def fetch_sample_properties():
    """Fetch 3 sample properties from different areas"""
    url = f"{SUPABASE_URL}/rest/v1/unified_data_DataType_Raghu"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    # Get 3 properties from different popular areas
    params = {
        "select": "*",
        "city": "eq.Hyderabad",
        "limit": 3,
        "offset": 100  # Skip first 100 to get variety
    }
    
    response = requests.get(url, headers=headers, params=params)
    return response.json()

def fetch_location_data(location_name):
    """Fetch location insights for a given area"""
    # First get location ID
    url = f"{SUPABASE_URL}/rest/v1/locations"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    
    params = {
        "select": "id,name,city,geom",
        "name": f"ilike.%{location_name}%",
        "limit": 1
    }
    
    response = requests.get(url, headers=headers, params=params)
    locations = response.json()
    
    if not locations:
        return None
    
    location_id = locations[0]['id']
    
    # Get location insights
    url = f"{SUPABASE_URL}/rest/v1/location_insights"
    params = {
        "select": "*",
        "location_id": f"eq.{location_id}",
        "limit": 1
    }
    
    response = requests.get(url, headers=headers, params=params)
    insights = response.json()
    
    return {
        "location": locations[0],
        "insights": insights[0] if insights else None
    }

def visualize_data():
    """Fetch and visualize sample data"""
    print("="*80)
    print("🔍 FETCHING SAMPLE DATA FOR COMPARISON FEATURE")
    print("="*80)
    
    # Fetch properties
    print("\n📦 Fetching sample properties...")
    properties = fetch_sample_properties()
    
    print(f"\n✅ Found {len(properties)} properties\n")
    
    for i, prop in enumerate(properties, 1):
        print(f"\n{'='*80}")
        print(f"PROPERTY {i}: {prop.get('projectname', 'Unknown')}")
        print(f"{'='*80}")
        
        # Basic Info
        print(f"\n📋 BASIC INFO:")
        print(f"  • ID: {prop.get('id')}")
        print(f"  • Builder: {prop.get('buildername')}")
        print(f"  • Area: {prop.get('areaname')}")
        print(f"  • City: {prop.get('city')}")
        print(f"  • BHK: {prop.get('bhk')}")
        
        # Pricing
        print(f"\n💰 PRICING:")
        print(f"  • Price/sqft: ₹{prop.get('price_per_sft', 'N/A')}")
        print(f"  • Base Price: ₹{prop.get('baseprojectprice', 'N/A')} Cr")
        print(f"  • Sqft: {prop.get('sqfeet')}")
        
        # Specifications
        print(f"\n📐 SPECIFICATIONS:")
        print(f"  • Carpet Area %: {prop.get('carpet_area_percentage')}")
        print(f"  • Floor Height: {prop.get('floor_to_ceiling_height')}")
        print(f"  • Parking: {prop.get('no_of_car_parkings')}")
        print(f"  • Facing: {prop.get('facing')}")
        
        # Project Details
        print(f"\n🏗️ PROJECT:")
        print(f"  • Type: {prop.get('project_type')}")
        print(f"  • Status: {prop.get('construction_status')}")
        print(f"  • Possession: {prop.get('possession_date')}")
        print(f"  • RERA: {prop.get('rera_number')}")
        print(f"  • Towers: {prop.get('number_of_towers')}")
        print(f"  • Floors: {prop.get('number_of_floors')}")
        print(f"  • Open Space: {prop.get('open_space')}%")
        
        # Builder Info
        print(f"\n👷 BUILDER:")
        print(f"  • Age: {prop.get('builder_age')} years")
        print(f"  • Completed: {prop.get('builder_completed_properties')} projects")
        print(f"  • Ongoing: {prop.get('builder_ongoing_projects')} projects")
        print(f"  • Total: {prop.get('builder_total_properties')} projects")
        
        # Amenities
        print(f"\n🏊 AMENITIES:")
        amenities = prop.get('external_amenities', '')
        if amenities:
            amenities_list = [a.strip() for a in amenities.split(',')[:5]]
            for amenity in amenities_list:
                print(f"  • {amenity}")
            if len(amenities.split(',')) > 5:
                print(f"  • ... and {len(amenities.split(',')) - 5} more")
        else:
            print("  • No amenities data")
        
        # Coordinates
        print(f"\n📍 LOCATION:")
        print(f"  • Coordinates: {prop.get('google_place_location', 'N/A')}")
        
        # Fetch location insights
        area_name = prop.get('areaname')
        if area_name:
            print(f"\n🎯 FETCHING LOCATION INSIGHTS FOR: {area_name}")
            location_data = fetch_location_data(area_name)
            
            if location_data and location_data['insights']:
                insights = location_data['insights']
                print(f"\n  📊 LOCATION SCORES:")
                print(f"    • Connectivity: {insights.get('connectivity_score', 'N/A')}/10")
                print(f"    • Amenities: {insights.get('amenities_score', 'N/A')}/10")
                print(f"    • Growth: {insights.get('growth_score', 'N/A')}/10")
                print(f"    • Investment: {insights.get('investment_score', 'N/A')}/10")
                print(f"    • Sentiment: {insights.get('avg_sentiment_score', 'N/A')}")
                
                print(f"\n  📝 SUMMARIES:")
                print(f"    • Sentiment: {insights.get('sentiment_summary', 'N/A')[:100]}...")
                print(f"    • Growth: {insights.get('growth_summary', 'N/A')[:100]}...")
                print(f"    • Investment: {insights.get('invest_summary', 'N/A')[:100]}...")
            else:
                print(f"  ⚠️ No location insights found for {area_name}")
    
    # Save to JSON for visualization
    print(f"\n\n{'='*80}")
    print("💾 SAVING DATA TO comparison_sample_data.json")
    print(f"{'='*80}")
    
    output = {
        "properties": properties,
        "location_data": {}
    }
    
    for prop in properties:
        area_name = prop.get('areaname')
        if area_name:
            location_data = fetch_location_data(area_name)
            if location_data:
                output["location_data"][area_name] = location_data
    
    with open('comparison_sample_data.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n✅ Data saved! You can now visualize what's available for comparison.")
    
    # Print summary
    print(f"\n\n{'='*80}")
    print("📊 DATA AVAILABILITY SUMMARY")
    print(f"{'='*80}")
    
    print("\n✅ AVAILABLE FOR COMPARISON:")
    print("  Property Level:")
    print("    • Pricing (price/sqft, base price)")
    print("    • Specifications (BHK, carpet area, parking, facing)")
    print("    • Project details (type, status, possession, RERA)")
    print("    • Builder info (age, completed projects, track record)")
    print("    • Amenities list")
    print("    • Coordinates")
    
    print("\n  Location Level:")
    has_insights = any(output["location_data"].get(area, {}).get('insights') for area in output["location_data"])
    if has_insights:
        print("    • Connectivity score")
        print("    • Amenities score")
        print("    • Growth score")
        print("    • Investment score")
        print("    • Sentiment analysis")
        print("    • AI-generated summaries")
    else:
        print("    ⚠️ Limited location insights available")
    
    print(f"\n{'='*80}")

if __name__ == "__main__":
    visualize_data()
