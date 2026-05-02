# Requirements Document

## Introduction

The Property Comparison feature enables users of the real estate intelligence platform to compare 3-4 properties side-by-side to make informed purchase decisions. Users can select properties from the map or properties panel, view them in a comparison table with key metrics, and analyze differences across pricing, specifications, project details, builder track record, amenities, and location insights. The feature integrates with the existing vanilla JavaScript frontend and Supabase backend, maintaining consistency with the current UI/UX patterns.

## Glossary

- **Comparison_Manager**: The JavaScript module responsible for managing the comparison state, including adding/removing properties and persisting selections
- **Comparison_UI**: The user interface component that displays the side-by-side comparison table
- **Property_Card**: The visual representation of a property in the properties panel with comparison controls
- **Comparison_Slot**: One of the 3-4 available positions in the comparison table
- **Location_Insights**: Aggregated data about a property's location including connectivity, amenities, growth, and investment scores
- **Property_Detail**: The complete set of property attributes including pricing, specifications, project info, and builder data
- **Comparison_State**: The current set of properties selected for comparison, persisted in browser storage
- **Properties_Panel**: The existing right-side panel that displays properties for a selected location
- **Supabase_RPC**: Remote procedure call functions in the Supabase PostgreSQL database

## Requirements

### Requirement 1: Property Selection for Comparison

**User Story:** As a property buyer, I want to select properties for comparison from the map or properties panel, so that I can analyze multiple options side-by-side.

#### Acceptance Criteria

1. WHEN a user views a property card in the Properties_Panel, THE Property_Card SHALL display a "Compare" button
2. WHEN a user clicks the "Compare" button on a property, THE Comparison_Manager SHALL add the property to the Comparison_State
3. IF the Comparison_State already contains 4 properties, THEN THE Comparison_Manager SHALL display a notification "Maximum 4 properties can be compared"
4. WHEN a property is added to the Comparison_State, THE Property_Card SHALL update the button to show "Remove from Compare" with a visual indicator
5. WHEN a user clicks "Remove from Compare", THE Comparison_Manager SHALL remove the property from the Comparison_State
6. THE Comparison_Manager SHALL persist the Comparison_State in browser localStorage
7. WHEN the page loads, THE Comparison_Manager SHALL restore the Comparison_State from localStorage
8. WHEN the Comparison_State changes, THE Comparison_Manager SHALL update a comparison counter badge showing the number of selected properties

### Requirement 2: Comparison View Access

**User Story:** As a property buyer, I want to open the comparison view to see my selected properties side-by-side, so that I can analyze them together.

#### Acceptance Criteria

1. WHEN at least 2 properties are in the Comparison_State, THE Comparison_UI SHALL display a floating "Compare Properties" button
2. WHEN a user clicks the "Compare Properties" button, THE Comparison_UI SHALL open a full-screen comparison modal
3. THE Comparison_UI SHALL display a close button to exit the comparison view
4. WHEN the comparison view is closed, THE Comparison_State SHALL remain unchanged
5. WHEN fewer than 2 properties are in the Comparison_State, THE Comparison_UI SHALL hide the "Compare Properties" button
6. THE Comparison_UI SHALL be accessible via keyboard navigation (Tab, Enter, Escape keys)

### Requirement 3: Comparison Table Display

**User Story:** As a property buyer, I want to see properties displayed in a side-by-side table format, so that I can easily compare their attributes.

#### Acceptance Criteria

1. THE Comparison_UI SHALL display properties in vertical columns with one column per property
2. THE Comparison_UI SHALL display comparison attributes in horizontal rows with one row per attribute
3. THE Comparison_UI SHALL display property images at the top of each column
4. THE Comparison_UI SHALL display the project name and builder name as column headers
5. THE Comparison_UI SHALL group attributes into sections: Pricing, Specifications, Project Details, Builder Track Record, Amenities, and Location Insights
6. THE Comparison_UI SHALL display section headers with visual separation between sections
7. WHEN a property lacks data for an attribute, THE Comparison_UI SHALL display "N/A" in that cell
8. THE Comparison_UI SHALL make the table horizontally scrollable when displaying 3-4 properties
9. THE Comparison_UI SHALL fix the attribute labels column on the left during horizontal scrolling

### Requirement 4: Pricing Comparison

**User Story:** As a property buyer, I want to compare pricing information across properties, so that I can evaluate affordability and value.

#### Acceptance Criteria

1. THE Comparison_UI SHALL display price per square foot for each property
2. THE Comparison_UI SHALL display base project price for each property
3. THE Comparison_UI SHALL display total buildup area for each property
4. THE Comparison_UI SHALL display the BHK configuration for each property
5. THE Comparison_UI SHALL highlight the lowest price per square foot with a visual indicator
6. THE Comparison_UI SHALL highlight the highest price per square foot with a different visual indicator
7. THE Comparison_UI SHALL format prices with Indian numbering system (lakhs and crores)
8. THE Comparison_UI SHALL display currency symbol (₹) for all price values

### Requirement 5: Specifications Comparison

**User Story:** As a property buyer, I want to compare property specifications, so that I can evaluate space and features.

#### Acceptance Criteria

1. THE Comparison_UI SHALL display carpet area percentage for each property
2. THE Comparison_UI SHALL display floor-to-ceiling height for each property
3. THE Comparison_UI SHALL display number of car parking spaces for each property
4. THE Comparison_UI SHALL display property facing direction for each property
5. THE Comparison_UI SHALL display square footage for each property
6. WHEN comparing parking spaces, THE Comparison_UI SHALL highlight the property with the most parking spaces
7. WHEN comparing carpet area percentage, THE Comparison_UI SHALL highlight the property with the highest percentage

### Requirement 6: Project Details Comparison

**User Story:** As a property buyer, I want to compare project-level details, so that I can evaluate project quality and timeline.

#### Acceptance Criteria

1. THE Comparison_UI SHALL display project type (Apartment/Villa) for each property
2. THE Comparison_UI SHALL display construction status (Under Construction/Ready to Move) for each property
3. THE Comparison_UI SHALL display possession date for each property
4. THE Comparison_UI SHALL display RERA registration number for each property
5. THE Comparison_UI SHALL display number of towers for each property
6. THE Comparison_UI SHALL display number of floors for each property
7. THE Comparison_UI SHALL display open space percentage for each property
8. WHEN comparing possession dates, THE Comparison_UI SHALL highlight the earliest possession date
9. WHEN comparing open space percentage, THE Comparison_UI SHALL highlight the property with the highest percentage

### Requirement 7: Builder Track Record Comparison

**User Story:** As a property buyer, I want to compare builder track records, so that I can evaluate builder reliability and experience.

#### Acceptance Criteria

1. THE Comparison_UI SHALL display builder age in years for each property
2. THE Comparison_UI SHALL display number of completed projects for each property
3. THE Comparison_UI SHALL display number of ongoing projects for each property
4. THE Comparison_UI SHALL display total number of projects for each property
5. WHEN comparing builder age, THE Comparison_UI SHALL highlight the builder with the most experience
6. WHEN comparing completed projects, THE Comparison_UI SHALL highlight the builder with the most completed projects

### Requirement 8: Amenities Comparison

**User Story:** As a property buyer, I want to compare amenities across properties, so that I can evaluate lifestyle features.

#### Acceptance Criteria

1. THE Comparison_UI SHALL display a list of external amenities for each property
2. THE Comparison_UI SHALL display amenities as a bulleted list or comma-separated values
3. THE Comparison_UI SHALL display amenity count for each property
4. WHEN comparing amenity counts, THE Comparison_UI SHALL highlight the property with the most amenities
5. WHEN a property has no amenities data, THE Comparison_UI SHALL display "No amenities data available"

### Requirement 9: Location Insights Comparison

**User Story:** As a property buyer, I want to compare location-level insights, so that I can evaluate neighborhood quality and investment potential.

#### Acceptance Criteria

1. THE Comparison_UI SHALL fetch location insights from hyderabad_locations or bangalore_locations tables based on property city
2. THE Comparison_UI SHALL display connectivity score (0-10) for each property's location
3. THE Comparison_UI SHALL display amenities score (0-10) for each property's location
4. THE Comparison_UI SHALL display growth score (0-10) for each property's location
5. THE Comparison_UI SHALL display investment score (0-10) for each property's location
6. THE Comparison_UI SHALL display average sentiment score for each property's location
7. WHEN comparing location scores, THE Comparison_UI SHALL highlight the highest score in each category
8. WHEN location insights are unavailable, THE Comparison_UI SHALL display "Location insights not available"
9. THE Comparison_UI SHALL display infrastructure distances (metro, hospital, school) for each location

### Requirement 10: Property Removal from Comparison

**User Story:** As a property buyer, I want to remove properties from the comparison view, so that I can focus on the most relevant options.

#### Acceptance Criteria

1. WHEN viewing the comparison table, THE Comparison_UI SHALL display a remove button (×) on each property column header
2. WHEN a user clicks the remove button, THE Comparison_Manager SHALL remove that property from the Comparison_State
3. WHEN a property is removed, THE Comparison_UI SHALL update the table to show remaining properties
4. WHEN only 1 property remains after removal, THE Comparison_UI SHALL display a message "Add at least one more property to compare"
5. THE Comparison_UI SHALL maintain the comparison view open after removing a property
6. THE Comparison_Manager SHALL update the comparison counter badge when a property is removed

### Requirement 11: Comparison State Persistence

**User Story:** As a property buyer, I want my comparison selections to persist across sessions, so that I can continue my analysis later.

#### Acceptance Criteria

1. WHEN a property is added to the Comparison_State, THE Comparison_Manager SHALL save the property ID to localStorage
2. WHEN a property is removed from the Comparison_State, THE Comparison_Manager SHALL update localStorage
3. WHEN the page loads, THE Comparison_Manager SHALL read property IDs from localStorage
4. WHEN the page loads with saved property IDs, THE Comparison_Manager SHALL fetch full property details using Supabase_RPC
5. WHEN localStorage contains invalid property IDs, THE Comparison_Manager SHALL remove them from the Comparison_State
6. THE Comparison_Manager SHALL store comparison state under the key "relai_comparison_state"
7. THE Comparison_Manager SHALL handle localStorage quota exceeded errors gracefully

### Requirement 12: Visual Highlighting and Indicators

**User Story:** As a property buyer, I want important differences to be visually highlighted, so that I can quickly identify the best options.

#### Acceptance Criteria

1. WHEN comparing numeric values, THE Comparison_UI SHALL apply a green highlight to the best value (lowest price, highest score)
2. WHEN comparing numeric values, THE Comparison_UI SHALL apply a red highlight to the worst value (highest price, lowest score)
3. THE Comparison_UI SHALL use neutral styling for middle-range values
4. THE Comparison_UI SHALL use a gold/yellow highlight for "best overall" indicators
5. THE Comparison_UI SHALL maintain consistent color coding across all comparison sections
6. THE Comparison_UI SHALL ensure highlights meet WCAG AA contrast requirements
7. WHEN all properties have the same value for an attribute, THE Comparison_UI SHALL not apply any highlighting

### Requirement 13: Responsive Design for Comparison View

**User Story:** As a property buyer using a mobile device, I want the comparison view to work on my screen, so that I can compare properties on the go.

#### Acceptance Criteria

1. WHEN the viewport width is less than 768px, THE Comparison_UI SHALL switch to a card-based layout
2. WHEN in card-based layout, THE Comparison_UI SHALL display one property per card
3. WHEN in card-based layout, THE Comparison_UI SHALL allow swiping between property cards
4. WHEN in card-based layout, THE Comparison_UI SHALL display navigation dots to indicate current card position
5. THE Comparison_UI SHALL maintain all comparison data in mobile view
6. THE Comparison_UI SHALL adjust font sizes and spacing for mobile readability
7. WHEN in desktop view (viewport ≥ 768px), THE Comparison_UI SHALL display the side-by-side table layout

### Requirement 14: Comparison Data Fetching

**User Story:** As a property buyer, I want comparison data to load quickly, so that I can analyze properties without delays.

#### Acceptance Criteria

1. WHEN the comparison view opens, THE Comparison_Manager SHALL fetch full property details using the get_property_by_id_func Supabase_RPC
2. WHEN the comparison view opens, THE Comparison_Manager SHALL fetch location insights for each property's area
3. THE Comparison_Manager SHALL fetch property details and location insights in parallel
4. WHEN data fetching is in progress, THE Comparison_UI SHALL display loading spinners for incomplete sections
5. WHEN data fetching fails for a property, THE Comparison_UI SHALL display an error message in that property's column
6. WHEN data fetching fails for location insights, THE Comparison_UI SHALL display "Unable to load location insights"
7. THE Comparison_Manager SHALL cache fetched property details to avoid redundant API calls
8. THE Comparison_Manager SHALL implement a 10-second timeout for data fetching operations

### Requirement 15: Export Comparison Data

**User Story:** As a property buyer, I want to export the comparison table, so that I can share it with family or save it for later reference.

#### Acceptance Criteria

1. WHEN viewing the comparison table, THE Comparison_UI SHALL display an "Export" button
2. WHEN a user clicks the "Export" button, THE Comparison_UI SHALL display export format options: PDF and CSV
3. WHEN a user selects PDF export, THE Comparison_Manager SHALL generate a PDF document with the comparison table
4. WHEN a user selects CSV export, THE Comparison_Manager SHALL generate a CSV file with comparison data
5. THE Comparison_Manager SHALL include all visible comparison attributes in the export
6. THE Comparison_Manager SHALL format the exported file with property names as column headers
7. THE Comparison_Manager SHALL trigger a browser download for the exported file
8. THE Comparison_Manager SHALL name the exported file with format "property-comparison-YYYY-MM-DD.pdf" or "property-comparison-YYYY-MM-DD.csv"

### Requirement 16: Comparison Analytics Tracking

**User Story:** As a platform owner, I want to track comparison feature usage, so that I can understand user behavior and improve the feature.

#### Acceptance Criteria

1. WHEN a user adds a property to comparison, THE Comparison_Manager SHALL log an analytics event "comparison_property_added"
2. WHEN a user removes a property from comparison, THE Comparison_Manager SHALL log an analytics event "comparison_property_removed"
3. WHEN a user opens the comparison view, THE Comparison_Manager SHALL log an analytics event "comparison_view_opened"
4. WHEN a user exports comparison data, THE Comparison_Manager SHALL log an analytics event "comparison_exported" with the export format
5. THE Comparison_Manager SHALL include property IDs in analytics events
6. THE Comparison_Manager SHALL include timestamp in analytics events
7. THE Comparison_Manager SHALL store analytics events in browser localStorage under key "relai_comparison_analytics"
8. THE Comparison_Manager SHALL limit analytics storage to the most recent 100 events

### Requirement 17: Integration with Existing Properties Panel

**User Story:** As a property buyer, I want comparison controls to integrate seamlessly with the existing properties panel, so that the feature feels native to the platform.

#### Acceptance Criteria

1. THE Property_Card SHALL add comparison controls without disrupting the existing card layout
2. THE Property_Card SHALL maintain the current gold/blue color scheme for comparison buttons
3. WHEN a property is in the Comparison_State, THE Property_Card SHALL display a visual indicator (checkmark or badge)
4. THE Comparison_Manager SHALL work with the existing project grouping in the Properties_Panel
5. THE Comparison_Manager SHALL handle properties loaded via the get_properties_func Supabase_RPC
6. THE Comparison_Manager SHALL work with lead-filtered properties from the Expert Dashboard
7. THE Comparison_Manager SHALL maintain compatibility with the existing property detail drawer

### Requirement 18: Error Handling and Edge Cases

**User Story:** As a property buyer, I want the comparison feature to handle errors gracefully, so that I have a smooth experience even when issues occur.

#### Acceptance Criteria

1. WHEN localStorage is unavailable, THE Comparison_Manager SHALL display a warning "Comparison state cannot be saved"
2. WHEN a property fetch fails, THE Comparison_UI SHALL display "Unable to load property details" in that column
3. WHEN location insights fetch fails, THE Comparison_UI SHALL display "Location insights unavailable" in that section
4. WHEN the comparison view is opened with no properties, THE Comparison_UI SHALL display "No properties selected for comparison"
5. WHEN a property is deleted from the database, THE Comparison_Manager SHALL remove it from the Comparison_State on next load
6. WHEN network connectivity is lost, THE Comparison_Manager SHALL display "Network error - please check your connection"
7. THE Comparison_Manager SHALL validate property data before displaying to prevent rendering errors
8. WHEN export fails, THE Comparison_Manager SHALL display "Export failed - please try again"
