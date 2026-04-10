#!/usr/bin/env python3
"""
Update Bangalore locations table to match the provided unique list
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Your FINAL unique Bangalore locations list
UNIQUE_BANGALORE_LOCATIONS = {
    34: "Bengaluru Urban",
    45: "Attibele",
    49: "Bagalur",
    51: "Balagere",
    55: "Bannerghatta Road",
    57: "Begur",
    58: "Bellandur",
    60: "Bhoganahalli",
    65: "Budigere Cross",
    74: "Choodasandra",
    77: "Devanahalli",
    78: "Doddaballapura Road",
    79: "Dommasandra",
    82: "Electronic City",
    93: "Gunjur",
    100: "Hebbal",
    101: "Hennur",
    105: "ITPL",
    106: "IVC Road",
    108: "Indiranagar",
    111: "JP Nagar",
    112: "Jakkur",
    115: "KR Puram",
    120: "Kanakapura Road",
    130: "Kodathi",
    131: "Kogilu",
    136: "Koramangala",
    169: "Mysore Road",
    182: "Old Airport Road",
    183: "Old Madras Road",
    201: "Rajajinagar",
    209: "Sarjapur",
    210: "Sarjapur Road",
    212: "Seegehalli",
    227: "Thanisandra Road",
    235: "Varthur",
    237: "Whitefield",
    240: "Yelahanka",
    241: "Yeshwanthpur",
    265: "Agara",
    266: "Anugondanahalli",
    267: "Aerospace",
    268: "Aerospace Park",
    269: "Agrahara",
    270: "Akshaya Nagar",
    272: "Anekal",
    273: "Anjanapura",
    274: "Bidarahalli",
    276: "Bommanahalli",
    278: "Banashankari",
    282: "Belahalli",
    283: "Belathur",
    284: "Bellahalli",
    286: "Bettahalasuru",
    287: "Bidadi",
    288: "Binnypet",
    289: "Bommasandra",
    290: "Bommenahalli",
    292: "Bovipalya",
    293: "Budigere",
    294: "Budigere Road",
    295: "Bukkasagara",
    296: "Byrathi",
    297: "Chambenahalli",
    298: "Chikkanayakanahalli",
    299: "Carmelaram",
    300: "Chandapura",
    301: "Chikkabanahalli",
    302: "Chikkagubbi",
    303: "Chokkanahalli",
    304: "Chowdenahalli",
    305: "Defence & Aerospace Park",
    306: "Doddaballapura",
    307: "Doddakannelli",
    308: "Dollars Colony",
    309: "Dommasandra Road",
    310: "Electronic City Phase 1",
    311: "Electronic City Phase 2",
    313: "Gattahalli",
    314: "Geddalahalli",
    315: "Gollahalli",
    316: "Gottigere",
    317: "Govindaraja Nagar",
    318: "Guddahatti",
    319: "Hesaraghatta",
    320: "Hosahalli",
    321: "HSR Layout",
    322: "Harohalli",
    323: "Hennur Main Road",
    326: "Horamavu",
    327: "Hoskote",
    328: "Hulimangala",
    330: "Industrial Area",
    332: "Jayanagar",
    334: "Kannamangala",
    337: "Kyalasanahalli",
    338: "Kadubeesanahalli",
    339: "Kadugondanahalli",
    340: "Kalkere",
    341: "Kammanahalli",
    342: "Kasavanahalli",
    343: "Kempapura",
    344: "Kempapura Agrahara",
    345: "Kengeri",
    347: "Kodigehalli",
    348: "Kodigenahalli",
    349: "Konadasapura",
    351: "Krishnarajapura",
    353: "Krishnasagara",
    354: "Kudlu",
    357: "MG Road",
    358: "Madiwala",
    360: "Mahadevapura",
    361: "Mallasandra",
    362: "Malleshwaram",
    363: "Maragondanahalli",
    364: "Marathahalli",
    365: "Marsur",
    366: "Mathikere",
    367: "Nagondanahalli",
    368: "Narayanaghatta",
    369: "Nagawara",
    371: "Narasapura",
    373: "Padmanabhanagar",
    374: "Panathur",
    375: "Panathur Main Road",
    378: "RMV 2nd Stage",
    379: "RR Nagar",
    380: "Rajarajeshwari Nagar",
    382: "Rajanukunte",
    384: "Ramanagara",
    388: "Sadashivanagar",
    389: "Sahakar Nagar",
    391: "Samethanahalli",
    392: "Sampangiram Nagar",
    394: "Singasandra",
    395: "Sompura",
    396: "Sriramapura",
    397: "St. John's Road",
    398: "Subramanyapura",
    399: "Thubarahalli",
    400: "Thanisandra",
    401: "Thanisandra Main Road",
    402: "Thirupalya",
    403: "Uttarahalli",
    407: "Vajarahalli",
    408: "Veerasandra",
    409: "Vignana Kendra",
    410: "Vijayanagar",
    414: "Yadavanahalli",
    415: "Yelahanka New Town",
    416: "Yelenahalli",
    417: "Yeshwanthpur",
    418: "Ittamadu",
    419: "Jakkur",
    420: "Marenahalli"
}

def update_bangalore_locations():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    print("🔄 Updating Bangalore locations to match unique list...")
    print("="*60)
    print(f"📋 Target: {len(UNIQUE_BANGALORE_LOCATIONS)} unique locations")
    
    # Step 1: Get current Bangalore locations
    try:
        url = f"{supabase_url}/rest/v1/locations"
        params = {'select': 'id,name,city', 'city': 'eq.Bangalore'}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch locations: {response.status_code}")
            return
        
        current_locations = response.json()
        current_ids = {loc['id']: loc['name'] for loc in current_locations}
        
        print(f"💾 Current database: {len(current_locations)} Bangalore locations")
        
        # Step 2: Find locations to delete (in DB but not in unique list)
        to_delete = [loc_id for loc_id in current_ids.keys() if loc_id not in UNIQUE_BANGALORE_LOCATIONS]
        
        print(f"\n🗑️  Locations to DELETE: {len(to_delete)}")
        if to_delete:
            for loc_id in sorted(to_delete):
                print(f"   - ID {loc_id}: {current_ids[loc_id]}")
        
        # Step 3: Find locations to update (name mismatch)
        to_update = []
        for loc_id, target_name in UNIQUE_BANGALORE_LOCATIONS.items():
            if loc_id in current_ids and current_ids[loc_id] != target_name:
                to_update.append((loc_id, current_ids[loc_id], target_name))
        
        print(f"\n✏️  Locations to UPDATE: {len(to_update)}")
        if to_update:
            for loc_id, old_name, new_name in to_update:
                print(f"   - ID {loc_id}: '{old_name}' → '{new_name}'")
        
        # Step 4: Find locations to add (in unique list but not in DB)
        to_add = [loc_id for loc_id in UNIQUE_BANGALORE_LOCATIONS.keys() if loc_id not in current_ids]
        
        print(f"\n➕ Locations to ADD: {len(to_add)}")
        if to_add:
            for loc_id in sorted(to_add):
                print(f"   - ID {loc_id}: {UNIQUE_BANGALORE_LOCATIONS[loc_id]}")
        
        # Confirm before proceeding
        print(f"\n" + "="*60)
        print(f"⚠️  SUMMARY:")
        print(f"   Delete: {len(to_delete)} locations")
        print(f"   Update: {len(to_update)} locations")
        print(f"   Add: {len(to_add)} locations")
        print(f"   Final count: {len(UNIQUE_BANGALORE_LOCATIONS)} locations")
        print("="*60)
        
        confirm = input("\n❓ Proceed with updates? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Aborted by user")
            return
        
        # Execute deletions
        if to_delete:
            print(f"\n🗑️  Deleting {len(to_delete)} locations...")
            delete_headers = headers.copy()
            delete_headers['Prefer'] = 'return=minimal'
            for loc_id in to_delete:
                delete_url = f"{supabase_url}/rest/v1/locations?id=eq.{loc_id}"
                response = requests.delete(delete_url, headers=delete_headers)
                if response.status_code in [200, 204]:
                    print(f"   ✅ Deleted ID {loc_id}")
                else:
                    print(f"   ❌ Failed to delete ID {loc_id}: {response.status_code} - {response.text}")
        
        # Execute updates
        if to_update:
            print(f"\n✏️  Updating {len(to_update)} locations...")
            for loc_id, old_name, new_name in to_update:
                update_url = f"{supabase_url}/rest/v1/locations"
                params = {'id': f'eq.{loc_id}'}
                body = {'name': new_name}
                response = requests.patch(update_url, headers=headers, params=params, json=body)
                if response.status_code == 200:
                    print(f"   ✅ Updated ID {loc_id}")
                else:
                    print(f"   ❌ Failed to update ID {loc_id}: {response.status_code}")
        
        # Note about additions
        if to_add:
            print(f"\n➕ Note: {len(to_add)} locations need to be added")
            print(f"   These IDs don't exist in the database yet.")
            print(f"   You may need to insert them with proper coordinates and city='Bangalore'")
        
        print(f"\n✅ Update complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_bangalore_locations()
