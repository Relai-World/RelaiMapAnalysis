"""
Interactive Location Manager
Fetch all Hyderabad locations and let user correct/remove them
"""

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

class InteractiveLocationManager:
    
    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "post@123"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        self.cur = self.conn.cursor()
        self.changes_made = []
    
    def get_all_locations(self):
        """Fetch all Hyderabad locations"""
        query = """
            SELECT id, name
            FROM locations
            WHERE city = 'Hyderabad'
            ORDER BY name
        """
        self.cur.execute(query)
        return self.cur.fetchall()
    
    def update_location(self, location_id, old_name, new_name):
        """Update location name"""
        try:
            query = "UPDATE locations SET name = %s WHERE id = %s AND city = 'Hyderabad'"
            self.cur.execute(query, (new_name, location_id))
            self.conn.commit()
            print(f"   ✅ Updated: '{old_name}' → '{new_name}'")
            self.changes_made.append({
                'action': 'update',
                'id': location_id,
                'old': old_name,
                'new': new_name
            })
            return True
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.conn.rollback()
            return False
    
    def delete_location(self, location_id, name):
        """Delete location"""
        try:
            query = "DELETE FROM locations WHERE id = %s AND city = 'Hyderabad'"
            self.cur.execute(query, (location_id,))
            self.conn.commit()
            print(f"   🗑️  Deleted: '{name}'")
            self.changes_made.append({
                'action': 'delete',
                'id': location_id,
                'name': name
            })
            return True
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.conn.rollback()
            return False
    
    def run(self):
        """Interactive session"""
        print("\n" + "="*80)
        print("🔧 INTERACTIVE LOCATION MANAGER")
        print("="*80)
        print("\nFetching all Hyderabad locations from database...")
        
        locations = self.get_all_locations()
        total = len(locations)
        
        print(f"\n✅ Found {total} locations\n")
        print("="*80)
        print("Instructions:")
        print("  - Press ENTER to keep location as is")
        print("  - Type new name to update spelling")
        print("  - Type 'DELETE' to remove location")
        print("  - Type 'QUIT' to exit")
        print("="*80)
        
        for idx, (location_id, name) in enumerate(locations, 1):
            print(f"\n[{idx}/{total}] Current: '{name}'")
            
            action = input("   Action (ENTER=keep, new name=update, DELETE=remove, QUIT=exit): ").strip()
            
            if action.upper() == 'QUIT':
                print("\n👋 Exiting...")
                break
            
            elif action.upper() == 'DELETE':
                confirm = input(f"   ⚠️  Confirm delete '{name}'? (yes/no): ")
                if confirm.lower() == 'yes':
                    self.delete_location(location_id, name)
            
            elif action and action != '':
                # Update to new name
                self.update_location(location_id, name, action)
            
            else:
                # Keep as is
                print(f"   ✓ Kept: '{name}'")
        
        self.show_summary()
        self.close()
    
    def show_summary(self):
        """Show summary of changes"""
        print("\n" + "="*80)
        print("📊 SUMMARY OF CHANGES")
        print("="*80)
        
        if not self.changes_made:
            print("\nNo changes were made")
            return
        
        updates = [c for c in self.changes_made if c['action'] == 'update']
        deletes = [c for c in self.changes_made if c['action'] == 'delete']
        
        if updates:
            print(f"\n✏️  Updated ({len(updates)}):")
            for change in updates:
                print(f"   '{change['old']}' → '{change['new']}'")
        
        if deletes:
            print(f"\n🗑️  Deleted ({len(deletes)}):")
            for change in deletes:
                print(f"   '{change['name']}'")
        
        print(f"\n📊 Total changes: {len(self.changes_made)}")
    
    def close(self):
        """Close database connection"""
        self.cur.close()
        self.conn.close()


if __name__ == "__main__":
    manager = InteractiveLocationManager()
    
    try:
        manager.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        manager.show_summary()
        manager.close()
