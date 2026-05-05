# Perplexity API Configuration Fix

## 🎯 Problem
Property reviews showing "No review available" because Perplexity API was returning **400 Bad Request** error.

## 🔍 Root Cause
Two issues with the Perplexity API configuration:

1. **Wrong Model Name**: Used `llama-3.1-sonar-small-128k-online` (invalid)
2. **Wrong API Endpoint**: Used `/chat/completions` (old endpoint)

## ✅ Solution Applied

### Fixed in `api.py`:

**Before (BROKEN):**
```python
perplexity_url = "https://api.perplexity.ai/chat/completions"
payload = {
    "model": "llama-3.1-sonar-small-128k-online",  # ❌ Invalid model
    ...
}
```

**After (FIXED):**
```python
perplexity_url = "https://api.perplexity.ai/v1/sonar"  # ✅ Correct endpoint
payload = {
    "model": "sonar",  # ✅ Correct model name
    ...
}
```

## 📋 Changes Made

### 1. Updated API Endpoint
- **Old**: `https://api.perplexity.ai/chat/completions`
- **New**: `https://api.perplexity.ai/v1/sonar`

### 2. Updated Model Name
- **Old**: `llama-3.1-sonar-small-128k-online`
- **New**: `sonar`

## 🧪 Verification

### Test Script Results:
```bash
python test_perplexity_api.py
```

**Output:**
```
Status Code: 200
✅ Perplexity API is working!
```

## 🚀 Next Steps

### 1. Restart Backend Server
```bash
# Stop current server (Ctrl+C)
python api.py
```

### 2. Test Property Review Endpoint
```bash
python test_property_review_fixed.py
```

**Expected Output:**
```
Status: 200
✅ POST request successful!

Full Response:
{
  "success": true,
  "review": "[AI-generated review text]",
  "source": "perplexity_api",
  "property_id": 5601
}
```

### 3. Test in Browser
1. Open http://localhost:5501
2. Compare 2 properties
3. Wait 10-30 seconds for AI review
4. Verify review appears in "🤖 AI Insights" section

## 📊 Expected Behavior

### First Time (No Cache):
1. Frontend calls `/api/property-review`
2. Backend checks database (no review found)
3. Backend calls Perplexity API with correct endpoint and model
4. Perplexity returns web-grounded review
5. Backend saves review to database
6. Frontend displays review

### Second Time (Cached):
1. Frontend calls `/api/property-review`
2. Backend finds existing review in database
3. Backend returns cached review instantly
4. Frontend displays review (no API call needed)

## 🔑 Perplexity API Details

### Model: `sonar`
- **Type**: Search model
- **Purpose**: Web-grounded AI responses
- **Best For**: Quick factual queries, topic summaries, current events
- **Cost**: ~$0.005 per request + token costs

### Endpoint: `/v1/sonar`
- **Method**: POST
- **Auth**: Bearer token in Authorization header
- **Response**: Includes citations and search results

### Response Structure:
```json
{
  "id": "...",
  "model": "sonar",
  "choices": [{
    "message": {
      "content": "AI-generated review text"
    }
  }],
  "citations": ["url1", "url2", ...],
  "search_results": [...]
}
```

## 📝 Files Modified
- ✅ `api.py` - Updated endpoint URL and model name
- ✅ `test_perplexity_api.py` - Test script for direct API testing

## 🐛 Troubleshooting

### Still Getting 400 Error?
- **Check**: Backend server restarted?
- **Solution**: Stop server (Ctrl+C) and restart with `python api.py`

### Getting "No review available"?
- **Check**: Browser console for errors
- **Check**: Backend console for API call logs
- **Solution**: Verify backend is using new endpoint (check logs)

### API Key Error?
- **Check**: `.env` has `PERPLEXITY_API_KEY=pplx-...`
- **Solution**: Verify API key is valid and not expired

## ✨ Summary

**Issue**: Wrong Perplexity API configuration  
**Fix**: Updated endpoint to `/v1/sonar` and model to `sonar`  
**Status**: ✅ Fixed - Restart backend to apply changes  
**Next**: Test in browser to verify reviews appear

---

**Last Updated**: May 4, 2026  
**Fixed By**: Kiro AI Assistant  
**Issue**: Perplexity API 400 Bad Request  
**Resolution**: Corrected endpoint URL and model name
