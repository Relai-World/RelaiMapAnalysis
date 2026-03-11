"""
Fully Automated IGRS Scraper with 2Captcha Integration
Zero manual intervention - handles CAPTCHA automatically
"""

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
from pathlib import Path
import logging
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_auto.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FullyAutomatedScraper:
    
    def __init__(self, captcha_api_key=None):
        """
        Initialize scraper
        
        Args:
            captcha_api_key: 2Captcha API key (get from https://2captcha.com)
                           If None, will prompt for manual CAPTCHA solving
        """
        self.base_url = "https://registration.telangana.gov.in"
        self.captcha_api_key = captcha_api_key or os.getenv("CAPTCHA_API_KEY")
        self.results = []
        self.progress_file = "scraper_progress.json"
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # All Hyderabad metro area locations
        self.locations_config = {
            "RANGAREDDY": {
                "Serilingampally": [
                    "Gachibowli", "Madhapur", "Kondapur", "Hitech City",
                    "Nanakramguda", "Manikonda", "Hafeezpet", "Miyapur"
                ],
                "Rajendranagar": [
                    "Attapur", "Rajendranagar", "Shamshabad", "Budvel"
                ],
                "Shamshabad": ["Shamshabad", "Airport Area"]
            },
            "HYDERABAD": {
                "Khairatabad": ["Banjara Hills", "Jubilee Hills", "Somajiguda"],
                "Secunderabad": ["Secunderabad", "Trimulgherry", "Alwal"],
                "Charminar": ["Charminar", "Malakpet", "Santosh Nagar"]
            },
            "MEDCHAL MALKAJGIRI": {
                "Medchal": ["Medchal", "Kompally", "Dundigal"],
                "Malkajgiri": ["Malkajgiri", "Sainikpuri", "Kapra"],
                "Keesara": ["Keesara", "Ghatkesar"]
            }
        }
        
        # Quarterly date ranges 2019-2026
        self.date_ranges = self._generate_quarterly_ranges()
        self.progress = self._load_progress()
        
    def _generate_quarterly_ranges(self):
        """Generate quarterly date ranges"""
        ranges = []
        for year in range(2019, 2027):
            ranges.extend([
                (f"01-01-{year}", f"31-03-{year}", f"{year}Q1"),
                (f"01-04-{year}", f"30-06-{year}", f"{year}Q2"),
                (f"01-07-{year}", f"30-09-{year}", f"{year}Q3"),
                (f"01-10-{year}", f"31-12-{year}", f"{year}Q4")
            ])
        return ranges
    
    def _load_progress(self):
        """Load progress"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {"completed": set(), "failed": [], "stats": {"total_records": 0}}
    
    def _save_progress(self):
        """Save progress"""
        progress_copy = self.progress.copy()
        progress_copy["completed"] = list(self.progress["completed"])
        with open(self.progress_file, 'w') as f:
            json.dump(progress_copy, f, indent=2)
    
    def solve_captcha_2captcha(self, driver):
        """
        Solve CAPTCHA using 2Captcha service
        Returns True if solved, False otherwise
        """
        if not self.captcha_api_key:
            logger.warning("No 2Captcha API key provided")
            return False
        
        try:
            # Get CAPTCHA image
            captcha_img = driver.find_element(By.ID, "captchaImage")
            captcha_src = captcha_img.get_attribute("src")
            
            # Download image
            img_response = requests.get(captcha_src)
            
            # Send to 2Captcha
            files = {'file': ('captcha.png', img_response.content)}
            data = {
                'key': self.captcha_api_key,
                'method': 'post',
                'json': 1
            }
            
            response = requests.post('http://2captcha.com/in.php', files=files, data=data)
            result = response.json()
            
            if result['status'] != 1:
                logger.error(f"2Captcha error: {result}")
                return False
            
            captcha_id = result['request']
            logger.info(f"⏳ CAPTCHA sent to 2Captcha (ID: {captcha_id})")
            
            # Wait for solution
            for _ in range(30):
                time.sleep(5)
                result_response = requests.get(
                    f'http://2captcha.com/res.php?key={self.captcha_api_key}&action=get&id={captcha_id}&json=1'
                )
                result_data = result_response.json()
                
                if result_data['status'] == 1:
                    captcha_text = result_data['request']
                    logger.info(f"✅ CAPTCHA solved: {captcha_text}")
                    
                    # Enter CAPTCHA
                    captcha_input = driver.find_element(By.ID, "captchaInput")
                    captcha_input.clear()
                    captcha_input.send_keys(captcha_text)
                    return True
                
                elif result_data['request'] != 'CAPCHA_NOT_READY':
                    logger.error(f"2Captcha error: {result_data}")
                    return False
            
            logger.warning("CAPTCHA solving timeout")
            return False
            
        except Exception as e:
            logger.error(f"CAPTCHA solving error: {e}")
            return False
    
    def manual_captcha_prompt(self, driver):
        """Prompt user to solve CAPTCHA manually"""
        logger.info("🔐 Please solve the CAPTCHA manually in the browser")
        logger.info("   Press ENTER here after solving...")
        input()
        return True
    
    def setup_driver(self):
        """Setup Chrome driver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)
        return driver
    
    def scrape_data_from_page(self, driver):
        """Extract data from current results page"""
        try:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.find('table')
            
            if not table:
                return []
            
            rows = table.find_all('tr')[1:]
            data = []
            
            for row in rows:
                cols = [c.text.strip() for c in row.find_all('td')]
                if len(cols) >= 6:
                    data.append({
                        "document_number": cols[0],
                        "transaction_date": cols[1],
                        "village": cols[2],
                        "property_type": cols[3],
                        "extent_area": cols[4],
                        "sale_consideration_value": cols[5]
                    })
            
            return data
        except Exception as e:
            logger.error(f"Page scraping error: {e}")
            return []
    
    def scrape_all_pages(self, driver):
        """Scrape all pagination pages"""
        all_data = []
        page = 1
        
        while True:
            logger.info(f"      📄 Page {page}")
            
            page_data = self.scrape_data_from_page(driver)
            if not page_data:
                break
            
            all_data.extend(page_data)
            
            # Check for next page
            try:
                next_links = driver.find_elements(By.CSS_SELECTOR, "a.next, a[rel='next']")
                if not next_links or "disabled" in next_links[0].get_attribute("class"):
                    break
                
                next_links[0].click()
                time.sleep(3)
                page += 1
                
            except Exception:
                break
        
        return all_data
    
    def scrape_combination(self, driver, district, mandal, village, date_range):
        """Scrape single district-mandal-village-daterange combination"""
        start_date, end_date, quarter = date_range
        task_key = f"{district}|{mandal}|{village}|{quarter}"
        
        # Skip if completed
        if task_key in self.progress["completed"]:
            logger.info(f"      ⏭️  Already completed")
            return []
        
        try:
            # Navigate to form
            driver.get(self.base_url)
            time.sleep(2)
            
            # Fill form
            Select(driver.find_element(By.ID, "district")).select_by_visible_text(district)
            time.sleep(1)
            
            Select(driver.find_element(By.ID, "mandal")).select_by_visible_text(mandal)
            time.sleep(1)
            
            Select(driver.find_element(By.ID, "village")).select_by_visible_text(village)
            time.sleep(1)
            
            driver.find_element(By.ID, "fromDate").send_keys(start_date)
            driver.find_element(By.ID, "toDate").send_keys(end_date)
            time.sleep(1)
            
            # Solve CAPTCHA
            if self.captcha_api_key:
                if not self.solve_captcha_2captcha(driver):
                    self.manual_captcha_prompt(driver)
            else:
                self.manual_captcha_prompt(driver)
            
            # Submit
            driver.find_element(By.ID, "submit").click()
            time.sleep(5)
            
            # Scrape results
            data = self.scrape_all_pages(driver)
            
            # Add metadata
            for record in data:
                record.update({
                    "district": district,
                    "mandal": mandal,
                    "quarter": quarter,
                    "scraped_at": datetime.now().isoformat()
                })
            
            # Mark completed
            self.progress["completed"].add(task_key)
            self.progress["stats"]["total_records"] += len(data)
            self._save_progress()
            
            logger.info(f"      ✅ {len(data)} records")
            return data
            
        except Exception as e:
            logger.error(f"      ❌ Error: {e}")
            self.progress["failed"].append({
                "task": task_key,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            self._save_progress()
            return []
    
    def run(self):
        """Main execution"""
        logger.info("🚀 Starting Fully Automated IGRS Scraper")
        logger.info(f"📅 Quarters: {len(self.date_ranges)}")
        logger.info(f"🔑 2Captcha: {'Enabled' if self.captcha_api_key else 'Manual'}")
        
        driver = self.setup_driver()
        
        try:
            for district, mandals in self.locations_config.items():
                logger.info(f"\n{'='*80}")
                logger.info(f"🏛️  {district}")
                logger.info(f"{'='*80}")
                
                for mandal, villages in mandals.items():
                    logger.info(f"\n   📍 {mandal}")
                    
                    for village in villages:
                        logger.info(f"\n      🏘️  {village}")
                        
                        for date_range in self.date_ranges:
                            quarter = date_range[2]
                            logger.info(f"         📅 {quarter}")
                            
                            data = self.scrape_combination(driver, district, mandal, village, date_range)
                            self.results.extend(data)
                            
                            # Save checkpoint every 100 records
                            if len(self.results) >= 100:
                                self.save_checkpoint()
                                self.results = []
            
            self.save_final()
            
        except KeyboardInterrupt:
            logger.info("\n⚠️ Interrupted")
            self.save_checkpoint()
        finally:
            driver.quit()
    
    def save_checkpoint(self):
        """Save checkpoint"""
        if self.results:
            df = pd.DataFrame(self.results)
            file = self.data_dir / f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(file, index=False)
            logger.info(f"💾 Checkpoint: {len(df)} records")
    
    def save_final(self):
        """Combine all checkpoints and save final file"""
        checkpoint_files = list(self.data_dir.glob("checkpoint_*.csv"))
        
        if not checkpoint_files:
            logger.warning("No data to save")
            return
        
        # Combine all checkpoints
        dfs = [pd.read_csv(f) for f in checkpoint_files]
        df = pd.concat(dfs, ignore_index=True)
        
        # Clean data
        df["sale_consideration_value"] = pd.to_numeric(
            df["sale_consideration_value"].str.replace(",", "").str.replace("₹", ""),
            errors="coerce"
        )
        df["extent_area"] = pd.to_numeric(df["extent_area"], errors="coerce")
        df["price_per_sqft"] = df["sale_consideration_value"] / df["extent_area"]
        
        df["transaction_date"] = pd.to_datetime(df["transaction_date"], format="%d-%m-%Y", errors="coerce")
        df["year"] = df["transaction_date"].dt.year
        df["month"] = df["transaction_date"].dt.month
        df["year_quarter"] = df["transaction_date"].dt.to_period("Q")
        
        # Remove duplicates
        df = df.drop_duplicates(subset=["document_number"], keep="first")
        
        # Save
        final_file = self.data_dir / f"igrs_complete_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(final_file, index=False)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ SCRAPING COMPLETE")
        logger.info(f"💾 File: {final_file}")
        logger.info(f"📊 Records: {len(df):,}")
        logger.info(f"📅 Range: {df['transaction_date'].min()} to {df['transaction_date'].max()}")
        logger.info(f"💰 Total Value: ₹{df['sale_consideration_value'].sum():,.0f}")
        logger.info(f"{'='*80}")


if __name__ == "__main__":
    # Option 1: With 2Captcha (fully automated)
    # scraper = FullyAutomatedScraper(captcha_api_key="YOUR_2CAPTCHA_API_KEY")
    
    # Option 2: Manual CAPTCHA solving
    scraper = FullyAutomatedScraper()
    
    scraper.run()
