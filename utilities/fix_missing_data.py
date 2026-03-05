"""Fix: Fill missing insights, infrastructure, and costs for locations that have gaps."""
import psycopg2, os, sys
from dotenv import load_dotenv
sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "post@123"),
    dbname=os.getenv("DB_NAME", "real_estate_intelligence"),
    port=os.getenv("DB_PORT", "5432")
)
cur = conn.cursor()

# Find and fix missing insights
cur.execute("""
    SELECT l.id, l.name FROM locations l 
    LEFT JOIN location_insights li ON li.location_id = l.id 
    WHERE li.location_id IS NULL
""")
missing_insights = cur.fetchall()
print(f"Missing insights: {len(missing_insights)}")
for loc_id, name in missing_insights:
    cur.execute("""
        INSERT INTO location_insights (location_id, avg_sentiment_score, growth_score, investment_score)
        VALUES (%s, 0.0, 0.5, 0.5)
    """, (loc_id,))
    print(f"  Fixed insights: {name} (ID:{loc_id})")

# Find and fix missing infrastructure
cur.execute("""
    SELECT l.id, l.name FROM locations l 
    LEFT JOIN location_infrastructure li ON li.location_id = l.id 
    WHERE li.location_id IS NULL
""")
missing_infra = cur.fetchall()
print(f"\nMissing infrastructure: {len(missing_infra)}")
for loc_id, name in missing_infra:
    cur.execute("""
        INSERT INTO location_infrastructure (location_id, hospitals, schools, metro, airports)
        VALUES (%s, 0, 0, 0, 0)
    """, (loc_id,))
    print(f"  Fixed infra: {name} (ID:{loc_id})")

# Find and fix missing costs
cur.execute("""
    SELECT l.id, l.name FROM locations l 
    LEFT JOIN location_costs lc ON lc.location_id = l.id 
    WHERE lc.location_id IS NULL
""")
missing_costs = cur.fetchall()
print(f"\nMissing costs: {len(missing_costs)}")
for loc_id, name in missing_costs:
    cur.execute("""
        INSERT INTO location_costs (location_id, location_name, property_count, avg_base_price, avg_price_sqft, min_base_price, max_base_price, min_price_sqft, max_price_sqft)
        VALUES (%s, %s, 0, 0, 0, 0, 0, 0, 0)
    """, (loc_id, name))
    print(f"  Fixed costs: {name} (ID:{loc_id})")

conn.commit()

# Final verification
cur.execute("SELECT COUNT(*) FROM locations")
loc_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM location_insights")
ins_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM location_infrastructure")
infra_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM location_costs")
cost_count = cur.fetchone()[0]

print(f"\n{'='*50}")
print(f"  locations:              {loc_count}")
print(f"  location_insights:      {ins_count}")
print(f"  location_infrastructure:{infra_count}")
print(f"  location_costs:         {cost_count}")
print(f"  ALL SYNCED: {'YES' if loc_count == ins_count == infra_count == cost_count else 'NO'}")
print(f"{'='*50}")

cur.close()
conn.close()
