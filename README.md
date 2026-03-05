# 🏢 West Hyderabad Real Estate Intelligence
> **AI-Powered Investment Analysis for Hyderabad's Growth Corridors**

![Status](https://img.shields.io/badge/Status-Production-green)
![Tech](https://img.shields.io/badge/Stack-FastAPI%20%7C%20PostgreSQL%20%7C%20FinBERT-blue)

A professional-grade real estate analytics platform that actively monitors news, social sentiment, and infrastructure developments to calculate **Growth Potential** and **Investment Risk** for key micro-markets in West Hyderabad (HITEC City, Financial District, etc.).

---

## 🚀 Key Features

### 📊 AI-Driven Sentiment (FinBERT)
Unlike generic sentiment analysis, this system uses **ProsusAI/finbert** (Financial BERT) to analyze news from an **investor's perspective**. 
- *OLD:* "Heavy construction in Kokapet" -> Negative (Noise/Dust).
- *NEW:* "Heavy construction in Kokapet" -> **Positive** (Economic Growth/Development).

### 📈 Dynamic Growth Scoring
Calculates a **0-10 Growth Score** based on:
1.  **News Volume (Buzz):** High activity = High relevance.
2.  **Infrastructure Signals:** Metro, Flyovers, Tech Parks.
3.  **Market Sentiment:** Weighted 30% in the final score.

### 🗺️ Interactive Intelligence Map
- **3D Visualization:** MapLibre GL JS tailored map.
- **Micro-Market Insights:** Click any location for a detailed dossier (Price trends, Sentiment, Pros/Cons).
- **Amenity Heatmaps:** 5km analysis of Schools, Hospitals, and Malls.

---

## 🏗️ Architecture

The system is split into **three core components**:

### 1. The Pipeline (`update_pipeline.py`)
Runs locally or on a scheduled worker.
- **Scrapes:** Google News, Reddit, Twitter.
- **Processes:** Runs text through FinBERT Model.
- **Upserts:** Pushes clean scores to the PostgreSQL Database.

### 2. The API (`api.py`)
Hosted on **Render / Cloud**.
- **FastAPI:** High-performance async endpoints.
- **PostgreSQL:** Stores `location_insights`, `price_trends`, and `amenities`.
- **Endpoints:**
    - `GET /api/v1/insights` (Main Map Data)
    - `GET /api/v1/location/{id}/trends` (Price History)

### 3. The Frontend (`frontend/`)
Hosted on **GitHub Pages / Netlify**.
- Pure HTML/JS (No framework overhead).
- Connects to the API to fetch live data.
- Uses **PMTiles** for serverless map data.

---

## 📂 Project Structure

```bash
├── api.py                 # Main Backend Application (FastAPI)
├── update_pipeline.py     # Orchestrator for Data/AI Pipeline
├── requirements.txt       # Lightweight dependencies for Cloud API
├── requirements-ai.txt    # Heavy AI dependencies for Local Pipeline
├── Procfile               # Deployment config for Render
├── frontend/              # Web Application Code
│   ├── app.js             # Map Logic & Data Fetching
│   ├── index.html         # Main Dashboard
│   └── ...
├── scraper/               # News & Reddit Scrapers
├── sentiment/             # FinBERT Model Logic
├── aggregation/           # Scoring Algorithms (Growth/Inv Logic)
├── utilities/             # Helper scripts (Migrations, Tests)
└── docs/                  # Project Documentation
```

---

## 🛠️ Setup & Installation

### Prerequisite: Database
You need a PostgreSQL database (Local or Cloud like **Neon.tech** / **Supabase**).
Create a `.env` file with:
```ini
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_HOST=...
DB_PORT=5432
```

### 1. Run the API (Backend)
```bash
pip install -r requirements.txt
uvicorn api:app --reload
```

### 2. Run the Pipeline (Data Update)
*Note: Requires ~2GB RAM for FinBERT.*
```bash
pip install -r requirements-ai.txt
python update_pipeline.py
```

### 3. Launch Frontend
Open `frontend/index.html` in your browser (Live Server).

---

## 📜 Deployment

- **Backend:** Deploy `api.py` to **Render** (Web Service).
- **Frontend:** Deploy `frontend/` to **GitHub Pages**.
- **Database:** Hosted on **Neon.tech** (Free Tier).

---

## 🛡️ License
Proprietary Intelligence System.
Built for Hyper-Local Real Estate Analysis.
