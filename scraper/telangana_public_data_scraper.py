"""
Telangana Public Data Scraper
Scrapes publicly available property data from various Telangana government portals
No login required - focuses on public datasets
"""

import asyncio
from playwright.async_api import async_playwright
import psycopg2
from datetime import datetime
import logging
import json
import pandas as pd
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelanganaPublicDataScraper:
    def __init__(self):
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
        """Create table for public data"""
        try:
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS telangana_public_data (
                    id SERIAL PRIMARY KEY,
                    data_type VARCHAR(100),
                    source_url TEXT,
                    district VARCHAR(255),
                    mandal VARCHAR(255),
                    village VARCHAR(255),
                    data_json JSONB,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Registration fees/charges reference
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS telangana_registration_fees (
                    id SERIAL PRIMARY KEY,
                    property_value_min DECIMAL(15, 2),
                    property_value_max DECIMAL(15, 2),
                    stamp_duty_percent DECIMAL(5, 2),
                    registration_fee_percent DECIMAL(5, 2),
                    transfer_duty_percent DECIMAL(5, 2),
                    property_type VARCHAR(100),
                    effective_date DATE,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            self.conn.commit()
            logger.info("✅ Database schema ready")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Schema error: {e}")
    
    async def scrape_registration_calculator_data(self, page):
        """Scrape registration charges calculator to understand fee structure"""
        try:
            url = "https://bhubharati.telangana.gov.in/registrationChrgCal"
            logger.info(f"📊 Scraping: {url}")
            
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract any tables with fee structure
            tables = soup.find_all('table')
            
            data = {
                'url': url,
                'tables_found': len(tables),
                'fee_structure': []
            }
            
            for idx, table in enumerate(tables):
                rows = table.find_all('tr')
                table_data = []
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    if row_data:
                        table_data.append(row_data)
                
                if table_data:
                    data['fee_structure'].append({
                        'table_index': idx,
                        'rows': table_data
                    })
            
            # Save to database
            self.cur.execute("""
                INSERT INTO telangana_public_data (data_type, source_url, data_json)
                VALUES (%s, %s, %s)
            """, ('registration_fees', url, json.dumps(data)))
            self.conn.commit()
            
            logger.info(f"✅ Scraped registration calculator data: {len(tables)} tables")
            return data
            
        except Exception as e:
            logger.error(f"Registration calculator error: {e}")
            return None
    
    async def scrape_site_map(self, page):
        """Scrape site map to discover all available services"""
        try:
            url = "https://bhubharati.telangana.gov.in/getSiteMap"
            logger.info(f"🗺️  Scraping: {url}")
            
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find all links in sitemap
            links = soup.find_all('a')
            services = []
            
            for link in links:
                href = link.get('href')
                text = link.get_text(strip=True)
                if href and text:
                    services.append({
                        'name': text,
                        'url': href,
                        'is_public': not any(x in href.lower() for x in ['login', 'signup', 'auth'])
                    })
            
            # Save
            with open('telangana_sitemap.json', 'w', encoding='utf-8') as f:
                json.dump(services, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Found {len(services)} services in sitemap")
            
            # Filter public services
            public_services = [s for s in services if s['is_public']]
            logger.info(f"📂 {len(public_services)} public services available")
            
            return services
            
        except Exception as e:
            logger.error(f"Sitemap error: {e}")
            return []
    
    async def scrape_information_page(self, page):
        """Scrape general information page"""
        try:
            url = "https://bhubharati.telangana.gov.in/information"
            logger.info(f"ℹ️  Scraping: {url}")
            
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract all text content
            text_content = soup.get_text(separator='\n', strip=True)
            
            # Look for structured data
            data = {
                'url': url,
                'content': text_content,
                'tables': [],
                'lists': []
            }
            
            # Extract tables
            tables = soup.find_all('table')
            for table in tables:
                rows = []
                for row in table.find_all('tr'):
                    cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                    if cells:
                        rows.append(cells)
                if rows:
                    data['tables'].append(rows)
            
            # Extract lists
            lists = soup.find_all(['ul', 'ol'])
            for lst in lists:
                items = [li.get_text(strip=True) for li in lst.find_all('li')]
                if items:
                    data['lists'].append(items)
            
            # Save
            self.cur.execute("""
                INSERT INTO telangana_public_data (data_type, source_url, data_json)
                VALUES (%s, %s, %s)
            """, ('information_page', url, json.dumps(data)))
            self.conn.commit()
            
            logger.info(f"✅ Scraped information page: {len(data['tables'])} tables, {len(data['lists'])} lists")
            return data
            
        except Exception as e:
            logger.error(f"Information page error: {e}")
            return None
    
    async def run(self):
        """Run all public data scrapers"""
        logger.info("🚀 Starting Telangana Public Data Scraper")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            # Scrape all public endpoints
            await self.scrape_site_map(page)
            await self.scrape_registration_calculator_data(page)
            await self.scrape_information_page(page)
            
            await browser.close()
        
        self.cur.close()
        self.conn.close()
        logger.info("✅ Scraping completed")

if __name__ == "__main__":
    scraper = TelanganaPublicDataScraper()
    try:
        asyncio.run(scraper.run())
    except KeyboardInterrupt:
        logger.info("Interrupted")
    except Exception as e:
        logger.error(f"Error: {e}")
