"""
Telangana Market Value Scraper - Price Data Extractor
=====================================================
Extracts actual property prices per sq yard for all locations
"""

import asyncio
import aiohttp
import json
import csv
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

BASE_URL = "https://registration.telangana.gov.in"

# Key districts for Hyderabad metro area
DISTRICTS = {
    "RANGAREDDY": "15_1",
    "MEDCHAL-MALKAJGIRI": "15_2", 
    "SANGAREDDY": "17_2",
}

class MarketValueScraper:
    def __init__(self):
        self.session = None
        self.market_values = []
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": f"{BASE_URL}/UnitRateMV/getDistrictList.htm",
            "Content-Type": "application/x-www-form-urlencoded",
        }
    
    def parse_list_response(self, text):
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
    
    def parse_market_value_table(self, html, location_info):
        """Parse market value HTML table"""
        values = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all tables
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        try:
                            # Different table formats
                            classification = cells[0].get_text(strip=True)
                            value_text = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                            unit = cells[2].get_text(strip=True) if len(cells) > 2 else "Sq.Yd"
                            effective = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                            
                            # Skip headers/empty
                            if not value_text or classification.lower() in ['classification', 'type', 's.no', 'sl.no']:
                                continue
                            
                            # Parse value
                            value_clean = re.sub(r'[^\d.]', '', value_text)
                            if value_clean:
                                value = float(value_clean)
                                if value > 0:
                                    values.append({
                                        **location_info,
                                        "classification": classification,
                                        "value_per_unit": value,
                                        "unit": unit,
                                        "effective_from": effective,
                                        "scraped_at": datetime.now().isoformat()
                                    })
                        except:
                            continue
        except Exception as e:
            print(f"  ⚠️ Parse error: {e}")
        
        return values
    
    async def fetch_market_values(self, session, district_code, district_name, 
                                   mandal_code, mandal_name, village_code, village_name):
        """Fetch market values for a specific location"""
        try:
            # Build form data
            form_data = {
                "districtId": district_code,
                "mandalCode": mandal_code,
                "villageCode": village_code,
                "divCode": "",
                "locality": "",
                "locName": "",
                "mndlName": mandal_name,
                "vlgName": village_name,
                "search_by": "L",
                "RateType": "U",
                "rValue": "U",
                "tFlag": "",
            }
            
            url = f"{BASE_URL}/UnitRateMV/unitRateMV"
            
            async with session.post(url, data=form_data) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    
                    location_info = {
                        "district": district_name,
                        "district_code": district_code,
                        "mandal": mandal_name,
                        "mandal_code": mandal_code,
                        "village": village_name,
                        "village_code": village_code,
                        "rate_type": "Non-Agriculture"
                    }
                    
                    values = self.parse_market_value_table(html, location_info)
                    self.market_values.extend(values)
                    return values
        except Exception as e:
            print(f"    ⚠️ Error fetching {village_name}: {e}")
        
        return []
    
    async def get_mandals(self, session, district_code):
        """Get mandals for district"""
        url = f"{BASE_URL}/UnitRateMV/getMandalListByDistCode"
        try:
            async with session.get(url, params={"districtcode": district_code}) as resp:
                if resp.status == 200:
                    return self.parse_list_response(await resp.text())
        except:
            pass
        return []
    
    async def get_villages(self, session, district_code, mandal_code):
        """Get villages for mandal"""
        url = f"{BASE_URL}/UnitRateMV/getVillageListByDistCode"
        params = {"districtcode": district_code, "mandalcode": mandal_code, "sType": "U"}
        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    return self.parse_list_response(await resp.text())
        except:
            pass
        return []
    
    async def run(self, districts_to_scrape=None, villages_per_mandal=5):
        """Main scraper"""
        print("""
╔═══════════════════════════════════════════════════════════════════╗
║      TELANGANA MARKET VALUE SCRAPER - PRICE EXTRACTOR             ║
║                                                                   ║
║  Extracting: Property Prices per Sq.Yard                          ║
║  Source: https://registration.telangana.gov.in/                   ║
╚═══════════════════════════════════════════════════════════════════╝
        """)
        
        if districts_to_scrape is None:
            districts_to_scrape = DISTRICTS
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            for district_name, district_code in districts_to_scrape.items():
                print(f"\n📍 Processing: {district_name}")
                
                mandals = await self.get_mandals(session, district_code)
                print(f"  Found {len(mandals)} mandals")
                
                for mandal in mandals[:5]:  # Limit mandals for demo
                    print(f"  📌 {mandal['name']}")
                    
                    villages = await self.get_villages(session, district_code, mandal['code'])
                    
                    for village in villages[:villages_per_mandal]:
                        values = await self.fetch_market_values(
                            session, district_code, district_name,
                            mandal['code'], mandal['name'],
                            village['code'], village['name']
                        )
                        if values:
                            print(f"      ✓ {village['name']}: {len(values)} price records")
                        else:
                            print(f"      • {village['name']}: checking...")
                        
                        await asyncio.sleep(0.3)
                    
                    await asyncio.sleep(0.5)
        
        # Export results
        self.export_results()
        
        return self.market_values
    
    def export_results(self):
        """Export market values to files"""
        output_dir = Path(__file__).parent.parent / "scraped_data"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON export
        json_file = output_dir / f"market_values_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "source": "https://registration.telangana.gov.in",
                "extracted_at": datetime.now().isoformat(),
                "total_records": len(self.market_values),
                "market_values": self.market_values
            }, f, indent=2, ensure_ascii=False)
        
        # CSV export
        csv_file = output_dir / f"market_values_{timestamp}.csv"
        if self.market_values:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.market_values[0].keys())
                writer.writeheader()
                writer.writerows(self.market_values)
        
        print(f"\n{'='*70}")
        print("📊 MARKET VALUE EXTRACTION COMPLETE!")
        print(f"{'='*70}")
        print(f"  Total Price Records: {len(self.market_values)}")
        print(f"\n📁 Output Files:")
        print(f"  • {json_file}")
        print(f"  • {csv_file}")
        print(f"{'='*70}")
        
        # Show sample
        if self.market_values:
            print("\n📋 SAMPLE PRICE DATA:")
            print("-"*70)
            for mv in self.market_values[:10]:
                print(f"  {mv['district']} > {mv['mandal']} > {mv['village']}")
                print(f"    Classification: {mv['classification']}")
                print(f"    Price: ₹{mv['value_per_unit']:,.2f} per {mv['unit']}")
                print()


async def main():
    scraper = MarketValueScraper()
    await scraper.run(villages_per_mandal=3)


if __name__ == "__main__":
    # Install beautifulsoup4 if needed
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        import subprocess
        subprocess.run(["pip", "install", "beautifulsoup4", "--quiet"])
    
    asyncio.run(main())
