# 🗺️ OSM Amenities Extraction Guide

## ✅ Yes! You Can Extract Amenities from OpenStreetMap

### **What This Script Does:**

Extracts **30+ types of amenities** for your 7 West Hyderabad locations from OpenStreetMap:

### **Amenities Tracked:**

#### 🏥 **Healthcare (3 types)**
- Hospitals
- Clinics  
- Pharmacies

#### 🏫 **Education (4 types)**
- Schools
- Colleges
- Universities
- Kindergartens

#### 🏪 **Shopping (3 types)**
- Malls
- Supermarkets
- Convenience Stores

#### 🍽️ **Food & Dining (3 types)**
- Restaurants
- Cafes
- Fast Food

#### 🚇 **Transportation (3 types)**
- Metro Stations
- Bus Stops
- Airports

#### 🏦 **Banking (2 types)**
- Banks
- ATMs

#### 🎯 **Recreation (4 types)**
- Parks
- Gyms
- Cinemas
- Playgrounds

#### 🕌 **Religious (1 type)**
- Places of Worship

#### 🚔 **Safety (2 types)**
- Police Stations
- Fire Stations

#### 📚 **Others (3 types)**
- Libraries
- Community Centers
- Post Offices

---

## 🚀 How to Run

### **Step 1: Run the extraction script**
```bash
python extract_osm_amenities.py
```

**Note:** This will take **15-20 minutes** because:
- 7 locations × 30 amenity types = 210 API calls
- 1 second delay between calls (to be polite to OSM)
- Each call takes 2-3 seconds

### **Step 2: View the results**

The script creates two output files:

1. **`OSM_AMENITIES_REPORT.txt`** - Human-readable report
2. **`OSM_AMENITIES_DATA.json`** - Machine-readable JSON

---

## 📊 Sample Output

```
FINANCIAL DISTRICT
==================
Total Amenities: 245

Amenity Type                  Count
-----------------------------------------
Restaurants                   45
ATMs                         38
Banks                        22
Schools                      18
Hospitals                    12
Cafes                        15
...
```

---

## 💾 Next Steps After Extraction

### **Option 1: Store in Database**
Create a table to store this data permanently:

```sql
CREATE TABLE location_amenities_osm (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    amenity_type VARCHAR(50),
    count INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Option 2: Display in Frontend**
Add amenities section to your intel card showing:
- 🏥 12 Hospitals nearby
- 🏫 18 Schools nearby
- 🚇 3 Metro stations nearby
- etc.

### **Option 3: Create API Endpoint**
```python
@app.get("/api/v1/location/{id}/amenities")
def get_amenities(location_id: int):
    # Return stored OSM amenity data
    pass
```

---

## ⚡ Quick Test (Single Location)

If you want to test with just one location first:

```python
# Modify the script to test with just Gachibowli
TARGET_LOCATIONS = ['Gachibowli']
```

Then run it - will take only 1-2 minutes.

---

## 🎯 Your 7 Locations

The script will extract amenities for:
1. Financial District
2. Gachibowli
3. HITEC City
4. Kondapur
5. Kukatpally
6. Madhapur
7. Nanakramguda

---

## ⚠️ Important Notes

1. **API Rate Limits**: The script includes 1-second delays to respect OSM's fair use policy
2. **Accuracy**: Counts are based on OSM data quality (generally very good for urban areas)
3. **Radius**: Searches within 2km of each location center
4. **Real-time**: Data is fetched live from OSM (most up-to-date)

---

## 🔄 Re-running

You can re-run this script:
- **Weekly** - To get updated amenity counts
- **Monthly** - For regular updates
- **On-demand** - When you need fresh data

The data doesn't change frequently, so monthly updates are usually sufficient.

---

Ready to extract? Run:
```bash
python extract_osm_amenities.py
```

This will give you **accurate, comprehensive amenity data** for all your locations! 🚀
