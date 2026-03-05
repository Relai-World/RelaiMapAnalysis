"""
Telangana Registration Site Explorer
Discovers available data endpoints and structure
"""

import asyncio
from playwright.async_api import async_playwright
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def explore_site():
    """Explore the Telangana Registration site structure"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Visible browser
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        logger.info("🔍 Exploring https://registration.telangana.gov.in")
        
        try:
            await page.goto("https://registration.telangana.gov.in", timeout=60000)
            await page.wait_for_load_state('networkidle', timeout=30000)
            
            # Get page title
            title = await page.title()
            logger.info(f"📄 Page Title: {title}")
            
            # Find all links
            links = await page.query_selector_all('a')
            logger.info(f"\n🔗 Found {len(links)} links:")
            
            link_data = []
            for link in links[:50]:  # First 50 links
                try:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    if href and text.strip():
                        link_data.append({
                            'text': text.strip(),
                            'href': href
                        })
                        logger.info(f"  • {text.strip()}: {href}")
                except:
                    pass
            
            # Check for forms
            forms = await page.query_selector_all('form')
            logger.info(f"\n📝 Found {len(forms)} forms")
            
            # Check for select dropdowns
            selects = await page.query_selector_all('select')
            logger.info(f"\n📋 Found {len(selects)} dropdown menus:")
            for select in selects:
                try:
                    name = await select.get_attribute('name')
                    id_attr = await select.get_attribute('id')
                    logger.info(f"  • Name: {name}, ID: {id_attr}")
                    
                    # Get options
                    options = await select.query_selector_all('option')
                    logger.info(f"    Options: {len(options)}")
                    for opt in options[:10]:  # First 10 options
                        value = await opt.get_attribute('value')
                        text = await opt.inner_text()
                        logger.info(f"      - {text}: {value}")
                except:
                    pass
            
            # Save page content for analysis
            content = await page.content()
            with open('telangana_registration_page.html', 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("\n💾 Saved page HTML to telangana_registration_page.html")
            
            # Save link data
            with open('telangana_registration_links.json', 'w', encoding='utf-8') as f:
                json.dump(link_data, f, indent=2, ensure_ascii=False)
            logger.info("💾 Saved links to telangana_registration_links.json")
            
            # Wait for manual inspection
            logger.info("\n⏸️  Browser will stay open for 60 seconds for manual inspection...")
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(explore_site())
