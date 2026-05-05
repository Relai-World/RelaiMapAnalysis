# FastAPI Endpoint Positioning Guide

## 🎯 The Golden Rule
**All route endpoints MUST be defined BEFORE `app.mount()`**

## 📊 Visual Structure

```
api.py Structure:
┌─────────────────────────────────────────────┐
│ 1. Imports                                  │
│    - FastAPI, CORS, StaticFiles             │
│    - requests, os, dotenv                   │
│    - Supabase client                        │
├─────────────────────────────────────────────┤
│ 2. Configuration                            │
│    - Load environment variables             │
│    - Initialize Supabase client             │
│    - Create FastAPI app                     │
│    - Configure CORS                         │
├─────────────────────────────────────────────┤
│ 3. Pydantic Models                          │
│    - Request/Response schemas               │
│    - PropertyReviewRequest                  │
├─────────────────────────────────────────────┤
│ 4. API ENDPOINTS (ALL MUST BE HERE!)        │ ✅ CORRECT ZONE
│    ┌───────────────────────────────────┐   │
│    │ @app.get("/api/...")              │   │
│    │ @app.post("/api/...")             │   │
│    │ @app.post("/api/property-review") │   │ ← MOVED HERE
│    │ @app.options("/api/...")          │   │
│    └───────────────────────────────────┘   │
├─────────────────────────────────────────────┤
│ 5. Static Files Mount (MUST BE LAST!)      │
│    app.mount("/", StaticFiles(...))         │ ← BARRIER
├─────────────────────────────────────────────┤
│ 6. Main Entry Point                         │
│    if __name__ == "__main__":               │
│        uvicorn.run(...)                     │
└─────────────────────────────────────────────┘
     ❌ NO ENDPOINTS ALLOWED BELOW THIS LINE
```

## ❌ What Was Wrong

```python
# Line 860
app.mount("/", StaticFiles(directory="frontend", html=True))
# ↑ This creates a catch-all route for static files

# Line 868
@app.post("/api/property-review")  # ❌ TOO LATE!
def get_property_review():
    pass
# This endpoint is NEVER registered because the static
# file handler already caught the "/" route
```

### Why It Failed:
1. `app.mount("/", ...)` registers a catch-all route
2. All requests to any path go to static file handler first
3. Endpoints defined after this are never reached
4. Result: HTTP 405 "Method Not Allowed"

## ✅ What's Fixed

```python
# Line 858
@app.post("/api/property-review")  # ✅ BEFORE app.mount()
@app.options("/api/property-review")
async def get_property_review():
    pass
# This endpoint is properly registered

# Line 1000
app.mount("/", StaticFiles(directory="frontend", html=True))
# ↑ Static files are mounted LAST
```

### Why It Works:
1. Endpoint is registered first
2. FastAPI knows about `/api/property-review` route
3. Static file handler is registered last
4. Requests to `/api/property-review` go to endpoint
5. Other requests go to static files
6. Result: HTTP 200 ✅

## 🔍 Request Flow

### Before Fix (BROKEN):
```
Browser Request: POST /api/property-review
         ↓
    FastAPI Router
         ↓
    Static File Handler (mounted at "/")
         ↓
    "No static file at /api/property-review"
         ↓
    HTTP 405 Method Not Allowed ❌
```

### After Fix (WORKING):
```
Browser Request: POST /api/property-review
         ↓
    FastAPI Router
         ↓
    Check registered endpoints first
         ↓
    Found: @app.post("/api/property-review")
         ↓
    Execute endpoint function
         ↓
    Return review data
         ↓
    HTTP 200 OK ✅
```

## 📝 Checklist for Adding New Endpoints

When adding a new endpoint to `api.py`:

- [ ] Define Pydantic models (if needed) BEFORE endpoints
- [ ] Define endpoint with `@app.get/post/put/delete`
- [ ] Place endpoint BEFORE `app.mount()` line
- [ ] Test endpoint with curl or test script
- [ ] Verify endpoint appears in FastAPI docs at `/docs`

## 🚨 Common Mistakes

### Mistake 1: Endpoint After Mount
```python
app.mount("/", StaticFiles(...))

@app.post("/api/new-endpoint")  # ❌ WRONG!
def new_endpoint():
    pass
```

### Mistake 2: Forgetting OPTIONS for CORS
```python
@app.post("/api/endpoint")  # ❌ Missing OPTIONS
def endpoint():
    pass
```

**Fix:**
```python
@app.post("/api/endpoint")
@app.options("/api/endpoint")  # ✅ Add OPTIONS
async def endpoint():
    pass
```

### Mistake 3: Multiple Mounts
```python
app.mount("/", StaticFiles(...))
app.mount("/api", ...)  # ❌ Can't mount after catch-all
```

## 🎓 Key Takeaways

1. **Order matters** in FastAPI route registration
2. **`app.mount("/", ...)` must be LAST**
3. **All endpoints before mount**
4. **Static files are catch-all**
5. **Test after every endpoint addition**

## 🔗 Related Files
- `api.py` - Main backend file
- `test_property_review_fixed.py` - Test script
- `PROPERTY_REVIEW_FIX_SUMMARY.md` - Quick reference
- `NEXT_STEPS_PROPERTY_REVIEW.md` - Testing guide
