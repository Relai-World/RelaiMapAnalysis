"""
Bhu Bharati (Dharani) Portal Scraper
Scrapes: Land Records, Market Values, Property Details
Source: https://bhubharati.telangana.gov.in/
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

class BhuBharatiScraper:
    def __init__(self):
        self.base_url = "https://bhubharati.telangana.gov.in"
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
        """Create tables for Bhu Bharati data"""
        try:
            # Market Values by Location
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS bhubharati_market_values (
                    id SERIAL PRIMARY KEY,
                    district VARCHAR(255),
                    mandal VARCHAR(255),
                    village VARCHAR(255),
                    survey_number VARCHAR(100),
                    land_type VARCHAR(100),
                    land_use VARCHAR(100),
                    market_value_per_sqyd DECIMAL(12, 2),
                    market_value_per_acre DECIMAL(15, 2),
                    effective_from DATE,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(district, mandal, village, survey_number, land_type, effective_from)
                );
            """)
            
            # Property Transactions
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS bhubharati_transactions (
                    id SERIAL PRIMARY KEY,
                    district VARCHAR(255),
                    mandal VARCHAR(255),
                    village VARCHAR(255),
                    survey_number VARCHAR(100),
                    document_number VARCHAR(100) UNIQUE,
                    document_type VARCHAR(100),
                    registration_date DATE,
                    transaction_value DECIMAL(15, 2),
                    property_area DECIMAL(10, 2),
                    area_unit VARCHAR(20),
                    buyer_name VARCHAR(255),
                    seller_name VARCHAR(255),
                    sro_office VARCHAR(255),
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Land Ownership Records
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS bhubharati_land_records (
                    id SERIAL PRIMARY KEY,
                    district VARCHAR(255),
                    mandal VARCHAR(255),
                    village VARCHAR(255),
                    survey_number VARCHAR(100),
                    pattadar_name VARCHAR(255),
                    extent_acres DECIMAL(10, 4),
                    land_nature VARCHAR(100),
                    land_classification VARCHAR(100),
                    passbook_number VARCHAR(100),
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(district, mandal, village, survey_number, pattadar_name)
                );
            """)
            
            self.conn.commit()
            logger.info("✅ Database schema ready")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Schema creation error: {e}")
    
    async def explore_portal(self, page):
        """Explore the Bhu Bharati portal structure"""
        try:
            await page.goto(f"{self.base_url}/Citizen", timeout=60000)
            await page.wait_for_load_state('networkidle')
            
            # Find all service links
            links = await page.query_selector_all('a')
            services = []
            
            for link in links:
                try:
                    text = await link.inner_text()
                    href = await link.get_attribute('href')
                    if text and href and text.strip():
                        services.append({
                            'name': text.strip(),
                            'url': href
                        })
                        logger.info(f"  📌 {text.strip()}: {href}")
                except:
                    pass
            
            return services
            
        except Exception as e:
            logger.error(f"Portal exploration error: {e}")
            return []
    
    async def scrape_market_values(self, page, district, mandal, village):
        """Scrape market values for a location"""
        try:
            # Navigate to market value search
            await page.goto(f"{self.base_url}/Citizen/MarketValue", timeout=30000)
            
            # Fill form
            await page.select_option('select#district', district)
            await asyncio.sleep(1)
            
            await page.select_option('select#mandal', mandal)
            await asyncio.sleep(1)
            
            await page.select_option('select#village', village)
            await asyncio.sleep(1)
            
            # Submit
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # Extract data from results table
            rows = await page.query_selector_all('table.market-value-table tbody tr')
            
            data = []
            for row in rows:
                cells = await row.query_selector_all('td')
                if len(cells) >= 5:
                    land_type = await cells[0].inner_text()
                    land_use = await cells[1].inner_text()
                    value_sqyd = await cells[2].inner_text()
                    value_acre = await cells[3].inner_text()
                    effective_date = await cells[4].inner_text()
                    
                    # Parse values
                    value_sqyd_clean = float(value_sqyd.replace(',', '').replace('₹', '').strip())
                    value_acre_clean = float(value_acre.replace(',', '').replace('₹', '').strip())
                    
                    data.append({
                        'district': district,
                        'mandal': mandal,
                        'village': village,
                        'land_type': land_type.strip(),
                        'land_use': land_use.strip(),
                        'value_sqyd': value_sqyd_clean,
                        'value_acre': value_acre_clean,
                        'effective_date': effective_date.strip()
                    })
            
            # Insert into database
            for item in data:
                try:
                    self.cur.execute("""
                        INSERT INTO bhubharati_market_values 
                        (district, mandal, village, land_type, land_use, 
                         market_value_per_sqyd, market_value_per_acre, effective_from)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (district, mandal, village, survey_number, land_type, effective_from)
                        DO UPDATE SET 
                            market_value_per_sqyd = EXCLUDED.market_value_per_sqyd,
                            market_value_per_acre = EXCLUDED.market_value_per_acre
                    """, (
                        item['district'], item['mandal'], item['village'],
                        item['land_type'], item['land_use'],
                        item['value_sqyd'], item['value_acre'], item['effective_date']
                    ))
                    self.conn.commit()
                except Exception as e:
                    self.conn.rollback()
                    logger.error(f"Insert error: {e}")
            
            logger.info(f"✅ Scraped {len(data)} market values for {village}")
            return data
            
        except Exception as e:
            logger.error(f"Market value scraping error: {e}")
            return []
    
    async def run_explorer(self):
        """Run portal exploration"""
        logger.info("🔍 Exploring Bhu Bharati Portal")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            services = await self.explore_portal(page)
            
            # Save services
            with open('bhubharati_services.json', 'w', encoding='utf-8') as f:
                json.dump(services, f, indent=2, ensure_ascii=False)
            logger.info("💾 Saved services to bhubharati_services.json")
            
            # Keep browser open for inspection
            logger.info("\n⏸️  Browser open for 60 seconds...")
            await asyncio.sleep(60)
            
            await browser.close()
        
        self.cur.close()
        self.conn.close()

if __name__ == "__main__":
    scraper = BhuBharatiScraper()
    try:
        asyncio.run(scraper.run_explorer())
    except KeyboardInterrupt:
        logger.info("Scraper interrupted")
    except Exception as e:
        logger.error(f"Error: {e}")
