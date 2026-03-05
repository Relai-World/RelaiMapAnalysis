"""
Bhu Bharati Manual Login Scraper
You login manually, then the scraper takes over
"""

import asyncio
from playwright.async_api import async_playwright
import psycopg2
from datetime import datetime
import logging
import json
import time
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BhuBharatiManualScraper:
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
        """Create comprehensive tables"""
        try:
            # Market Values
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
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Raw scraped data
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS bhubharati_raw_data (
                    id SERIAL PRIMARY KEY,
                    data_type VARCHAR(100),
                    source_page VARCHAR(255),
                    data_json JSONB,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            self.conn.commit()
            logger.info("✅ Database schema ready")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Schema error: {e}")
    
    async def wait_for_manual_login(self, page):
        """Wait for user to login manually"""
        logger.info("\n" + "="*60)
        logger.info("🔐 MANUAL LOGIN REQUIRED")
        logger.info("="*60)
        logger.info("Please login manually in the browser window.")
        logger.info("Once you're logged in and see the dashboard/home page,")
        logger.info("press ENTER in this terminal to continue...")
        logger.info("="*60 + "\n")
        
        # Wait for user confirmation
        input("Press ENTER after you've logged in successfully: ")
        
        # Take screenshot to confirm
        await page.screenshot(path='after_manual_login.png')
        logger.info("📸 Saved screenshot: after_manual_login.png")
        logger.info(f"✅ Current URL: {page.url}")
        
        return True
    
    async def explore_authenticated_sections(self, page):
        """Explore what's available after login"""
        try:
            logger.info("\n🔍 Exploring authenticated sections...")
            
            # Get page content
            content = await page.content()
            
            # Get all navigation links
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
            
            # Save discovered services
            with open('bhubharati_authenticated_services.json', 'w', encoding='utf-8') as f:
                json.dump(services, f, indent=2, ensure_ascii=False)
            
            logger.info(f"\n✅ Found {len(services)} authenticated services")
            logger.info("💾 Saved to: bhubharati_authenticated_services.json")
            
            return services
            
        except Exception as e:
            logger.error(f"Exploration error: {e}")
            return []
    
    async def scrape_page_data(self, page, url, data_type):
        """Generic function to scrape any page and save raw data"""
        try:
            logger.info(f"\n📄 Scraping: {url}")
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state('networkidle')
            
            # Get page content
            content = await page.content()
            
            # Take screenshot
            screenshot_name = f"scraped_{data_type}_{int(time.time())}.png"
            await page.screenshot(path=screenshot_name)
            
            # Save raw HTML
            self.cur.execute("""
                INSERT INTO bhubharati_raw_data (data_type, source_page, data_json)
                VALUES (%s, %s, %s)
            """, (data_type, url, json.dumps({'html': content[:10000], 'screenshot': screenshot_name})))
            self.conn.commit()
            
            logger.info(f"✅ Saved data for: {data_type}")
            logger.info(f"📸 Screenshot: {screenshot_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Scraping error for {url}: {e}")
            return False
    
    async def interactive_scraping(self, page, services):
        """Interactive scraping - let user guide what to scrape"""
        logger.info("\n" + "="*60)
        logger.info("🎯 INTERACTIVE SCRAPING MODE")
        logger.info("="*60)
        logger.info("I found these services. Let's scrape them one by one.")
        logger.info("You can navigate manually and I'll save the data.")
        logger.info("="*60 + "\n")
        
        while True:
            print("\nOptions:")
            print("1. List all discovered services")
            print("2. Scrape current page")
            print("3. Navigate to a specific service (I'll list them)")
            print("4. Manual navigation (you navigate, I'll wait)")
            print("5. Finish and exit")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == "1":
                print("\n📋 Discovered Services:")
                for idx, service in enumerate(services, 1):
                    print(f"{idx}. {service['name']}: {service['url']}")
            
            elif choice == "2":
                data_type = input("Enter data type name (e.g., 'market_values', 'land_records'): ").strip()
                await self.scrape_page_data(page, page.url, data_type)
            
            elif choice == "3":
                print("\n📋 Available Services:")
                for idx, service in enumerate(services, 1):
                    print(f"{idx}. {service['name']}")
                
                service_num = input("\nEnter service number: ").strip()
                try:
                    idx = int(service_num) - 1
                    if 0 <= idx < len(services):
                        service = services[idx]
                        url = service['url']
                        if not url.startswith('http'):
                            url = f"{self.base_url}{url}"
                        
                        data_type = service['name'].lower().replace(' ', '_')
                        await self.scrape_page_data(page, url, data_type)
                    else:
                        print("Invalid service number")
                except:
                    print("Invalid input")
            
            elif choice == "4":
                print("\n⏸️  Navigate manually in the browser.")
                input("Press ENTER when you're ready to continue: ")
                await page.screenshot(path=f'manual_nav_{int(time.time())}.png')
                logger.info(f"Current URL: {page.url}")
            
            elif choice == "5":
                logger.info("\n✅ Finishing scraping session...")
                break
            
            else:
                print("Invalid choice, please try again")
    
    async def scrape_all_services(self, page, services):
        """Automatically scrape all discovered services"""
        logger.info("\n" + "="*60)
        logger.info("🤖 AUTO-SCRAPING ALL SERVICES")
        logger.info("="*60)
        
        total = len(services)
        scraped = 0
        failed = 0
        
        for idx, service in enumerate(services, 1):
            try:
                name = service['name']
                url = service['url']
                
                # Skip non-actionable links
                if url in ['#', 'javascript:void(0)', ''] or url.startswith('#'):
                    logger.info(f"[{idx}/{total}] ⏭️  Skipping: {name} (no URL)")
                    continue
                
                # Make URL absolute
                if not url.startswith('http'):
                    url = f"{self.base_url}{url}"
                
                logger.info(f"\n[{idx}/{total}] 🔄 Scraping: {name}")
                logger.info(f"         URL: {url}")
                
                # Navigate to the service
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state('networkidle', timeout=20000)
                
                # Get page content
                content = await page.content()
                
                # Take screenshot
                screenshot_name = f"scraped_{idx}_{name.replace(' ', '_')[:30]}.png"
                await page.screenshot(path=screenshot_name)
                
                # Extract any tables
                tables = await page.query_selector_all('table')
                table_data = []
                for table in tables:
                    rows = await table.query_selector_all('tr')
                    table_rows = []
                    for row in rows:
                        cells = await row.query_selector_all(['td', 'th'])
                        cell_texts = []
                        for cell in cells:
                            text = await cell.inner_text()
                            cell_texts.append(text.strip())
                        if cell_texts:
                            table_rows.append(cell_texts)
                    if table_rows:
                        table_data.append(table_rows)
                
                # Extract any forms
                forms = await page.query_selector_all('form')
                form_data = []
                for form in forms:
                    inputs = await form.query_selector_all('input, select, textarea')
                    form_fields = []
                    for inp in inputs:
                        name_attr = await inp.get_attribute('name')
                        type_attr = await inp.get_attribute('type')
                        if name_attr:
                            form_fields.append({'name': name_attr, 'type': type_attr})
                    if form_fields:
                        form_data.append(form_fields)
                
                # Save to database
                data_json = {
                    'url': url,
                    'html_preview': content[:5000],
                    'screenshot': screenshot_name,
                    'tables_count': len(table_data),
                    'tables': table_data[:3],  # First 3 tables
                    'forms_count': len(form_data),
                    'forms': form_data
                }
                
                self.cur.execute("""
                    INSERT INTO bhubharati_raw_data (data_type, source_page, data_json)
                    VALUES (%s, %s, %s)
                """, (name, url, json.dumps(data_json)))
                self.conn.commit()
                
                logger.info(f"         ✅ Saved! Tables: {len(table_data)}, Forms: {len(form_data)}")
                scraped += 1
                
                # Small delay between requests
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"         ❌ Failed: {e}")
                failed += 1
                continue
        
        logger.info("\n" + "="*60)
        logger.info(f"📊 SCRAPING SUMMARY")
        logger.info("="*60)
        logger.info(f"Total services: {total}")
        logger.info(f"Successfully scraped: {scraped}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Skipped: {total - scraped - failed}")
        logger.info("="*60)
    
    async def run(self):
        """Run manual login scraper"""
        logger.info("🚀 Starting Bhu Bharati Manual Login Scraper")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Visible browser
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            # Navigate to login page
            await page.goto(f"{self.base_url}/Citizen", timeout=60000)
            
            # Wait for manual login
            await self.wait_for_manual_login(page)
            
            # Explore authenticated sections
            services = await self.explore_authenticated_sections(page)
            
            # AUTO-SCRAPE EVERYTHING
            await self.scrape_all_services(page, services)
            
            # Keep browser open for inspection
            logger.info("\n⏸️  Browser will stay open for 30 seconds for inspection...")
            await asyncio.sleep(30)
            
            await browser.close()
        
        self.cur.close()
        self.conn.close()
        logger.info("✅ Scraping completed")

if __name__ == "__main__":
    scraper = BhuBharatiManualScraper()
    try:
        asyncio.run(scraper.run())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}")
