# API Endpoints - Quick Reference

## ✅ USED BY FRONTEND (7 endpoints)

1. **GET /api/v1/insights**
   - Used on page load
   - Returns all locations with sentiment/growth/investment scores

2. **GET /api/v1/search?q={query}**
   - Used in search box
   - Searches locations by name

3. **GET /api/v1/properties?area={name}&bhk={optional}**
   - Used when clicking location
   - Returns properties for that area

4. **GET /api/v1/properties/{id}**
   - Used when clicking property card
   - Returns single property details

5. **GET /api/v1/location/{id}/trends**
   - Used for price chart
   - Returns price trends 2020-2026

6. **GET /api/v1/property-costs/{name}**
   - Used in location card
   - Returns avg/min/max property costs

7. **GET /api/v1/location/{id}/amenities/{type}**
   - Used when clicking amenity buttons
   - Returns nearby hospitals/schools/malls/etc

---

## ❌ NOT USED (24 endpoints)

### Debug/Health (2)
- GET / (health check)
- GET /api/v1/search/debug

### Infrastructure (1)
- GET /api/v1/location/{id}/infra

### Market Data (3)
- GET /api/v1/market-trends
- GET /api/v1/location-costs
- GET /api/v1/property-costs

### Boundaries (3)
- GET /api/v1/location-costs/{name} (duplicate)
- GET /api/v1/locations/{id}/boundary
- GET /api/v1/locations/boundaries

### Telangana Registration (11)
- GET /api/v1/telangana/districts
- GET /api/v1/telangana/districts/{code}/mandals
- GET /api/v1/telangana/mandals/{dc}/{mc}/villages
- GET /api/v1/telangana/market-values
- GET /api/v1/telangana/top-locations
- GET /api/v1/telangana/price-stats
- GET /api/v1/telangana/search
- GET /api/v1/telangana/stats
- GET /api/v1/telangana/village/{id}/boundary
- (+ 2 more boundary endpoints)

### Detailed Property Costs (1)
- GET /api/v1/property-costs/{area_name}

---

## Summary
- **7 endpoints** = Actually used by your website
- **24 endpoints** = Not used anywhere
- **31 total** endpoints defined in api.py
