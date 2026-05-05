# Consultation Report Design

## Overview
A comprehensive PDF report for expert consultation sessions that includes:
- Session metadata (date, client, expert)
- Map screenshots with layers and amenities
- Property comparison table
- Location insights
- Expert recommendations

## Report Structure

### Page 1: Cover Page
- **Title**: "Property Consultation Report"
- **Client Name**: (optional)
- **Consultation Date**: Auto-generated
- **Expert Name**: (optional)
- **Locations Explored**: List of areas viewed
- **Properties Compared**: Count and names
- **Company Logo/Branding**

### Page 2-3: Map Views
- **Main Map Screenshot**: Current view with all active layers
- **Layer Legend**: What layers are visible (Metro, Flood zones, etc.)
- **Amenities Highlighted**: Schools, hospitals, malls visible
- **Property Pins**: Properties that were clicked/viewed
- **Annotations**: Optional notes about specific areas

### Page 4-N: Property Comparison
- **Current comparison table** (already implemented)
- All sections: Pricing, Project Info, Specs, Location, Amenities, Reviews

### Page N+1: Location Insights
- **For each location explored**:
  - Area name
  - Grid scores (connectivity, amenities, growth, investment)
  - Key highlights
  - Concerns/Issues
  - Market trends

### Last Page: Recommendations
- **Expert Notes**: Text area for consultant to add recommendations
- **Next Steps**: Action items for client
- **Contact Information**: Follow-up details

## Implementation Approach

### Option 1: Enhanced html2pdf (Recommended)
**Pros**: 
- Reuses existing html2pdf.js
- Can capture map canvas directly
- Single library for everything
- Easy to style with CSS

**Cons**:
- Need to build HTML structure for report
- Map screenshot requires canvas capture

### Option 2: jsPDF with plugins
**Pros**:
- More control over layout
- Can add images easily
- Better for multi-page reports

**Cons**:
- More complex code
- Need to manually position everything

### Option 3: Backend PDF generation (Python)
**Pros**:
- Professional libraries (ReportLab, WeasyPrint)
- Better for complex layouts
- Can generate on server

**Cons**:
- Need to send all data to backend
- More complex architecture

## Recommended Solution: Hybrid Approach

### Frontend: Capture & Collect
1. **Capture map screenshot** using `map.getCanvas().toDataURL()`
2. **Collect session data**:
   - Locations viewed (track in session)
   - Properties compared (already have)
   - Active layers (from city-layers.js)
   - Timestamps
3. **Build report HTML** with all sections
4. **Use html2pdf** to generate final PDF

### Backend: Optional Enhancements
- Store report metadata in database
- Email report to client
- Generate report ID for tracking

## Technical Implementation

### 1. Session Tracking
```javascript
class ConsultationSession {
  constructor() {
    this.startTime = new Date();
    this.locationsViewed = new Set();
    this.propertiesViewed = new Set();
    this.propertiesCompared = [];
    this.activeLayers = [];
    this.mapScreenshots = [];
    this.expertNotes = '';
  }
  
  trackLocationView(areaName) {
    this.locationsViewed.add(areaName);
  }
  
  trackPropertyView(propertyId) {
    this.propertiesViewed.add(propertyId);
  }
  
  captureMapState() {
    return {
      center: map.getCenter(),
      zoom: map.getZoom(),
      layers: this.activeLayers,
      timestamp: new Date()
    };
  }
}
```

### 2. Map Screenshot Capture
```javascript
async captureMapScreenshot() {
  const canvas = map.getCanvas();
  const dataURL = canvas.toDataURL('image/png', 1.0);
  return dataURL;
}
```

### 3. Report Builder
```javascript
class ConsultationReportBuilder {
  constructor(session, comparisonData) {
    this.session = session;
    this.comparisonData = comparisonData;
  }
  
  buildReportHTML() {
    return `
      <div class="consultation-report">
        ${this.buildCoverPage()}
        ${this.buildMapSection()}
        ${this.buildComparisonSection()}
        ${this.buildLocationInsights()}
        ${this.buildRecommendations()}
      </div>
    `;
  }
  
  async generatePDF() {
    const reportHTML = this.buildReportHTML();
    const opt = {
      margin: 15,
      filename: `consultation-report-${Date.now()}.pdf`,
      image: { type: 'jpeg', quality: 0.95 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
      pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
    };
    
    await html2pdf().set(opt).from(reportHTML).save();
  }
}
```

### 4. UI Integration
```javascript
// Add "Generate Consultation Report" button
<button onclick="generateConsultationReport()">
  📄 Generate Consultation Report
</button>

// Before generating, show modal to collect:
// - Client name (optional)
// - Expert notes
// - Which sections to include
```

## Data Flow

```
User Session
    ↓
Track interactions (locations, properties, layers)
    ↓
User clicks "Generate Report"
    ↓
Show report options modal
    ↓
Capture map screenshot
    ↓
Collect all session data
    ↓
Build report HTML
    ↓
Generate PDF with html2pdf
    ↓
Download report
```

## Report Sections Detail

### 1. Cover Page
- Branding/Logo
- Report title
- Date and time
- Client name (if provided)
- Summary stats (X locations, Y properties)

### 2. Session Summary
- **Locations Explored**: List with timestamps
- **Properties Viewed**: Count and names
- **Properties Compared**: Detailed list
- **Session Duration**: Start to end time

### 3. Map Views
- **Main Map**: Screenshot with current view
- **Active Layers**: Legend showing what's visible
  - Metro lines and stations
  - Flood-prone areas
  - Ward boundaries
  - Property pins
- **Amenities**: Highlighted on map
- **Annotations**: Optional expert notes on map

### 4. Property Comparison
- **Reuse existing comparison table**
- All sections already implemented
- Property reviews included

### 5. Location Insights
For each location explored:
- **Area Name**
- **Grid Scores**:
  - Connectivity: X/10
  - Amenities: X/10
  - Growth: X/10
  - Investment: X/10
- **Key Highlights**: Bullet points
- **Concerns**: Issues to be aware of
- **Market Trends**: Price trends, demand

### 6. Expert Recommendations
- **Text area**: Expert's personalized advice
- **Pros/Cons**: For each property
- **Best Match**: Recommended property with reasoning
- **Next Steps**: Action items
- **Follow-up**: Contact information

## Styling Considerations

### Print-Friendly CSS
```css
.consultation-report {
  font-family: 'Segoe UI', Arial, sans-serif;
  color: #333;
  background: white;
}

.report-page {
  page-break-after: always;
  padding: 20mm;
}

.report-header {
  border-bottom: 3px solid #3350c0;
  padding-bottom: 10px;
  margin-bottom: 20px;
}

.map-screenshot {
  width: 100%;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin: 20px 0;
}

.location-insight-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 15px;
  margin: 15px 0;
  page-break-inside: avoid;
}
```

## Implementation Priority

### Phase 1: Basic Report (MVP)
1. ✅ Property comparison (already done)
2. 🔲 Cover page with session info
3. 🔲 Map screenshot capture
4. 🔲 Simple PDF generation

### Phase 2: Enhanced Report
1. 🔲 Location insights section
2. 🔲 Session tracking
3. 🔲 Multiple map screenshots
4. 🔲 Layer legend

### Phase 3: Professional Features
1. 🔲 Expert notes/recommendations
2. 🔲 Report customization modal
3. 🔲 Branding/logo support
4. 🔲 Email delivery
5. 🔲 Report history/storage

## Estimated Effort

- **Phase 1 (MVP)**: 4-6 hours
- **Phase 2 (Enhanced)**: 6-8 hours
- **Phase 3 (Professional)**: 8-10 hours

**Total**: 18-24 hours for complete implementation

## Next Steps

1. Review this design with stakeholders
2. Prioritize which sections are must-have
3. Decide on Phase 1 scope
4. Implement session tracking
5. Build report HTML structure
6. Test PDF generation
7. Iterate based on feedback
