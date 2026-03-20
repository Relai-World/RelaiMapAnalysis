# 🚨 EMERGENCY SECURITY FIXES - IMMEDIATE ACTION REQUIRED

## ⏰ CRITICAL FIXES (NEXT 2 HOURS)

### 1. **SECURE YOUR CREDENTIALS IMMEDIATELY**

**Step 1: Rotate Google API Key**
```bash
# Go to Google Cloud Console
# 1. Disable current key: AIzaSyDnREtiEfU6adEdXJvTbLtLcHe26kWvz-g
# 2. Create new API key with IP restrictions
# 3. Update .env file with new key
```

**Step 2: Change Database Password**
```sql
-- In Supabase dashboard, change postgres password
-- Update .env with new password
```

**Step 3: Remove .env from Git**
```bash
git rm --cached .env
echo ".env" >> .gitignore
git add .gitignore
git commit -m "Remove .env from version control"
git push
```

### 2. **FIX CORS CONFIGURATION**

**File:** `api.py`
```python
# Replace lines 44-48 with:
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://hyderabad-intelligence.onrender.com",
        "https://west-hyderabad-intelliweb.onrender.com"
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True
)
```

### 3. **ADD BASIC API AUTHENTICATION**

**File:** `api.py` - Add at top:
```python
from fastapi import HTTPException, Depends, Header
from typing import Optional

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    expected_key = os.getenv("BACKEND_API_KEY")
    if not x_api_key or x_api_key != expected_key:
        raise HTTPException(
            status_code=401, 
            detail="Invalid or missing API key"
        )
    return x_api_key

# Add to ALL endpoints:
@app.get("/api/v1/properties")
async def get_properties(auth: str = Depends(verify_api_key)):
    # existing code
```

### 4. **SECURE DATABASE CONNECTIONS**

**File:** `api.py` - Update get_db():
```python
def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode='require',  # ✅ FORCE SSL
        connect_timeout=10
    )
```

---

## 🔧 QUICK FIXES (NEXT 4 HOURS)

### 5. **FIX SQL INJECTION IN UTILITIES**

**Create:** `utilities/secure_db_utils.py`
```python
ALLOWED_TABLES = {
    'locations', 'properties', 'amenities', 'location_costs',
    'property_costs', 'real_estate_projects', 'csv_properties'
}

ALLOWED_COLUMNS = {
    'id', 'location_id', 'property_id', 'name', 'area_name',
    'location', 'coordinates', 'price', 'bhk'
}

def safe_table_name(table: str) -> str:
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table}")
    return table

def safe_column_name(column: str) -> str:
    if column not in ALLOWED_COLUMNS:
        raise ValueError(f"Invalid column name: {column}")
    return column

def safe_delete_by_location(cur, table: str, location_id: int):
    table = safe_table_name(table)
    cur.execute(f"DELETE FROM {table} WHERE location_id = %s", (location_id,))
```

### 6. **ADD INPUT VALIDATION**

**File:** `api.py` - Add validation functions:
```python
from pydantic import BaseModel, validator
from typing import Optional

class LocationQuery(BaseModel):
    location_id: int
    
    @validator('location_id')
    def validate_location_id(cls, v):
        if v < 1 or v > 10000:  # Reasonable bounds
            raise ValueError('Invalid location ID')
        return v

class PropertyQuery(BaseModel):
    property_id: int
    
    @validator('property_id')
    def validate_property_id(cls, v):
        if v < 1 or v > 100000:  # Reasonable bounds
            raise ValueError('Invalid property ID')
        return v

# Update endpoints:
@app.get("/api/v1/location/{location_id}/infra")
def location_infra(query: LocationQuery = Depends()):
    location_id = query.location_id
    # existing code
```

### 7. **MASK SENSITIVE DATA**

**File:** `api.py` - Add data masking:
```python
def mask_email(email: str) -> str:
    if not email or '@' not in email:
        return email
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        return f"{'*' * len(local)}@{domain}"
    return f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}@{domain}"

def mask_phone(phone: str) -> str:
    if not phone:
        return phone
    # Keep first 3 and last 2 digits
    if len(phone) > 5:
        return f"{phone[:3]}{'*' * (len(phone) - 5)}{phone[-2:]}"
    return '*' * len(phone)

def sanitize_property_data(data: dict) -> dict:
    """Remove or mask sensitive information"""
    sensitive_fields = ['poc_email', 'poc_phone', 'builder_email', 'contact_email']
    
    for field in sensitive_fields:
        if field in data and data[field]:
            if 'email' in field:
                data[field] = mask_email(data[field])
            elif 'phone' in field:
                data[field] = mask_phone(data[field])
    
    return data
```

---

## 🛡️ SECURITY HEADERS (NEXT 2 HOURS)

### 8. **ADD SECURITY HEADERS**

**File:** `api.py` - Add middleware:
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import Response

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["hyderabad-intelligence.onrender.com", "localhost"]
)
```

### 9. **FRONTEND SECURITY**

**File:** `frontend/index.html` - Add CSP meta tag:
```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; 
               style-src 'self' 'unsafe-inline' https://unpkg.com; 
               img-src 'self' data: https:; 
               connect-src 'self' https://hyderabad-intelligence.onrender.com;">
```

**File:** `frontend/app.js` - Add API key header:
```javascript
// Update all fetch calls to include API key
const API_HEADERS = {
    'Content-Type': 'application/json',
    'X-API-Key': 'west-hyd-intel-secure-key-2026'  // From your .env
};

// Example:
fetch(`${API_BASE_URL}/api/v1/locations`, {
    headers: API_HEADERS
})
```

---

## 📋 DEPLOYMENT CHECKLIST

### Before Deploying Fixes:

- [ ] **New .env file created** with rotated credentials
- [ ] **Old API keys revoked** in Google Cloud Console
- [ ] **Database password changed** in Supabase
- [ ] **CORS origins updated** to specific domains
- [ ] **API authentication added** to all endpoints
- [ ] **Input validation implemented**
- [ ] **Security headers added**
- [ ] **Sensitive data masking enabled**

### After Deployment:

- [ ] **Test API with new authentication**
- [ ] **Verify CORS is working correctly**
- [ ] **Check that sensitive data is masked**
- [ ] **Monitor for any errors in logs**
- [ ] **Update frontend to use API keys**

---

## 🚨 CRITICAL REMINDERS

1. **DO NOT commit the new .env file** - keep it local only
2. **Test thoroughly** before deploying to production
3. **Monitor API usage** for any unusual activity
4. **Set up alerts** for failed authentication attempts
5. **Document all changes** for your team

---

## 📞 EMERGENCY CONTACTS

If you encounter issues during implementation:

1. **Database Issues:** Check Supabase dashboard for connection errors
2. **API Issues:** Check Render deployment logs
3. **Frontend Issues:** Check browser console for CORS errors
4. **Authentication Issues:** Verify API key in headers

---

## ⏱️ TIMELINE

- **Hour 1:** Rotate credentials, fix CORS
- **Hour 2:** Add API authentication
- **Hour 3:** Fix SQL injection vulnerabilities  
- **Hour 4:** Add input validation and security headers
- **Hour 5:** Test and deploy
- **Hour 6:** Monitor and verify fixes

**Remember:** These are emergency fixes. You'll need comprehensive security implementation for long-term protection, but these fixes will address the most critical vulnerabilities immediately.