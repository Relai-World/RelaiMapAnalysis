"""
Interactive Location Spelling Fixer
Review and approve each correction individually
"""

import psycopg2
from dotenv import load_dotenv
import os
import logging
from difflib import get_close_matches

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Known correct spellings
CORRECT_LOCATIONS = [
    "Gachibowli", "Madhapur", "Kondapur", "Hitech City", "Nanakramguda",
    "Manikonda", "Miyapur", "Kukatpally", "Banjara Hills", "Jubilee Hills",
    "Secunderabad", "Attapur", "Shamshabad", "Kompally", "Sainikpuri",
    "Ghatkesar", "Hafeezpet", "Chanda Nagar", "Lingampally", "Nallagandla",
    "Gowlidoddy", "Kokapet", "Tellapur", "Kollur", "Bachupally", "Nizampet",
    "Pragathi Nagar", "Moosapet", "Ameerpet", "Begumpet", "Somajiguda",
    "Panjagutta", "Mehdipatnam", "Tolichowki", "Malakpet", "Dilsukhnagar",
    "LB Nagar", "Uppal", "Nacharam", "Habsiguda", "Tarnaka", "Malkajgiri",
    "Kapra", "Medchal", "Dundigal", "Keesara", "Alwal", "Trimulgherry",
    "Bowenpally", "Serilingampally", "Rajendranagar"
]

class InteractiveLocationFixer:
    
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        self.cur = self.conn.cursor()
        self.corrections_made = []
    
    def find_location_columns(self):
        """Find all tables with location columns"""
        self.cur.execute("""
            SELECT DISTINCT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND (
                column_name IN ('location', 'village', 'locality', 'area_name', 'mandal', 'district')
                OR column_name ILIKE '%location%'
                OR column_name ILIKE '%village%'
                OR column_name ILIKE '%locality%'
            )
            ORDER BY table_name, column_name;
        """)
        return self.cur.fetchall()
    
    def get_unique_values(self, table, column):
        """Get unique location values with counts"""
        query = f"""
            SELECT {column}, COUNT(*) as count
            FROM {table}
            WHERE {column} IS NOT NULL AND {column} != ''
            GROUP BY {column}
            ORDER BY count DESC
        """
        self.cur.execute(query)
        return self.cur.fetchall()
    
    def suggest_correction(self, incorrect_spelling):
        """Suggest correct spelling using fuzzy matching"""
        matches = get_close_matches(incorrect_spelling, CORRECT_LOCATIONS, n=3, cutoff=0.6)
        return matches
    
    def update_location(self, table, column, old_value, new_value):
        """Update location spelling in database"""
        try:
            query = f"UPDATE {table} SET {column} = %s WHERE {column} = %s"
            self.cur.execute(query, (new_value, old_value))
            affected = self.cur.rowcount
            self.conn.commit()
            
            self.corrections_made.append({
                'table': table,
                'column': column,
                'old': old_value,
                'new': new_value,
                'count': affected
            })
            
            logger.info(f"✅ Updated {affected} records")
            return True
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            self.conn.rollback()
            return False
    
    def run_interactive(self):
        """Interactive correction process"""
        print("\n" + "="*80)
        print("🔧 INTERACTIVE LOCATION SPELLING FIXER")
        print("="*80)
        
        tables_columns = self.find_location_columns()
        
        print(f"\nFound {len(tables_columns)} location columns")
        
        for table, column in tables_columns:
            print(f"\n{'='*80}")
            print(f"📋 Table: {table}.{column}")
            print("="*80)
            
            locations = self.get_unique_values(table, column)
            
            if not locations:
                print("   No data found")
                continue
            
            print(f"\nFound {len(locations)} unique values:\n")
            
            for location, count in locations:
                # Check if it's potentially misspelled
                if location not in CORRECT_LOCATIONS:
                    print(f"\n❓ '{location}' ({count} records)")
                    
                    # Suggest corrections
                    suggestions = self.suggest_correction(location)
                    
                    if suggestions:
                        print(f"   💡 Suggestions: {', '.join(suggestions)}")
                    
                    print("\n   Options:")
                    print("   1. Enter correct spelling")
                    print("   2. Skip (it's correct)")
                    print("   3. Skip all remaining in this table")
                    print("   4. Quit")
                    
                    choice = input("\n   Your choice (1/2/3/4): ").strip()
                    
                    if choice == "1":
                        correct = input("   Enter correct spelling: ").strip()
                        if correct:
                            confirm = input(f"   Update '{location}' → '{correct}'? (y/n): ")
                            if confirm.lower() == 'y':
                                self.update_location(table, column, location, correct)
                    
                    elif choice == "2":
                        print("   ⏭️  Skipped")
                        continue
                    
                    elif choice == "3":
                        print("   ⏭️  Skipping remaining in this table")
                        break
                    
                    elif choice == "4":
                        print("\n👋 Exiting...")
                        self.show_summary()
                        return
        
        self.show_summary()
    
    def show_summary(self):
        """Show summary of corrections made"""
        print("\n" + "="*80)
        print("📊 CORRECTION SUMMARY")
        print("="*80)
        
        if not self.corrections_made:
            print("\nNo corrections were made")
            return
        
        print(f"\nTotal corrections: {len(self.corrections_made)}")
        total_records = sum(c['count'] for c in self.corrections_made)
        print(f"Total records updated: {total_records}\n")
        
        for correction in self.corrections_made:
            print(f"✅ {correction['table']}.{correction['column']}")
            print(f"   '{correction['old']}' → '{correction['new']}' ({correction['count']} records)")
    
    def close(self):
        """Close database connection"""
        self.cur.close()
        self.conn.close()


if __name__ == "__main__":
    fixer = InteractiveLocationFixer()
    
    try:
        fixer.run_interactive()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        fixer.show_summary()
    finally:
        fixer.close()
