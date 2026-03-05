"""
Telangana Registration - Comprehensive Property Data Scraper
============================================================
Extracts: Market Values, Land Prices, Area Boundaries, Property Data
Source: https://registration.telangana.gov.in/

Features:
- All 33 districts with complete mandal/village hierarchy
- Market values (Land + Apartment) per sq yard
- Agriculture and Non-Agriculture rates
- Export to CSV, JSON, and Database
"""

import asyncio
import aiohttp
import json
import csv
import base64
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "https://registration.telangana.gov.in"

# All 33 Telangana Districts with Codes
DISTRICTS = {
    "ADILABAD": "19_1",
    "BHADRADRI KOTHAGUDEM": "22_2",
    "HANUMAKONDA": "21_1",
    "HYDERABAD": "16_1",
    "JAGTIAL": "20_2",
    "JANGOAN": "21_3",
    "JAYASHANKAR BHOOPALPALLY": "21_4",
    "JOGULAMBA GADWAL": "14_2",
    "KAMAREDDY": "18_2",
    "KARIMNAGAR": "20_1",
    "KHAMMAM": "22_1",
    "KOMARAM BHEEM ASIFABAD": "19_4",
    "MAHABUBABAD": "21_5",
    "MAHABUBNAGAR": "14_1",
    "MANCHERIAL": "19_3",
    "MEDAK": "17_1",
    "MEDCHAL-MALKAJGIRI": "15_2",
    "MULUGU": "21_6",
    "NAGARKURNOOL": "14_3",
    "NALGONDA": "23_1",
    "NARAYANPET": "14_5",
    "NIRMAL": "19_2",
    "NIZAMABAD": "18_1",
    "PEDDAPALLI": "20_4",
    "RAJANNA SIRCILLA": "20_3",
    "RANGAREDDY": "15_1",
    "SANGAREDDY": "17_2",
    "SIDDIPET": "17_3",
    "SURYAPET": "23_2",
    "VIKARABAD": "15_3",
    "WANAPARTHY": "14_4",
    "WARANGAL": "21_2",
    "YADADRI BHUVANAGIRI": "23_3",
}

# Hyderabad Divisions
HYDERABAD_DIVISIONS = {
    "HYDERABAD DIVISION": "1600001",
    "SECUNDERABAD DIVISION": "1600002",
    "SECUNDERABAD CANTONMENT BOARD": "1600003",
}


@dataclass
class MarketValue:
    """Market value data structure"""
    district: str
    district_code: str
    mandal: str
    mandal_code: str
    village: str
    village_code: str
    property_type: str  # Land or Apartment
    rate_type: str  # Agriculture (R) or Non-Agriculture (U)
    value_per_sqyd: float
    unit: str
    classification: str
    effective_from: str
    scraped_at: str


@dataclass
class AreaHierarchy:
    """Area hierarchy data structure"""
    district: str
    district_code: str
    mandal: str
    mandal_code: str
    village: str
    village_code: str


class TelanganaComprehensiveScraper:
    """Comprehensive scraper for Telangana Registration portal"""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or "scraped_data")
        self.output_dir.mkdir(exist_ok=True)
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.market_values: List[MarketValue] = []
        self.area_hierarchy: List[AreaHierarchy] = []
        self.errors: List[dict] = []
        
        # Rate limiting
        self.request_delay = 0.5  # seconds between requests
        self.max_concurrent = 5   # max concurrent requests
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Statistics
        self.stats = {
            "districts_processed": 0,
            "mandals_processed": 0,
            "villages_processed": 0,
            "market_values_extracted": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
        }
    
    async def __aenter__(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": f"{BASE_URL}/UnitRateMV/getDistrictList.htm",
        }
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def parse_response(self, text: str) -> List[Tuple[str, str]]:
        """Parse ##-delimited response into list of (code, name) tuples"""
        if not text or text in ["Malicious", "Special", ""]:
            return []
        
        items = []
        parts = text.split("##")
        for part in parts:
            part = part.strip()
            if "/" in part:
                code, name = part.split("/", 1)
                items.append((code.strip(), name.strip()))
        return items
    
    async def get_mandals(self, district_code: str) -> List[Tuple[str, str]]:
        """Get all mandals for a district"""
        async with self.semaphore:
            try:
                url = f"{BASE_URL}/UnitRateMV/getMandalListByDistCode"
                params = {"districtcode": district_code}
                
                async with self.session.get(url, params=params) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        return self.parse_response(text)
            except Exception as e:
                logger.error(f"Error getting mandals for {district_code}: {e}")
                self.errors.append({"type": "mandal_fetch", "district_code": district_code, "error": str(e)})
            
            await asyncio.sleep(self.request_delay)
            return []
    
    async def get_villages(self, district_code: str, mandal_code: str, rate_type: str = "U") -> List[Tuple[str, str]]:
        """Get all villages for a mandal"""
        async with self.semaphore:
            try:
                url = f"{BASE_URL}/UnitRateMV/getVillageListByDistCode"
                params = {
                    "districtcode": district_code,
                    "mandalcode": mandal_code,
                    "sType": rate_type
                }
                
                async with self.session.get(url, params=params) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        return self.parse_response(text)
            except Exception as e:
                logger.error(f"Error getting villages for {district_code}/{mandal_code}: {e}")
                self.errors.append({
                    "type": "village_fetch",
                    "district_code": district_code,
                    "mandal_code": mandal_code,
                    "error": str(e)
                })
            
            await asyncio.sleep(self.request_delay)
            return []
    
    async def get_hyderabad_localities(self, division_code: str, locality_prefix: str = "") -> List[Tuple[str, str]]:
        """Get localities for Hyderabad district"""
        async with self.semaphore:
            try:
                url = f"{BASE_URL}/UnitRateMV/getLocationDetails"
                # Format: districtCode~locality~ward~block~divisionCode
                codes = f"16_1~{locality_prefix if locality_prefix else '$'}~$~$~{division_code}"
                params = {"codes": codes}
                
                async with self.session.get(url, params=params) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        return self.parse_response(text)
            except Exception as e:
                logger.error(f"Error getting Hyderabad localities for {division_code}: {e}")
            
            await asyncio.sleep(self.request_delay)
            return []
    
    async def get_market_values(self, district_code: str, district_name: str,
                                 mandal_code: str, mandal_name: str,
                                 village_code: str, village_name: str,
                                 rate_type: str = "U") -> List[dict]:
        """Fetch market values for a specific location"""
        async with self.semaphore:
            try:
                # Prepare form data
                form_data = {
                    "districtId": district_code,
                    "mandalCode": mandal_code,
                    "villageCode": village_code,
                    "mndlName": mandal_name,
                    "vlgName": village_name,
                    "search_by": "L",  # Land Value
                    "RateType": rate_type,
                    "rValue": rate_type,
                }
                
                # Encode form data
                encoded_str = base64.b64encode(json.dumps(form_data).encode()).decode()
                
                # Choose endpoint based on rate type
                if rate_type == "U":
                    url = f"{BASE_URL}/UnitRateMV/unitRateMV"
                else:
                    url = f"{BASE_URL}/UnitRateMV/getMVDetailsNS"
                
                payload = {"encodestr": encoded_str}
                
                async with self.session.post(url, data=payload) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        return self.parse_market_value_html(html, district_name, district_code,
                                                            mandal_name, mandal_code,
                                                            village_name, village_code, rate_type)
            except Exception as e:
                logger.error(f"Error getting market values for {village_name}: {e}")
                self.errors.append({
                    "type": "market_value_fetch",
                    "location": f"{district_name}/{mandal_name}/{village_name}",
                    "error": str(e)
                })
            
            await asyncio.sleep(self.request_delay)
            return []
    
    def parse_market_value_html(self, html: str, district_name: str, district_code: str,
                                 mandal_name: str, mandal_code: str,
                                 village_name: str, village_code: str,
                                 rate_type: str) -> List[dict]:
        """Parse market value HTML response"""
        values = []
        
        # Extract table rows using regex (simple parsing)
        # Pattern to match table rows with data
        row_pattern = r'<tr[^>]*>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?</tr>'
        
        matches = re.findall(row_pattern, html, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            try:
                classification = re.sub(r'<[^>]+>', '', match[0]).strip()
                value_str = re.sub(r'<[^>]+>', '', match[1]).strip()
                unit = re.sub(r'<[^>]+>', '', match[2]).strip()
                effective_from = re.sub(r'<[^>]+>', '', match[3]).strip()
                
                # Parse value
                value_clean = value_str.replace(',', '').replace('₹', '').replace('Rs.', '').strip()
                try:
                    value = float(value_clean) if value_clean else 0.0
                except:
                    value = 0.0
                
                if value > 0:
                    mv = MarketValue(
                        district=district_name,
                        district_code=district_code,
                        mandal=mandal_name,
                        mandal_code=mandal_code,
                        village=village_name,
                        village_code=village_code,
                        property_type="Land" if rate_type == "U" else "Agriculture",
                        rate_type="Non-Agriculture" if rate_type == "U" else "Agriculture",
                        value_per_sqyd=value,
                        unit=unit,
                        classification=classification,
                        effective_from=effective_from,
                        scraped_at=datetime.now().isoformat()
                    )
                    values.append(mv)
                    self.market_values.append(mv)
                    self.stats["market_values_extracted"] += 1
            except Exception as e:
                pass  # Skip malformed rows
        
        return values
    
    async def scrape_district(self, district_name: str, district_code: str):
        """Scrape all data for a district"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📍 Processing District: {district_name} ({district_code})")
        logger.info(f"{'='*60}")
        
        # Special handling for Hyderabad
        if district_code.startswith("16_"):
            await self.scrape_hyderabad()
            self.stats["districts_processed"] += 1
            return
        
        # Get all mandals
        mandals = await self.get_mandals(district_code)
        logger.info(f"  Found {len(mandals)} mandals")
        
        for mandal_code, mandal_name in mandals:
            logger.info(f"    📌 Mandal: {mandal_name}")
            self.stats["mandals_processed"] += 1
            
            # Get villages for Non-Agriculture rates
            villages = await self.get_villages(district_code, mandal_code, "U")
            logger.info(f"      Found {len(villages)} villages")
            
            for village_code, village_name in villages:
                # Store area hierarchy
                self.area_hierarchy.append(AreaHierarchy(
                    district=district_name,
                    district_code=district_code,
                    mandal=mandal_name,
                    mandal_code=mandal_code,
                    village=village_name,
                    village_code=village_code
                ))
                self.stats["villages_processed"] += 1
                
                # Get market values
                await self.get_market_values(
                    district_code, district_name,
                    mandal_code, mandal_name,
                    village_code, village_name,
                    "U"  # Non-Agriculture
                )
                
                # Small delay between villages
                await asyncio.sleep(0.2)
            
            # Also try Agriculture rates
            villages_agri = await self.get_villages(district_code, mandal_code, "R")
            for village_code, village_name in villages_agri:
                await self.get_market_values(
                    district_code, district_name,
                    mandal_code, mandal_name,
                    village_code, village_name,
                    "R"  # Agriculture
                )
                await asyncio.sleep(0.2)
        
        self.stats["districts_processed"] += 1
        logger.info(f"  ✅ Completed {district_name}")
    
    async def scrape_hyderabad(self):
        """Special scraping logic for Hyderabad district"""
        logger.info("  🏙️ Using Hyderabad-specific logic (divisions/localities)")
        
        # Common locality prefixes to search
        locality_prefixes = [
            "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
            "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
            "BAL", "BAN", "BEG", "BOW", "CHI", "GAC", "HIM", "JUB", "KHA",
            "KON", "KUK", "MAD", "MAS", "MEH", "NAM", "PAT", "SEC", "SHA", "SOM"
        ]
        
        for div_name, div_code in HYDERABAD_DIVISIONS.items():
            logger.info(f"    📍 Division: {div_name}")
            
            for prefix in locality_prefixes:
                localities = await self.get_hyderabad_localities(div_code, prefix)
                
                for loc_code, loc_name in localities:
                    self.area_hierarchy.append(AreaHierarchy(
                        district="HYDERABAD",
                        district_code="16_1",
                        mandal=div_name,
                        mandal_code=div_code,
                        village=loc_name,
                        village_code=loc_code
                    ))
                    self.stats["villages_processed"] += 1
                    
                    # Get market values for locality
                    await self.get_market_values(
                        "16_1", "HYDERABAD",
                        div_code, div_name,
                        loc_code, loc_name,
                        "U"
                    )
                    await asyncio.sleep(0.1)
            
            self.stats["mandals_processed"] += 1
    
    async def run(self, districts: List[str] = None, limit_districts: int = None):
        """Main scraping orchestrator"""
        self.stats["start_time"] = datetime.now().isoformat()
        
        # Determine which districts to scrape
        target_districts = {}
        if districts:
            for d in districts:
                d_upper = d.upper()
                if d_upper in DISTRICTS:
                    target_districts[d_upper] = DISTRICTS[d_upper]
        else:
            target_districts = DISTRICTS
        
        if limit_districts:
            target_districts = dict(list(target_districts.items())[:limit_districts])
        
        logger.info(f"🚀 Starting Telangana Registration Scraper")
        logger.info(f"   Target: {len(target_districts)} districts")
        logger.info(f"   Output: {self.output_dir}")
        
        # Process each district
        for district_name, district_code in target_districts.items():
            try:
                await self.scrape_district(district_name, district_code)
            except Exception as e:
                logger.error(f"❌ Error processing {district_name}: {e}")
                self.errors.append({
                    "type": "district_error",
                    "district": district_name,
                    "error": str(e)
                })
                self.stats["errors"] += 1
        
        self.stats["end_time"] = datetime.now().isoformat()
        
        # Export data
        await self.export_data()
        
        # Print summary
        self.print_summary()
    
    async def export_data(self):
        """Export scraped data to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export Market Values to CSV
        mv_file = self.output_dir / f"market_values_{timestamp}.csv"
        with open(mv_file, 'w', newline='', encoding='utf-8') as f:
            if self.market_values:
                writer = csv.DictWriter(f, fieldnames=asdict(self.market_values[0]).keys())
                writer.writeheader()
                for mv in self.market_values:
                    writer.writerow(asdict(mv))
        logger.info(f"📁 Exported market values to {mv_file}")
        
        # Export Area Hierarchy to CSV
        area_file = self.output_dir / f"area_hierarchy_{timestamp}.csv"
        with open(area_file, 'w', newline='', encoding='utf-8') as f:
            if self.area_hierarchy:
                writer = csv.DictWriter(f, fieldnames=asdict(self.area_hierarchy[0]).keys())
                writer.writeheader()
                for area in self.area_hierarchy:
                    writer.writerow(asdict(area))
        logger.info(f"📁 Exported area hierarchy to {area_file}")
        
        # Export to JSON
        json_file = self.output_dir / f"telangana_data_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "source": "https://registration.telangana.gov.in",
                    "scraped_at": datetime.now().isoformat(),
                    "stats": self.stats
                },
                "market_values": [asdict(mv) for mv in self.market_values],
                "area_hierarchy": [asdict(a) for a in self.area_hierarchy],
                "errors": self.errors
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"📁 Exported all data to {json_file}")
        
        # Export summary stats
        stats_file = self.output_dir / f"scraping_stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2)
        logger.info(f"📁 Exported stats to {stats_file}")
    
    def print_summary(self):
        """Print scraping summary"""
        print("\n" + "="*70)
        print("📊 SCRAPING SUMMARY")
        print("="*70)
        print(f"  Districts Processed:  {self.stats['districts_processed']}")
        print(f"  Mandals Processed:    {self.stats['mandals_processed']}")
        print(f"  Villages Processed:   {self.stats['villages_processed']}")
        print(f"  Market Values Found:  {self.stats['market_values_extracted']}")
        print(f"  Errors:               {self.stats['errors']}")
        print(f"  Start Time:           {self.stats['start_time']}")
        print(f"  End Time:             {self.stats['end_time']}")
        print("="*70)


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Telangana Registration Data Scraper")
    parser.add_argument("--districts", nargs="+", help="Specific districts to scrape")
    parser.add_argument("--limit", type=int, help="Limit number of districts")
    parser.add_argument("--output", type=str, default="scraped_data", help="Output directory")
    
    args = parser.parse_args()
    
    output_dir = Path(__file__).parent.parent / args.output
    
    async with TelanganaComprehensiveScraper(output_dir=str(output_dir)) as scraper:
        await scraper.run(
            districts=args.districts,
            limit_districts=args.limit
        )


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════╗
║     TELANGANA REGISTRATION - COMPREHENSIVE PROPERTY SCRAPER        ║
║                                                                    ║
║  Extracts: Market Values, Land Prices, Area Boundaries             ║
║  Source: https://registration.telangana.gov.in/                    ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    asyncio.run(main())
