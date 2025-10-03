/*
 * Viewport Detection for Mobile Chart Optimization
 * 
 * This script detects the viewport size and updates the viewport-size store
 * to enable mobile-optimized chart rendering.
 */

// Viewport size detection function
function detectViewportSize() {
    const width = window.innerWidth;
    
    if (width < 768) {
        return "mobile";
    } else if (width < 1024) {
        return "tablet";
    } else {
        return "desktop";
    }
}

// Update viewport size on load and resize
function updateViewportSize() {
    const viewportSize = detectViewportSize();
    
    // Update the Dash store with viewport size
    try {
        if (window.dash_clientside && window.dash_clientside.set_props) {
            const viewportElement = document.getElementById("viewport-size");
            if (viewportElement) {
                window.dash_clientside.set_props("viewport-size", {"data": viewportSize});
            }
        }
    } catch (error) {
        console.warn("Could not update viewport size:", error);
    }
}

// Initialize viewport detection when DOM is ready
document.addEventListener("DOMContentLoaded", function() {
    updateViewportSize();
    
    // Update viewport size on window resize (debounced)
    let resizeTimeout;
    window.addEventListener("resize", function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(updateViewportSize, 150);
    });
});

// Client-side callback for viewport detection
if (window.dash_clientside) {
    window.dash_clientside.viewport_detection = {
        detect_viewport: function() {
            return detectViewportSize();
        }
    };
}
