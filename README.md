# 🏙️ West Hyderabad Intelligence

**A Premium Real Estate Intelligence Dashboard for West Hyderabad.**

[![Frontend](https://img.shields.io/badge/Frontend-GitHub--Pages-blue?style=for-the-badge&logo=github)](https://harjeet1309.github.io/west-hyderabad-intelliweb/)
[![Backend](https://img.shields.io/badge/Backend-Render-green?style=for-the-badge&logo=render)](https://west-hyderabad-intelliweb.onrender.com)
[![Database](https://img.shields.io/badge/Database-Supabase-3ecf8e?style=for-the-badge&logo=supabase)](https://supabase.com)

---

## 🌟 Overview

West Hyderabad Intelligence provides investors, developers, and home buyers with deep data-driven insights into the rapidly growing real estate market of West Hyderabad. The platform combines interactive geospatial data with market sentiment and investment potential analysis.

---

## 🚀 Key Features

### 1. **Interactive Intelligence Map**
- **Vector Layers**: High-performance mapping using **PMTiles** (Schools, Highways, Metro, ORR, Lakes).
- **Customized Markers**: Minimalist design with interactive intelligence "hotspots" for key locations.
- **Smart Toggling**: Toggle multiple infrastructure layers instantly from a compact, floating grid.

### 2. **Deep Data Insights (Intel Card)**
- **Market Sentiment**: Analyzing real estate trends to determine positive/neutral/negative outlooks.
- **Growth Potential**: Predictive scoring for future appreciation.
- **Investment Score**: Comprehensive rating (Excellent/Good/Average) based on integrated data points.
- **Location Imagery**: Dynamic image fetching for every mapped location.

### 3. **Reporting & Persistence**
- **PDF Generation**: Download professional location-based reports with a single click.
- **Supabase Integration**: Robust PostgreSQL backend with PostGIS for location-based queries.

---

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | Vanilla HTML5/JS/CSS, MapLibre GL JS, PMTiles, jsPDF |
| **Backend** | Python, FastAPI, Psycopg2, Requests |
| **Mapping** | Protomaps (PMTiles), Overpass API (OpenStreetMap) |
| **Database** | PostgreSQL + PostGIS (Supabase/Neon) |
| **Hosting** | GitHub Pages (UI), Render (API) |

---

## 💻 Local Development

### 1. Backend (FastAPI)
```bash
# Install dependencies
pip install -r requirements.txt

# Start the dev server
uvicorn api:app --reload
```
*API accessible at `http://127.0.0.1:8000`*

### 2. Frontend (Static Site)
```bash
# Using Python
python -m http.server 3000 --directory frontend

# OR Using NPX
npx serve frontend
```
*Dashboard accessible at `http://localhost:3000`*

---

## 📄 Documentation

For a detailed breakdown of the architecture, database schema, and system design, please refer to the [PROJECT_DOCUMENTATION.md](./PROJECT_DOCUMENTATION.md).

---

## 🤝 Contribution

1. Fork the project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

*Developed with ❤️ for the West Hyderabad Community.*
