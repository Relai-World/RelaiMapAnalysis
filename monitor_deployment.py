#!/usr/bin/env python3
"""
Monitor frontend deployment status
"""
import requests
import time
import sys

def check_deployment_status():
    """Check if the new version is deployed by looking for the updated console message"""
    
    # Common GitHub Pages URLs
    possible_urls = [
        "https://harjeet1309.github.io/Hyderabad-intelligence/",
        "https://harjeet1309.github.io/Hyderabad-intelligence/frontend/",
        "https://harjeet1309.github.io/west-hyderabad-intelliweb/",
        "https://harjeet1309.github.io/west-hyderabad-intelliweb/frontend/"
    ]
    
    print("🔍 Checking deployment status...")
    print("Looking for updated version with 'Future Development Fixed' message")
    print("-" * 60)
    
    for url in possible_urls:
        try:
            print(f"Checking: {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # Check if the updated version is deployed
                if "Future Development Fixed" in response.text or "V 2.1" in response.text:
                    print(f"✅ NEW VERSION DEPLOYED at: {url}")
                    print("🎉 Future Development Insights should now work!")
                    return url
                else:
                    print(f"⏳ Old version still active at: {url}")
            else:
                print(f"❌ Not accessible: {response.status_code}")
                
        except requests.RequestException as e:
            print(f"❌ Error accessing {url}: {e}")
        
        print()
    
    return None

def monitor_until_deployed(max_attempts=20, delay=30):
    """Monitor deployment until new version is live"""
    
    print(f"🚀 Starting deployment monitor...")
    print(f"Will check every {delay} seconds for up to {max_attempts} attempts")
    print("=" * 60)
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n📡 Attempt {attempt}/{max_attempts}")
        
        deployed_url = check_deployment_status()
        
        if deployed_url:
            print("\n" + "=" * 60)
            print("🎉 DEPLOYMENT SUCCESSFUL!")
            print(f"✅ New version live at: {deployed_url}")
            print("\n📋 Next Steps:")
            print("1. Open your application in browser")
            print("2. Click on Gachibowli location")
            print("3. Click the robot icon for Future Insights")
            print("4. Click 'What are the future developments?'")
            print("5. Should now show development data!")
            return True
        
        if attempt < max_attempts:
            print(f"⏳ Waiting {delay} seconds before next check...")
            time.sleep(delay)
    
    print("\n⚠️ Deployment monitoring timed out")
    print("The deployment might take longer than expected.")
    print("Check your GitHub repository's Actions tab for deployment status.")
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Single check
        deployed_url = check_deployment_status()
        if not deployed_url:
            print("\n⏳ Deployment still in progress. Run without --once to monitor continuously.")
    else:
        # Continuous monitoring
        monitor_until_deployed()