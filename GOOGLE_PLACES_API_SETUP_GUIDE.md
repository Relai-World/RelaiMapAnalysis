# Google Places API Setup Guide

## Current Issue
Your API key `AIzaSyAaU6-ro0uOVjDJSO4sImdX15tktW8WrJM` is getting blocked with these errors:

### Places API (New) Error:
```
"message": "Requests to this API places.googleapis.com method google.maps.places.v1.Places.SearchNearby are blocked."
"reason": "API_KEY_SERVICE_BLOCKED"
```

### Legacy Places API Error:
```
"status": "REQUEST_DENIED"
"error_message": "This API key is not authorized to use this service or API."
```

## Solution Steps

### 1. Go to Google Cloud Console
- Visit: https://console.cloud.google.com/
- Select your project (Project ID: 1043849319620)

### 2. Enable Required APIs
Go to **APIs & Services > Library** and enable these APIs:

#### For Places API (New) - RECOMMENDED:
- Search for: **"Places API (New)"**
- Enable: `places.googleapis.com`

#### For Legacy Places API - FALLBACK:
- Search for: **"Places API"** (the legacy one)
- Enable: `maps.googleapis.com`

### 3. Configure API Key Restrictions
Go to **APIs & Services > Credentials**:

1. Find your API key: `AIzaSyAaU6-ro0uOVjDJSO4sImdX15tktW8WrJM`
2. Click **Edit** (pencil icon)
3. Under **API restrictions**:
   - Select **"Restrict key"**
   - Add these APIs:
     - **Places API (New)** (`places.googleapis.com`)
     - **Places API** (`maps.googleapis.com`) - as fallback
4. Under **Application restrictions**:
   - Select **"HTTP referrers (web sites)"** if using from frontend
   - OR **"IP addresses"** if using from backend only
   - Add your domain/IP as needed
5. Click **Save**

### 4. Enable Billing
- Go to **Billing** in Google Cloud Console
- Ensure billing is enabled for your project
- Places API requires billing to be enabled

### 5. Wait for Propagation
- API key changes can take 5-10 minutes to propagate
- Test again after waiting

## Testing
Run this command to test:
```bash
python test_google_places_api.py
```

## Current Implementation
Your app is configured to use **Places API (New)** which is the modern, recommended approach:
- Endpoint: `https://places.googleapis.com/v1/places:searchNearby`
- Method: POST with JSON body
- Better performance and features than legacy API

## Fallback Option
If Places API (New) doesn't work, we can fall back to the legacy Places API by modifying the code.