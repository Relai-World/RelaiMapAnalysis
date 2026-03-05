"""
Bhu Bharati Dashboard Scraper
Scrapes the dashboard and all accessible data after manual login
"""

import asyncio
from playwright.async_api import async_playwright
import psycopg2
from datetime import datetime
import logging
import json
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BhuBharatiDashboardScraper:
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
        """Create tables"""
        try:
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS bhubharati_scraped_data (
                    id SERIAL PRIMARY KEY,
                    data_type VARCHAR(255),
                    page_title VARCHAR(255),
                    page_url TEXT,
                    content_text TEXT,
                    tables_json JSONB,
                    forms_json JSONB,
                    screenshot_path VARCHAR(255),
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
        logger.info("Once you're logged in and see the dashboard,")
        logger.info("press ENTER in this terminal to continue...")
        logger.info("="*60 + "\n")
        
        input("Press ENTER after you've logged in successfully: ")
        
        await page.screenshot(path='dashboard_initial.png')
        logger.info(f"✅ Current URL: {page.url}")
        
        return True
    
    async def scrape_current_page(self, page, page_name):
        """Scrape the current page comprehensively"""
        try:
            logger.info(f"\n📄 Scraping: {page_name}")
            
            # Get page info
            url = page.url
            title = await page.title()
            
            # Get full page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract text content
            text_content = soup.get_text(separator='\n', strip=True)
            
            # Extract all tables
            tables = []
            table_elements = soup.find_all('table')
            for idx, table in enumerate(table_elements):
                rows = []
                for row in table.find_all('tr'):
                    cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                    if cells:
                        rows.append(cells)
                if rows:
                    tables.append({
                        'table_index': idx,
                        'rows': rows
                    })
            
            # Extract all forms
            forms = []
            form_elements = soup.find_all('form')
            for idx, form in enumerate(form_elements):
                fields = []
                for inp in form.find_all(['input', 'select', 'textarea']):
                    field_info = {
                        'name': inp.get('name'),
                        'type': inp.get('type'),
                        'id': inp.get('id'),
                        'placeholder': inp.get('placeholder')
                    }
                    if field_info['name']:
                        fields.append(field_info)
                
                if fields:
                    forms.append({
                        'form_index': idx,
                        'action': form.get('action'),
                        'method': form.get('method'),
                        'fields': fields
                    })
            
            # Take screenshot
            screenshot_name = f"scraped_{page_name.replace(' ', '_')[:30]}_{int(time.time())}.png"
            await page.screenshot(path=screenshot_name, full_page=True)
            
            # Save to database
            self.cur.execute("""
                INSERT INTO bhubharati_scraped_data 
                (data_type, page_title, page_url, content_text, tables_json, forms_json, screenshot_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                page_name,
                title,
                url,
                text_content[:10000],  # First 10k chars
                json.dumps(tables),
                json.dumps(forms),
                screenshot_name
            ))
            self.conn.commit()
            
            logger.info(f"✅ Saved: {len(tables)} tables, {len(forms)} forms")
            logger.info(f"📸 Screenshot: {screenshot_name}")
            
            return {
                'tables': len(tables),
                'forms': len(forms),
                'screenshot': screenshot_name
            }
            
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return None
    
    async def explore_dashboard_sections(self, page):
        """Find and click through all dashboard sections"""
        try:
            logger.info("\n🔍 Exploring dashboard sections...")
            
            # Look for menu items, cards, buttons
            clickable_selectors = [
                'button',
                'a.btn',
                '.card',
                '.menu-item',
                '.nav-link',
                '[role="button"]',
                '.dashboard-card',
                '.service-card'
            ]
            
            sections = []
            for selector in clickable_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        text = await element.inner_text()
                        if text and text.strip():
                            sections.append({
                                'text': text.strip(),
                                'selector': selector,
                                'element': element
                            })
                except:
                    pass
            
            logger.info(f"Found {len(sections)} clickable sections")
            
            # Display sections
            for idx, section in enumerate(sections[:20], 1):  # First 20
                logger.info(f"  {idx}. {section['text'][:50]}")
            
            return sections
            
        except Exception as e:
            logger.error(f"Exploration error: {e}")
            return []
    
    async def click_and_scrape(self, page, element, section_name):
        """Click an element and scrape the resulting page"""
        try:
            logger.info(f"\n🖱️  Clicking: {section_name}")
            
            # Click the element
            await element.click()
            await asyncio.sleep(2)
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Scrape the page
            await self.scrape_current_page(page, section_name)
            
            # Go back to dashboard
            await page.go_back()
            await asyncio.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"Click and scrape error: {e}")
            return False
    
    async def run(self):
        """Run dashboard scraper"""
        logger.info("🚀 Starting Bhu Bharati Dashboard Scraper")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            # Navigate to login page
            await page.goto(f"{self.base_url}/Citizen", timeout=60000)
            
            # Wait for manual login
            await self.wait_for_manual_login(page)
            
            # Scrape the dashboard itself
            await self.scrape_current_page(page, "Dashboard_Main")
            
            # Explore sections
            sections = await self.explore_dashboard_sections(page)
            
            # Auto-scrape all sections
            logger.info("\n" + "="*60)
            logger.info("🤖 AUTO-SCRAPING ALL SECTIONS")
            logger.info("="*60)
            
            scraped = 0
            for idx, section in enumerate(sections[:20], 1):  # First 20 sections
                try:
                    await self.click_and_scrape(page, section['element'], section['text'])
                    scraped += 1
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Failed to scrape {section['text']}: {e}")
            
            logger.info(f"\n✅ Successfully scraped {scraped} sections")
            
            # Keep browser open
            logger.info("\n⏸️  Browser open for 60 seconds for inspection...")
            await asyncio.sleep(60)
            
            await browser.close()
        
        self.cur.close()
        self.conn.close()
        logger.info("✅ Scraping completed")

if __name__ == "__main__":
    scraper = BhuBharatiDashboardScraper()
    try:
        asyncio.run(scraper.run())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted")
    except Exception as e:
        logger.error(f"Error: {e}")
