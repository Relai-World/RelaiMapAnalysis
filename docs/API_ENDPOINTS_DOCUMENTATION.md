# 🚀 West Hyderabad Intelligence - API Endpoints Documentation

## Base URL
- **Local Development**: `http://127.0.0.1:8000`
- **Production (Render)**: `https://west-hyderabad-intelliweb.onrender.com`

---

## 📋 All Available Endpoints

### 1. **Health Check** ✅
```
GET /
```

**Description**: Check if the API server is running

**Response**:
```json
{
  "status": "ok",
  "message": "West Hyderabad Intelligence API is running"
}
```

**Usage**:
```bash
curl http://127.0.0.1:8000/
```

---

### 2. **Get All Location Insights** 📍
```
GET /api/v1/insights
```

**Description**: Fetch all locations with their investment insights, sentiment scores, and growth scores

**Response**:
```json
[
  {
    "location_id": 1,
    "location": "Gachibowli",
    "longitude": 78.3489,
    "latitude": 17.4400,
    "avg_sentiment": 0.15,
    "growth_score": 0.85,
    "investment_score": 0.78
  },
  {
    "location_id": 2,
    "location": "Kondapur",
    "longitude": 78.3639,
    "latitude": 17.4650,
    "avg_sentiment": 0.12,
    "growth_score": 0.82,
    "investment_score": 0.75
  }
  // ... more locations
]
```

**Fields**:
- `location_id`: Unique identifier for the location
- `location`: Name of the area
- `longitude`, `latitude`: Geographic coordinates
- `avg_sentiment`: Average sentiment score (-1.0 to 1.0)
  - Positive (> 0.05): Good market sentiment
  - Neutral (-0.05 to 0.05): Mixed signals
  - Negative (< -0.05): Negative sentiment
- `growth_score`: Growth potential (0.0 to 1.0)
  - High (> 0.8): Strong growth
  - Medium (0.5 to 0.8): Moderate growth
  - Low (< 0.5): Limited growth
- `investment_score`: Overall investment rating (0.0 to 1.0)
  - Excellent (> 0.7)
  - Good (0.5 to 0.7)
  - Average (< 0.5)

**Usage**:
```bash
curl http://127.0.0.1:8000/api/v1/insights
```

**Used By**: Frontend map initialization to display all location markers

---

### 3. **Get Location Infrastructure Counts** 🏥
```
GET /api/v1/location/{location_id}/infra
```

**Description**: Fetch real-time infrastructure counts (hospitals, schools, metro stations, etc.) within 2km radius of a location using OpenStreetMap Overpass API

**Path Parameters**:
- `location_id` (integer): The ID of the location

**Response**:
```json
{
  "hospitals": 5,
  "schools": 12,
  "metro": 2,
  "airports": 0,
  "malls": 3
}
```

**Example**:
```bash
# Get infrastructure for Gachibowli (location_id = 1)
curl http://127.0.0.1:8000/api/v1/location/1/infra
```

**Notes**:
- Uses Overpass API (may take 2-3 seconds)
- Searches within 2000m radius
- Returns 0 if data unavailable or API fails
- Has 0.5 second delay between requests to be polite to Overpass API

**Used By**: Can be used for detailed location analysis (currently not displayed in frontend)

---

### 4. **Get Price Trends** 📈
```
GET /api/v1/location/{location_id}/trends
```

**Description**: Fetch historical price trends (year-wise average price per square foot) for a location

**Path Parameters**:
- `location_id` (integer): The ID of the location

**Response**:
```json
[
  { "year": 2018, "price": 6500 },
  { "year": 2019, "price": 7200 },
  { "year": 2020, "price": 7800 },
  { "year": 2021, "price": 8500 },
  { "year": 2022, "price": 9200 },
  { "year": 2023, "price": 10100 },
  { "year": 2024, "price": 11000 }
]
```

**Fields**:
- `year`: Calendar year
- `price`: Average price per square foot (in Rupees)

**Example**:
```bash
# Get price trends for Gachibowli (location_id = 1)
curl http://127.0.0.1:8000/api/v1/location/1/trends
```

**Used By**: Frontend intel card - displays as a Chart.js line graph with CAGR calculation

---

### 5. **Get All Location Costs** 💰
```
GET /api/v1/location-costs
```

**Description**: Fetch property cost statistics for ALL locations

**Response**:
```json
[
  {
    "location": "Financial District",
    "count": 202,
    "avgBase": 2.31,
    "avgSqft": 8824,
    "minBase": 0.56,
    "maxBase": 15.60,
    "minSqft": 3500,
    "maxSqft": 18000
  },
  {
    "location": "Gachibowli",
    "count": 181,
    "avgBase": 2.40,
    "avgSqft": 9691,
    "minBase": 0.50,
    "maxBase": 19.58,
    "minSqft": 4000,
    "maxSqft": 20000
  }
  // ... more locations
]
```

**Fields**:
- `location`: Location name
- `count`: Number of properties analyzed
- `avgBase`: Average base price (in Crores)
- `avgSqft`: Average price per square foot (in Rupees)
- `minBase`: Minimum base price (in Crores)
- `maxBase`: Maximum base price (in Crores)
- `minSqft`: Minimum price per square foot (in Rupees)
- `maxSqft`: Maximum price per square foot (in Rupees)

**Example**:
```bash
curl http://127.0.0.1:8000/api/v1/location-costs
```

**Used By**: Can be used to display a comparison table of all locations

---

### 6. **Get Specific Location Cost** 💵
```
GET /api/v1/location-costs/{location_name}
```

**Description**: Fetch property cost statistics for a SPECIFIC location

**Path Parameters**:
- `location_name` (string): The name of the location (case-insensitive)

**Response (Success)**:
```json
{
  "location": "Gachibowli",
  "count": 181,
  "avgBase": 2.40,
  "avgSqft": 9691,
  "minBase": 0.50,
  "maxBase": 19.58,
  "minSqft": 4000,
  "maxSqft": 20000
}
```

**Response (Not Found)**:
```json
{
  "error": "Location not found"
}
```

**Examples**:
```bash
# Get costs for Gachibowli
curl http://127.0.0.1:8000/api/v1/location-costs/Gachibowli

# Get costs for HITEC City (with space in name)
curl http://127.0.0.1:8000/api/v1/location-costs/HITEC%20City

# Case-insensitive search
curl http://127.0.0.1:8000/api/v1/location-costs/gachibowli
```

**Notes**:
- Uses `ILIKE` for case-insensitive matching
- URL encode spaces and special characters
- Returns error object if location not found in database

**Used By**: Frontend intel card - dynamically loads property costs when a location is clicked

---

## 🗺️ API Usage Flow in Frontend

### **Map Initialization**:
```
1. Frontend loads
2. Calls GET /api/v1/insights
3. Displays all location markers on map
```

### **Location Click**:
```
1. User clicks on a location marker
2. Intel card opens with basic info
3. Calls GET /api/v1/location/{id}/trends (for price chart)
4. Calls GET /api/v1/location-costs/{name} (for property costs)
5. Displays complete location intelligence
```

---

## 📊 Database Tables Used

| Endpoint | Tables Used |
|----------|-------------|
| `/api/v1/insights` | `locations`, `location_insights` |
| `/api/v1/location/{id}/infra` | `locations` (+ Overpass API) |
| `/api/v1/location/{id}/trends` | `price_trends` |
| `/api/v1/location-costs` | `location_costs` |
| `/api/v1/location-costs/{name}` | `location_costs` |

---

## 🔧 Testing Your Endpoints

### **Method 1: Browser**
Simply paste the URL in your browser:
```
http://127.0.0.1:8000/api/v1/insights
```

### **Method 2: Python**
```python
import requests

response = requests.get("http://127.0.0.1:8000/api/v1/insights")
print(response.json())
```

### **Method 3: PowerShell**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/insights"
```

### **Method 4: FastAPI Docs (Interactive)**
Open in browser:
```
http://127.0.0.1:8000/docs
```
This gives you an interactive Swagger UI to test all endpoints!

---

## 🎯 Quick Reference Table

| Endpoint | Method | Purpose | Response Time |
|----------|--------|---------|---------------|
| `/` | GET | Health check | < 10ms |
| `/api/v1/insights` | GET | All locations data | ~100ms |
| `/api/v1/location/{id}/infra` | GET | Infrastructure counts | 2-3 seconds |
| `/api/v1/location/{id}/trends` | GET | Price history | ~50ms |
| `/api/v1/location-costs` | GET | All property costs | ~100ms |
| `/api/v1/location-costs/{name}` | GET | Specific property costs | ~50ms |

---

## 🚨 Error Handling

All endpoints return proper error responses:

**Database Connection Error**:
```json
{
  "error": "connection error message",
  "message": "Failed to connect to database or fetch insights"
}
```

**Location Not Found**:
```json
{
  "error": "Location not found"
}
```

**Empty Results**:
```json
[]
```

---

## 🔐 CORS Configuration

Your API allows requests from:
- ✅ All origins (`allow_origins=["*"]`)
- ✅ All methods (GET, POST, etc.)
- ✅ All headers

This is perfect for development. For production, consider restricting to your frontend domain:
```python
allow_origins=["https://harjeet1309.github.io"]
```

---

## 📝 Summary

**Total Endpoints**: **6**

**Active Endpoints** (used by frontend):
1. ✅ `GET /api/v1/insights` - Map markers
2. ✅ `GET /api/v1/location/{id}/trends` - Price chart
3. ✅ `GET /api/v1/location-costs/{name}` - Property costs

**Available but Unused**:
4. ⚪ `GET /` - Health check
5. ⚪ `GET /api/v1/location/{id}/infra` - Infrastructure
6. ⚪ `GET /api/v1/location-costs` - All costs

**Your API is well-designed, RESTful, and production-ready!** 🎉
