"""
Bhu Bharati Authenticated Scraper
Logs in and scrapes all available property data
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

class BhuBharatiAuthScraper:
    def __init__(self):
        self.base_url = "https://bhubharati.telangana.gov.in"
        self.username = os.getenv("BHUBHARATI_USERNAME")
        self.password = os.getenv("BHUBHARATI_PASSWORD")
        
        if not self.username or not self.password:
            raise ValueError("Missing BHUBHARATI_USERNAME or BHUBHARATI_PASSWORD in .env")
        
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
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
            
            # Land Records
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
            
            # Raw scraped data (for anything we can't parse)
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
    
    async def login(self, page):
        """Login to Bhu Bharati portal"""
        try:
            logger.info("🔐 Logging in...")
            await page.goto(f"{self.base_url}/Citizen", timeout=60000)
            await page.wait_for_load_state('networkidle')
            
            # Take screenshot for debugging
            await page.screenshot(path='login_page.png')
            logger.info("📸 Saved screenshot: login_page.png")
            
            # Look for login link/button to open modal
            login_triggers = [
                'a:has-text("Login")',
                'button:has-text("Login")',
                'a:has-text("Sign In")',
                'button:has-text("Sign In")',
                '#loginModal',
                '[data-target="#loginModal"]',
                '.login-btn'
            ]
            
            for trigger in login_triggers:
                try:
                    element = await page.query_selector(trigger)
                    if element:
                        logger.info(f"Found login trigger: {trigger}")
                        await element.click()
                        await asyncio.sleep(2)  # Wait for modal to open
                        break
                except:
                    pass
            
            # Wait for login form to be visible
            await asyncio.sleep(2)
            
            # Try to find visible username field
            username_selectors = [
                'input[name="username"]:visible',
                'input[name="mobile"]:visible',
                'input[name="phone"]:visible',
                'input[type="text"]:visible',
                'input#username',
                'input#mobile',
                '#loginModal input[type="text"]',
                '.modal input[type="text"]'
            ]
            
            username_filled = False
            for selector in username_selectors:
                try:
                    # Wait for element to be visible
                    await page.wait_for_selector(selector, state='visible', timeout=5000)
                    await page.fill(selector, self.username)
                    logger.info(f"✅ Filled username with: {selector}")
                    username_filled = True
                    break
                except Exception as e:
                    logger.debug(f"Could not use selector {selector}: {e}")
                    continue
            
            if not username_filled:
                logger.error("❌ Could not fill username field")
                await page.screenshot(path='login_error.png')
                return False
            
            # Try to find visible password field
            password_selectors = [
                'input[name="password"]:visible',
                'input[type="password"]:visible',
                'input#password',
                '#loginModal input[type="password"]',
                '.modal input[type="password"]'
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    await page.wait_for_selector(selector, state='visible', timeout=5000)
                    await page.fill(selector, self.password)
                    logger.info(f"✅ Filled password with: {selector}")
                    password_filled = True
                    break
                except Exception as e:
                    logger.debug(f"Could not use selector {selector}: {e}")
                    continue
            
            if not password_filled:
                logger.error("❌ Could not fill password field")
                await page.screenshot(path='login_error.png')
                return False
            
            # Find and click login button
            login_button_selectors = [
                'button[type="submit"]:visible',
                'input[type="submit"]:visible',
                'button:has-text("Login"):visible',
                'button:has-text("Sign In"):visible',
                '#loginModal button[type="submit"]',
                '.modal button[type="submit"]'
            ]
            
            for selector in login_button_selectors:
                try:
                    await page.wait_for_selector(selector, state='visible', timeout=5000)
                    await page.click(selector)
                    logger.info(f"✅ Clicked login button: {selector}")
                    break
                except:
                    continue
            
            # Wait for navigation or modal to close
            await asyncio.sleep(3)
            await page.wait_for_load_state('networkidle', timeout=30000)
            
            # Take screenshot after login
            await page.screenshot(path='after_login.png')
            logger.info("📸 Saved screenshot: after_login.png")
            
            # Check if login successful
            current_url = page.url
            logger.info(f"Current URL: {current_url}")
            
            # Check for error messages
            error_selectors = ['.error', '.alert-danger', '.login-error']
            for selector in error_selectors:
                try:
                    error = await page.query_selector(selector)
                    if error:
                        error_text = await error.inner_text()
                        logger.error(f"❌ Login error message: {error_text}")
                        return False
                except:
                    pass
            
            logger.info("✅ Login completed (check screenshots to verify)")
            return True
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            await page.screenshot(path='login_exception.png')
            return False
    
    async def explore_authenticated_sections(self, page):
        """Explore what's available after login"""
        try:
            logger.info("🔍 Exploring authenticated sections...")
            
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
            
            logger.info(f"✅ Found {len(services)} authenticated services")
            return services
            
        except Exception as e:
            logger.error(f"Exploration error: {e}")
            return []
    
    async def scrape_market_values(self, page, district, mandal, village):
        """Scrape market values for a location"""
        try:
            logger.info(f"💰 Scraping market values: {village}, {mandal}, {district}")
            
            # Navigate to market value page (adjust URL as needed)
            await page.goto(f"{self.base_url}/marketValue", timeout=30000)
            
            # Fill form
            await page.select_option('select[name="district"]', district)
            await asyncio.sleep(1)
            
            await page.select_option('select[name="mandal"]', mandal)
            await asyncio.sleep(1)
            
            await page.select_option('select[name="village"]', village)
            await asyncio.sleep(1)
            
            # Submit
            await page.click('button[type="submit"]')
            await page.wait_for_load_state('networkidle')
            
            # Extract data
            content = await page.content()
            
            # Save raw data
            self.cur.execute("""
                INSERT INTO bhubharati_raw_data (data_type, source_page, data_json)
                VALUES (%s, %s, %s)
            """, ('market_values', f"{district}/{mandal}/{village}", json.dumps({'html': content[:5000]})))
            self.conn.commit()
            
            logger.info(f"✅ Saved market value data for {village}")
            return True
            
        except Exception as e:
            logger.error(f"Market value scraping error: {e}")
            return False
    
    async def run_explorer(self):
        """Run authenticated exploration"""
        logger.info("🚀 Starting Bhu Bharati Authenticated Scraper")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Visible for debugging
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            # Login
            if await self.login(page):
                # Explore authenticated sections
                services = await self.explore_authenticated_sections(page)
                
                # Keep browser open for manual inspection
                logger.info("\n⏸️  Browser open for 120 seconds for manual inspection...")
                logger.info("   Check what data is available and note the URLs")
                await asyncio.sleep(120)
            else:
                logger.error("❌ Login failed, cannot proceed")
            
            await browser.close()
        
        self.cur.close()
        self.conn.close()
        logger.info("✅ Exploration completed")

if __name__ == "__main__":
    scraper = BhuBharatiAuthScraper()
    try:
        asyncio.run(scraper.run_explorer())
    except KeyboardInterrupt:
        logger.info("Interrupted")
    except Exception as e:
        logger.error(f"Error: {e}")
