# Performance Optimization Plan

## Current Issues

### 1. get_all_insights RPC is SLOW
- Processes 346 locations
- Joins multiple tables (locations, properties, news)
- Calculates aggregations on every request
- No caching

### 2. Frontend loads ALL locations at once
- 346 locations loaded on map initialization
- Large JSON payload
- No pagination or lazy loading

### 3. Property searches are unoptimized
- Full table scans on unified_data_DataType_Raghu
- No indexes on areaname
- Fuzzy matching is expensive

## Optimization Strategy

### Phase 1: Database Optimization (Quick Wins)
1. **Add indexes** to speed up queries
2. **Cache get_all_insights** results in a materialized view
3. **Add index on areaname** for property searches

### Phase 2: API Optimization
1. **Add caching** to API responses
2. **Paginate** location data
3. **Lazy load** properties only when needed

### Phase 3: Frontend Optimization
1. **Lazy load** map markers
2. **Debounce** search inputs
3. **Cache** API responses in browser

## Implementation Priority

**HIGH PRIORITY** (Do Now):
- Add database indexes
- Create materialized view for get_all_insights
- Add API response caching

**MEDIUM PRIORITY** (Do Soon):
- Implement pagination
- Add lazy loading for properties

**LOW PRIORITY** (Nice to Have):
- Frontend caching
- Service worker for offline support
