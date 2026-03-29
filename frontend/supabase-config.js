// Supabase Configuration Loader
// This file fetches Supabase credentials from the backend API
// SECURITY: Credentials are stored in .env and served by the backend

(async function loadSupabaseConfig() {
  try {
    // Fetch config from backend API
    const response = await fetch(`${window.API_BASE_URL}/api/config/supabase`);
    
    if (!response.ok) {
      throw new Error(`Failed to load Supabase config: ${response.status}`);
    }
    
    const config = await response.json();
    
    // Store globally for app.js to use
    window.SUPABASE_CONFIG = {
      url: config.url,
      key: config.key
    };
    
    console.log('✅ Supabase config loaded from backend');
    
    // Dispatch event to notify app.js that config is ready
    window.dispatchEvent(new Event('supabase-config-loaded'));
    
  } catch (error) {
    console.error('❌ Failed to load Supabase config:', error);
    // Fallback: app will fail gracefully
    window.SUPABASE_CONFIG = { url: '', key: '' };
  }
})();
