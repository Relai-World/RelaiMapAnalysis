"""
Fix Incorrect Location Spellings in Database
Identifies and corrects misspelled location names
"""

import psycopg2
from psycopg2.extras import execute_batch
import pandas as pd
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Correct spelling mappings
LOCATION_CORRECTIONS = {
    # Common misspellings in Hyderabad area
    "Gachibowli": ["Gachibowli", "Gachi Bowli", "Gacchi Bowli", "Gachibouli"],
    "Madhapur": ["Madhapur", "Madhpur", "Madapoor", "Madhapoor"],
    "Kondapur": ["Kondapur", "Kondapoor", "Konda Pur"],
    "Hitech City": ["Hitech City", "Hi-Tech City", "Hi Tech City", "Hitec City", "HITEC City"],
    "Nanakramguda": ["Nanakramguda", "Nanakram Guda", "Nanak Ramguda", "Nanakramguda"],
    "Manikonda": ["Manikonda", "Mani Konda", "Manikonda"],
    "Miyapur": ["Miyapur", "Miyapoor", "Miya Pur"],
    "Kukatpally": ["Kukatpally", "Kukatpalli", "Kukat Pally", "KPHB"],
    "Banjara Hills": ["Banjara Hills", "Banjarahills", "Banjara Hill"],
    "Jubilee Hills": ["Jubilee Hills", "Jubileehills", "Jubilee Hill"],
    "Secunderabad": ["Secunderabad", "Secundrabad", "Secunderabad"],
    "Attapur": ["Attapur", "Atta Pur", "Attapoor"],
    "Shamshabad": ["Shamshabad", "Shamsabad", "Shamshabad"],
    "Kompally": ["Kompally", "Kompalli", "Kom Pally"],
    "Sainikpuri": ["Sainikpuri", "Sainik Puri", "Sainikpuri"],
    "Ghatkesar": ["Ghatkesar", "Ghatkeser", "Ghatkeshar"],
    "Hafeezpet": ["Hafeezpet", "Hafeez Pet", "Hafizpet"],
    "Chanda Nagar": ["Chanda Nagar", "Chandanagar", "Chanda Nagar"],
    "Lingampally": ["Lingampally", "Lingampalli", "Lingam Pally"],
    "Nallagandla": ["Nallagandla", "Nalla Gandla", "Nallagandla"],
    "Gowlidoddy": ["Gowlidoddy", "Gowli Doddy", "Gowlidoddi"],
    "Kokapet": ["Kokapet", "Koka Pet", "Kokapeta"],
    "Tellapur": ["Tellapur", "Tella Pur", "Tellapoor"],
    "Kollur": ["Kollur", "Kolluru", "Kolur"],
    "Bachupally": ["Bachupally", "Bachupalli", "Bachu Pally"],
    "Nizampet": ["Nizampet", "Nizam Pet", "Nizampeta"],
    "Pragathi Nagar": ["Pragathi Nagar", "Pragathinagar", "Pragati Nagar"],
    "Moosapet": ["Moosapet", "Moosa Pet", "Moosapeta"],
    "Ameerpet": ["Ameerpet", "Ameer Pet", "Ameerpeta"],
    "Begumpet": ["Begumpet", "Begum Pet", "Begumpeta"],
    "Somajiguda": ["Somajiguda", "Somaji Guda", "Somajiguda"],
    "Panjagutta": ["Panjagutta", "Panja Gutta", "Punjagutta"],
    "Mehdipatnam": ["Mehdipatnam", "Mehdi Patnam", "Mehdipatnam"],
    "Tolichowki": ["Tolichowki", "Toli Chowki", "Tolichowki"],
    "Malakpet": ["Malakpet", "Malak Pet", "Malakpeta"],
    "Dilsukhnagar": ["Dilsukhnagar", "Dilsukh Nagar", "Dilsukhnagar"],
    "LB Nagar": ["LB Nagar", "L.B.Nagar", "LB Nagar", "Lal Bahadur Nagar"],
    "Uppal": ["Uppal", "Uppala", "Uppal"],
    "Nacharam": ["Nacharam", "Nacha Ram", "Nacharam"],
    "Habsiguda": ["Habsiguda", "Habsi Guda", "Habsiguda"],
    "Tarnaka": ["Tarnaka", "Tar Naka", "Tarnaka"],
    "Malkajgiri": ["Malkajgiri", "Malkaj Giri", "Malkajgiri"],
    "Kapra": ["Kapra", "Kapara", "Kapra"],
    "Medchal": ["Medchal", "Med Chal", "Medchal"],
    "Dundigal": ["Dundigal", "Dundi Gal", "Dundigal"],
    "Keesara": ["Keesara", "Keesara", "Kisara"],
    "Alwal": ["Alwal", "Al Wal", "Alwal"],
    "Trimulgherry": ["Trimulgherry", "Trimulgerry", "Trimulgherry"],
    "Bowenpally": ["Bowenpally", "Bowen Pally", "Bowenpalli"],
    "Serilingampally": ["Serilingampally", "Serilingampalli", "Seriling Ampally"],
    "Rajendranagar": ["Rajendranagar", "Rajendra Nagar", "Rajendranagar"],
}

class LocationSpellingFixer:
    
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        self.cur = self.conn.cursor()
        
        # Build reverse mapping (incorrect -> correct)
        self.correction_map = {}
        for correct, variants in LOCATION_CORRECTIONS.items():
            for variant in variants:
                self.correction_map[variant.lower()] = correct
    
    def get_all_tables_with_location_columns(self):
        """Find all tables that have location-related columns"""
        self.cur.execute("""
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND (
                column_name ILIKE '%location%' OR
                column_name ILIKE '%village%' OR
                column_name ILIKE '%locality%' OR
                column_name ILIKE '%area%' OR
                column_name ILIKE '%mandal%' OR
                column_name ILIKE '%district%'
            )
            ORDER BY table_name, column_name;
        """)
        
        results = self.cur.fetchall()
        logger.info(f"Found {len(results)} location columns across tables")
        
        return results
    
    def get_unique_locations(self, table_name, column_name):
        """Get all unique location values from a table column"""
        try:
            query = f"SELECT DISTINCT {column_name}, COUNT(*) as count FROM {table_name} WHERE {column_name} IS NOT NULL GROUP BY {column_name} ORDER BY count DESC"
            self.cur.execute(query)
            results = self.cur.fetchall()
            return results
        except Exception as e:
            logger.error(f"Error getting locations from {table_name}.{column_name}: {e}")
            return []
    
    def identify_misspellings(self):
        """Identify all misspelled locations in database"""
        logger.info("\n" + "="*80)
        logger.info("🔍 IDENTIFYING MISSPELLINGS")
        logger.info("="*80)
        
        tables_columns = self.get_all_tables_with_location_columns()
        
        all_corrections = []
        
        for table_name, column_name in tables_columns:
            logger.info(f"\n📋 Table: {table_name}.{column_name}")
            
            locations = self.get_unique_locations(table_name, column_name)
            
            if not locations:
                continue
            
            misspellings_found = []
            
            for location, count in locations:
                if not location:
                    continue
                
                location_lower = location.strip().lower()
                
                # Check if this is a known misspelling
                if location_lower in self.correction_map:
                    correct_spelling = self.correction_map[location_lower]
                    
                    # Only flag if it's different from correct spelling
                    if location.strip() != correct_spelling:
                        misspellings_found.append({
                            'table': table_name,
                            'column': column_name,
                            'incorrect': location,
                            'correct': correct_spelling,
                            'count': count
                        })
                        logger.info(f"   ❌ '{location}' ({count} records) → ✅ '{correct_spelling}'")
            
            all_corrections.extend(misspellings_found)
        
        return all_corrections
    
    def preview_corrections(self, corrections):
        """Show summary of corrections to be made"""
        if not corrections:
            logger.info("\n✅ No misspellings found! All locations are correctly spelled.")
            return
        
        logger.info(f"\n" + "="*80)
        logger.info(f"📊 CORRECTION SUMMARY")
        logger.info("="*80)
        
        df = pd.DataFrame(corrections)
        
        # Group by table
        for table in df['table'].unique():
            table_corrections = df[df['table'] == table]
            total_records = table_corrections['count'].sum()
            logger.info(f"\n📋 {table}: {len(table_corrections)} corrections, {total_records} records affected")
            
            for _, row in table_corrections.iterrows():
                logger.info(f"   {row['column']}: '{row['incorrect']}' → '{row['correct']}' ({row['count']} records)")
        
        total_records = df['count'].sum()
        logger.info(f"\n📊 Total: {len(corrections)} corrections, {total_records} records affected")
    
    def apply_corrections(self, corrections, dry_run=True):
        """Apply corrections to database"""
        if not corrections:
            logger.info("No corrections to apply")
            return
        
        if dry_run:
            logger.info("\n⚠️  DRY RUN MODE - No changes will be made")
        else:
            logger.info("\n🔧 APPLYING CORRECTIONS")
        
        for correction in corrections:
            table = correction['table']
            column = correction['column']
            incorrect = correction['incorrect']
            correct = correction['correct']
            count = correction['count']
            
            query = f"UPDATE {table} SET {column} = %s WHERE {column} = %s"
            
            if dry_run:
                logger.info(f"   [DRY RUN] Would update {count} records in {table}.{column}")
            else:
                try:
                    self.cur.execute(query, (correct, incorrect))
                    affected = self.cur.rowcount
                    logger.info(f"   ✅ Updated {affected} records in {table}.{column}: '{incorrect}' → '{correct}'")
                except Exception as e:
                    logger.error(f"   ❌ Error updating {table}.{column}: {e}")
                    self.conn.rollback()
                    continue
        
        if not dry_run:
            self.conn.commit()
            logger.info("\n✅ All corrections applied successfully!")
    
    def add_custom_correction(self, incorrect, correct):
        """Add a custom correction mapping"""
        self.correction_map[incorrect.lower()] = correct
        logger.info(f"Added custom correction: '{incorrect}' → '{correct}'")
    
    def export_corrections_csv(self, corrections, filename="location_corrections.csv"):
        """Export corrections to CSV for review"""
        if corrections:
            df = pd.DataFrame(corrections)
            df.to_csv(filename, index=False)
            logger.info(f"\n💾 Corrections exported to {filename}")
    
    def run(self, dry_run=True):
        """Main execution"""
        logger.info("🚀 Starting Location Spelling Fixer")
        
        # Identify misspellings
        corrections = self.identify_misspellings()
        
        # Preview
        self.preview_corrections(corrections)
        
        # Export for review
        if corrections:
            self.export_corrections_csv(corrections)
        
        # Apply corrections
        if corrections:
            logger.info("\n" + "="*80)
            if dry_run:
                logger.info("Run with dry_run=False to apply changes")
            else:
                confirm = input("\n⚠️  Apply these corrections? (yes/no): ")
                if confirm.lower() == 'yes':
                    self.apply_corrections(corrections, dry_run=False)
                else:
                    logger.info("Cancelled")
        
        self.cur.close()
        self.conn.close()


if __name__ == "__main__":
    fixer = LocationSpellingFixer()
    
    # Step 1: Run in dry-run mode to see what will be changed
    fixer.run(dry_run=True)
    
    # Step 2: Uncomment below to actually apply corrections
    # fixer.run(dry_run=False)
