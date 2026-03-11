"""
IGRS Property Transaction Scraper - Production Version
Scrapes property data from IGRS Telangana for all database locations
Features:
- Robust error handling
- Progress tracking with resume capability
- Automatic data validation
- Checkpoint system
- Detailed logging
"""

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    StaleElementReferenceException, WebDriverException
)
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
from pathlib import Path
import logging
import psycopg2
from dotenv import load_dotenv
import sys

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('igrs_scraper.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class IGRSScraper:
    """
    Main scraper class for IGRS property transaction data
    """
    
    def __init__(self, district="RANGAREDDY", mandal="Serilingampally"):
        """
        Initialize scraper with configuration
        
        Args:
            district: District name (RANGAREDDY, HYDERABAD, MEDCHAL MALKAJGIRI)
            mandal: Mandal name within the district
        """
        self.base_url = "https://registration.telangana.gov.in"
        self.district = district
        self.mandal = mandal
        
        # Setup directories
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Progress tracking
        self.progress_file = "igrs_progress.json"
        self.progress = self._load_progress()
        
        # Results storage
        self.results = []
        self.checkpoint_size = 50  # Save every 50 records
        
        # Database connection
        self.conn = None
        self.cur = None
        self._connect_db()
        
        # Date ranges (2019-2026, quarterly)
        self.date_ranges = self._generate_date_ranges()
        
        logger.info("="*80)
        logger.info("IGRS SCRAPER INITIALIZED")
        logger.info("="*80)
        logger.info(f"District: {self.district}")
        logger.info(f"Mandal: {self.mandal}")
        logger.info(f"Date ranges: {len(self.date_ranges)} quarters")
        logger.info("="*80)
    
    def _connect_db(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "post@123"),
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5432")
            )
            self.cur = self.conn.cursor()
            logger.info("✅ Database connected")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
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
        """Load scraping progress from file"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['completed'] = set(data.get('completed', []))
                    logger.info(f"📂 Loaded progress: {len(data['completed'])} tasks completed")
                    return data
            except Exception as e:
                logger.warning(f"⚠️ Could not load progress file: {e}")
                # Backup corrupted file
                if os.path.exists(self.progress_file):
                    backup = f"{self.progress_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    os.rename(self.progress_file, backup)
                    logger.info(f"   Backed up to: {backup}")
        
        return {
            'completed': set(),
            'failed': [],
            'stats': {
                'total_records': 0,
                'locations_completed': 0,
                'locations_total': 0,
                'started_at': datetime.now().isoformat()
            }
        }
    
    def _save_progress(self):
        """Save progress to file"""
        try:
            progress_copy = self.progress.copy()
            progress_copy['completed'] = list(self.progress['completed'])
            progress_copy['stats']['last_updated'] = datetime.now().isoformat()
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_copy, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Could not save progress: {e}")
    
    def get_locations_from_db(self):
        """
        Fetch all unique Hyderabad locations from database
        
        Returns:
            list: List of location names
        """
        logger.info("📍 Fetching locations from database...")
        
        query = """
            SELECT DISTINCT name
            FROM locations
            WHERE city = 'Hyderabad'
            ORDER BY name
        """
        
        self.cur.execute(query)
        locations = [row[0] for row in self.cur.fetchall()]
        
        logger.info(f"✅ Found {len(locations)} unique locations")
        return locations
    
    def setup_driver(self):
        """
        Setup Selenium WebDriver with optimal configuration
        
        Returns:
            webdriver: Configured Chrome WebDriver
        """
        options = webdriver.ChromeOptions()
        
        # Performance optimizations
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        
        # Remove automation flags
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User agent
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            driver = webdriver.Chrome(options=options)
            logger.info("✅ Chrome driver initialized")
            return driver
        except Exception as e:
            logger.error(f"❌ Failed to initialize driver: {e}")
            raise
    
    def wait_for_captcha(self, driver, timeout=180):
        """
        Wait for user to solve CAPTCHA
        
        Args:
            driver: Selenium WebDriver
            timeout: Maximum wait time in seconds
            
        Returns:
            bool: True if CAPTCHA solved, False if timeout
        """
        logger.info("🔐 Waiting for CAPTCHA to be solved...")
        logger.info("   Please solve the CAPTCHA in the browser window")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check if submit button is clickable (indicates CAPTCHA solved)
                submit_btn = driver.find_element(By.ID, "submit")
                if submit_btn.is_enabled():
                    logger.info("✅ CAPTCHA solved!")
                    return True
            except:
                pass
            
            time.sleep(2)
        
        logger.warning("⚠️ CAPTCHA timeout")
        return False
    
    def extract_table_data(self, driver):
        """
        Extract data from results table on current page
        
        Args:
            driver: Selenium WebDriver
            
        Returns:
            list: List of dictionaries containing row data
        """
        try:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.find('table')
            
            if not table:
                return []
            
            rows = table.find_all('tr')[1:]  # Skip header row
            data = []
            
            for row in rows:
                cols = [c.text.strip() for c in row.find_all('td')]
                
                # Validate row has minimum required columns
                if len(cols) >= 6:
                    record = {
                        "document_number": cols[0],
                        "transaction_date": cols[1],
                        "village": cols[2],
                        "property_type": cols[3],
                        "extent_area": cols[4],
                        "sale_consideration_value": cols[5]
                    }
                    
                    # Basic validation
                    if record["document_number"] and record["transaction_date"]:
                        data.append(record)
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Error extracting table data: {e}")
            return []
    
    def scrape_all_pages(self, driver):
        """
        Scrape data from all pagination pages
        
        Args:
            driver: Selenium WebDriver
            
        Returns:
            list: Combined data from all pages
        """
        all_data = []
        page_num = 1
        max_pages = 100  # Safety limit
        
        while page_num <= max_pages:
            logger.info(f"         📄 Page {page_num}")
            
            # Extract data from current page
            page_data = self.extract_table_data(driver)
            
            if not page_data:
                logger.info(f"         ℹ️  No data on page {page_num}, stopping pagination")
                break
            
            all_data.extend(page_data)
            logger.info(f"         ✅ Extracted {len(page_data)} records")
            
            # Check for next page
            try:
                # Find next button
                next_buttons = driver.find_elements(By.CSS_SELECTOR, "a.next, a[rel='next'], a:contains('Next')")
                
                if not next_buttons:
                    break
                
                next_btn = next_buttons[0]
                
                # Check if disabled
                if "disabled" in next_btn.get_attribute("class") or not next_btn.is_enabled():
                    break
                
                # Click next
                next_btn.click()
                time.sleep(3)  # Wait for page load
                page_num += 1
                
            except (NoSuchElementException, StaleElementReferenceException):
                # No more pages
                break
            except Exception as e:
                logger.warning(f"         ⚠️  Pagination error: {e}")
                break
        
        return all_data
    
    def scrape_location_quarter(self, driver, location, date_range):
        """
        Scrape data for specific location and quarter
        
        Args:
            driver: Selenium WebDriver
            location: Location name
            date_range: Tuple of (start_date, end_date, quarter_label)
            
        Returns:
            list: Scraped records
        """
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
            
            # Fill district
            try:
                district_select = Select(driver.find_element(By.ID, "district"))
                district_select.select_by_visible_text(self.district)
                time.sleep(1)
            except Exception as e:
                logger.error(f"         ❌ Could not select district: {e}")
                return []
            
            # Fill mandal
            try:
                mandal_select = Select(driver.find_element(By.ID, "mandal"))
                mandal_select.select_by_visible_text(self.mandal)
                time.sleep(1)
            except Exception as e:
                logger.error(f"         ❌ Could not select mandal: {e}")
                return []
            
            # Fill village
            try:
                village_select = Select(driver.find_element(By.ID, "village"))
                village_select.select_by_visible_text(location)
                time.sleep(1)
            except NoSuchElementException:
                logger.warning(f"         ⚠️  Location '{location}' not found in dropdown")
                self.progress['failed'].append({
                    'task': task_key,
                    'error': 'Location not in dropdown',
                    'timestamp': datetime.now().isoformat()
                })
                self._save_progress()
                return []
            
            # Fill dates
            from_date_input = driver.find_element(By.ID, "fromDate")
            from_date_input.clear()
            from_date_input.send_keys(start_date)
            
            to_date_input = driver.find_element(By.ID, "toDate")
            to_date_input.clear()
            to_date_input.send_keys(end_date)
            
            time.sleep(1)
            
            # Wait for CAPTCHA
            if not self.wait_for_captcha(driver):
                logger.warning(f"         ⚠️  CAPTCHA timeout, skipping")
                return []
            
            # Submit form
            submit_btn = driver.find_element(By.ID, "submit")
            submit_btn.click()
            time.sleep(5)
            
            # Check for "no records" message
            page_text = driver.page_source.lower()
            if "no records" in page_text or "no data" in page_text or "no results" in page_text:
                logger.info(f"         ℹ️  No records found")
                self.progress['completed'].add(task_key)
                self._save_progress()
                return []
            
            # Scrape all pages
            data = self.scrape_all_pages(driver)
            
            # Add metadata to each record
            for record in data:
                record.update({
                    "district": self.district,
                    "mandal": self.mandal,
                    "quarter": quarter,
                    "scraped_at": datetime.now().isoformat()
                })
            
            # Mark as completed
            self.progress['completed'].add(task_key)
            self.progress['stats']['total_records'] += len(data)
            self._save_progress()
            
            logger.info(f"         ✅ Scraped {len(data)} records")
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
        if not self.results:
            return
        
        try:
            df = pd.DataFrame(self.results)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            checkpoint_file = self.data_dir / f"checkpoint_{timestamp}.csv"
            df.to_csv(checkpoint_file, index=False, encoding='utf-8')
            
            logger.info(f"💾 Checkpoint saved: {checkpoint_file.name} ({len(df)} records)")
            
            # Clear results after saving
            self.results = []
            
        except Exception as e:
            logger.error(f"❌ Could not save checkpoint: {e}")
    
    def run(self):
        """Main scraping execution"""
        logger.info("\n" + "="*80)
        logger.info("🚀 STARTING IGRS SCRAPER")
        logger.info("="*80)
        
        # Get locations
        locations = self.get_locations_from_db()
        self.progress['stats']['locations_total'] = len(locations)
        
        logger.info(f"\n📊 Configuration:")
        logger.info(f"   Locations: {len(locations)}")
        logger.info(f"   Quarters: {len(self.date_ranges)}")
        logger.info(f"   Total tasks: {len(locations) * len(self.date_ranges)}")
        logger.info(f"   Already completed: {len(self.progress['completed'])}")
        
        # Setup driver
        driver = self.setup_driver()
        
        try:
            for idx, location in enumerate(locations, 1):
                logger.info(f"\n{'='*80}")
                logger.info(f"📍 [{idx}/{len(locations)}] {location}")
                logger.info(f"{'='*80}")
                
                for date_range in self.date_ranges:
                    quarter = date_range[2]
                    logger.info(f"      📅 {quarter}")
                    
                    # Scrape this location-quarter combination
                    data = self.scrape_location_quarter(driver, location, date_range)
                    
                    if data:
                        self.results.extend(data)
                    
                    # Save checkpoint if needed
                    if len(self.results) >= self.checkpoint_size:
                        self.save_checkpoint()
                
                # Update location completion
                self.progress['stats']['locations_completed'] = idx
                self._save_progress()
                
                # Progress summary
                logger.info(f"\n   📊 Progress: {idx}/{len(locations)} locations")
                logger.info(f"   📊 Total records: {self.progress['stats']['total_records']}")
            
            # Final checkpoint
            self.save_checkpoint()
            
            # Combine and clean data
            self.finalize_data()
            
        except KeyboardInterrupt:
            logger.info("\n⚠️ Interrupted by user")
            self.save_checkpoint()
        except Exception as e:
            logger.error(f"\n❌ Fatal error: {e}")
            self.save_checkpoint()
        finally:
            driver.quit()
            self.cleanup()
    
    def finalize_data(self):
        """Combine all checkpoints and create final cleaned dataset"""
        logger.info("\n" + "="*80)
        logger.info("📦 FINALIZING DATA")
        logger.info("="*80)
        
        checkpoint_files = list(self.data_dir.glob("checkpoint_*.csv"))
        
        if not checkpoint_files:
            logger.warning("No checkpoint files found")
            return
        
        logger.info(f"Found {len(checkpoint_files)} checkpoint files")
        
        # Load all checkpoints
        dfs = []
        for file in checkpoint_files:
            try:
                df = pd.read_csv(file, encoding='utf-8')
                dfs.append(df)
                logger.info(f"   ✅ Loaded: {file.name} ({len(df)} records)")
            except Exception as e:
                logger.error(f"   ❌ Error loading {file.name}: {e}")
        
        if not dfs:
            logger.warning("No data to finalize")
            return
        
        # Combine all data
        df = pd.concat(dfs, ignore_index=True)
        logger.info(f"\n✅ Combined: {len(df)} total records")
        
        # Data cleaning
        logger.info("\n🧹 Cleaning data...")
        
        # Clean sale value
        df["sale_consideration_value"] = pd.to_numeric(
            df["sale_consideration_value"].astype(str).str.replace(",", "").str.replace("₹", "").str.strip(),
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
        df["year_quarter"] = df["transaction_date"].dt.to_period("Q").astype(str)
        
        # Remove duplicates
        before_dedup = len(df)
        df = df.drop_duplicates(subset=["document_number"], keep="first")
        logger.info(f"   Removed {before_dedup - len(df)} duplicates")
        
        # Remove invalid records
        df = df[df["sale_consideration_value"].notna()]
        df = df[df["sale_consideration_value"] > 0]
        logger.info(f"   Final records: {len(df)}")
        
        # Save final file
        final_file = self.data_dir / f"igrs_final_{datetime.now().strftime('%Y%m%d')}.csv"
        df.to_csv(final_file, index=False, encoding='utf-8')
        
        # Summary
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ SCRAPING COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"💾 Final File: {final_file}")
        logger.info(f"📊 Total Records: {len(df):,}")
        logger.info(f"📅 Date Range: {df['transaction_date'].min()} to {df['transaction_date'].max()}")
        logger.info(f"💰 Total Value: ₹{df['sale_consideration_value'].sum():,.0f}")
        logger.info(f"📍 Unique Locations: {df['village'].nunique()}")
        logger.info(f"🏠 Property Types: {', '.join(df['property_type'].value_counts().head(5).index.tolist())}")
        logger.info(f"{'='*80}")
    
    def cleanup(self):
        """Cleanup resources"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        logger.info("✅ Cleanup complete")


if __name__ == "__main__":
    scraper = IGRSScraper(
        district="RANGAREDDY",
        mandal="Serilingampally"
    )
    scraper.run()
