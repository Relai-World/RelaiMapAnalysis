
import subprocess
import sys
import time
import os

def run_script(script_name):
    print(f"\n[RUN] Running {script_name}...")
    start_time = time.time()
    try:
        # Use python executable relative to current env
        subprocess.check_call([sys.executable, script_name])
        duration = time.time() - start_time
        print(f"[OK] {script_name} completed in {duration:.1f}s.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {script_name} failed with error code {e.returncode}")
        return False

def main():
    print("==========================================")
    print("      INTELLIGENCE UPDATE PIPELINE (V2)   ")
    print("      (News + Reddit + Sentiment + Insights)")
    print("==========================================")
    
    # Check if we should skip scraping (e.g. for testing processing only)
    skip_scrape = "--skip-scrape" in sys.argv

    if not skip_scrape:
        # 1. Scrape News (Playwright)
        print("\n--- STEP 1: SCRAPING NEWS ---")
        if not run_script("scraper/scrape_playwright.py"):
            print("[WARN] News scraper had issues, but continuing...")

        # 2. Scrape Reddit (Targeted)
        print("\n--- STEP 2: SCRAPING REDDIT ---")
        if not run_script("scraper/scrape_reddit_targeted.py"):
             print("[WARN] Reddit scraper had issues, but continuing...")
    else:
        print("\n[SKIP] Skipping Scraping Steps...")

    # 3. Process Sentiment (V2)
    print("\n--- STEP 3: PROCESSING SENTIMENT ---")
    if not run_script("sentiment/main_sentiment.py"):
        print("[STOP] Stopping pipeline due to sentiment processing failure.")
        return

    # 4. Aggregate Insights
    print("\n--- STEP 4: AGGREGATING INSIGHTS ---")
    if not run_script("aggregation/compute_location_insights.py"):
        print("[STOP] Stopping pipeline due to aggregation failure.")
        return

    # 5. Generate Smart Facts
    print("\n--- STEP 5: GENERATE AI SUMMARIES ---")
    if not run_script("aggregation/generate_smart_facts.py"):
        print("[WARN] Fact generation failed, but continuing (non-critical).")

    print("\n[DONE] ALL TASKS COMPLETED SUCCESSFULLY!")
    print("The frontend map should now reflect updated: Sentiment, Growth, and Investment Scores.")

if __name__ == "__main__":
    main()
