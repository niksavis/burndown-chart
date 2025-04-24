/**
 * Keyboard Navigation Checker
 * 
 * This script helps audit keyboard navigation on a page.
 * Paste it in your browser console to highlight the focus order.
 */

(function() {
    // Configuration
    const config = {
        focusDelay: 500,        // Time between focus shifts (ms)
        highlightColor: 'red',  // Color of the focus indicator
        outlineWidth: '3px',    // Width of the outline
        numberColor: 'white',   // Color of the order number
        maxElements: 50         // Maximum elements to test
    };
    
    // Get all focusable elements
    const focusableElements = Array.from(document.querySelectorAll(
        'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )).filter(el => {
        // Filter out invisible elements
        const style = window.getComputedStyle(el);
        return !(style.display === 'none' || style.visibility === 'hidden' || el.offsetParent === null);
    });
    
    if (focusableElements.length === 0) {
        console.log('No focusable elements found on the page.');
        return;
    }
    
    console.log(`Found ${focusableElements.length} focusable elements.`);
    console.log('Starting focus order test...');
    
    // Create a container for the focus order indicators
    const container = document.createElement('div');
    container.id = 'focus-order-test-container';
    container.style.position = 'fixed';
    container.style.zIndex = '10000';
    container.style.pointerEvents = 'none';
    document.body.appendChild(container);
    
    // Store original outline styles to restore later
    const originalStyles = new Map();
    
    // Function to create a focus indicator
    function createFocusIndicator(element, index) {
        // Save original style
        originalStyles.set(element, {
            outline: element.style.outline,
            outlineOffset: element.style.outlineOffset
        });
        
        // Set focus styles
        element.style.outline = `${config.outlineWidth} solid ${config.highlightColor}`;
        element.style.outlineOffset = '2px';
        
        // Create order number indicator
        const rect = element.getBoundingClientRect();
        const indicator = document.createElement('div');
        indicator.textContent = index + 1;
        indicator.style.position = 'absolute';
        indicator.style.top = `${rect.top}px`;
        indicator.style.left = `${rect.left}px`;
        indicator.style.backgroundColor = config.highlightColor;
        indicator.style.color = config.numberColor;
        indicator.style.padding = '2px 6px';
        indicator.style.borderRadius = '50%';
        indicator.style.fontSize = '14px';
        indicator.style.fontWeight = 'bold';
        indicator.style.zIndex = '10001';
        
        container.appendChild(indicator);
        
        console.log(`${index + 1}: ${getElementDescription(element)}`);
        
        return indicator;
    }
    
    // Helper function to get a descriptive string for an element
    function getElementDescription(element) {
        let desc = element.tagName.toLowerCase();
        
        if (element.id) {
            desc += `#${element.id}`;
        }
        
        if (element.className && typeof element.className === 'string') {
            desc += `.${element.className.split(' ').join('.')}`;
        }
        
        // Add accessible name if available
        const accessibleName = element.getAttribute('aria-label') || 
                               element.getAttribute('alt') || 
                               element.getAttribute('placeholder') || 
                               element.textContent;
                               
        if (accessibleName && accessibleName.trim()) {
            desc += ` "${accessibleName.trim().substring(0, 20)}${accessibleName.length > 20 ? '...' : ''}"`;
        }
        
        return desc;
    }
    
    // Function to clean up
    function cleanup() {
        // Restore original styles
        originalStyles.forEach((style, element) => {
            element.style.outline = style.outline;
            element.style.outlineOffset = style.outlineOffset;
        });
        
        // Remove the container
        if (container.parentNode) {
            container.parentNode.removeChild(container);
        }
        
        console.log('Focus order test completed.');
    }
    
    // Test focus order
    let currentIndex = 0;
    const indicators = [];
    
    function testNextElement() {
        if (currentIndex >= focusableElements.length || currentIndex >= config.maxElements) {
            cleanup();
            return;
        }
        
        const element = focusableElements[currentIndex];
        const indicator = createFocusIndicator(element, currentIndex);
        indicators.push(indicator);
        
        // Focus the element
        try {
            element.focus();
        } catch (e) {
            console.error(`Error focusing element: ${e}`);
        }
        
        // Move to next element
        currentIndex++;
        setTimeout(testNextElement, config.focusDelay);
    }
    
    // Start the test
    testNextElement();
    
    // Add keyboard shortcut to stop the test
    document.addEventListener('keydown', function(e) {
        // Stop on Escape key
        if (e.key === 'Escape') {
            cleanup();
        }
    });
    
    // Return a function to manually stop the test
    return cleanup;
})();
