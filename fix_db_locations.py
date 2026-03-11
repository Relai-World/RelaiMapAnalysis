"""
Fix Location Spellings in Database
Fetches all 180 locations from DB and corrects misspellings
"""

import psycopg2
from psycopg2.extras import execute_batch
import pandas as pd
from dotenv import load_dotenv
import os
import logging
from difflib import get_close_matches
import json

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Comprehensive correct spellings for Hyderabad locations
CORRECT_SPELLINGS = {
    # Major IT hubs
    "Gachibowli": ["Gachibowli", "Gachi Bowli", "Gacchi Bowli", "Gachibouli", "Gachibowly"],
    "Madhapur": ["Madhapur", "Madhpur", "Madapoor", "Madhapoor", "Madhapur"],
    "Kondapur": ["Kondapur", "Kondapoor", "Konda Pur", "Kondapoor"],
    "HITEC City": ["HITEC City", "Hitech City", "Hi-Tech City", "Hi Tech City", "Hitec City", "HiTec City"],
    "Nanakramguda": ["Nanakramguda", "Nanakram Guda", "Nanak Ramguda", "Nanakramguda", "Nanakram guda"],
    "Financial District": ["Financial District", "Fin District", "Financial Dist"],
    
    # Residential areas
    "Manikonda": ["Manikonda", "Mani Konda", "Manikonda"],
    "Miyapur": ["Miyapur", "Miyapoor", "Miya Pur", "Miyapur"],
    "Kukatpally": ["Kukatpally", "Kukatpalli", "Kukat Pally", "KPHB", "Kukatpally"],
    "Hafeezpet": ["Hafeezpet", "Hafeez Pet", "Hafizpet", "Hafeezpet"],
    "Nallagandla": ["Nallagandla", "Nalla Gandla", "Nallagandla"],
    "Gopanpally": ["Gopanpally", "Gopan Pally", "Gopanpalli", "Gopanpally"],
    "Kokapet": ["Kokapet", "Koka Pet", "Kokapeta", "Kokapet"],
    "Tellapur": ["Tellapur", "Tella Pur", "Tellapoor", "Tellapur"],
    "Kollur": ["Kollur", "Kolluru", "Kolur", "Kollur"],
    "Bachupally": ["Bachupally", "Bachupalli", "Bachu Pally", "Bachupally"],
    "Nizampet": ["Nizampet", "Nizam Pet", "Nizampeta", "Nizampet"],
    "Pragathi Nagar": ["Pragathi Nagar", "Pragathinagar", "Pragati Nagar", "Pragathi Nagar"],
    "Lingampally": ["Lingampally", "Lingampalli", "Lingam Pally", "Lingampally"],
    "Chandanagar": ["Chandanagar", "Chanda Nagar", "Chanda nagar", "Chandanagar"],
    
    # Central areas
    "Banjara Hills": ["Banjara Hills", "Banjarahills", "Banjara Hill", "Banjara Hills"],
    "Jubilee Hills": ["Jubilee Hills", "Jubileehills", "Jubilee Hill", "Jubilee Hills"],
    "Somajiguda": ["Somajiguda", "Somaji Guda", "Somajiguda"],
    "Panjagutta": ["Panjagutta", "Panja Gutta", "Punjagutta", "Panjagutta"],
    "Punjagutta": ["Punjagutta", "Punja Gutta", "Panjagutta", "Punjagutta"],
    "Ameerpet": ["Ameerpet", "Ameer Pet", "Ameerpeta", "Ameerpet"],
    "Begumpet": ["Begumpet", "Begum Pet", "Begumpeta", "Begumpet"],
    "Mehdipatnam": ["Mehdipatnam", "Mehdi Patnam", "Mehdipatnam"],
    "Tolichowki": ["Tolichowki", "Toli Chowki", "Tolichowki"],
    
    # East Hyderabad
    "Uppal": ["Uppal", "Uppala", "Uppal"],
    "Nacharam": ["Nacharam", "Nacha Ram", "Nacharam"],
    "Habsiguda": ["Habsiguda", "Habsi Guda", "Habsiguda"],
    "Tarnaka": ["Tarnaka", "Tar Naka", "Tarnaka"],
    "Malkajgiri": ["Malkajgiri", "Malkaj Giri", "Malkajgiri"],
    "Kapra": ["Kapra", "Kapara", "Kapra"],
    "Boduppal": ["Boduppal", "Bodupal", "Boduppal"],
    "Peerzadiguda": ["Peerzadiguda", "Peerzadi Guda", "Peerzadiguda"],
    
    # South Hyderabad
    "Attapur": ["Attapur", "Atta Pur", "Attapoor", "Attapur"],
    "Rajendra Nagar": ["Rajendra Nagar", "Rajendranagar", "Rajendra nagar", "Rajendra Nagar"],
    "Shamshabad": ["Shamshabad", "Shamsabad", "Shamshabad"],
    "Malakpet": ["Malakpet", "Malak Pet", "Malakpeta", "Malakpet"],
    "Dilsukhnagar": ["Dilsukhnagar", "Dilsukh Nagar", "Dilsukhnagar"],
    "LB Nagar": ["LB Nagar", "L.B.Nagar", "L B Nagar", "Lal Bahadur Nagar", "LB Nagar"],
    "Kothapet": ["Kothapet", "Kotha Pet", "Kothapeta", "Kothapet"],
    "Meerpet": ["Meerpet", "Meer Pet", "Meerpeta", "Meerpet"],
    
    # North Hyderabad
    "Secunderabad": ["Secunderabad", "Secundrabad", "Secunderabad"],
    "Alwal": ["Alwal", "Al Wal", "Alwal"],
    "Trimulgherry": ["Trimulgherry", "Trimulgerry", "Trimulgherry"],
    "Bowenpally": ["Bowenpally", "Bowen Pally", "Bowenpalli", "Bowenpally"],
    "Sainikpuri": ["Sainikpuri", "Sainik Puri", "Sainikpuri"],
    "Kompally": ["Kompally", "Kompalli", "Kom Pally", "Kompally"],
    "Medchal": ["Medchal", "Med Chal", "Medchal"],
    "Dundigal": ["Dundigal", "Dundi Gal", "Dundigal"],
    "Keesara": ["Keesara", "Keesara", "Kisara", "Keesara"],
    "Ghatkesar": ["Ghatkesar", "Ghatkeser", "Ghatkeshar", "Ghatkesar"],
    
    # Other areas
    "Serilingampally": ["Serilingampally", "Serilingampalli", "Seriling Ampally", "Serilingampally"],
    "Gowlidoddy": ["Gowlidoddy", "Gowli Doddy", "Gowlidoddi", "Gowlidoddy"],
    "Puppalaguda": ["Puppalaguda", "Puppala Guda", "Puppalaguda"],
    "Khajaguda": ["Khajaguda", "Khaja Guda", "Khajaguda"],
    "Kismatpur": ["Kismatpur", "Kismat Pur", "Kismatpur"],
    "Moosapet": ["Moosapet", "Moosa Pet", "Moosapeta", "Moosapet"],
    "Yousufguda": ["Yousufguda", "Yousuf Guda", "Yousufguda"],
    "Kachiguda": ["Kachiguda", "Kachi Guda", "Kachiguda"],
    "Abids": ["Abids", "Abid", "Abids"],
    "Charminar": ["Charminar", "Char Minar", "Charminar"],
    "Himayat Nagar": ["Himayat Nagar", "Himayatnagar", "Himayat nagar", "Himayat Nagar"],
    "Sanath Nagar": ["Sanath Nagar", "Sanathnagar", "Sanath nagar", "Sanath Nagar"],
    "Ashok Nagar": ["Ashok Nagar", "Ashoknagar", "Ashok nagar", "Ashok Nagar"],
    "Osman Nagar": ["Osman Nagar", "Osmannagar", "Osman nagar", "Osman Nagar"],
    "Saidabad": ["Saidabad", "Saida Bad", "Saidabad"],
    "Hayathnagar": ["Hayathnagar", "Hayath Nagar", "Hayathnagar"],
    "Rampally": ["Rampally", "Ram Pally", "Rampalli", "Rampally"],
    "Turkayamjal": ["Turkayamjal", "Turkayam Jal", "Turkayamjal"],
    "Adibatla": ["Adibatla", "Adi Batla", "Adibatla"],
    "Ameenpur": ["Ameenpur", "Ameen Pur", "Ameenpur"],
    "Budwel": ["Budwel", "Budvel", "Budwel"],
    "Chegur": ["Chegur", "Cheguru", "Chegur"],
    "Hakimpet": ["Hakimpet", "Hakim Pet", "Hakimpet"],
    "Gundlapochampally": ["Gundlapochampally", "Gundla Pochampally", "Gundlapochampally"],
    "Yamnampet": ["Yamnampet", "Yamnam Pet", "Yamnampet"],
    "Bacharam": ["Bacharam", "Bacha Ram", "Bacharam"],
    "Chitkul": ["Chitkul", "Chit Kul", "Chitkul"],
    "Dulapally": ["Dulapally", "Dula Pally", "Dulapalli", "Dulapally"],
    "Guttala Begumpet": ["Guttala Begumpet", "Guttala Begum Pet", "Guttala Begumpet"],
    "Hastinapuram": ["Hastinapuram", "Hastina Puram", "Hastinapuram"],
    "Bolarum": ["Bolarum", "Bola Rum", "Bolarum"],
    "Bollaram": ["Bollaram", "Bolla Ram", "Bollaram"],
    "Bowrampet": ["Bowrampet", "Bowram Pet", "Bowrampet"],
    "Chengicherla": ["Chengicherla", "Chengi Cherla", "Chengicherla"],
    "Chiryala": ["Chiryala", "Chir Yala", "Chiryala"],
    "Gollur": ["Gollur", "Golluru", "Gollur"],
    "Gowdavalli": ["Gowdavalli", "Gowda Valli", "Gowdavalli"],
    "Injapur": ["Injapur", "Inja Pur", "Injapur"],
    "Kajaguda": ["Kajaguda", "Kaja Guda", "Kajaguda"],
    "Kongara Kalan": ["Kongara Kalan", "Kongara kalan", "Kongara Kalan"],
    "Krishnareddypet": ["Krishnareddypet", "Krishna Reddy Pet", "Krishnareddypet"],
    "Madeenaguda": ["Madeenaguda", "Madeena Guda", "Madeenaguda"],
    "Mangalpalli": ["Mangalpalli", "Mangal Palli", "Mangalpalli"],
    "Kandukur": ["Kandukur", "Kandu Kur", "Kandukur"],
    "Manneguda": ["Manneguda", "Manne Guda", "Manneguda"],
    "Mansanpally": ["Mansanpally", "Mansan Pally", "Mansanpalli", "Mansanpally"],
    "Muthangi": ["Muthangi", "Muthan Gi", "Muthangi"],
    "Shankarpally": ["Shankarpally", "Shankar Pally", "Shankarpalli", "Shankarpally"],
    "Suraram": ["Suraram", "Sura Ram", "Suraram"],
    "Neopolis": ["Neopolis", "Neo Polis", "Neopolis"],
    "Pati Kollur": ["Pati Kollur", "Pati kollur", "Pati Kollur"],
    "Patighanpur": ["Patighanpur", "Patighan Pur", "Patighanpur"],
    "Peeramcheruvu": ["Peeramcheruvu", "Peeram Cheruvu", "Peeramcheruvu"],
    "Pocharam": ["Pocharam", "Pocha Ram", "Pocharam"],
    "Gagillapur": ["Gagillapur", "Gagilla Pur", "Gagillapur"],
    "Alkapur": ["Alkapur", "Alka Pur", "Alkapur"],
    "Isnapur": ["Isnapur", "Isna Pur", "Isnapur"],
    "Kavadiguda": ["Kavadiguda", "Kavadi Guda", "Kavadiguda"],
    "Kandlakoya": ["Kandlakoya", "Kandla Koya", "Kandlakoya"],
    "Karmanghat": ["Karmanghat", "Karman Ghat", "Karmanghat"],
    "Mansoorabad": ["Mansoorabad", "Mansoora Bad", "Mansoorabad"],
    "Tukkuguda": ["Tukkuguda", "Tukku Guda", "Tukkuguda"],
    "Raviryal": ["Raviryal", "Ravi Ryal", "Raviryal"],
    "Annojiguda": ["Annojiguda", "Annoji Guda", "Annojiguda"],
    "Appa Junction": ["Appa Junction", "Appa junction", "Appa Junction"],
    "Yapral": ["Yapral", "Yap Ral", "Yapral"],
    "Gandamguda": ["Gandamguda", "Gandam Guda", "Gandamguda"],
    "Gandi Maisamma": ["Gandi Maisamma", "Gandi maisamma", "Gandi Maisamma"],
}

class DatabaseLocationFixer:
    
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        self.cur = self.conn.cursor()
        
        # Build reverse lookup
        self.correction_map = {}
        for correct, variants in CORRECT_SPELLINGS.items():
            for variant in variants:
                self.correction_map[variant.lower().strip()] = correct
    
    def get_all_unique_locations(self):
        """Get all unique location names from database"""
        logger.info("🔍 Fetching all unique locations from database...")
        
        # Query to get all unique locations from locations table
        query = """
            SELECT name, COUNT(*) as count
            FROM locations
            WHERE name IS NOT NULL AND city = 'Hyderabad'
            GROUP BY name
            ORDER BY name
        """
        
        try:
            self.cur.execute(query)
            results = self.cur.fetchall()
            logger.info(f"✅ Found {len(results)} unique locations in Hyderabad")
            return results
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return []
    
    def analyze_spellings(self, locations):
        """Analyze and identify misspellings"""
        logger.info("\n" + "="*80)
        logger.info("📊 SPELLING ANALYSIS")
        logger.info("="*80)
        
        corrections = []
        correct_count = 0
        incorrect_count = 0
        
        for location, count in locations:
            location_clean = location.strip()
            location_lower = location_clean.lower()
            
            # Check if it needs correction
            if location_lower in self.correction_map:
                correct_spelling = self.correction_map[location_lower]
                
                if location_clean != correct_spelling:
                    corrections.append({
                        'incorrect': location_clean,
                        'correct': correct_spelling,
                        'count': count
                    })
                    incorrect_count += 1
                    logger.info(f"❌ '{location_clean}' ({count} records) → ✅ '{correct_spelling}'")
                else:
                    correct_count += 1
                    logger.info(f"✅ '{location_clean}' ({count} records) - Correct")
            else:
                logger.warning(f"⚠️  '{location_clean}' ({count} records) - Unknown location")
        
        logger.info(f"\n📊 Summary:")
        logger.info(f"   ✅ Correct: {correct_count}")
        logger.info(f"   ❌ Incorrect: {incorrect_count}")
        logger.info(f"   ⚠️  Unknown: {len(locations) - correct_count - incorrect_count}")
        
        return corrections
    
    def apply_corrections(self, corrections, dry_run=True):
        """Apply corrections to database"""
        if not corrections:
            logger.info("\n✅ No corrections needed!")
            return
        
        logger.info(f"\n{'='*80}")
        if dry_run:
            logger.info("⚠️  DRY RUN MODE - No changes will be made")
        else:
            logger.info("🔧 APPLYING CORRECTIONS")
        logger.info(f"{'='*80}\n")
        
        total_records = 0
        
        for correction in corrections:
            incorrect = correction['incorrect']
            correct = correction['correct']
            count = correction['count']
            
            if dry_run:
                logger.info(f"[DRY RUN] Would update {count} records: '{incorrect}' → '{correct}'")
                total_records += count
            else:
                try:
                    query = "UPDATE locations SET name = %s WHERE name = %s AND city = 'Hyderabad'"
                    self.cur.execute(query, (correct, incorrect))
                    affected = self.cur.rowcount
                    self.conn.commit()
                    total_records += affected
                    logger.info(f"✅ Updated {affected} records: '{incorrect}' → '{correct}'")
                except Exception as e:
                    logger.error(f"❌ Error updating '{incorrect}': {e}")
                    self.conn.rollback()
        
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 Total records {'would be ' if dry_run else ''}updated: {total_records}")
        logger.info(f"{'='*80}")
    
    def export_report(self, locations, corrections):
        """Export detailed report"""
        report = {
            'total_locations': len(locations),
            'corrections_needed': len(corrections),
            'all_locations': [{'name': loc, 'count': cnt} for loc, cnt in locations],
            'corrections': corrections
        }
        
        with open('location_spelling_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("\n💾 Report exported to: location_spelling_report.json")
    
    def run(self, dry_run=True):
        """Main execution"""
        logger.info("🚀 Database Location Spelling Fixer")
        logger.info("="*80)
        
        # Get all locations
        locations = self.get_all_unique_locations()
        
        if not locations:
            logger.error("No locations found in database")
            return
        
        # Analyze spellings
        corrections = self.analyze_spellings(locations)
        
        # Export report
        self.export_report(locations, corrections)
        
        # Apply corrections
        self.apply_corrections(corrections, dry_run=dry_run)
        
        if dry_run and corrections:
            logger.info("\n" + "="*80)
            logger.info("ℹ️  To apply corrections, run: python fix_db_locations.py --apply")
            logger.info("="*80)
        
        self.cur.close()
        self.conn.close()


if __name__ == "__main__":
    import sys
    
    # Check if --apply flag is provided
    apply_changes = '--apply' in sys.argv
    
    fixer = DatabaseLocationFixer()
    fixer.run(dry_run=not apply_changes)
