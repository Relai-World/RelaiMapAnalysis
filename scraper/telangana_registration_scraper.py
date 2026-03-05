"""
Telangana Registration & Stamps Department Data Scraper
Scrapes: Market Values, EC Data, Property Transactions, SRO Info
Source: https://registration.telangana.gov.in/
"""

import asyncio
from playwright.async_api import async_playwright
import psycopg2
from datetime import datetime
import logging
import json
import time
import random
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelanganaRegistrationScraper:
    def __init__(self):
        self.base_url = "https://registration.telangana.gov.in"
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        self.cur = self.conn.cursor()
        self._ensure_schema()
        
    def _ensure_schema(self):
        """Create tables for storing scraped data"""
        try:
            # Market Values Table
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS telangana_market_values (
                    id SERIAL PRIMARY KEY,
                    district VARCHAR(255),
                    mandal VARCHAR(255),
                    village VARCHAR(255),
                    property_type VARCHAR(100),
                    land_type VARCHAR(100),
                    market_value_per_sqyd DECIMAL(12, 2),
                    effective_date DATE,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(district, mandal, village, property_type, land_type, effective_date)
                );
            """)
            
            # SRO (Sub-Registrar Office) Information
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS telangana_sro_info (
                    id SERIAL PRIMARY KEY,
                    sro_code VARCHAR(50) UNIQUE,
                    sro_name VARCHAR(255),
                    district VARCHAR(255),
                    mandal VARCHAR(255),
                    villages TEXT[],
                    address TEXT,
                    contact_number VARCHAR(50),
                    email VARCHAR(255),
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Property Transactions (if available)
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS telangana_property_transactions (
                    id SERIAL PRIMARY KEY,
                    district VARCHAR(255),
                    mandal VARCHAR(255),
                    village VARCHAR(255),
                    document_type VARCHAR(100),
                    registration_date DATE,
                    transaction_value DECIMAL(15, 2),
                    property_area DECIMAL(10, 2),
                    stamp_duty DECIMAL(12, 2),
                    registration_fee DECIMAL(12, 2),
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            self.conn.commit()
            logger.info("✅ Database schema ready")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Schema creation error: {e}")
    
    async def scrape_market_values(self, page, district, mandal, village):
        """Scrape market values for a specific location"""
        try:
            # Navigate to market value search
            await page.goto(f"{self.base_url}/marketvalue", timeout=30000)
            
            # Select district
            await page.select_option('select[name="district"]', district)
            await asyncio.sleep(1)
            
            # Select mandal
            await page.select_option('select[name="mandal"]', mandal)
            await asyncio.sleep(1)
            
            # Select village
            await page.select_option('select[name="village"]', village)
            await asyncio.sleep(1)
            
            # Submit form
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # Extract market value data
            rows = await page.query_selector_all('table tbody tr')
            
            data = []
            for row in rows:
                cells = await row.query_selector_all('td')
                if len(cells) >= 4:
                    property_type = await cells[0].inner_text()
                    land_type = await cells[1].inner_text()
                    value = await cells[2].inner_text()
                    effective_date = await cells[3].inner_text()
                    
                    # Clean and parse value
                    value_clean = float(value.replace(',', '').replace('₹', '').strip())
                    
                    data.append({
                        'district': district,
                        'mandal': mandal,
                        'village': village,
                        'property_type': property_type.strip(),
                        'land_type': land_type.strip(),
                        'market_value': value_clean,
                        'effective_date': effective_date.strip()
                    })
            
            # Insert into database
            for item in data:
                try:
                    self.cur.execute("""
                        INSERT INTO telangana_market_values 
                        (district, mandal, village, property_type, land_type, 
                         market_value_per_sqyd, effective_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (district, mandal, village, property_type, land_type, effective_date)
                        DO UPDATE SET market_value_per_sqyd = EXCLUDED.market_value_per_sqyd
                    """, (
                        item['district'], item['mandal'], item['village'],
                        item['property_type'], item['land_type'],
                        item['market_value'], item['effective_date']
                    ))
                    self.conn.commit()
                except Exception as e:
                    self.conn.rollback()
                    logger.error(f"Insert error: {e}")
            
            logger.info(f"✅ Scraped {len(data)} market values for {village}, {mandal}, {district}")
            return data
            
        except Exception as e:
            logger.error(f"Market value scraping error: {e}")
            return []
    
    async def scrape_sro_info(self, page, district):
        """Scrape SRO (Sub-Registrar Office) information"""
        try:
            await page.goto(f"{self.base_url}/sro", timeout=30000)
            
            # Select district
            await page.select_option('select[name="district"]', district)
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # Extract SRO data
            sro_cards = await page.query_selector_all('.sro-card')
            
            data = []
            for card in sro_cards:
                sro_code = await card.query_selector('.sro-code')
                sro_name = await card.query_selector('.sro-name')
                address = await card.query_selector('.address')
                contact = await card.query_selector('.contact')
                
                if sro_code and sro_name:
                    data.append({
                        'sro_code': await sro_code.inner_text(),
                        'sro_name': await sro_name.inner_text(),
                        'district': district,
                        'address': await address.inner_text() if address else '',
                        'contact': await contact.inner_text() if contact else ''
                    })
            
            # Insert into database
            for item in data:
                try:
                    self.cur.execute("""
                        INSERT INTO telangana_sro_info 
                        (sro_code, sro_name, district, address, contact_number)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (sro_code) DO UPDATE 
                        SET sro_name = EXCLUDED.sro_name,
                            address = EXCLUDED.address,
                            contact_number = EXCLUDED.contact_number
                    """, (
                        item['sro_code'], item['sro_name'], item['district'],
                        item['address'], item['contact']
                    ))
                    self.conn.commit()
                except Exception as e:
                    self.conn.rollback()
                    logger.error(f"SRO insert error: {e}")
            
            logger.info(f"✅ Scraped {len(data)} SRO offices for {district}")
            return data
            
        except Exception as e:
            logger.error(f"SRO scraping error: {e}")
            return []
    
    async def run(self, districts=None):
        """Main scraping orchestrator"""
        if districts is None:
            # Hyderabad area districts
            districts = [
                "Hyderabad",
                "Rangareddy",
                "Medchal-Malkajgiri"
            ]
        
        logger.info(f"🚀 Starting Telangana Registration scraper for {len(districts)} districts")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            for district in districts:
                logger.info(f"\n{'='*60}")
                logger.info(f"📍 Processing District: {district}")
                logger.info(f"{'='*60}")
                
                # Scrape SRO info
                await self.scrape_sro_info(page, district)
                time.sleep(random.uniform(2, 4))
                
                # TODO: Add mandal/village iteration for market values
                # This requires getting the list of mandals and villages first
                
            await browser.close()
        
        self.cur.close()
        self.conn.close()
        logger.info("✅ Scraping completed")

if __name__ == "__main__":
    scraper = TelanganaRegistrationScraper()
    try:
        asyncio.run(scraper.run())
    except KeyboardInterrupt:
        logger.info("Scraper interrupted by user")
    except Exception as e:
        logger.error(f"Scraper error: {e}")
