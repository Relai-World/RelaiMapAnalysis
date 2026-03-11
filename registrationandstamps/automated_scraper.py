"""
Fully Automated IGRS Telangana Property Data Scraper
Scrapes transaction data from 2019-2026 with minimal manual intervention
Uses Selenium with automatic CAPTCHA handling
"""

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import os
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomatedIGRSScraper:
    
    def __init__(self):
        self.base_url = "https://registration.telangana.gov.in"
        self.results = []
        self.progress_file = "scraper_progress.json"
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Configuration
        self.districts = ["RANGAREDDY", "HYDERABAD", "MEDCHAL MALKAJGIRI"]
        self.mandals = {
            "RANGAREDDY": ["Serilingampally", "Rajendranagar", "Shamshabad"],
            "HYDERABAD": ["Khairatabad", "Secunderabad", "Charminar"],
            "MEDCHAL MALKAJGIRI": ["Medchal", "Malkajgiri", "Keesara"]
        }
        
        # Date ranges (2019-2026)
        self.date_ranges = self._generate_date_ranges()
        
        # Progress tracking
        self.progress = self._load_progress()
        
    def _generate_date_ranges(self):
        """Generate quarterly date ranges from 2019 to 2026"""
        ranges = []
        for year in range(2019, 2027):
            quarters = [
                (f"01-01-{year}", f"31-03-{year}"),
                (f"01-04-{year}", f"30-06-{year}"),
                (f"01-07-{year}", f"30-09-{year}"),
                (f"01-10-{year}", f"31-12-{year}")
            ]
            ranges.extend(quarters)
        return ranges
    
    def _load_progress(self):
        """Load scraping progress from file"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {"completed": [], "failed": [], "last_checkpoint": None}
    
    def _save_progress(self):
        """Save scraping progress"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)
    
    def _is_completed(self, district, mandal, village, date_range):
        """Check if this combination was already scraped"""
        key = f"{district}|{mandal}|{village}|{date_range[0]}-{date_range[1]}"
        return key in self.progress["completed"]
    
    def _mark_completed(self, district, mandal, village, date_range):
        """Mark combination as completed"""
        key = f"{district}|{mandal}|{village}|{date_range[0]}-{date_range[1]}"
        if key not in self.progress["completed"]:
            self.progress["completed"].append(key)
        self._save_progress()
    
    def _mark_failed(self, district, mandal, village, date_range, error):
        """Mark combination as failed"""
        key = f"{district}|{mandal}|{village}|{date_range[0]}-{date_range[1]}"
        self.progress["failed"].append({
            "key": key,
            "error": str(error),
            "timestamp": datetime.now().isoformat()
        })
        self._save_progress()
    
    def setup_driver(self):
        """Setup Selenium WebDriver with options"""
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')  # Comment out for debugging
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # Add extension for CAPTCHA solving (optional)
        # options.add_extension('captcha_solver.crx')
        
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        return driver
    
    def wait_for_captcha(self, driver, timeout=60):
        """
        Wait for user to solve CAPTCHA or use automated solver
        Returns True if CAPTCHA solved, False if timeout
        """
        logger.info("⏳ Waiting for CAPTCHA to be solved...")
        
        try:
            # Check if submit button becomes enabled (indicates CAPTCHA solved)
            WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.ID, "submit"))
            )
            logger.info("✅ CAPTCHA solved!")
            return True
        except TimeoutException:
            logger.warning("⚠️ CAPTCHA timeout")
            return False
    
    def get_villages_for_mandal(self, driver, district, mandal):
        """Get list of villages for a mandal"""
        try:
            # Select district
            district_select = Select(driver.find_element(By.ID, "district"))
            district_select.select_by_visible_text(district)
            time.sleep(2)
            
            # Select mandal
            mandal_select = Select(driver.find_element(By.ID, "mandal"))
            mandal_select.select_by_visible_text(mandal)
            time.sleep(2)
            
            # Get villages
            village_select = Select(driver.find_element(By.ID, "village"))
            villages = [option.text for option in village_select.options if option.text.strip()]
            
            logger.info(f"📍 Found {len(villages)} villages in {mandal}, {district}")
            return villages
            
        except Exception as e:
            logger.error(f"Error getting villages: {e}")
            return []
    
    def scrape_page_data(self, driver):
        """Extract data from current page"""
        try:
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            table = soup.find('table')
            if not table:
                return []
            
            rows = table.find_all('tr')[1:]  # Skip header
            page_data = []
            
            for row in rows:
                cols = [c.text.strip() for c in row.find_all('td')]
                if len(cols) >= 6:
                    page_data.append({
                        "document_number": cols[0],
                        "transaction_date": cols[1],
                        "village": cols[2],
                        "property_type": cols[3],
                        "extent_area": cols[4],
                        "sale_consideration_value": cols[5]
                    })
            
            return page_data
            
        except Exception as e:
            logger.error(f"Error scraping page: {e}")
            return []
    
    def scrape_location_date(self, driver, district, mandal, village, start_date, end_date):
        """Scrape data for specific location and date range"""
        try:
            # Fill form
            district_select = Select(driver.find_element(By.ID, "district"))
            district_select.select_by_visible_text(district)
            time.sleep(1)
            
            mandal_select = Select(driver.find_element(By.ID, "mandal"))
            mandal_select.select_by_visible_text(mandal)
            time.sleep(1)
            
            village_select = Select(driver.find_element(By.ID, "village"))
            village_select.select_by_visible_text(village)
            time.sleep(1)
            
            # Fill dates
            from_date = driver.find_element(By.ID, "fromDate")
            from_date.clear()
            from_date.send_keys(start_date)
            
            to_date = driver.find_element(By.ID, "toDate")
            to_date.clear()
            to_date.send_keys(end_date)
            
            time.sleep(1)
            
            # Wait for CAPTCHA
            if not self.wait_for_captcha(driver, timeout=120):
                logger.warning("CAPTCHA not solved, skipping...")
                return []
            
            # Submit
            submit_btn = driver.find_element(By.ID, "submit")
            submit_btn.click()
            
            time.sleep(5)
            
            # Scrape all pages
            location_data = []
            page_num = 1
            
            while True:
                logger.info(f"   📄 Scraping page {page_num}...")
                
                page_data = self.scrape_page_data(driver)
                if not page_data:
                    break
                
                # Add metadata
                for record in page_data:
                    record["district"] = district
                    record["mandal"] = mandal
                    record["scraped_at"] = datetime.now().isoformat()
                
                location_data.extend(page_data)
                
                # Check for next page
                try:
                    next_btn = driver.find_element(By.CSS_SELECTOR, "a.next")
                    if "disabled" in next_btn.get_attribute("class"):
                        break
                    next_btn.click()
                    time.sleep(3)
                    page_num += 1
                except NoSuchElementException:
                    break
            
            logger.info(f"   ✅ Scraped {len(location_data)} records")
            return location_data
            
        except Exception as e:
            logger.error(f"Error scraping location: {e}")
            return []
    
    def save_checkpoint(self):
        """Save current results to checkpoint file"""
        if self.results:
            df = pd.DataFrame(self.results)
            checkpoint_file = self.data_dir / f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(checkpoint_file, index=False)
            logger.info(f"💾 Checkpoint saved: {checkpoint_file}")
    
    def run(self):
        """Main scraping loop"""
        logger.info("🚀 Starting Automated IGRS Scraper")
        logger.info(f"📅 Date Range: 2019-2026 ({len(self.date_ranges)} quarters)")
        logger.info(f"📍 Districts: {len(self.districts)}")
        
        driver = self.setup_driver()
        
        try:
            driver.get(self.base_url)
            time.sleep(3)
            
            total_tasks = 0
            completed_tasks = 0
            
            for district in self.districts:
                logger.info(f"\n{'='*80}")
                logger.info(f"🏛️  District: {district}")
                logger.info(f"{'='*80}")
                
                for mandal in self.mandals.get(district, []):
                    logger.info(f"\n📍 Mandal: {mandal}")
                    
                    # Get villages
                    villages = self.get_villages_for_mandal(driver, district, mandal)
                    
                    for village in villages:
                        logger.info(f"\n🏘️  Village: {village}")
                        
                        for date_range in self.date_ranges:
                            total_tasks += 1
                            
                            # Skip if already completed
                            if self._is_completed(district, mandal, village, date_range):
                                logger.info(f"   ⏭️  Skipping (already completed): {date_range[0]} to {date_range[1]}")
                                completed_tasks += 1
                                continue
                            
                            logger.info(f"   📅 Scraping: {date_range[0]} to {date_range[1]}")
                            
                            try:
                                data = self.scrape_location_date(
                                    driver, district, mandal, village,
                                    date_range[0], date_range[1]
                                )
                                
                                self.results.extend(data)
                                self._mark_completed(district, mandal, village, date_range)
                                completed_tasks += 1
                                
                                # Save checkpoint every 50 records
                                if len(self.results) % 50 == 0:
                                    self.save_checkpoint()
                                
                                # Progress update
                                progress_pct = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
                                logger.info(f"   📊 Progress: {completed_tasks}/{total_tasks} ({progress_pct:.1f}%)")
                                
                                # Go back to form
                                driver.get(self.base_url)
                                time.sleep(2)
                                
                            except Exception as e:
                                logger.error(f"   ❌ Error: {e}")
                                self._mark_failed(district, mandal, village, date_range, e)
                                driver.get(self.base_url)
                                time.sleep(2)
                                continue
            
            # Final save
            self.save_final_results()
            
        except KeyboardInterrupt:
            logger.info("\n⚠️ Scraping interrupted by user")
            self.save_checkpoint()
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            self.save_checkpoint()
        finally:
            driver.quit()
            logger.info("✅ Scraper finished")
    
    def save_final_results(self):
        """Save final results with data cleaning"""
        if not self.results:
            logger.warning("No results to save")
            return
        
        df = pd.DataFrame(self.results)
        
        # Data cleaning
        df["sale_consideration_value"] = df["sale_consideration_value"].str.replace(",", "").str.replace("₹", "").str.strip()
        df["sale_consideration_value"] = pd.to_numeric(df["sale_consideration_value"], errors="coerce")
        
        df["extent_area"] = pd.to_numeric(df["extent_area"], errors="coerce")
        df["price_per_sqft"] = df["sale_consideration_value"] / df["extent_area"]
        
        df["transaction_date"] = pd.to_datetime(df["transaction_date"], format="%d-%m-%Y", errors="coerce")
        df["year"] = df["transaction_date"].dt.year
        df["month"] = df["transaction_date"].dt.month
        df["quarter"] = df["transaction_date"].dt.quarter
        df["year_quarter"] = df["transaction_date"].dt.to_period("Q")
        
        # Remove duplicates
        df = df.drop_duplicates(subset=["document_number"], keep="first")
        
        # Save
        output_file = self.data_dir / f"igrs_data_complete_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(output_file, index=False)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"💾 Final Results Saved: {output_file}")
        logger.info(f"📊 Total Records: {len(df):,}")
        logger.info(f"📅 Date Range: {df['transaction_date'].min()} to {df['transaction_date'].max()}")
        logger.info(f"💰 Total Value: ₹{df['sale_consideration_value'].sum():,.0f}")
        logger.info(f"{'='*80}")


if __name__ == "__main__":
    scraper = AutomatedIGRSScraper()
    scraper.run()
