# Real Estate Intelligence: The Daily Operations & Data Lifecycle

This document provides a detailed breakdown of how the platform operates continuously to ensure market intelligence is always fresh, accurate, and insightful.

---

## 1. The Core Philosophy
The system is built on a **"Living Data"** model. It does not wait for manual updates. Instead, it wakes up automatically, listens to the city, thinks about the data using AI, and updates the map instantly.

---

## 2. The 3-Step Continuous Loop
This cycle repeats automatically (e.g., every 2 weeks or on-demand).

### Step 1: LISTENING (Data Harvesting)
**"What is the city saying?"**

*   **The Problem:** Manually reading news for 494 locations is impossible.
*   **The Solution:** Automated Scrapers (Playwright).
*   **How it works:**
    *   **Scheduled Wake-Up:** The system activates a background job.
    *   **Incremental Scanning:** It ignores old news. It specifically asks Google News & Reddit: *"What happened in Hyderabad's Real Estate since last week?"*
    *   **Entity tagging:** It reads thousands of headlines and automatically tags them to specific locations.
        *   *Article:* "New flyover at **LB Nagar** approved."
        *   *Action:* System tags this article to **LB Nagar (ID: 42)**.

### Step 2: THINKING (Intelligence Processing)
**"Is this good news or bad news?"**

*   **The Problem:** Raw text is subjective. "Price Hike" is bad for buyers but good for investors.
*   **The Solution:** **FinBERT** (Financial Artificial Intelligence).
*   **How it works:**
    *   **Sentiment Analysis:** The tagged text is fed into FinBERT.
        *   *Input:* "Metro line delayed." → *Output:* **Negative (-0.8)**
        *   *Input:* "New IT Park opening." → *Output:* **Positive (+0.9)**
    *   **Score Update (Moving Average):**
        *   The system creates a new "Global Score" by blending the *New Intelligence* with the *Historical Intelligence*.
        *   This ensures one bad article doesn't crash a location's score, but a consistent stream of bad news will slowly drag it down.

### Step 3: PUBLISHING (Visual Feedback)
**"Show me the reality."**

*   **The Problem:** Spreadsheets are boring. Users need instant visual understanding.
*   **The Solution:** Dynamic Vector Maps.
*   **How it works:**
    *   **Database Update:** The new scores are saved to the Live Database (`location_insights`).
    *   **Instant UI Refresh:** The next time a user opens the map:
        *   **Color Changes:** A pin might turn from Yellow (Average) to Green (Hot) if sentiment improved.
        *   **Smart Copy:** The sidebar text changes from *"Stable Market"* to *"🚀 Emerging Hotspot"* based on the new math.

---

## 3. Visual Layers: How Users See It

| Layer Level | What User Sees | What System Does |
| :--- | :--- | :--- |
| **Macro (The City)** | **Color-Coded Map Pins** | Uses aggregated scores to color-code entire neighborhoods (Heatmap). |
| **Micro (The Area)** | **"Intel Card" Sidebar** | Fetches specific details: *"Why is this green?"* -> *"Because 5 new schools opened."* |
| **Deep (The Data)** | **Trend Charts** | Plots the score history over time to prove the trend is real, not a glitch. |

---

## Summary
The platform is not a static directory. It is a **Self-Updating Intelligence Engine**.
1.  **Scrapers** fetch the news.
2.  **FinBERT** understands the meaning.
3.  **The Map** visualizes the truth.

This ensures that the "Real Estate Intelligence" is truly **Intelligent** and always **Current**.
