"""
IGRS Scraper - Database-Driven
Fetches all locations from database and scrapes IGRS data for each
Fully automated with progress tracking and resume capability
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
from datetime import datetime
import os
from pathlib import Path
import logging
import psycopg2
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('igrs_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseDrivenIGRSScraper:
    
    def __init__(self):
        self.base_url = "https://registration.telangana.gov.in"
        self.results = []
        self.progress_file = "scraping_progress.json"
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Database connection
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        self.cur = self.conn.cursor()
        
        # Configuration
        self.district = "RANGAREDDY"
        self.mandal = "Serilingampally"
        
        # Date ranges (2019-2026, quarterly)
        self.date_ranges = self._generate_date_ranges()
        
        # Progress tracking
        self.progress = self._load_progress()
        
    def _generate_date_ranges(self):
        """Generate quarterly date ranges from 2019 to 2026"""
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
        """Load scraping progress"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    # Convert completed list to set for faster lookup
                    data['completed'] = set(data.get('completed', []))
                    return data
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"⚠️ Corrupted progress file, starting fresh: {e}")
                # Backup corrupted file
                backup_file = f"{self.progress_file}.backup"
                try:
                    os.rename(self.progress_file, backup_file)
                    logger.info(f"   Backed up to: {backup_file}")
                except:
                    pass
        
        return {
            'completed': set(),
            'failed': [],
            'stats': {
                'total_records': 0,
                'locations_completed': 0,
                'locations_total': 0
            }
        }
    
    def _save_progress(self):
        """Save scraping progress"""
        progress_copy = self.progress.copy()
        progress_copy['completed'] = list(self.progress['completed'])
        with open(self.progress_file, 'w') as f:
            json.dump(progress_copy, f, indent=2)
    
    def get_locations_from_db(self):
        """Fetch all Hyderabad locations from database"""
        logger.info("📍 Fetching locations from database...")
        
        query = """
            SELECT name
            FROM locations
            WHERE city = 'Hyderabad'
            ORDER BY name
        """
        
        self.cur.execute(query)
        locations = [row[0] for row in self.cur.fetchall()]
        
        logger.info(f"✅ Found {len(locations)} locations in database")
        return locations
    
    def setup_driver(self):
        """Setup Selenium WebDriver"""
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')  # Uncomment for headless mode
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=options)
        return driver
    
    def wait_for_captcha_manual(self, driver, timeout=120):
        """Wait for user to solve CAPTCHA manually"""
        logger.info("🔐 Please solve the CAPTCHA in the browser...")
        logger.info("   The script will continue automatically once solved")
        
        try:
            # Wait for submit button to become clickable (indicates CAPTCHA solved)
            WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.ID, "submit"))
            )
            logger.info("✅ CAPTCHA solved!")
            return True
        except TimeoutException:
            logger.warning("⚠️ CAPTCHA timeout")
            return False
    
    def scrape_page_data(self, driver):
        """Extract data from current results page"""
        try:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.find('table')
            
            if not table:
                return []
            
            rows = table.find_all('tr')[1:]  # Skip header
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
            logger.error(f"Error scraping page: {e}")
            return []
    
    def scrape_all_pages(self, driver):
        """Scrape all pagination pages"""
        all_data = []
        page = 1
        
        while True:
            logger.info(f"         📄 Page {page}")
            
            page_data = self.scrape_page_data(driver)
            if not page_data:
                break
            
            all_data.extend(page_data)
            
            # Check for next page
            try:
                next_links = driver.find_elements(By.CSS_SELECTOR, "a.next, a[rel='next']")
                if not next_links:
                    break
                
                # Check if disabled
                if "disabled" in next_links[0].get_attribute("class"):
                    break
                
                next_links[0].click()
                time.sleep(3)
                page += 1
                
            except Exception:
                break
        
        return all_data
    
    def scrape_location_date(self, driver, location, date_range):
        """Scrape data for specific location and date range"""
        start_date, end_date, quarter = date_range
        task_key = f"{self.district}|{self.mandal}|{location}|{quarter}"
        
        # Skip if already completed
        if task_key in self.progress['completed']:
            logger.info(f"         ⏭️  Already completed")
            return []
        
        try:
            # Navigate to form
            driver.get(self.base_url)
            time.sleep(2)
            
            # Fill form
            Select(driver.find_element(By.ID, "district")).select_by_visible_text(self.district)
            time.sleep(1)
            
            Select(driver.find_element(By.ID, "mandal")).select_by_visible_text(self.mandal)
            time.sleep(1)
            
            # Try to select village
            try:
                Select(driver.find_element(By.ID, "village")).select_by_visible_text(location)
            except Exception as e:
                logger.warning(f"         ⚠️  Location '{location}' not found in dropdown")
                self.progress['failed'].append({
                    'task': task_key,
                    'error': 'Location not in dropdown',
                    'timestamp': datetime.now().isoformat()
                })
                self._save_progress()
                return []
            
            time.sleep(1)
            
            # Fill dates
            driver.find_element(By.ID, "fromDate").send_keys(start_date)
            driver.find_element(By.ID, "toDate").send_keys(end_date)
            time.sleep(1)
            
            # Wait for CAPTCHA
            if not self.wait_for_captcha_manual(driver):
                logger.warning(f"         ⚠️  CAPTCHA timeout, skipping...")
                return []
            
            # Submit
            driver.find_element(By.ID, "submit").click()
            time.sleep(5)
            
            # Check if "No records found" message
            page_text = driver.page_source.lower()
            if "no records" in page_text or "no data" in page_text:
                logger.info(f"         ℹ️  No records found")
                self.progress['completed'].add(task_key)
                self._save_progress()
                return []
            
            # Scrape all pages
            data = self.scrape_all_pages(driver)
            
            # Add metadata
            for record in data:
                record.update({
                    "district": self.district,
                    "mandal": self.mandal,
                    "quarter": quarter,
                    "scraped_at": datetime.now().isoformat()
                })
            
            # Mark completed
            self.progress['completed'].add(task_key)
            self.progress['stats']['total_records'] += len(data)
            self._save_progress()
            
            logger.info(f"         ✅ {len(data)} records")
            return data
            
        except Exception as e:
            logger.error(f"         ❌ Error: {e}")
            self.progress['failed'].append({
                'task': task_key,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            self._save_progress()
            return []
    
    def save_checkpoint(self):
        """Save current results to checkpoint file"""
        if self.results:
            df = pd.DataFrame(self.results)
            checkpoint_file = self.data_dir / f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(checkpoint_file, index=False)
            logger.info(f"💾 Checkpoint saved: {len(df)} records")
            self.results = []  # Clear results after saving
    
    def run(self):
        """Main scraping execution"""
        logger.info("="*80)
        logger.info("🚀 DATABASE-DRIVEN IGRS SCRAPER")
        logger.info("="*80)
        
        # Get locations from database
        locations = self.get_locations_from_db()
        self.progress['stats']['locations_total'] = len(locations)
        
        logger.info(f"\n📊 Configuration:")
        logger.info(f"   District: {self.district}")
        logger.info(f"   Mandal: {self.mandal}")
        logger.info(f"   Locations: {len(locations)}")
        logger.info(f"   Date Ranges: {len(self.date_ranges)} quarters (2019-2026)")
        logger.info(f"   Total Tasks: {len(locations) * len(self.date_ranges)}")
        
        driver = self.setup_driver()
        
        try:
            for idx, location in enumerate(locations, 1):
                logger.info(f"\n{'='*80}")
                logger.info(f"📍 [{idx}/{len(locations)}] {location}")
                logger.info(f"{'='*80}")
                
                location_has_data = False
                
                for date_range in self.date_ranges:
                    quarter = date_range[2]
                    logger.info(f"      📅 {quarter}")
                    
                    data = self.scrape_location_date(driver, location, date_range)
                    
                    if data:
                        location_has_data = True
                        self.results.extend(data)
                    
                    # Save checkpoint every 100 records
                    if len(self.results) >= 100:
                        self.save_checkpoint()
                
                if location_has_data:
                    self.progress['stats']['locations_completed'] += 1
                    self._save_progress()
                
                # Progress summary
                logger.info(f"\n   📊 Progress: {self.progress['stats']['locations_completed']}/{len(locations)} locations")
                logger.info(f"   📊 Total Records: {self.progress['stats']['total_records']}")
            
            # Final save
            self.save_checkpoint()
            self.combine_and_save_final()
            
        except KeyboardInterrupt:
            logger.info("\n⚠️ Interrupted by user")
            self.save_checkpoint()
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            self.save_checkpoint()
        finally:
            driver.quit()
            self.cur.close()
            self.conn.close()
            logger.info("\n✅ Scraper finished")
    
    def combine_and_save_final(self):
        """Combine all checkpoints and save final cleaned dataset"""
        logger.info("\n" + "="*80)
        logger.info("📦 COMBINING AND CLEANING DATA")
        logger.info("="*80)
        
        checkpoint_files = list(self.data_dir.glob("checkpoint_*.csv"))
        
        if not checkpoint_files:
            logger.warning("No checkpoint files found")
            return
        
        logger.info(f"Found {len(checkpoint_files)} checkpoint files")
        
        # Combine all checkpoints
        dfs = []
        for file in checkpoint_files:
            df = pd.read_csv(file)
            dfs.append(df)
            logger.info(f"   Loaded: {file.name} ({len(df)} records)")
        
        df = pd.concat(dfs, ignore_index=True)
        logger.info(f"\n✅ Combined: {len(df)} total records")
        
        # Data cleaning
        logger.info("\n🧹 Cleaning data...")
        
        # Clean sale consideration value
        df["sale_consideration_value"] = pd.to_numeric(
            df["sale_consideration_value"].str.replace(",", "").str.replace("₹", "").str.strip(),
            errors="coerce"
        )
        
        # Clean area
        df["extent_area"] = pd.to_numeric(df["extent_area"], errors="coerce")
        
        # Calculate price per sqft
        df["price_per_sqft"] = df["sale_consideration_value"] / df["extent_area"]
        
        # Parse dates
        df["transaction_date"] = pd.to_datetime(df["transaction_date"], format="%d-%m-%Y", errors="coerce")
        df["year"] = df["transaction_date"].dt.year
        df["month"] = df["transaction_date"].dt.month
        df["year_quarter"] = df["transaction_date"].dt.to_period("Q")
        
        # Remove duplicates
        before_dedup = len(df)
        df = df.drop_duplicates(subset=["document_number"], keep="first")
        after_dedup = len(df)
        logger.info(f"   Removed {before_dedup - after_dedup} duplicates")
        
        # Remove invalid records
        df = df[df["sale_consideration_value"].notna()]
        df = df[df["sale_consideration_value"] > 0]
        logger.info(f"   Final records: {len(df)}")
        
        # Save final file
        final_file = self.data_dir / f"igrs_complete_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(final_file, index=False)
        
        # Generate summary
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ SCRAPING COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"💾 Final File: {final_file}")
        logger.info(f"📊 Total Records: {len(df):,}")
        logger.info(f"📅 Date Range: {df['transaction_date'].min()} to {df['transaction_date'].max()}")
        logger.info(f"💰 Total Transaction Value: ₹{df['sale_consideration_value'].sum():,.0f}")
        logger.info(f"📍 Unique Locations: {df['village'].nunique()}")
        logger.info(f"🏠 Property Types: {', '.join(df['property_type'].unique()[:5])}")
        logger.info(f"{'='*80}")


if __name__ == "__main__":
    scraper = DatabaseDrivenIGRSScraper()
    scraper.run()
