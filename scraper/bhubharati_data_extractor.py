"""
Bhu Bharati Data Extractor
Focuses on finding and using search forms to extract actual property data
"""

import asyncio
from playwright.async_api import async_playwright
import psycopg2
from datetime import datetime
import logging
import json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BhuBharatiDataExtractor:
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
        
    async def wait_for_manual_login(self, page):
        """Wait for user to login"""
        logger.info("\n" + "="*60)
        logger.info("🔐 Please login manually in the browser")
        logger.info("="*60 + "\n")
        
        input("Press ENTER after login: ")
        await page.screenshot(path='logged_in.png')
        logger.info(f"✅ Logged in at: {page.url}")
        return True
    
    async def analyze_dashboard(self, page):
        """Analyze the dashboard to understand available features"""
        logger.info("\n📊 ANALYZING DASHBOARD")
        logger.info("="*60)
        
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Look for keywords that indicate data services
        keywords = [
            'search', 'find', 'query', 'market value', 'property',
            'land', 'survey', 'registration', 'transaction', 'record',
            'pattadar', 'passbook', 'encumbrance', 'EC'
        ]
        
        found_features = []
        for keyword in keywords:
            if keyword.lower() in text.lower():
                found_features.append(keyword)
        
        logger.info(f"Found keywords: {', '.join(found_features)}")
        
        # Find all forms
        forms = soup.find_all('form')
        logger.info(f"\nFound {len(forms)} forms on dashboard")
        
        for idx, form in enumerate(forms, 1):
            logger.info(f"\nForm {idx}:")
            inputs = form.find_all(['input', 'select', 'textarea'])
            for inp in inputs:
                name = inp.get('name', 'unnamed')
                inp_type = inp.get('type', inp.name)
                placeholder = inp.get('placeholder', '')
                logger.info(f"  - {name} ({inp_type}): {placeholder}")
        
        # Find all links with interesting text
        links = soup.find_all('a')
        interesting_links = []
        for link in links:
            text = link.get_text(strip=True)
            href = link.get('href', '')
            if any(kw in text.lower() for kw in keywords):
                interesting_links.append({'text': text, 'href': href})
        
        if interesting_links:
            logger.info(f"\nFound {len(interesting_links)} interesting links:")
            for link in interesting_links[:10]:
                logger.info(f"  - {link['text']}: {link['href']}")
        
        # Save analysis
        with open('dashboard_analysis.json', 'w', encoding='utf-8') as f:
            json.dump({
                'keywords_found': found_features,
                'forms_count': len(forms),
                'interesting_links': interesting_links,
                'full_text': text[:2000]
            }, f, indent=2, ensure_ascii=False)
        
        logger.info("\n💾 Saved analysis to: dashboard_analysis.json")
        
        return {
            'forms': len(forms),
            'links': interesting_links
        }
    
    async def interactive_exploration(self, page):
        """Let user guide the exploration"""
        logger.info("\n" + "="*60)
        logger.info("🎯 INTERACTIVE EXPLORATION MODE")
        logger.info("="*60)
        logger.info("The browser will stay open.")
        logger.info("Navigate to any data page you want to scrape.")
        logger.info("="*60 + "\n")
        
        while True:
            print("\nOptions:")
            print("1. Scrape current page")
            print("2. Show current URL")
            print("3. Take screenshot")
            print("4. Extract all tables from current page")
            print("5. Extract all forms from current page")
            print("6. Save page HTML")
            print("7. Exit")
            
            choice = input("\nChoice: ").strip()
            
            if choice == "1":
                await self.scrape_current_page(page)
            elif choice == "2":
                logger.info(f"Current URL: {page.url}")
            elif choice == "3":
                filename = f"screenshot_{int(datetime.now().timestamp())}.png"
                await page.screenshot(path=filename, full_page=True)
                logger.info(f"📸 Saved: {filename}")
            elif choice == "4":
                await self.extract_tables(page)
            elif choice == "5":
                await self.extract_forms(page)
            elif choice == "6":
                content = await page.content()
                filename = f"page_{int(datetime.now().timestamp())}.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"💾 Saved HTML: {filename}")
            elif choice == "7":
                break
    
    async def scrape_current_page(self, page):
        """Scrape whatever is on the current page"""
        try:
            url = page.url
            title = await page.title()
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract tables
            tables = []
            for table in soup.find_all('table'):
                rows = []
                for row in table.find_all('tr'):
                    cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                    if cells:
                        rows.append(cells)
                if rows:
                    tables.append(rows)
            
            # Save
            filename = f"scraped_data_{int(datetime.now().timestamp())}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'url': url,
                    'title': title,
                    'tables': tables,
                    'text': soup.get_text(separator='\n', strip=True)[:5000]
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Scraped {len(tables)} tables")
            logger.info(f"💾 Saved to: {filename}")
            
        except Exception as e:
            logger.error(f"Scraping error: {e}")
    
    async def extract_tables(self, page):
        """Extract and display all tables"""
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        tables = soup.find_all('table')
        
        logger.info(f"\n📊 Found {len(tables)} tables:")
        for idx, table in enumerate(tables, 1):
            logger.info(f"\nTable {idx}:")
            rows = table.find_all('tr')[:5]  # First 5 rows
            for row in rows:
                cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                logger.info(f"  {cells}")
    
    async def extract_forms(self, page):
        """Extract and display all forms"""
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        forms = soup.find_all('form')
        
        logger.info(f"\n📝 Found {len(forms)} forms:")
        for idx, form in enumerate(forms, 1):
            logger.info(f"\nForm {idx}:")
            logger.info(f"  Action: {form.get('action')}")
            logger.info(f"  Method: {form.get('method')}")
            inputs = form.find_all(['input', 'select', 'textarea'])
            for inp in inputs:
                logger.info(f"  - {inp.get('name')} ({inp.get('type', inp.name)})")
    
    async def run(self):
        """Run interactive extractor"""
        logger.info("🚀 Starting Bhu Bharati Data Extractor")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            await page.goto(f"{self.base_url}/Citizen", timeout=60000)
            await self.wait_for_manual_login(page)
            
            # Analyze dashboard
            await self.analyze_dashboard(page)
            
            # Interactive mode
            await self.interactive_exploration(page)
            
            await browser.close()
        
        self.cur.close()
        self.conn.close()
        logger.info("✅ Completed")

if __name__ == "__main__":
    scraper = BhuBharatiDataExtractor()
    try:
        asyncio.run(scraper.run())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted")
    except Exception as e:
        logger.error(f"Error: {e}")
