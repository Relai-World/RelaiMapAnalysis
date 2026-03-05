# Project Documentation: West Hyderabad Intelligence

## 1. System Architecture

The project follows a **Decoupled Client-Server Architecture**:

- **Client (Frontend)**: A high-performance static web application hosted on GitHub Pages. It communicates with the backend via RESTful API calls.
- **Server (Backend)**: A lightweight FastAPI service hosted on Render. It handles database connections, business logic, and external API integrations (Overpass API).
- **Storage (Database)**: A PostgreSQL database with the **PostGIS** extension, enabling spatial geometry data types and spatial indexing.

---

## 2. Technical Stack Detail

### **Geospatial Processing**
- **PMTiles (Protomaps)**: Used to serve vector tiles for infrastructure layers. This allows for fast, serverless map rendering of large datasets like "Schools" and "Lakes" without needing a dedicated Tile Server.
- **MapLibre GL JS**: The primary mapping engine used for rendering the interactive map and handling user interactions.

### **Backend Logic**
- **FastAPI**: Chosen for its high performance and asynchronous capabilities.
- **Overpass API**: Used to dynamically fetch the count of nearby infrastructure (schools, hospitals, etc.) for locations that aren't already hardcoded in the primary database.

---

## 3. Database Schema

The database consists of two primary tables linked by a common `location_id`.

### **`locations` Table**
Used for storing the base location data and geometry.
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | SERIAL (PK) | Unique Location ID |
| `name` | VARCHAR | Name of the area (e.g., Manikonda, Madhapur) |
| `geom` | GEOMETRY(POINT) | PostGIS coordinates for the location center |

### **`location_insights` Table**
Used for storing the analytical scores.
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | SERIAL (PK) | Unique ID |
| `location_id` | INT (FK) | Reference to `locations` |
| `avg_sentiment_score` | FLOAT | Sentiment Score (-1.0 to 1.0) |
| `growth_score` | FLOAT | Predicted growth index |
| `investment_score` | FLOAT | Overall investment rating |

---

## 4. UI/UX Design System

### **Theme: Modern Dark Mode**
- **Background**: `#020617` (Deep Midnight Blue)
- **Primary Color**: `#2563eb` (Brand Blue)
- **Sentiment Colors**:
  - Positive/Excellent: `#4ade80` (Emerald Green)
  - Neutral: `#60a5fa` (Sky Blue)
  - Negative: `#f87171` (Red/Coral)

### **Responsive Behavior**
- **Desktop**: Sidebar (Intel Card) on the left, floating Layers panel on the right.
- **Mobile**: Intel Card transforms into a **Slide-up Bottom Sheet**, and Layers panel is centered for thumb-reach access.

---

## 5. API Reference

### `GET /api/v1/insights`
Returns all locations with their associated investment insights.
- **Response Format**: List of JSON objects containing `location`, `latitude`, `longitude`, and scores.

### `GET /api/v1/location/{id}/infra`
Fetches a real-time count of infrastructure (Hospitals, Schools, Metro) within a 3km radius from the location.
- **External Dependency**: Calls the OpenStreetMap Overpass API.

---

## 6. Implementation Notes

### **PDF Generation**
Uses `jsPDF` on the client-side. The PDF is generated entirely within the browser based on the `activeMarker` properties, avoiding server-side load for file generation.

### **Frontend State Management**
Uses a simplified global state in `app.js`. Viewport changes and layer visibility are directly bound to MapLibre's internal source/layer management.
