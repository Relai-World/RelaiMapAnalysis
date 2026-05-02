/**
 * ComparisonUI - Manages the comparison modal and rendering
 * 
 * Version: 2.8
 * - Use AREA NAME instead of coordinates to fetch amenities
 * - Backend looks up coordinates from locations table (hyderabad_locations/bangalore_locations)
 * - Much simpler and more reliable - every property has area name!
 * - Store counts in 5 database columns: hospitals_count, shopping_malls_count, schools_count, restaurants_count, metro_stations_count
 * 
 * Responsibilities:
 * - Render comparison modal
 * - Display comparison table (desktop)
 * - Display comparison cards (mobile)
 * - Handle user interactions
 * - Export functionality
 */

class ComparisonUI {
  constructor(comparisonManager) {
    this.manager = comparisonManager;
    this.modal = null;
    this.isOpen = false;
    this.currentData = null;
    
    // Create modal element
    this.createModal();
    
    // Subscribe to comparison state changes
    this.manager.subscribe((state) => this.handleStateChange(state));
    
    console.log('✅ ComparisonUI initialized');
  }
  
  /**
   * Handle comparison state changes
   * Closes modal if property count drops below 2 while modal is open
   */
  handleStateChange(state) {
    if (this.isOpen && state.propertyIds.length < 2) {
      this.close();
      this.manager.showNotification('Comparison closed: need at least 2 properties', 'info');
    }
  }
  
  /* ===============================
     MODAL MANAGEMENT
  =============================== */
  
  /**
   * Create the modal structure
   */
  createModal() {
    // Check if modal already exists
    if (document.getElementById('comparison-modal')) {
      this.modal = document.getElementById('comparison-modal');
      return;
    }
    
    // Create modal HTML
    const modalHTML = `
      <div class="comparison-modal-overlay" id="comparison-modal-overlay">
        <div class="comparison-modal" id="comparison-modal">
          <div class="comparison-modal-header">
            <div class="comparison-modal-title-section">
              <h2>⚖️ Property Comparison</h2>
              <p class="comparison-modal-subtitle" id="comparison-subtitle">
                Compare properties side-by-side
              </p>
            </div>
            <div class="comparison-modal-actions">
              <button class="comparison-clear-btn" id="comparison-clear-btn" title="Clear all properties">
                🗑️ Clear All
              </button>
              <button class="comparison-export-btn" id="comparison-export-btn" title="Export comparison">
                📥 Export
              </button>
              <button class="comparison-close-btn" id="comparison-close-btn" title="Close">
                ✕
              </button>
            </div>
          </div>
          
          <div class="comparison-modal-body" id="comparison-modal-body">
            <!-- Content will be rendered here -->
          </div>
        </div>
      </div>
    `;
    
    // Add to DOM
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Get references
    this.modal = document.getElementById('comparison-modal');
    this.overlay = document.getElementById('comparison-modal-overlay');
    this.body = document.getElementById('comparison-modal-body');
    
    // Add event listeners
    this.setupEventListeners();
  }
  
  /**
   * Setup event listeners for modal
   */
  setupEventListeners() {
    // Close button
    const closeBtn = document.getElementById('comparison-close-btn');
    if (closeBtn) {
      closeBtn.onclick = () => this.close();
    }
    
    // Clear All button
    const clearBtn = document.getElementById('comparison-clear-btn');
    if (clearBtn) {
      clearBtn.onclick = () => this.clearAllComparison();
    }
    
    // Export button
    const exportBtn = document.getElementById('comparison-export-btn');
    if (exportBtn) {
      exportBtn.onclick = () => this.showExportMenu();
    }
    
    // Click outside to close
    this.overlay.onclick = (e) => {
      if (e.target === this.overlay) {
        this.close();
      }
    };
    
    // Escape key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
      }
    });
  }
  
  /**
   * Open the comparison modal
   */
  async open() {
    if (this.isOpen) return;
    
    const propertyCount = this.manager.getPropertyCount();
    
    if (propertyCount < 2) {
      this.manager.showNotification('Please select at least 2 properties to compare', 'warning');
      return;
    }
    
    // Show modal with loading state
    this.overlay.style.display = 'flex';
    this.isOpen = true;
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
    
    // Show loading
    this.body.innerHTML = `
      <div class="comparison-loading">
        <div class="comparison-spinner"></div>
        <p>Loading comparison data...</p>
      </div>
    `;
    
    try {
      // Fetch all comparison data
      const data = await this.manager.fetchAllComparisonData();
      this.currentData = data;
      
      // Render comparison
      this.render();
      
    } catch (error) {
      console.error('❌ Failed to load comparison data:', error);
      console.error('Error message:', error.message);
      console.error('Error stack:', error.stack);
      
      // Show detailed error in UI for debugging
      const errorDetails = error.message || 'Unknown error';
      
      this.body.innerHTML = `
        <div class="comparison-error">
          <div class="comparison-error-icon">⚠️</div>
          <h3>Failed to Load Comparison</h3>
          <p>Unable to fetch property data. Please try again.</p>
          <details style="margin-top: 15px; text-align: left;">
            <summary style="cursor: pointer; color: #666;">Show error details</summary>
            <pre style="background: #f5f5f5; padding: 10px; margin-top: 10px; border-radius: 5px; font-size: 12px; overflow-x: auto;">${errorDetails}\n\n${error.stack || ''}</pre>
          </details>
          <button class="comparison-retry-btn" onclick="window.comparisonUI.open()">
            Retry
          </button>
        </div>
      `;
    }
  }
  
  /**
   * Close the comparison modal
   */
  close() {
    if (!this.isOpen) return;
    
    this.overlay.style.display = 'none';
    this.isOpen = false;
    document.body.style.overflow = ''; // Restore scrolling
    
    console.log('✅ Comparison modal closed');
  }
  
  /**
   * Clear all properties from comparison
   */
  clearAllComparison() {
    // Show confirmation dialog
    const confirmed = confirm(
      `Are you sure you want to clear all ${this.manager.getPropertyCount()} properties from comparison?\n\nThis action cannot be undone.`
    );
    
    if (!confirmed) {
      return;
    }
    
    // Clear all properties
    this.manager.clearAll();
    
    // Close modal
    this.close();
    
    // Show success notification
    this.manager.showNotification('All properties cleared from comparison', 'success');
    
    console.log('✅ Cleared all properties from comparison');
  }
  
  /* ===============================
     RENDERING
  =============================== */
  
  /**
   * Main render function - decides desktop vs mobile layout
   */
  render() {
    if (!this.currentData) {
      console.error('❌ No data to render');
      return;
    }
    
    const { properties, locationInsights } = this.currentData;
    
    if (!properties || properties.length === 0) {
      this.body.innerHTML = `
        <div class="comparison-empty">
          <div class="comparison-empty-icon">📊</div>
          <h3>No Properties to Compare</h3>
          <p>The selected properties could not be loaded.</p>
        </div>
      `;
      return;
    }
    
    // Update subtitle
    const subtitle = document.getElementById('comparison-subtitle');
    if (subtitle) {
      subtitle.textContent = `Comparing ${properties.length} ${properties.length === 1 ? 'property' : 'properties'}`;
    }
    
    // Check viewport width for responsive rendering
    const isMobile = window.innerWidth < 768;
    
    if (isMobile) {
      this.renderMobileCards(properties, locationInsights);
    } else {
      this.renderDesktopTable(properties, locationInsights);
    }
  }
  
  /**
   * Render desktop comparison table
   */
  renderDesktopTable(properties, locationInsights) {
    const tableHTML = `
      <div class="comparison-table-container">
        <table class="comparison-table">
          <thead>
            <tr class="comparison-header-row">
              <th class="comparison-attribute-header">Attribute</th>
              ${properties.map(prop => `
                <th class="comparison-property-header">
                  <div class="comparison-property-header-content">
                    ${this.renderPropertyImage(prop)}
                    <h3 class="comparison-property-name">${prop.projectname || 'Unnamed Project'}</h3>
                    <p class="comparison-property-builder">${prop.buildername || 'Unknown Builder'}</p>
                    <button class="comparison-remove-btn" data-property-id="${prop.id}" title="Remove from comparison">
                      ✕
                    </button>
                  </div>
                </th>
              `).join('')}
            </tr>
          </thead>
          <tbody>
            ${this.renderPricingSection(properties)}
            ${this.renderProjectSection(properties)}
            ${this.renderSpecsSection(properties)}
            ${this.renderLocationSection(properties, locationInsights)}
            ${this.renderAmenitiesSection(properties)}
          </tbody>
        </table>
      </div>
    `;
    
    this.body.innerHTML = tableHTML;
    
    // Add remove button handlers
    this.body.querySelectorAll('.comparison-remove-btn').forEach((btn, index) => {
      btn.onclick = (e) => {
        e.stopPropagation();
        const propertyId = parseInt(btn.dataset.propertyId);
        
        // Remove from manager
        this.manager.removeProperty(propertyId);
        
        const remainingCount = this.manager.getPropertyCount();
        
        // If less than 2 properties remain, close modal
        if (remainingCount < 2) {
          this.close();
          this.manager.showNotification('Need at least 2 properties to compare', 'info');
        } else {
          // Remove the column dynamically without reloading
          this.removePropertyColumn(index + 1); // +1 because first column is attribute labels
          
          // Update subtitle
          const subtitle = document.getElementById('comparison-subtitle');
          if (subtitle) {
            subtitle.textContent = `Comparing ${remainingCount} ${remainingCount === 1 ? 'property' : 'properties'}`;
          }
          
          // Show notification
          this.manager.showNotification('Property removed from comparison', 'success');
        }
      };
    });
    
    // Fetch amenities from Google Places API for properties without stored amenities
    this.fetchAmenitiesFromGoogle(properties);
  }
  
  /**
   * Remove a property column from the table dynamically
   * @param {number} columnIndex - The column index to remove (0-based, where 0 is attribute labels)
   */
  removePropertyColumn(columnIndex) {
    const table = this.body.querySelector('.comparison-table');
    if (!table) return;
    
    // Remove header cell
    const headerRow = table.querySelector('.comparison-header-row');
    if (headerRow) {
      const headerCells = headerRow.querySelectorAll('th');
      if (headerCells[columnIndex]) {
        headerCells[columnIndex].remove();
      }
    }
    
    // Remove all data cells in that column
    const dataRows = table.querySelectorAll('.comparison-attribute-row');
    dataRows.forEach(row => {
      const cells = row.querySelectorAll('td');
      if (cells[columnIndex]) {
        cells[columnIndex].remove();
      }
    });
    
    // Remove section header cells (they span all columns, need to update colspan)
    const sectionRows = table.querySelectorAll('.comparison-section-header-row');
    sectionRows.forEach(row => {
      const cell = row.querySelector('.comparison-section-header');
      if (cell) {
        const currentColspan = parseInt(cell.getAttribute('colspan') || '1');
        cell.setAttribute('colspan', currentColspan - 1);
      }
    });
    
    console.log(`✅ Removed property column ${columnIndex} dynamically`);
  }
  
  /**
   * Render property image
   */
  renderPropertyImage(property) {
    let imageUrl = null;
    
    if (property.images) {
      try {
        const images = typeof property.images === 'string' ? JSON.parse(property.images) : property.images;
        if (Array.isArray(images) && images.length > 0) {
          imageUrl = images[0];
        }
      } catch (e) {
        console.warn('Failed to parse images:', e);
      }
    }
    
    if (imageUrl) {
      return `<img src="${imageUrl}" alt="${property.projectname}" class="comparison-property-image" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
              <div class="comparison-property-image-placeholder" style="display:none;">🏢</div>`;
    } else {
      return `<div class="comparison-property-image-placeholder">🏢</div>`;
    }
  }
  
  /* ===============================
     SECTION RENDERERS
  =============================== */
  
  /**
   * Render pricing section
   */
  renderPricingSection(properties) {
    const pricesPerSqft = properties.map(p => {
      const price = p.price_per_sft || p.full_details?.price_per_sft;
      return price || 0;
    });
    const basePrices = properties.map(p => {
      const price = p.baseprojectprice || p.full_details?.baseprojectprice;
      return price || 0;
    });
    
    return `
      <tr class="comparison-section-header-row">
        <td colspan="${properties.length + 1}" class="comparison-section-header">
          💰 Pricing
        </td>
      </tr>
      ${this.renderAttributeRow('Price / sqft', properties.map((p, i) => {
        const price = p.price_per_sft || p.full_details?.price_per_sft;
        return price ? `₹${Math.round(price).toLocaleString()}` : 'N/A';
      }), pricesPerSqft, false)}
      ${this.renderAttributeRow('Base Price', properties.map(p => {
        const price = p.baseprojectprice || p.full_details?.baseprojectprice;
        return price ? `₹${(price / 10000000).toFixed(2)} Cr` : 'N/A';
      }), basePrices, false)}
    `;
  }
  
  /**
   * Render project information section
   */
  renderProjectSection(properties) {
    return `
      <tr class="comparison-section-header-row">
        <td colspan="${properties.length + 1}" class="comparison-section-header">
          🏗️ Project Information
        </td>
      </tr>
      ${this.renderAttributeRow('Project Name', properties.map(p => {
        const name = p.projectname || p.full_details?.projectname;
        return name || 'N/A';
      }))}
      ${this.renderAttributeRow('Builder Name', properties.map(p => {
        const builder = p.buildername || p.full_details?.buildername;
        return builder || 'N/A';
      }))}
      ${this.renderAttributeRow('RERA Number', properties.map(p => {
        const rera = p.rera_number || p.full_details?.rera_number;
        return rera || 'N/A';
      }))}
      ${this.renderAttributeRow('Project Type', properties.map(p => {
        const type = p.project_type || p.full_details?.project_type;
        return type || 'N/A';
      }))}
      ${this.renderAttributeRow('Community Type', properties.map(p => {
        const community = p.communitytype || p.full_details?.communitytype;
        return community || 'N/A';
      }))}
      ${this.renderAttributeRow('Construction Status', properties.map(p => {
        const status = p.construction_status || p.full_details?.construction_status;
        return status || 'N/A';
      }))}
      ${this.renderAttributeRow('Launch Date', properties.map(p => {
        const date = p.project_launch_date || p.full_details?.project_launch_date;
        return date || 'N/A';
      }))}
      ${this.renderAttributeRow('Possession Date', properties.map(p => {
        const date = p.possession_date || p.full_details?.possession_date;
        return date || 'N/A';
      }))}
      ${this.renderAttributeRow('Total Land Area', properties.map(p => {
        const area = p.total_land_area || p.full_details?.total_land_area;
        return (area && area > 0) ? `${area} sqft` : 'N/A';
      }))}
    `;
  }
  
  /**
   * Render unit specifications section
   */
  renderSpecsSection(properties) {
    const areas = properties.map(p => {
      const sqft = p.sqfeet || p.full_details?.sqfeet;
      return parseFloat(sqft) || 0;
    });
    
    return `
      <tr class="comparison-section-header-row">
        <td colspan="${properties.length + 1}" class="comparison-section-header">
          📐 Unit Specifications
        </td>
      </tr>
      ${this.renderAttributeRow('Area (sqft)', properties.map((p, i) => {
        const sqft = p.sqfeet || p.full_details?.sqfeet;
        return sqft ? parseFloat(sqft).toLocaleString() : 'N/A';
      }), areas, true)}
      ${this.renderAttributeRow('Power Backup', properties.map(p => {
        const power = p.powerbackup || p.full_details?.powerbackup;
        return power || 'N/A';
      }))}
      ${this.renderAttributeRow('Visitor Parking', properties.map(p => {
        const parking = p.visitor_parking || p.full_details?.visitor_parking;
        return parking || 'N/A';
      }))}
    `;
  }
  
  /**
   * Render location section
   */
  renderLocationSection(properties, locationInsights) {
    // Get location insights for each property
    const insights = properties.map(prop => {
      if (!prop.areaname) return null;
      return locationInsights.get(prop.areaname.toLowerCase()) || null;
    });
    
    return `
      <tr class="comparison-section-header-row">
        <td colspan="${properties.length + 1}" class="comparison-section-header">
          📍 Location & Ratings
        </td>
      </tr>
      ${this.renderAttributeRow('Area Name', properties.map(p => {
        const area = p.areaname || p.full_details?.areaname;
        return area || 'N/A';
      }))}
      ${this.renderAttributeRow('Google Rating', properties.map(p => {
        // Priority: direct field > full_details
        const rating = p.google_place_rating || p.full_details?.google_place_rating;
        const ratingsTotal = p.google_place_user_ratings_total || p.full_details?.google_place_user_ratings_total;
        if (rating) {
          return ratingsTotal ? `${rating} ⭐ (${ratingsTotal} reviews)` : `${rating} ⭐`;
        }
        return 'N/A';
      }))}
      ${this.renderAttributeRow('Grid Score', properties.map(p => {
        // Priority: grid_score > GRID_Score > full_details > calculate
        let gridScore = p.grid_score || p.GRID_Score || p.full_details?.GRID_Score || p.full_details?.grid_score;
        
        // If no GRID_Score, try to calculate from individual scores
        if (!gridScore) {
          const connectivity = p.connectivity_score || p.full_details?.connectivity_score || 0;
          const amenities = p.amenities_score || p.full_details?.amenities_score || 0;
          if (connectivity > 0 || amenities > 0) {
            gridScore = (connectivity + amenities) / 2;
          }
        }
        
        return gridScore ? gridScore.toFixed(1) : 'N/A';
      }))}
    `;
  }
  
  /**
   * Render amenities section with fallback to Google Places API
   */
  renderAmenitiesSection(properties) {
    return `
      <tr class="comparison-section-header-row">
        <td colspan="${properties.length + 1}" class="comparison-section-header">
          🏊 Amenities
        </td>
      </tr>
      ${this.renderAttributeRow('Hospitals', properties.map((p, index) => {
        return '<span class="amenities-loading hospitals-count" data-property-index="' + index + '">Fetching...</span>';
      }), null, false, true)}
      ${this.renderAttributeRow('Schools', properties.map((p, index) => {
        return '<span class="amenities-loading schools-count" data-property-index="' + index + '">Fetching...</span>';
      }), null, false, true)}
      ${this.renderAttributeRow('Shopping Malls', properties.map((p, index) => {
        return '<span class="amenities-loading malls-count" data-property-index="' + index + '">Fetching...</span>';
      }), null, false, true)}
      ${this.renderAttributeRow('Restaurants', properties.map((p, index) => {
        return '<span class="amenities-loading restaurants-count" data-property-index="' + index + '">Fetching...</span>';
      }), null, false, true)}
      ${this.renderAttributeRow('Metro Stations', properties.map((p, index) => {
        return '<span class="amenities-loading metro-count" data-property-index="' + index + '">Fetching...</span>';
      }), null, false, true)}
    `;
  }
  
  /**
   * Fetch amenities count from Google Places API and store in database
   * Uses area name to get coordinates from locations table
   * Fetches 5 categories: hospitals, shopping malls, schools, restaurants, metro stations
   * Stores in columns: hospitals_count, shopping_malls_count, schools_count, restaurants_count, metro_stations_count
   */
  async fetchAmenitiesFromGoogle(properties) {
    const amenitiesLoadingSpans = document.querySelectorAll('.amenities-loading');
    
    // Group spans by property index
    const spansByProperty = {};
    amenitiesLoadingSpans.forEach(span => {
      const index = parseInt(span.dataset.propertyIndex);
      if (!spansByProperty[index]) spansByProperty[index] = {};
      
      if (span.classList.contains('hospitals-count')) spansByProperty[index].hospitals = span;
      else if (span.classList.contains('schools-count')) spansByProperty[index].schools = span;
      else if (span.classList.contains('malls-count')) spansByProperty[index].malls = span;
      else if (span.classList.contains('restaurants-count')) spansByProperty[index].restaurants = span;
      else if (span.classList.contains('metro-count')) spansByProperty[index].metro = span;
    });
    
    for (const [index, spans] of Object.entries(spansByProperty)) {
      const property = properties[parseInt(index)];
      
      if (!property) continue;
      
      // Get area name
      const areaName = property.areaname || property.full_details?.areaname;
      
      if (areaName && areaName.trim()) {
        // Fetch amenities count using area name
        Object.values(spans).forEach(span => span.textContent = 'Counting...');
        
        try {
          const response = await fetch('http://localhost:8000/api/nearby-amenities', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
              area_name: areaName.trim(),
              radius: 1000,
              property_id: property.id
            })
          });
          
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
          }
          
          const data = await response.json();
          
          if (data.error) {
            Object.values(spans).forEach(span => span.innerHTML = '<em>Unable to fetch</em>');
            console.error('Amenities API error:', data.error);
          } else {
            // Display individual counts
            if (spans.hospitals) spans.hospitals.innerHTML = `<strong>${data.hospitals_count || 0}</strong>`;
            if (spans.schools) spans.schools.innerHTML = `<strong>${data.schools_count || 0}</strong>`;
            if (spans.malls) spans.malls.innerHTML = `<strong>${data.shopping_malls_count || 0}</strong>`;
            if (spans.restaurants) spans.restaurants.innerHTML = `<strong>${data.restaurants_count || 0}</strong>`;
            if (spans.metro) spans.metro.innerHTML = `<strong>${data.metro_stations_count || 0}</strong>`;
            
            console.log(`✅ Fetched amenities for property ${property.id} (${areaName}): H:${data.hospitals_count} S:${data.schools_count} M:${data.shopping_malls_count} R:${data.restaurants_count} Metro:${data.metro_stations_count}`);
          }
          
        } catch (fetchError) {
          console.error('Failed to fetch amenities:', fetchError);
          Object.values(spans).forEach(span => span.innerHTML = '<em>Unable to fetch</em>');
        }
        
      } else {
        Object.values(spans).forEach(span => span.innerHTML = '<em>Area unavailable</em>');
        console.warn('Property missing area name:', property.id);
      }
    }
  }
  
  /**
   * Render a single attribute row with optional highlighting
   */
  renderAttributeRow(label, values, numericValues = null, higherIsBetter = true, isLongText = false) {
    let highlightClasses = [];
    
    // Apply highlighting if numeric values provided
    if (numericValues && numericValues.some(v => v > 0)) {
      highlightClasses = this.highlightBestValue(numericValues, higherIsBetter);
    }
    
    return `
      <tr class="comparison-attribute-row">
        <td class="comparison-attribute-label">${label}</td>
        ${values.map((value, i) => `
          <td class="comparison-attribute-value ${highlightClasses[i] || ''} ${isLongText ? 'long-text' : ''}">
            ${value}
          </td>
        `).join('')}
      </tr>
    `;
  }
  
  /**
   * Determine highlight classes for values
   */
  highlightBestValue(values, higherIsBetter = true) {
    const validValues = values.map((v, i) => ({ value: v, index: i })).filter(v => v.value > 0);
    
    if (validValues.length === 0) return values.map(() => '');
    
    // Check if all values are the same
    const allSame = validValues.every(v => v.value === validValues[0].value);
    if (allSame) return values.map(() => '');
    
    // Find best and worst
    const sorted = [...validValues].sort((a, b) => higherIsBetter ? b.value - a.value : a.value - b.value);
    const bestIndex = sorted[0].index;
    const worstIndex = sorted[sorted.length - 1].index;
    
    // Apply classes
    return values.map((v, i) => {
      if (v === 0 || v === null) return '';
      if (i === bestIndex) return 'highlight-best';
      if (i === worstIndex && validValues.length > 2) return 'highlight-worst';
      return '';
    });
  }
  
  /* ===============================
     MOBILE RENDERING
  =============================== */
  
  /**
   * Render mobile comparison cards
   */
  renderMobileCards(properties, locationInsights) {
    this.currentCardIndex = 0;
    
    const cardsHTML = properties.map((prop, index) => {
      const insights = prop.areaname ? locationInsights.get(prop.areaname.toLowerCase()) : null;
      
      // Helper to get field value from prop or full_details
      const getField = (field) => prop[field] || prop.full_details?.[field];
      
      // Get grid score - priority: grid_score > GRID_Score > full_details > calculate
      let gridScore = prop.grid_score || getField('GRID_Score') || getField('grid_score');
      
      // If no GRID_Score, try to calculate from individual scores
      if (!gridScore) {
        const connectivity = getField('connectivity_score') || 0;
        const amenities = getField('amenities_score') || 0;
        if (connectivity > 0 || amenities > 0) {
          gridScore = (connectivity + amenities) / 2;
        }
      }
      
      const gridScoreDisplay = gridScore ? gridScore.toFixed(1) : 'N/A';
      
      // Get Google rating
      const googleRating = prop.google_place_rating || getField('google_place_rating');
      const ratingsTotal = prop.google_place_user_ratings_total || getField('google_place_user_ratings_total');
      const googleRatingDisplay = googleRating 
        ? (ratingsTotal ? `${googleRating} ⭐ (${ratingsTotal})` : `${googleRating} ⭐`)
        : 'N/A';
      
      // Always fetch amenities count from API (will be cached in DB)
      const amenitiesDisplay = '<span class="amenities-loading" data-property-index="' + index + '">Fetching count...</span>';
      
      return `
        <div class="comparison-card ${index === 0 ? 'active' : ''}" data-card-index="${index}">
          <div class="comparison-card-header">
            ${this.renderPropertyImage(prop)}
            <h3 class="comparison-card-title">${getField('projectname') || 'Unnamed Project'}</h3>
            <p class="comparison-card-builder">${getField('buildername') || 'Unknown Builder'}</p>
            <button class="comparison-card-remove-btn" data-property-id="${prop.id}">
              Remove from Compare
            </button>
          </div>
          
          <div class="comparison-card-content">
            ${this.renderMobileSection('💰 Pricing', [
              { label: 'Price / sqft', value: getField('price_per_sft') ? `₹${Math.round(getField('price_per_sft')).toLocaleString()}` : 'N/A' },
              { label: 'Base Price', value: getField('baseprojectprice') ? `₹${(getField('baseprojectprice') / 10000000).toFixed(2)} Cr` : 'N/A' }
            ])}
            
            ${this.renderMobileSection('🏗️ Project Information', [
              { label: 'Project Name', value: getField('projectname') || 'N/A' },
              { label: 'Builder Name', value: getField('buildername') || 'N/A' },
              { label: 'RERA Number', value: getField('rera_number') || 'N/A' },
              { label: 'Project Type', value: getField('project_type') || 'N/A' },
              { label: 'Community Type', value: getField('communitytype') || 'N/A' },
              { label: 'Construction Status', value: getField('construction_status') || 'N/A' },
              { label: 'Launch Date', value: getField('project_launch_date') || 'N/A' },
              { label: 'Possession Date', value: getField('possession_date') || 'N/A' },
              { label: 'Total Land Area', value: (getField('total_land_area') && getField('total_land_area') > 0) ? `${getField('total_land_area')} sqft` : 'N/A' }
            ])}
            
            ${this.renderMobileSection('📐 Unit Specifications', [
              { label: 'Area (sqft)', value: getField('sqfeet') ? parseFloat(getField('sqfeet')).toLocaleString() : 'N/A' },
              { label: 'Power Backup', value: getField('powerbackup') || 'N/A' },
              { label: 'Visitor Parking', value: getField('visitor_parking') || 'N/A' }
            ])}
            
            ${this.renderMobileSection('📍 Location & Ratings', [
              { label: 'Area Name', value: getField('areaname') || 'N/A' },
              { label: 'Google Rating', value: googleRatingDisplay },
              { label: 'Grid Score', value: gridScoreDisplay }
            ])}
            
            ${this.renderMobileSection('🏊 Amenities', [
              { label: 'Hospitals', value: '<span class="amenities-loading hospitals-count" data-property-index="' + index + '">Fetching...</span>' },
              { label: 'Schools', value: '<span class="amenities-loading schools-count" data-property-index="' + index + '">Fetching...</span>' },
              { label: 'Shopping Malls', value: '<span class="amenities-loading malls-count" data-property-index="' + index + '">Fetching...</span>' },
              { label: 'Restaurants', value: '<span class="amenities-loading restaurants-count" data-property-index="' + index + '">Fetching...</span>' },
              { label: 'Metro Stations', value: '<span class="amenities-loading metro-count" data-property-index="' + index + '">Fetching...</span>' }
            ])}
          </div>
        </div>
      `;
    }).join('');
    
    this.body.innerHTML = `
      <div class="comparison-cards-container">
        <div class="comparison-cards-wrapper" id="comparison-cards-wrapper">
          ${cardsHTML}
        </div>
        
        <div class="comparison-cards-navigation">
          <div class="comparison-cards-dots" id="comparison-cards-dots">
            ${properties.map((_, i) => `
              <button class="comparison-dot ${i === 0 ? 'active' : ''}" data-dot-index="${i}"></button>
            `).join('')}
          </div>
          <div class="comparison-cards-counter">
            <span id="current-card-number">1</span> / ${properties.length}
          </div>
        </div>
      </div>
    `;
    
    // Setup swipe navigation
    this.setupSwipeNavigation(properties.length);
    
    // Setup remove buttons
    this.body.querySelectorAll('.comparison-card-remove-btn').forEach((btn, index) => {
      btn.onclick = () => {
        const propertyId = parseInt(btn.dataset.propertyId);
        
        // Remove from manager
        this.manager.removeProperty(propertyId);
        
        const remainingCount = this.manager.getPropertyCount();
        
        // If less than 2 properties remain, close modal
        if (remainingCount < 2) {
          this.close();
          this.manager.showNotification('Need at least 2 properties to compare', 'info');
        } else {
          // For mobile, we need to reload to maintain swipe functionality
          // But we'll make it smoother by preserving the current position if possible
          const currentIndex = this.currentCardIndex;
          this.open().then(() => {
            // Try to maintain position, or go to previous card if we removed the last one
            const newIndex = currentIndex >= remainingCount ? remainingCount - 1 : currentIndex;
            if (newIndex >= 0) {
              this.goToCard(newIndex);
            }
          });
          
          // Show notification
          this.manager.showNotification('Property removed from comparison', 'success');
        }
      };
    });
    
    // Setup dot navigation
    this.body.querySelectorAll('.comparison-dot').forEach(dot => {
      dot.onclick = () => {
        const index = parseInt(dot.dataset.dotIndex);
        this.goToCard(index);
      };
    });
    
    // Fetch amenities from Google Places API for properties without stored amenities
    this.fetchAmenitiesFromGoogle(properties);
  }
  
  /**
   * Render a mobile section
   */
  renderMobileSection(title, items) {
    return `
      <div class="comparison-mobile-section">
        <h4 class="comparison-mobile-section-title">${title}</h4>
        <div class="comparison-mobile-section-content">
          ${items.map(item => `
            <div class="comparison-mobile-row">
              <span class="comparison-mobile-label">${item.label}</span>
              <span class="comparison-mobile-value">${item.value}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }
  
  /**
   * Setup swipe navigation for mobile cards
   */
  setupSwipeNavigation(totalCards) {
    const wrapper = document.getElementById('comparison-cards-wrapper');
    if (!wrapper) return;
    
    let startX = 0;
    let currentX = 0;
    let isDragging = false;
    
    // Touch events
    wrapper.addEventListener('touchstart', (e) => {
      startX = e.touches[0].clientX;
      isDragging = true;
      wrapper.style.transition = 'none';
    });
    
    wrapper.addEventListener('touchmove', (e) => {
      if (!isDragging) return;
      currentX = e.touches[0].clientX;
      const diff = currentX - startX;
      const offset = -this.currentCardIndex * 100;
      wrapper.style.transform = `translateX(calc(${offset}% + ${diff}px))`;
    });
    
    wrapper.addEventListener('touchend', (e) => {
      if (!isDragging) return;
      isDragging = false;
      
      const diff = currentX - startX;
      const threshold = 50; // Minimum swipe distance
      
      wrapper.style.transition = 'transform 0.3s ease';
      
      if (diff > threshold && this.currentCardIndex > 0) {
        // Swipe right - previous card
        this.goToCard(this.currentCardIndex - 1);
      } else if (diff < -threshold && this.currentCardIndex < totalCards - 1) {
        // Swipe left - next card
        this.goToCard(this.currentCardIndex + 1);
      } else {
        // Snap back
        this.goToCard(this.currentCardIndex);
      }
    });
    
    // Mouse events for desktop testing
    wrapper.addEventListener('mousedown', (e) => {
      startX = e.clientX;
      isDragging = true;
      wrapper.style.transition = 'none';
      wrapper.style.cursor = 'grabbing';
    });
    
    wrapper.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      currentX = e.clientX;
      const diff = currentX - startX;
      const offset = -this.currentCardIndex * 100;
      wrapper.style.transform = `translateX(calc(${offset}% + ${diff}px))`;
    });
    
    wrapper.addEventListener('mouseup', (e) => {
      if (!isDragging) return;
      isDragging = false;
      
      const diff = currentX - startX;
      const threshold = 50;
      
      wrapper.style.transition = 'transform 0.3s ease';
      wrapper.style.cursor = 'grab';
      
      if (diff > threshold && this.currentCardIndex > 0) {
        this.goToCard(this.currentCardIndex - 1);
      } else if (diff < -threshold && this.currentCardIndex < totalCards - 1) {
        this.goToCard(this.currentCardIndex + 1);
      } else {
        this.goToCard(this.currentCardIndex);
      }
    });
    
    wrapper.addEventListener('mouseleave', () => {
      if (isDragging) {
        isDragging = false;
        wrapper.style.transition = 'transform 0.3s ease';
        wrapper.style.cursor = 'grab';
        this.goToCard(this.currentCardIndex);
      }
    });
  }
  
  /**
   * Navigate to a specific card
   */
  goToCard(index) {
    this.currentCardIndex = index;
    
    const wrapper = document.getElementById('comparison-cards-wrapper');
    const dots = document.querySelectorAll('.comparison-dot');
    const counter = document.getElementById('current-card-number');
    
    if (wrapper) {
      wrapper.style.transform = `translateX(-${index * 100}%)`;
    }
    
    // Update dots
    dots.forEach((dot, i) => {
      dot.classList.toggle('active', i === index);
    });
    
    // Update counter
    if (counter) {
      counter.textContent = index + 1;
    }
  }
  
  /* ===============================
     EXPORT FUNCTIONALITY
  =============================== */
  
  /**
   * Show export menu
   */
  showExportMenu() {
    if (!this.currentData || !this.currentData.properties || this.currentData.properties.length === 0) {
      this.manager.showNotification('No data to export', 'warning');
      return;
    }
    
    // Create export menu
    const menu = document.createElement('div');
    menu.className = 'export-menu';
    menu.innerHTML = `
      <div class="export-menu-content">
        <h4>Export Comparison</h4>
        <button class="export-option-btn" data-format="pdf">
          <span class="export-icon">📄</span>
          <div class="export-option-text">
            <strong>Export as PDF</strong>
            <small>Formatted document for printing</small>
          </div>
        </button>
        <button class="export-option-btn" data-format="csv">
          <span class="export-icon">📊</span>
          <div class="export-option-text">
            <strong>Export as CSV</strong>
            <small>Spreadsheet for analysis</small>
          </div>
        </button>
        <button class="export-close-btn">Cancel</button>
      </div>
    `;
    
    document.body.appendChild(menu);
    
    // Add event listeners
    menu.querySelectorAll('.export-option-btn').forEach(btn => {
      btn.onclick = () => {
        const format = btn.dataset.format;
        menu.remove();
        
        if (format === 'pdf') {
          this.exportToPDF();
        } else if (format === 'csv') {
          this.exportToCSV();
        }
      };
    });
    
    menu.querySelector('.export-close-btn').onclick = () => {
      menu.remove();
    };
    
    // Click outside to close
    menu.onclick = (e) => {
      if (e.target === menu) {
        menu.remove();
      }
    };
  }
  
  /**
   * Export to PDF
   */
  exportToPDF() {
    try {
      const { jsPDF } = window.jspdf;
      if (!jsPDF) {
        this.manager.showNotification('PDF library not loaded', 'error');
        return;
      }
      
      const { properties, locationInsights } = this.currentData;
      const doc = new jsPDF('landscape', 'mm', 'a4');
      
      // Get location insights for each property
      const insights = properties.map(prop => 
        prop.areaname ? locationInsights.get(prop.areaname.toLowerCase()) : null
      );
      
      let y = 15;
      const pageWidth = doc.internal.pageSize.getWidth();
      const pageHeight = doc.internal.pageSize.getHeight();
      const margin = 15;
      const contentWidth = pageWidth - (margin * 2);
      
      // Title
      doc.setFont("helvetica", "bold");
      doc.setFontSize(18);
      doc.setTextColor(51, 80, 192); // Primary blue
      doc.text("Property Comparison Report", margin, y);
      y += 8;
      
      // Subtitle
      doc.setFontSize(10);
      doc.setTextColor(100);
      doc.text(`Generated on: ${new Date().toLocaleDateString()} | ${properties.length} properties compared`, margin, y);
      y += 10;
      
      // Separator line
      doc.setDrawColor(229, 231, 235);
      doc.line(margin, y, pageWidth - margin, y);
      y += 8;
      
      // Property names header
      doc.setFont("helvetica", "bold");
      doc.setFontSize(11);
      doc.setTextColor(0);
      
      const colWidth = contentWidth / properties.length;
      properties.forEach((prop, i) => {
        const x = margin + (i * colWidth);
        const text = doc.splitTextToSize(prop.projectname || 'Unnamed', colWidth - 5);
        doc.text(text, x + 2, y);
      });
      y += 12;
      
      // Helper function to add a section
      const addSection = (title, rows) => {
        // Check if we need a new page
        if (y > pageHeight - 40) {
          doc.addPage();
          y = 15;
        }
        
        // Section header
        doc.setFillColor(232, 237, 255); // Pale blue
        doc.rect(margin, y - 5, contentWidth, 8, 'F');
        doc.setFont("helvetica", "bold");
        doc.setFontSize(10);
        doc.setTextColor(51, 80, 192);
        doc.text(title, margin + 2, y);
        y += 10;
        
        // Rows
        doc.setFont("helvetica", "normal");
        doc.setFontSize(9);
        doc.setTextColor(0);
        
        rows.forEach(row => {
          if (y > pageHeight - 20) {
            doc.addPage();
            y = 15;
          }
          
          // Label
          doc.setFont("helvetica", "bold");
          doc.text(row.label + ':', margin + 2, y);
          
          // Values
          doc.setFont("helvetica", "normal");
          row.values.forEach((value, i) => {
            const x = margin + (i * colWidth);
            const text = doc.splitTextToSize(String(value), colWidth - 5);
            doc.text(text, x + 2, y);
          });
          
          y += 6;
        });
        
        y += 3;
      };
      
      // Pricing section
      addSection('💰 Pricing', [
        { label: 'Price/sqft', values: properties.map(p => {
          const price = p.price_per_sft || p.full_details?.price_per_sft;
          return price ? `₹${Math.round(price).toLocaleString()}` : 'N/A';
        })},
        { label: 'Base Price', values: properties.map(p => {
          const price = p.baseprojectprice || p.full_details?.baseprojectprice;
          return price ? `₹${(price / 10000000).toFixed(2)} Cr` : 'N/A';
        })}
      ]);
      
      // Project Information section
      addSection('🏗️ Project Information', [
        { label: 'Project Name', values: properties.map(p => {
          const name = p.projectname || p.full_details?.projectname;
          return name || 'N/A';
        })},
        { label: 'Builder Name', values: properties.map(p => {
          const builder = p.buildername || p.full_details?.buildername;
          return builder || 'N/A';
        })},
        { label: 'RERA Number', values: properties.map(p => {
          const rera = p.rera_number || p.full_details?.rera_number;
          return rera || 'N/A';
        })},
        { label: 'Project Type', values: properties.map(p => {
          const type = p.project_type || p.full_details?.project_type;
          return type || 'N/A';
        })},
        { label: 'Community Type', values: properties.map(p => {
          const community = p.communitytype || p.full_details?.communitytype;
          return community || 'N/A';
        })},
        { label: 'Construction Status', values: properties.map(p => {
          const status = p.construction_status || p.full_details?.construction_status;
          return status || 'N/A';
        })},
        { label: 'Launch Date', values: properties.map(p => {
          const date = p.project_launch_date || p.full_details?.project_launch_date;
          return date || 'N/A';
        })},
        { label: 'Possession Date', values: properties.map(p => {
          const date = p.possession_date || p.full_details?.possession_date;
          return date || 'N/A';
        })},
        { label: 'Total Land Area', values: properties.map(p => {
          const area = p.total_land_area || p.full_details?.total_land_area;
          return (area && area > 0) ? `${area} sqft` : 'N/A';
        })}
      ]);
      
      // Unit Specifications section
      addSection('📐 Unit Specifications', [
        { label: 'Area (sqft)', values: properties.map(p => {
          const sqft = p.sqfeet || p.full_details?.sqfeet;
          return sqft ? parseFloat(sqft).toLocaleString() : 'N/A';
        })},
        { label: 'Power Backup', values: properties.map(p => {
          const power = p.powerbackup || p.full_details?.powerbackup;
          return power || 'N/A';
        })},
        { label: 'Visitor Parking', values: properties.map(p => {
          const parking = p.visitor_parking || p.full_details?.visitor_parking;
          return parking || 'N/A';
        })}
      ]);
      
      // Location & Ratings section
      addSection('📍 Location & Ratings', [
        { label: 'Area Name', values: properties.map(p => {
          const area = p.areaname || p.full_details?.areaname;
          return area || 'N/A';
        })},
        { label: 'Google Rating', values: properties.map(p => {
          const rating = p.google_place_rating || p.full_details?.google_place_rating;
          return rating ? `${rating} ⭐` : 'N/A';
        })},
        { label: 'Grid Score', values: insights.map((ins, i) => {
          if (!ins) return 'N/A';
          const avgScore = ((ins.connectivity_score || 0) + (ins.amenities_score || 0) + 
                           ((ins.growth_score || 0) * 10) + ((ins.investment_score || 0) * 10)) / 4;
          return avgScore > 0 ? avgScore.toFixed(1) : 'N/A';
        })}
      ]);
      
      // Amenities section
      addSection('🏊 Amenities', [
        { label: 'Nearby Amenities', values: properties.map(p => {
          const amenities = p.external_amenities || p.full_details?.external_amenities;
          if (amenities && amenities.trim()) {
            const amenitiesList = amenities.split(',').map(a => a.trim()).filter(Boolean);
            return amenitiesList.length > 0 ? amenitiesList.slice(0, 3).join(', ') : 'N/A';
          }
          return 'N/A';
        })}
      ]);
      
      // Footer
      doc.setFontSize(8);
      doc.setTextColor(150);
      doc.text('Generated by Relai Analytics - Real Estate Intelligence Platform', margin, pageHeight - 10);
      
      // Save
      const filename = `property-comparison-${new Date().toISOString().split('T')[0]}.pdf`;
      doc.save(filename);
      
      this.manager.showNotification('PDF exported successfully!', 'success');
      this.manager.trackEvent('comparison_exported', { format: 'pdf', propertyCount: properties.length });
      
    } catch (error) {
      console.error('❌ PDF export failed:', error);
      this.manager.showNotification('Failed to export PDF', 'error');
    }
  }
  
  /**
   * Export to CSV
   */
  exportToCSV() {
    try {
      const { properties, locationInsights } = this.currentData;
      
      // Get location insights for each property
      const insights = properties.map(prop => 
        prop.areaname ? locationInsights.get(prop.areaname.toLowerCase()) : null
      );
      
      // Build CSV content
      let csv = '';
      
      // Header row - property names
      csv += 'Attribute,' + properties.map(p => {
        const name = p.projectname || p.full_details?.projectname || 'Unnamed';
        return `"${name.replace(/"/g, '""')}"`;
      }).join(',') + '\n';
      csv += 'Builder,' + properties.map(p => {
        const builder = p.buildername || p.full_details?.buildername || 'Unknown';
        return `"${builder.replace(/"/g, '""')}"`;
      }).join(',') + '\n';
      csv += '\n';
      
      // Pricing section
      csv += '"💰 PRICING"\n';
      csv += 'Price/sqft,' + properties.map(p => {
        const price = p.price_per_sft || p.full_details?.price_per_sft;
        return price ? Math.round(price) : 'N/A';
      }).join(',') + '\n';
      csv += 'Base Price (Cr),' + properties.map(p => {
        const price = p.baseprojectprice || p.full_details?.baseprojectprice;
        return price ? (price / 10000000).toFixed(2) : 'N/A';
      }).join(',') + '\n';
      csv += '\n';
      
      // Project Information section
      csv += '"🏗️ PROJECT INFORMATION"\n';
      csv += 'Project Name,' + properties.map(p => {
        const name = p.projectname || p.full_details?.projectname || 'N/A';
        return `"${name.replace(/"/g, '""')}"`;
      }).join(',') + '\n';
      csv += 'Builder Name,' + properties.map(p => {
        const builder = p.buildername || p.full_details?.buildername || 'N/A';
        return `"${builder.replace(/"/g, '""')}"`;
      }).join(',') + '\n';
      csv += 'RERA Number,' + properties.map(p => {
        const rera = p.rera_number || p.full_details?.rera_number || 'N/A';
        return `"${rera.replace(/"/g, '""')}"`;
      }).join(',') + '\n';
      csv += 'Project Type,' + properties.map(p => {
        const type = p.project_type || p.full_details?.project_type || 'N/A';
        return `"${type.replace(/"/g, '""')}"`;
      }).join(',') + '\n';
      csv += 'Community Type,' + properties.map(p => {
        const community = p.communitytype || p.full_details?.communitytype || 'N/A';
        return `"${community.replace(/"/g, '""')}"`;
      }).join(',') + '\n';
      csv += 'Construction Status,' + properties.map(p => {
        const status = p.construction_status || p.full_details?.construction_status || 'N/A';
        return `"${status.replace(/"/g, '""')}"`;
      }).join(',') + '\n';
      csv += 'Launch Date,' + properties.map(p => {
        const date = p.project_launch_date || p.full_details?.project_launch_date || 'N/A';
        return date;
      }).join(',') + '\n';
      csv += 'Possession Date,' + properties.map(p => {
        const date = p.possession_date || p.full_details?.possession_date || 'N/A';
        return date;
      }).join(',') + '\n';
      csv += 'Total Land Area (sqft),' + properties.map(p => {
        const area = p.total_land_area || p.full_details?.total_land_area;
        return (area && area > 0) ? area : 'N/A';
      }).join(',') + '\n';
      csv += '\n';
      
      // Unit Specifications section
      csv += '"� UNIT SPECIFICATIONS"\n';
      csv += 'Area (sqft),' + properties.map(p => {
        const sqft = p.sqfeet || p.full_details?.sqfeet;
        return sqft || 'N/A';
      }).join(',') + '\n';
      csv += 'Power Backup,' + properties.map(p => {
        const power = p.powerbackup || p.full_details?.powerbackup || 'N/A';
        return `"${power.replace(/"/g, '""')}"`;
      }).join(',') + '\n';
      csv += 'Visitor Parking,' + properties.map(p => {
        const parking = p.visitor_parking || p.full_details?.visitor_parking || 'N/A';
        return parking;
      }).join(',') + '\n';
      csv += '\n';
      
      // Location & Ratings section
      csv += '"📍 LOCATION & RATINGS"\n';
      csv += 'Area Name,' + properties.map(p => {
        const area = p.areaname || p.full_details?.areaname || 'N/A';
        return `"${area.replace(/"/g, '""')}"`;
      }).join(',') + '\n';
      csv += 'Google Rating,' + properties.map(p => {
        const rating = p.google_place_rating || p.full_details?.google_place_rating;
        return rating || 'N/A';
      }).join(',') + '\n';
      
      // Location & Ratings section
      csv += '"📍 LOCATION & RATINGS"\n';
      csv += 'Area Name,' + properties.map(p => {
        const area = p.areaname || p.full_details?.areaname || 'N/A';
        return `"${area.replace(/"/g, '""')}"`;
      }).join(',') + '\n';
      csv += 'Google Rating,' + properties.map(p => {
        const rating = p.google_place_rating || p.full_details?.google_place_rating;
        return rating || 'N/A';
      }).join(',') + '\n';
      csv += 'Grid Score,' + insights.map((ins, i) => {
        if (!ins) return 'N/A';
        const avgScore = ((ins.connectivity_score || 0) + (ins.amenities_score || 0) + 
                         ((ins.growth_score || 0) * 10) + ((ins.investment_score || 0) * 10)) / 4;
        return avgScore > 0 ? avgScore.toFixed(1) : 'N/A';
      }).join(',') + '\n';
      csv += '\n';
      
      // Amenities section
      csv += '"🏊 AMENITIES"\n';
      csv += 'Nearby Amenities,' + properties.map(p => {
        const amenities = p.external_amenities || p.full_details?.external_amenities;
        if (amenities && amenities.trim()) {
          const amenitiesList = amenities.split(',').map(a => a.trim()).filter(Boolean);
          const amenitiesStr = amenitiesList.length > 0 ? amenitiesList.slice(0, 5).join('; ') : 'N/A';
          return `"${amenitiesStr.replace(/"/g, '""')}"`;
        }
        return 'N/A';
      }).join(',') + '\n';
      
      // Create blob and download
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      
      link.setAttribute('href', url);
      link.setAttribute('download', `property-comparison-${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      this.manager.showNotification('CSV exported successfully!', 'success');
      this.manager.trackEvent('comparison_exported', { format: 'csv', propertyCount: properties.length });
      
    } catch (error) {
      console.error('❌ CSV export failed:', error);
      this.manager.showNotification('Failed to export CSV', 'error');
    }
  }
}

// Initialize ComparisonUI when ComparisonManager is ready
window.addEventListener('DOMContentLoaded', () => {
  if (window.comparisonManager) {
    window.comparisonUI = new ComparisonUI(window.comparisonManager);
    
    // Update floating button click handler
    const floatingBtn = document.getElementById('floating-compare-btn');
    if (floatingBtn) {
      floatingBtn.onclick = () => {
        window.comparisonUI.open();
      };
    }
  }
});

console.log('✅ ComparisonUI module loaded');
