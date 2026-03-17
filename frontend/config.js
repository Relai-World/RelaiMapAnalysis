// API Configuration - Updated for Future Development Fix
// Update this after deploying your API to Render
const API_CONFIG = {
  // Change this to your Render API URL after deployment
  PRODUCTION_API_URL: 'https://hyderabad-intelligence.onrender.com',
  
  // Local development
  LOCAL_API_URL: 'http://127.0.0.1:8000'
};

// Auto-detect environment
const isLocalhost = window.location.hostname === "localhost" || 
                    window.location.hostname === "127.0.0.1";

// Export the correct API URL - Fixed for Future Development
window.API_BASE_URL = isLocalhost ? API_CONFIG.LOCAL_API_URL : API_CONFIG.PRODUCTION_API_URL;

console.log('🌐 API Base URL (Future Dev Fixed):', window.API_BASE_URL);
