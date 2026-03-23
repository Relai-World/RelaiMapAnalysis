// API Configuration - Updated for Future Development Fix
// Update this after deploying your API to Render
const API_CONFIG = {
  // Change this to your Render API URL after deployment
  PRODUCTION_API_URL: 'https://relai-map-analysis.onrender.com',
  
  // Local development
  LOCAL_API_URL: 'http://127.0.0.1:8000'
};

// Auto-detect environment
const isLocalhost = window.location.hostname === "localhost" || 
                    window.location.hostname === "127.0.0.1";

// Export the correct API URL - Use local when developing locally
window.API_BASE_URL = isLocalhost ? API_CONFIG.LOCAL_API_URL : API_CONFIG.PRODUCTION_API_URL;

console.log('🌐 API Base URL:', window.API_BASE_URL);
console.log('🌐 Environment:', isLocalhost ? 'Local Development' : 'Production');
