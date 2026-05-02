# Design Document: Property Comparison Feature

## 1. System Architecture

### 1.1 Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Vanilla JS)                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │ Properties Panel │      │ Comparison Modal │            │
│  │                  │      │                  │            │
│  │ - Property Cards │◄────►│ - Comparison UI  │            │
│  │ - Compare Button │      │ - Data Display   │            │
│  │ - Visual Badge   │      │ - Export Controls│            │
│  └────────┬─────────┘      └────────┬─────────┘            │
│           │                         │                        │
│           └────────┬────────────────┘                        │
│                    │                                         │
│         ┌──────────▼──────────┐                             │
│         │ ComparisonManager   │                             │
│         │                     │                             │
│         │ - State Management  │                             │
│         │ - localStorage      │                             │
│         │ - Data Fetching     │                             │
│         │ - Analytics         │                             │
│         └──────────┬──────────┘                             │
│                    │                                         │
└────────────────────┼─────────────────────────────────────────┘
                     │
                     │ Supabase RPC Calls
                     │
┌────────────────────▼─────────────────────────────────────────┐
│                  Supabase PostgreSQL                          │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────┐  ┌──────────────────────────┐  │
│  │ get_property_by_id_func │  │ get_all_insights         │  │
│  │                         │  │                          │  │
│  │ Returns: Full property  │  │ Returns: Location data   │  │
│  │ details with all fields │  │ with scores & insights   │  │
│  └─────────────────────────┘  └──────────────────────────┘  │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Tables:                                                  │ │
│  │ - unified_data_DataType_Raghu (properties)              │ │
│  │ - hyderabad_locations (location insights)               │ │
│  │ - bangalore_locations (location insights)               │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 1.2 Module Structure

```
frontend/
├── app.js (existing - modifications needed)
│   ├── ComparisonManager class (NEW)
│   ├── createProjectGroupCard() (MODIFY - add compare button)
│   └── Property display functions (existing)
│
├── comparison.js (NEW)
│   ├── ComparisonUI class
│   ├── renderComparisonModal()
│   ├── renderComparisonTable()
│   ├── renderMobileComparisonCards()
│   └── exportComparison()
│
├── style.css (MODIFY - add comparison styles)
└── style-mobile.css (MODIFY - add mobile comparison styles)
```

## 2. Data Models

### 2.1 Comparison State Structure

```javascript
// Stored in localStorage as "relai_comparison_state"
{
  propertyIds: [4545, 7364, 60359],  // Array of property IDs (max 4)
  timestamp: 1735862400000,           // Last updated timestamp
  version: "1.0"                      // Schema version for future migrations
}
```

### 2.2 Property Data Structure (from Supabase)

```javascript
{
  // Basic Info
  id: 4545,
  projectname: "LUMBINI ELYSEE",
  buildername: "Lumbini Constructions Private Limited",
  areaname: "Puppalguda",
  city: "Hyderabad",
  
  // Pricing
  price_per_sft: 10750,
  baseprojectprice: 29207750,
  total_buildup_area: "2717",
  
  // Specifications
  bhk: "3",
  sqfeet: "2717",
  carpet_area_percentage: "65",
  floor_to_ceiling_height: "10",
  no_of_car_parkings: "1",
  facing: "East",
  
  // Project Details
  project_type: "Apartment",
  construction_status: "Under Construction",
  possession_date: "01/2028",
  rera_number: "P02400005840",
  number_of_towers: "10",
  number_of_floors: "15",
  open_space: "70%",
  
  // Builder Info
  builder_age: null,
  builder_completed_properties: null,
  builder_ongoing_projects: null,
  builder_total_properties: null,
  
  // Amenities
  external_amenities: "Swimming Pool, Gym, Club House...",
  
  // Location
  google_place_location: "{\"lat\":12.96,\"lng\":77.59}",
  images: "[\"url1\", \"url2\"]"
}
```

### 2.3 Location Insights Structure

```javascript
{
  location_id: 123,
  location: "Puppalguda",
  connectivity_score: 7.5,
  amenities_score: 8.2,
  growth_score: 0.75,
  investment_score: 0.68,
  avg_sentiment: 0.15,
  sentiment_summary: "Positive development...",
  growth_summary: "Infrastructure improving...",
  invest_summary: "Good long-term potential..."
}
```

## 3. Component Design

### 3.1 ComparisonManager Class

**Responsibilities:**
- Manage comparison state (add/remove properties)
- Persist state to localStorage
- Fetch property and location data
- Provide state to UI components
- Track analytics events

**Public API:**

```javascript
class ComparisonManager {
  constructor() {
    this.state = { propertyIds: [], timestamp: Date.now(), version: "1.0" };
    this.cache = new Map(); // Cache fetched property data
    this.loadState();
  }
  
  // State Management
  addProperty(propertyId) { }
  removeProperty(propertyId) { }
  hasProperty(propertyId) { }
  getPropertyCount() { }
  clearAll() { }
  
  // Data Fetching
  async fetchPropertyDetails(propertyId) { }
  async fetchLocationInsights(areaName, city) { }
  async fetchAllComparisonData() { }
  
  // Persistence
  loadState() { }
  saveState() { }
  
  // Analytics
  trackEvent(eventName, data) { }
  
  // Observers (for UI updates)
  subscribe(callback) { }
  notify() { }
}
```

### 3.2 ComparisonUI Class

**Responsibilities:**
- Render comparison modal
- Display comparison table (desktop)
- Display comparison cards (mobile)
- Handle user interactions
- Export functionality

**Public API:**

```javascript
class ComparisonUI {
  constructor(comparisonManager) {
    this.manager = comparisonManager;
    this.modal = null;
    this.isOpen = false;
  }
  
  // Modal Management
  open() { }
  close() { }
  
  // Rendering
  render() { }
  renderDesktopTable(properties, locationInsights) { }
  renderMobileCards(properties, locationInsights) { }
  
  // Sections
  renderPricingSection(properties) { }
  renderSpecsSection(properties) { }
  renderProjectSection(properties) { }
  renderBuilderSection(properties) { }
  renderAmenitiesSection(properties) { }
  renderLocationSection(properties, locationInsights) { }
  
  // Utilities
  highlightBestValue(values, higherIsBetter) { }
  formatPrice(value) { }
  
  // Export
  exportToPDF() { }
  exportToCSV() { }
}
```

## 4. UI/UX Design

### 4.1 Desktop Layout (≥768px)

```
┌─────────────────────────────────────────────────────────────────┐
│ ✕ Close                    Property Comparison            Export │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ ┌─────────────┬──────────────┬──────────────┬──────────────┐   │
│ │             │  Property 1  │  Property 2  │  Property 3  │   │
│ │             ├──────────────┼──────────────┼──────────────┤   │
│ │             │   [Image]    │   [Image]    │   [Image]    │   │
│ │             │ Project Name │ Project Name │ Project Name │   │
│ │             │   Builder    │   Builder    │   Builder    │   │
│ │             │      ✕       │      ✕       │      ✕       │   │
│ ├─────────────┼──────────────┼──────────────┼──────────────┤   │
│ │ 💰 PRICING                                                │   │
│ ├─────────────┼──────────────┼──────────────┼──────────────┤   │
│ │ Price/sqft  │  ₹10,750 🟢  │  ₹7,650 🟢   │  ₹10,750     │   │
│ │ Base Price  │  ₹2.92 Cr    │  ₹1.84 Cr 🟢 │  ₹3.36 Cr 🔴 │   │
│ │ BHK         │      3       │      3       │     3.5      │   │
│ │ Area (sqft) │    2,717     │    2,405     │    3,128 🟢  │   │
│ ├─────────────┼──────────────┼──────────────┼──────────────┤   │
│ │ 📐 SPECIFICATIONS                                         │   │
│ ├─────────────┼──────────────┼──────────────┼──────────────┤   │
│ │ Carpet Area │     65%      │     72% 🟢   │     65%      │   │
│ │ Floor Height│     10 ft    │     10 ft    │     10 ft    │   │
│ │ Parking     │      1       │      1       │     N/A      │   │
│ │ Facing      │     East     │     West     │     N/A      │   │
│ ├─────────────┼──────────────┼──────────────┼──────────────┤   │
│ │ 🏗️ PROJECT DETAILS                                        │   │
│ ├─────────────┼──────────────┼──────────────┼──────────────┤   │
│ │ Type        │  Apartment   │  Apartment   │  Apartment   │   │
│ │ Status      │Under Constr. │     RTM 🟢   │Under Constr. │   │
│ │ Possession  │   01/2028    │  03/2025 🟢  │   01/2028    │   │
│ │ RERA        │P02400005840  │P02200003216  │P02400005840  │   │
│ │ Towers      │     10       │      2       │     10       │   │
│ │ Floors      │     15       │     12       │     15       │   │
│ │ Open Space  │     70% 🟢   │     65%      │     70% 🟢   │   │
│ ├─────────────┼──────────────┼──────────────┼──────────────┤   │
│ │ 📍 LOCATION INSIGHTS                                      │   │
│ ├─────────────┼──────────────┼──────────────┼──────────────┤   │
│ │ Connectivity│     N/A      │     8.5 🟢   │     N/A      │   │
│ │ Amenities   │     N/A      │     7.8      │     N/A      │   │
│ │ Growth      │     N/A      │     0.82 🟢  │     N/A      │   │
│ │ Investment  │     N/A      │     0.75     │     N/A      │   │
│ └─────────────┴──────────────┴──────────────┴──────────────┘   │
│                                                                   │
│                    [← Scroll for more →]                         │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Mobile Layout (<768px)

```
┌───────────────────────────────┐
│ ✕ Close    Property 1 of 3    │
├───────────────────────────────┤
│                               │
│        [Property Image]       │
│                               │
│      LUMBINI ELYSEE          │
│  Lumbini Constructions Pvt   │
│                               │
│  ┌─────────────────────────┐ │
│  │ 💰 PRICING              │ │
│  ├─────────────────────────┤ │
│  │ Price/sqft: ₹10,750 🟢  │ │
│  │ Base Price: ₹2.92 Cr    │ │
│  │ BHK: 3                  │ │
│  │ Area: 2,717 sqft        │ │
│  └─────────────────────────┘ │
│                               │
│  ┌─────────────────────────┐ │
│  │ 📐 SPECIFICATIONS       │ │
│  ├─────────────────────────┤ │
│  │ Carpet Area: 65%        │ │
│  │ Floor Height: 10 ft     │ │
│  │ Parking: 1              │ │
│  │ Facing: East            │ │
│  └─────────────────────────┘ │
│                               │
│  ┌─────────────────────────┐ │
│  │ 🏗️ PROJECT DETAILS      │ │
│  ├─────────────────────────┤ │
│  │ Type: Apartment         │ │
│  │ Status: Under Constr.   │ │
│  │ Possession: 01/2028     │ │
│  │ RERA: P02400005840      │ │
│  └─────────────────────────┘ │
│                               │
│      [Remove from Compare]    │
│                               │
│         ● ○ ○  (dots)         │
│     [← Swipe to next →]       │
└───────────────────────────────┘
```

### 4.3 Compare Button in Property Card

```
┌─────────────────────────────────────┐
│  [Property Image]                   │
│                                     │
│  Project Name                       │
│  Builder Name                       │
│  ₹10,750/sqft • 3 BHK              │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │ View Details │  │ ✓ Compare   │ │  ← NEW
│  └──────────────┘  └─────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

### 4.4 Floating Compare Button

```
┌─────────────────────────────────────┐
│                                     │
│         [Map View]                  │
│                                     │
│                                     │
│                                     │
│                                     │
│  ┌─────────────────────────────┐   │
│  │  Compare 3 Properties  →    │   │  ← Floating button
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

## 5. Data Flow

### 5.1 Adding Property to Comparison

```
User clicks "Compare" button
         │
         ▼
ComparisonManager.addProperty(propertyId)
         │
         ├─► Check if already in state → Skip if exists
         ├─► Check if limit reached (4) → Show notification
         │
         ▼
Update state.propertyIds array
         │
         ▼
Save to localStorage
         │
         ▼
Notify observers (UI updates)
         │
         ▼
Update property card button → "✓ Compare"
Update floating button → "Compare X Properties"
Track analytics event
```

### 5.2 Opening Comparison View

```
User clicks "Compare X Properties" button
         │
         ▼
ComparisonUI.open()
         │
         ▼
Show modal with loading state
         │
         ▼
ComparisonManager.fetchAllComparisonData()
         │
         ├─► For each propertyId:
         │   ├─► Check cache
         │   ├─► If not cached: callSupabaseRPC('get_property_by_id_func')
         │   └─► Store in cache
         │
         ├─► For each unique location:
         │   ├─► callSupabaseRPC('get_all_insights')
         │   ├─► Filter by location name
         │   └─► Store location insights
         │
         ▼
All data fetched (parallel promises)
         │
         ▼
ComparisonUI.render(properties, locationInsights)
         │
         ├─► Check viewport width
         │   ├─► ≥768px: renderDesktopTable()
         │   └─► <768px: renderMobileCards()
         │
         ▼
Display comparison with highlights
Track analytics event
```

### 5.3 Exporting Comparison

```
User clicks "Export" → Selects format (PDF/CSV)
         │
         ▼
ComparisonUI.exportToPDF() or exportToCSV()
         │
         ▼
Gather all visible comparison data
         │
         ├─► PDF: Use jsPDF library (already in project)
         │   ├─► Create document
         │   ├─► Add title and headers
         │   ├─► Add comparison table
         │   └─► Trigger download
         │
         └─► CSV: Generate CSV string
             ├─► Create header row
             ├─► Add data rows
             ├─► Create Blob
             └─► Trigger download
         │
         ▼
Track analytics event
```

## 6. Styling Strategy

### 6.1 Color Scheme (Blue Theme)

```css
/* Primary Colors */
--primary-blue: #3350C0;
--light-blue: #5B7FE8;
--mid-blue: #2A42A0;
--pale-blue: #E8EDFF;

/* Comparison Highlights */
--highlight-best: #10B981;    /* Green for best values */
--highlight-worst: #EF4444;   /* Red for worst values */
--highlight-neutral: #6B7280; /* Gray for neutral */

/* Comparison UI */
--comparison-bg: #FFFFFF;
--comparison-border: #E5E7EB;
--comparison-header-bg: var(--pale-blue);
--comparison-row-hover: #F9FAFB;
```

### 6.2 Key CSS Classes

```css
/* Modal */
.comparison-modal { }
.comparison-modal-overlay { }
.comparison-modal-content { }
.comparison-modal-header { }
.comparison-modal-body { }

/* Desktop Table */
.comparison-table { }
.comparison-table-header { }
.comparison-table-body { }
.comparison-property-column { }
.comparison-attribute-row { }
.comparison-section-header { }

/* Mobile Cards */
.comparison-cards-container { }
.comparison-card { }
.comparison-card-navigation { }
.comparison-card-dots { }

/* Highlights */
.highlight-best { }
.highlight-worst { }
.highlight-neutral { }

/* Buttons */
.compare-btn { }
.compare-btn-active { }
.floating-compare-btn { }
.remove-from-compare-btn { }
```

## 7. Implementation Plan

### Phase 1: Core Infrastructure (Tasks 1-3)
1. Create ComparisonManager class with state management
2. Add localStorage persistence
3. Integrate with existing property cards (add compare button)

### Phase 2: Desktop UI (Tasks 4-7)
4. Create ComparisonUI class
5. Implement desktop comparison table
6. Add visual highlighting logic
7. Implement data fetching and caching

### Phase 3: Mobile UI (Tasks 8-9)
8. Implement mobile card-based layout
9. Add swipe navigation

### Phase 4: Export & Polish (Tasks 10-12)
10. Implement PDF export
11. Implement CSV export
12. Add analytics tracking

### Phase 5: Testing & Integration (Tasks 13-15)
13. Test with real data
14. Test responsive behavior
15. Test error handling

## 8. Technical Considerations

### 8.1 Performance Optimization

- **Caching**: Cache fetched property data to avoid redundant API calls
- **Parallel Fetching**: Fetch all property details in parallel using Promise.all()
- **Lazy Loading**: Only fetch location insights when comparison modal opens
- **Debouncing**: Debounce localStorage writes to avoid excessive I/O

### 8.2 Error Handling

```javascript
// Graceful degradation for missing data
function safeGet(obj, path, defaultValue = 'N/A') {
  return path.split('.').reduce((acc, part) => 
    acc && acc[part] !== undefined ? acc[part] : defaultValue, obj);
}

// localStorage error handling
function safeLocalStorageSet(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (e) {
    if (e.name === 'QuotaExceededError') {
      console.warn('localStorage quota exceeded');
      // Clear old analytics data
      localStorage.removeItem('relai_comparison_analytics');
      // Retry
      try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
      } catch (e2) {
        return false;
      }
    }
    return false;
  }
}
```

### 8.3 Accessibility

- **Keyboard Navigation**: Tab through properties, Enter to select, Escape to close
- **ARIA Labels**: Add aria-labels to all interactive elements
- **Focus Management**: Trap focus within modal when open
- **Screen Reader Support**: Add sr-only text for context
- **Color Contrast**: Ensure WCAG AA compliance for all highlights

### 8.4 Browser Compatibility

- **Target**: Modern browsers (Chrome, Firefox, Safari, Edge)
- **localStorage**: Check availability before use
- **CSS Grid**: Use for desktop table layout (widely supported)
- **Flexbox**: Use for mobile card layout
- **Touch Events**: Use for mobile swipe navigation

## 9. Testing Strategy

### 9.1 Unit Tests (Manual)

- ComparisonManager.addProperty() with various inputs
- ComparisonManager.removeProperty() edge cases
- localStorage persistence and recovery
- Data fetching with mock responses
- Highlighting logic with various value sets

### 9.2 Integration Tests

- Add property → Open comparison → Verify data displayed
- Remove property → Verify UI updates
- Export PDF → Verify file downloads
- Export CSV → Verify data format
- Mobile swipe → Verify navigation

### 9.3 User Acceptance Tests

- Compare 2 properties successfully
- Compare 4 properties (max limit)
- Try to add 5th property (should show notification)
- Close and reopen browser (state persists)
- Export comparison as PDF
- View on mobile device (responsive layout)

## 10. Future Enhancements

### 10.1 Phase 2 Features (Post-MVP)

- **Smart Recommendations**: AI-powered "Best Match" indicator based on user preferences
- **Comparison History**: Save multiple comparison sets
- **Share Comparison**: Generate shareable link
- **Print Optimization**: Print-friendly CSS
- **Advanced Filters**: Filter properties in comparison by criteria
- **Side-by-Side Map View**: Show all compared properties on map simultaneously
- **Commute Comparison**: Compare commute times from each property to user's office

### 10.2 Analytics Insights

Track these metrics for product improvement:
- Most compared property types (Apartment vs Villa)
- Average number of properties compared per session
- Most viewed comparison sections
- Export format preferences (PDF vs CSV)
- Mobile vs desktop usage
- Comparison abandonment rate

## 11. Dependencies

### 11.1 Existing Libraries (Already in Project)

- **jsPDF**: For PDF export (already used for location reports)
- **MapLibre GL**: For map integration (existing)
- **Supabase JS Client**: For API calls (existing)

### 11.2 New Dependencies (None Required)

All functionality can be implemented with vanilla JavaScript and existing libraries.

## 12. Security Considerations

- **XSS Prevention**: Sanitize all user-generated content before rendering
- **localStorage Limits**: Validate data before storing, handle quota errors
- **API Rate Limiting**: Implement request throttling for Supabase calls
- **Data Validation**: Validate all property data before display
- **CORS**: Ensure Supabase CORS settings allow frontend domain

## 13. Deployment Checklist

- [ ] Test on multiple browsers (Chrome, Firefox, Safari, Edge)
- [ ] Test on mobile devices (iOS Safari, Android Chrome)
- [ ] Test with slow network (throttle to 3G)
- [ ] Test with localStorage disabled
- [ ] Test with 0, 1, 2, 3, 4 properties in comparison
- [ ] Test export functionality (PDF and CSV)
- [ ] Verify analytics tracking
- [ ] Check accessibility with screen reader
- [ ] Verify color contrast ratios
- [ ] Test error scenarios (API failures, missing data)
- [ ] Update documentation
- [ ] Deploy to staging environment
- [ ] User acceptance testing
- [ ] Deploy to production
