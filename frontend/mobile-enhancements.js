/* ============================================================
   MOBILE ENHANCEMENTS
   JavaScript utilities for better mobile experience
   ============================================================ */

(function() {
  'use strict';

  // Detect if device is mobile
  const isMobile = () => {
    return window.innerWidth <= 768 || 
           /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  };

  // Initialize mobile-specific behaviors
  function initMobile() {
    if (!isMobile()) return;

    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.querySelector('.sidebar-toggle-btn');
    const map = document.getElementById('map');

    // Start with sidebar collapsed on mobile
    if (sidebar && !sidebar.classList.contains('collapsed')) {
      sidebar.classList.add('collapsed', 'mobile-init');
    }

    // Close sidebar when clicking on map (mobile only)
    if (map && sidebar) {
      map.addEventListener('click', function(e) {
        if (window.innerWidth <= 768 && !sidebar.classList.contains('collapsed')) {
          // Only close if not clicking on a marker or popup
          if (!e.target.closest('.maplibregl-popup') && 
              !e.target.closest('.maplibregl-marker')) {
            sidebar.classList.add('collapsed');
          }
        }
      });
    }

    // Close sidebar when selecting a location (mobile only)
    const searchResults = document.getElementById('search-results');
    if (searchResults) {
      searchResults.addEventListener('click', function(e) {
        if (e.target.classList.contains('search-result-item') && window.innerWidth <= 480) {
          setTimeout(() => {
            if (sidebar) sidebar.classList.add('collapsed');
          }, 300); // Small delay to see the selection
        }
      });
    }

    // Prevent body scroll when modals are open
    const modals = [
      document.getElementById('fi-modal-overlay'),
      document.getElementById('commute-modal-overlay'),
      document.getElementById('properties-panel'),
      document.getElementById('property-detail-drawer'),
      document.getElementById('amenities-list-card')
    ];

    modals.forEach(modal => {
      if (!modal) return;

      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.attributeName === 'style' || mutation.attributeName === 'class') {
            const isVisible = modal.style.display !== 'none' && 
                            !modal.style.display.includes('none') &&
                            (modal.classList.contains('open') || 
                             modal.style.display === 'flex' ||
                             modal.style.display === 'block');
            
            if (isVisible && window.innerWidth <= 768) {
              document.body.style.overflow = 'hidden';
            } else if (!isAnyModalOpen()) {
              document.body.style.overflow = '';
            }
          }
        });
      });

      observer.observe(modal, { 
        attributes: true, 
        attributeFilter: ['style', 'class'] 
      });
    });

    function isAnyModalOpen() {
      return modals.some(modal => {
        if (!modal) return false;
        return modal.style.display !== 'none' && 
               !modal.style.display.includes('none') &&
               (modal.classList.contains('open') || 
                modal.style.display === 'flex' ||
                modal.style.display === 'block');
      });
    }

    // Add swipe gesture to close sidebar (mobile only)
    if (sidebar && window.innerWidth <= 768) {
      let touchStartX = 0;
      let touchEndX = 0;

      sidebar.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
      }, { passive: true });

      sidebar.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
      }, { passive: true });

      function handleSwipe() {
        const swipeDistance = touchEndX - touchStartX;
        // Swipe left to close (at least 100px)
        if (swipeDistance < -100 && !sidebar.classList.contains('collapsed')) {
          sidebar.classList.add('collapsed');
        }
      }
    }

    // Improve touch scrolling for panels
    const scrollableElements = [
      document.getElementById('intel-card'),
      document.getElementById('prop-panel-body'),
      document.querySelector('.detail-content'),
      document.getElementById('amenities-list-content')
    ];

    scrollableElements.forEach(el => {
      if (el) {
        el.style.webkitOverflowScrolling = 'touch';
      }
    });

    // Add pull-to-refresh indicator (visual feedback only)
    if (sidebar) {
      let pullStartY = 0;
      let isPulling = false;

      sidebar.addEventListener('touchstart', (e) => {
        if (sidebar.scrollTop === 0) {
          pullStartY = e.touches[0].clientY;
          isPulling = true;
        }
      }, { passive: true });

      sidebar.addEventListener('touchmove', (e) => {
        if (!isPulling) return;
        
        const pullDistance = e.touches[0].clientY - pullStartY;
        if (pullDistance > 0 && sidebar.scrollTop === 0) {
          // Add visual feedback for pull-to-refresh
          sidebar.style.transform = `translateY(${Math.min(pullDistance * 0.3, 50)}px)`;
        }
      }, { passive: true });

      sidebar.addEventListener('touchend', () => {
        isPulling = false;
        sidebar.style.transform = '';
      }, { passive: true });
    }

    console.log('✅ Mobile enhancements initialized');
  }

  // Handle orientation changes
  function handleOrientationChange() {
    const sidebar = document.getElementById('sidebar');
    
    // Close sidebar on orientation change if on small screen
    if (window.innerWidth <= 480 && sidebar && !sidebar.classList.contains('collapsed')) {
      sidebar.classList.add('collapsed');
    }

    // Recalculate map size
    if (window.map && window.map.resize) {
      setTimeout(() => window.map.resize(), 100);
    }
  }

  // Optimize map interactions for mobile
  function optimizeMapForMobile() {
    if (!isMobile() || !window.map) return;

    // Disable map rotation on mobile (can be confusing)
    window.map.dragRotate.disable();
    window.map.touchZoomRotate.disableRotation();

    // Adjust zoom controls for touch
    window.map.touchZoomRotate.enable();
    window.map.doubleClickZoom.enable();

    console.log('✅ Map optimized for mobile');
  }

  // Improve layer control interactions on mobile
  function optimizeLayerControls() {
    if (!isMobile()) return;

    const layerControls = document.querySelector('.layer-controls');
    if (!layerControls) return;

    // Add touch feedback
    const layerCards = layerControls.querySelectorAll('.layer-card');
    layerCards.forEach(card => {
      card.addEventListener('touchstart', function() {
        this.style.transform = 'scale(0.95)';
      }, { passive: true });

      card.addEventListener('touchend', function() {
        this.style.transform = '';
      }, { passive: true });
    });

    // Improve horizontal scrolling
    let isScrolling = false;
    let startX;
    let scrollLeft;

    layerControls.addEventListener('touchstart', (e) => {
      isScrolling = true;
      startX = e.touches[0].pageX - layerControls.offsetLeft;
      scrollLeft = layerControls.scrollLeft;
    }, { passive: true });

    layerControls.addEventListener('touchmove', (e) => {
      if (!isScrolling) return;
      const x = e.touches[0].pageX - layerControls.offsetLeft;
      const walk = (x - startX) * 2;
      layerControls.scrollLeft = scrollLeft - walk;
    }, { passive: true });

    layerControls.addEventListener('touchend', () => {
      isScrolling = false;
    }, { passive: true });

    console.log('✅ Layer controls optimized for mobile');
  }

  // Add viewport meta tag if missing (for proper mobile scaling)
  function ensureViewportMeta() {
    let viewport = document.querySelector('meta[name="viewport"]');
    if (!viewport) {
      viewport = document.createElement('meta');
      viewport.name = 'viewport';
      viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes';
      document.head.appendChild(viewport);
      console.log('✅ Viewport meta tag added');
    }
  }

  // Prevent zoom on double-tap for specific elements
  function preventDoubleTapZoom() {
    if (!isMobile()) return;

    const elements = document.querySelectorAll('.city-btn, .amenity-btn, .metric-card, .prop-card');
    elements.forEach(el => {
      let lastTap = 0;
      el.addEventListener('touchend', (e) => {
        const currentTime = new Date().getTime();
        const tapLength = currentTime - lastTap;
        if (tapLength < 300 && tapLength > 0) {
          e.preventDefault();
        }
        lastTap = currentTime;
      });
    });
  }

  // Initialize everything when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  function init() {
    ensureViewportMeta();
    initMobile();
    optimizeLayerControls();
    preventDoubleTapZoom();

    // Wait for map to be ready
    if (window.map) {
      optimizeMapForMobile();
    } else {
      // Wait for map to be initialized
      const checkMap = setInterval(() => {
        if (window.map) {
          optimizeMapForMobile();
          clearInterval(checkMap);
        }
      }, 100);
    }

    // Handle orientation changes
    window.addEventListener('orientationchange', handleOrientationChange);
    window.addEventListener('resize', handleOrientationChange);

    console.log('✅ Mobile enhancements loaded');
  }

  // Expose utility functions globally
  window.mobileUtils = {
    isMobile,
    closeSidebar: () => {
      const sidebar = document.getElementById('sidebar');
      if (sidebar) sidebar.classList.add('collapsed');
    },
    openSidebar: () => {
      const sidebar = document.getElementById('sidebar');
      if (sidebar) sidebar.classList.remove('collapsed');
    }
  };

})();
