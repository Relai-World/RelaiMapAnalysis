"""
Quick Property Data Extractor - Telangana Registration
======================================================
Fast extraction of market values and area data
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from pathlib import Path
import csv

BASE_URL = "https://registration.telangana.gov.in"

# All Districts
DISTRICTS = {
    "ADILABAD": "19_1", "BHADRADRI KOTHAGUDEM": "22_2", "HANUMAKONDA": "21_1",
    "HYDERABAD": "16_1", "JAGTIAL": "20_2", "JANGOAN": "21_3",
    "JAYASHANKAR BHOOPALPALLY": "21_4", "JOGULAMBA GADWAL": "14_2",
    "KAMAREDDY": "18_2", "KARIMNAGAR": "20_1", "KHAMMAM": "22_1",
    "KOMARAM BHEEM ASIFABAD": "19_4", "MAHABUBABAD": "21_5",
    "MAHABUBNAGAR": "14_1", "MANCHERIAL": "19_3", "MEDAK": "17_1",
    "MEDCHAL-MALKAJGIRI": "15_2", "MULUGU": "21_6", "NAGARKURNOOL": "14_3",
    "NALGONDA": "23_1", "NARAYANPET": "14_5", "NIRMAL": "19_2",
    "NIZAMABAD": "18_1", "PEDDAPALLI": "20_4", "RAJANNA SIRCILLA": "20_3",
    "RANGAREDDY": "15_1", "SANGAREDDY": "17_2", "SIDDIPET": "17_3",
    "SURYAPET": "23_2", "VIKARABAD": "15_3", "WANAPARTHY": "14_4",
    "WARANGAL": "21_2", "YADADRI BHUVANAGIRI": "23_3",
}

def parse_response(text):
    """Parse ##-delimited response"""
    if not text or text in ["Malicious", "Special"]:
        return []
    items = []
    for part in text.split("##"):
        part = part.strip()
        if "/" in part:
            code, name = part.split("/", 1)
            items.append({"code": code.strip(), "name": name.strip()})
    return items

async def fetch(session, url, params=None):
    """Async fetch with error handling"""
    try:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                return await resp.text()
    except Exception as e:
        print(f"  ⚠️ Error: {e}")
    return ""

async def get_mandals(session, district_code):
    """Get mandals for a district"""
    url = f"{BASE_URL}/UnitRateMV/getMandalListByDistCode"
    text = await fetch(session, url, {"districtcode": district_code})
    return parse_response(text)

async def get_villages(session, district_code, mandal_code, rate_type="U"):
    """Get villages for a mandal"""
    url = f"{BASE_URL}/UnitRateMV/getVillageListByDistCode"
    params = {"districtcode": district_code, "mandalcode": mandal_code, "sType": rate_type}
    text = await fetch(session, url, params)
    return parse_response(text)

async def extract_district_data(session, district_name, district_code):
    """Extract all data for a district"""
    print(f"\n📍 {district_name} ({district_code})")
    
    # Skip Hyderabad for now (needs special handling)
    if district_code.startswith("16_"):
        print("  ⏭️  Skipping Hyderabad (requires special locality search)")
        return {"district": district_name, "code": district_code, "mandals": [], "note": "Requires special handling"}
    
    mandals = await get_mandals(session, district_code)
    print(f"  📌 Found {len(mandals)} mandals")
    
    district_data = {
        "district": district_name,
        "code": district_code,
        "mandals": []
    }
    
    for mandal in mandals[:10]:  # Limit for demo
        villages = await get_villages(session, district_code, mandal["code"])
        mandal_data = {
            "mandal": mandal["name"],
            "code": mandal["code"],
            "villages": villages[:20]  # Limit for demo
        }
        district_data["mandals"].append(mandal_data)
        print(f"    • {mandal['name']}: {len(villages)} villages")
        await asyncio.sleep(0.3)
    
    return district_data

async def main():
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║      TELANGANA REGISTRATION - QUICK DATA EXTRACTOR                ║
║                                                                   ║
║  Extracting: Districts → Mandals → Villages                       ║
║  Source: https://registration.telangana.gov.in/                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"{BASE_URL}/UnitRateMV/getDistrictList.htm",
    }
    
    all_data = {
        "source": "https://registration.telangana.gov.in",
        "extracted_at": datetime.now().isoformat(),
        "total_districts": len(DISTRICTS),
        "districts": []
    }
    
    # Focus districts (Hyderabad metro area)
    focus_districts = ["RANGAREDDY", "MEDCHAL-MALKAJGIRI", "SANGAREDDY", "NALGONDA", "KARIMNAGAR"]
    
    async with aiohttp.ClientSession(headers=headers) as session:
        print(f"🚀 Extracting data from {len(focus_districts)} key districts...\n")
        
        for dist_name in focus_districts:
            if dist_name in DISTRICTS:
                data = await extract_district_data(session, dist_name, DISTRICTS[dist_name])
                all_data["districts"].append(data)
                await asyncio.sleep(0.5)
    
    # Calculate stats
    total_mandals = sum(len(d.get("mandals", [])) for d in all_data["districts"])
    total_villages = sum(
        sum(len(m.get("villages", [])) for m in d.get("mandals", []))
        for d in all_data["districts"]
    )
    
    # Save data
    output_dir = Path(__file__).parent.parent / "scraped_data"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON output
    json_file = output_dir / f"telangana_hierarchy_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    
    # CSV output - flat structure
    csv_file = output_dir / f"telangana_areas_{timestamp}.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["District", "District_Code", "Mandal", "Mandal_Code", "Village", "Village_Code"])
        for district in all_data["districts"]:
            for mandal in district.get("mandals", []):
                for village in mandal.get("villages", []):
                    writer.writerow([
                        district["district"], district["code"],
                        mandal["mandal"], mandal["code"],
                        village["name"], village["code"]
                    ])
    
    # Print summary
    print("\n" + "="*70)
    print("📊 EXTRACTION COMPLETE!")
    print("="*70)
    print(f"  Districts:  {len(all_data['districts'])}")
    print(f"  Mandals:    {total_mandals}")
    print(f"  Villages:   {total_villages}")
    print(f"\n📁 Output Files:")
    print(f"  • {json_file}")
    print(f"  • {csv_file}")
    print("="*70)
    
    # Show sample data
    print("\n📋 SAMPLE DATA:")
    print("-"*70)
    for dist in all_data["districts"][:2]:
        print(f"\n🏛️ {dist['district']}:")
        for mandal in dist.get("mandals", [])[:3]:
            villages_preview = ", ".join([v["name"] for v in mandal.get("villages", [])[:5]])
            print(f"   📌 {mandal['mandal']}: {villages_preview}...")
    
    return all_data

if __name__ == "__main__":
    asyncio.run(main())
