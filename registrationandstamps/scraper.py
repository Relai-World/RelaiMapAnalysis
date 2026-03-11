import asyncio
import pandas as pd
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from locations import ALL_LOCATIONS

# -----------------------------
# SETTINGS
# -----------------------------

DISTRICT = "RANGAREDDY"
MANDAL = "Serilingampally"

BATCH_SIZE = 50
BATCH_NUMBER = 0   # change 0,1,2,3

DATE_RANGES = [
("01-01-2020","31-12-2020"),
("01-01-2021","31-12-2021"),
("01-01-2022","31-12-2022"),
("01-01-2023","31-12-2023"),
("01-01-2024","31-12-2024"),
("01-01-2025","31-12-2025")
]

# -----------------------------
# PREPARE BATCH
# -----------------------------

batches = [
    ALL_LOCATIONS[i:i+BATCH_SIZE]
    for i in range(0,len(ALL_LOCATIONS),BATCH_SIZE)
]

CURRENT_BATCH = batches[BATCH_NUMBER]

results = []

# -----------------------------
# SCRAPER
# -----------------------------

async def scrape():

    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=False)

        page = await browser.new_page()

        await page.goto("https://registration.telangana.gov.in")

        print("Portal opened")

        await page.wait_for_timeout(4000)

        for location in CURRENT_BATCH:

            for start_date,end_date in DATE_RANGES:

                print("Scraping:",location,start_date)

                try:

                    await page.select_option("#district",label=DISTRICT)

                    await page.wait_for_timeout(1000)

                    await page.select_option("#mandal",label=MANDAL)

                    await page.wait_for_timeout(1000)

                    await page.select_option("#village",label=location)

                    await page.fill("#fromDate",start_date)

                    await page.fill("#toDate",end_date)

                    print("Enter CAPTCHA then press Resume")

                    await page.pause()

                    await page.click("#submit")

                    await page.wait_for_timeout(5000)

                    while True:

                        html = await page.content()

                        soup = BeautifulSoup(html,"html.parser")

                        table = soup.find("table")

                        if table is None:
                            break

                        rows = table.find_all("tr")[1:]

                        for row in rows:

                            cols = [c.text.strip() for c in row.find_all("td")]

                            if len(cols) < 6:
                                continue

                            record = {
                                "document_number": cols[0],
                                "transaction_date": cols[1],  # Renamed for clarity
                                "village": cols[2],
                                "property_type": cols[3],
                                "extent_area": cols[4],  # Area in sq.yards/sq.ft
                                "sale_consideration_value": cols[5],  # Total transaction value
                                "mandal": MANDAL,
                                "district": DISTRICT
                            }

                            results.append(record)

                        next_button = await page.query_selector("a.next")

                        if next_button:

                            await next_button.click()

                            await page.wait_for_timeout(3000)

                        else:

                            break

                except Exception as e:

                    print("Error:",e)

                    continue

        await browser.close()

# -----------------------------
# RUN
# -----------------------------

asyncio.run(scrape())

df = pd.DataFrame(results)

# -----------------------------
# DATA CLEANING & ENRICHMENT
# -----------------------------

# Clean sale consideration value
df["sale_consideration_value"] = df["sale_consideration_value"].str.replace(",","").str.replace("₹","").str.strip()
df["sale_consideration_value"] = pd.to_numeric(df["sale_consideration_value"],errors="coerce")

# Clean area/extent
df["extent_area"] = pd.to_numeric(df["extent_area"],errors="coerce")

# Calculate price per sqft
df["price_per_sqft"] = df["sale_consideration_value"] / df["extent_area"]

# Parse transaction date
df["transaction_date"] = pd.to_datetime(df["transaction_date"], format="%d-%m-%Y", errors="coerce")

# Extract time components for trend analysis
df["year"] = df["transaction_date"].dt.year
df["month"] = df["transaction_date"].dt.month
df["quarter"] = df["transaction_date"].dt.quarter
df["year_month"] = df["transaction_date"].dt.to_period("M")
df["year_quarter"] = df["transaction_date"].dt.to_period("Q")

# Normalize property type for better grouping
df["property_type"] = df["property_type"].str.strip().str.title()

# -----------------------------
# SAVE
# -----------------------------

file_name = f"data/batch_{BATCH_NUMBER}_results.csv"

df.to_csv(file_name,index=False)

print("Scraping completed")

print("Records collected:",len(df))