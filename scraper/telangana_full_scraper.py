"""
Telangana Full 33-District Scraper
==================================
Scrapes ALL districts and loads into database
"""

import asyncio
import aiohttp
import json
import re
import psycopg2
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://registration.telangana.gov.in"

# All 33 Districts
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

class FullDistrictScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": f"{BASE_URL}/UnitRateMV/getDistrictList.htm",
        }
        self.conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            port=os.getenv("DB_PORT", "5432")
        )
        self.cur = self.conn.cursor()
        self.stats = {"districts": 0, "mandals": 0, "villages": 0, "prices": 0}
    
    def parse_list(self, text):
        if not text or text in ["Malicious", "Special"]:
            return []
        items = []
        for part in text.split("##"):
            if "/" in part:
                code, name = part.split("/", 1)
                items.append({"code": code.strip(), "name": name.strip()})
        return items
    
    def parse_prices(self, html):
        """Parse market value HTML"""
        prices = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            for table in soup.find_all('table'):
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 4:
                        try:
                            classification = cells[1].get_text(strip=True)
                            price_text = cells[3].get_text(strip=True)
                            if classification.lower() not in ['classification', 's.no', 'type']:
                                price = float(re.sub(r'[^\d.]', '', price_text) or 0)
                                if price > 0:
                                    prices.append({"classification": classification, "price": price})
                        except:
                            pass
        except:
            pass
        return prices
    
    async def fetch(self, session, url, params=None, data=None):
        try:
            if data:
                async with session.post(url, data=data, timeout=aiohttp.ClientTimeout(total=15)) as r:
                    return await r.text() if r.status == 200 else ""
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as r:
                return await r.text() if r.status == 200 else ""
        except:
            return ""
    
    async def scrape_district(self, session, dist_name, dist_code):
        """Scrape one district completely"""
        print(f"\n📍 {dist_name} ({dist_code})")
        
        # Skip Hyderabad (needs special handling)
        if dist_code.startswith("16_"):
            print("   ⏭️ Skipping (requires locality search)")
            return
        
        # Get mandals
        url = f"{BASE_URL}/UnitRateMV/getMandalListByDistCode"
        text = await self.fetch(session, url, params={"districtcode": dist_code})
        mandals = self.parse_list(text)
        print(f"   Found {len(mandals)} mandals")
        
        for mandal in mandals:
            m_name, m_code = mandal["name"], mandal["code"]
            
            # Insert mandal
            self.cur.execute("""
                INSERT INTO telangana_mandals (name, code, district_name, district_code)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (code, district_code) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
            """, (m_name, m_code, dist_name, dist_code))
            mandal_id = self.cur.fetchone()[0]
            self.stats["mandals"] += 1
            
            # Get villages
            url = f"{BASE_URL}/UnitRateMV/getVillageListByDistCode"
            text = await self.fetch(session, url, params={
                "districtcode": dist_code, "mandalcode": m_code, "sType": "U"
            })
            villages = self.parse_list(text)
            
            for village in villages:
                v_name, v_code = village["name"], village["code"]
                
                # Insert village
                self.cur.execute("""
                    INSERT INTO telangana_villages (name, code, mandal_id, mandal_name, mandal_code, district_name, district_code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (code, mandal_code, district_code) DO UPDATE SET name = EXCLUDED.name
                """, (v_name, v_code, mandal_id, m_name, m_code, dist_name, dist_code))
                self.stats["villages"] += 1
                
                # Get market values
                url = f"{BASE_URL}/UnitRateMV/unitRateMV"
                form_data = {
                    "districtId": dist_code, "mandalCode": m_code, "villageCode": v_code,
                    "mndlName": m_name, "vlgName": v_name, "search_by": "L",
                    "RateType": "U", "rValue": "U"
                }
                html = await self.fetch(session, url, data=form_data)
                prices = self.parse_prices(html)
                
                for p in prices:
                    self.cur.execute("""
                        INSERT INTO telangana_market_values 
                        (district, district_code, mandal, mandal_code, village, village_code,
                         classification, price_per_sqyd, rate_type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (village_code, classification, rate_type) 
                        DO UPDATE SET price_per_sqyd = EXCLUDED.price_per_sqyd
                    """, (dist_name, dist_code, m_name, m_code, v_name, v_code,
                          p["classification"], p["price"], "Non-Agriculture"))
                    self.stats["prices"] += 1
                
                await asyncio.sleep(0.2)
            
            self.conn.commit()
            print(f"   ✓ {m_name}: {len(villages)} villages")
            await asyncio.sleep(0.3)
        
        self.stats["districts"] += 1
    
    async def run(self):
        print("""
╔═══════════════════════════════════════════════════════════════════╗
║     TELANGANA FULL 33-DISTRICT SCRAPER                            ║
║     Source: registration.telangana.gov.in                         ║
╚═══════════════════════════════════════════════════════════════════╝
        """)
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            for dist_name, dist_code in DISTRICTS.items():
                try:
                    await self.scrape_district(session, dist_name, dist_code)
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                await asyncio.sleep(0.5)
        
        self.conn.commit()
        self.print_summary()
        self.conn.close()
    
    def print_summary(self):
        print("\n" + "="*60)
        print("📊 SCRAPING COMPLETE!")
        print("="*60)
        print(f"  Districts: {self.stats['districts']}")
        print(f"  Mandals:   {self.stats['mandals']}")
        print(f"  Villages:  {self.stats['villages']}")
        print(f"  Prices:    {self.stats['prices']}")
        print("="*60)

if __name__ == "__main__":
    scraper = FullDistrictScraper()
    asyncio.run(scraper.run())
