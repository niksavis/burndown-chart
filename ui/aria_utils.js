/**
 * ARIA Utilities
 * 
 * This module provides utilities for adding ARIA attributes to components
 * to improve accessibility.
 */

/**
 * Enhances icon-only buttons with proper ARIA labels
 * 
 * @param {Object} component - The button component to enhance
 * @param {string} label - The accessible label
 * @param {Object} options - Additional options
 * @returns {Object} The enhanced component
 */
function addAriaLabelToIconButton(component, label, options = {}) {
    // Default options
    const defaultOptions = {
        role: 'button',
        includeTooltip: true,
        tooltipPlacement: 'top'
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    // Check if the component already has props
    if (!component.props) {
        component.props = {};
    }
    
    // Add ARIA attributes to component props
    component.props['aria-label'] = label;
    
    if (mergedOptions.role) {
        component.props.role = mergedOptions.role;
    }
    
    // Add tooltip if requested and if dbc is available
    if (mergedOptions.includeTooltip && typeof window !== 'undefined') {
        try {
            const dbc = window.dash_bootstrap_components;
            
            if (component.props.id && dbc) {
                // Create unique tooltip ID
                const tooltipId = `${component.props.id}-tooltip`;
                
                // Create tooltip
                const tooltip = {
                    type: 'Tooltip',
                    namespace: 'dash_bootstrap_components',
                    props: {
                        target: component.props.id,
                        placement: mergedOptions.tooltipPlacement,
                        children: label
                    }
                };
                
                // Return both the button and tooltip
                return [component, tooltip];
            }
        } catch (e) {
            console.warn('Could not add tooltip to button', e);
        }
    }
    
    return component;
}

/**
 * Enhances a checkbox with proper ARIA attributes
 * 
 * @param {Object} component - The checkbox component to enhance
 * @param {string} label - The accessible label text
 * @returns {Object} The enhanced component
 */
function enhanceCheckbox(component, label) {
    if (!component.props) {
        component.props = {};
    }
    
    component.props['aria-label'] = label;
    component.props.role = 'checkbox';
    
    if (component.props.checked !== undefined) {
        component.props['aria-checked'] = !!component.props.checked;
    }
    
    return component;
}

/**
 * Creates visually hidden text for screen readers
 * 
 * @param {string} text - The text content for screen readers
 * @returns {Object} A component that's visually hidden but accessible to screen readers
 */
function createScreenReaderOnly(text) {
    return {
        type: 'span',
        namespace: 'dash_html_components',
        props: {
            children: text,
            style: {
                position: 'absolute',
                width: '1px',
                height: '1px',
                padding: '0',
                margin: '-1px',
                overflow: 'hidden',
                clip: 'rect(0, 0, 0, 0)',
                whiteSpace: 'nowrap',
                borderWidth: '0'
            }
        }
    };
}

/**
 * Add appropriate ARIA roles to tables
 * 
 * @param {Object} tableComponent - The table component to enhance
 * @param {Object} options - Additional options
 * @returns {Object} The enhanced table component
 */
function enhanceDataTable(tableComponent, options = {}) {
    // Set role="table" on the table element
    tableComponent.props.role = 'table';
    
    // Add caption if provided
    if (options.caption) {
        // Find or create a caption element
        let caption;
        const children = Array.isArray(tableComponent.props.children) 
            ? tableComponent.props.children 
            : [tableComponent.props.children];
            
        const captionIndex = children.findIndex(c => 
            c && c.type && c.type === 'caption');
            
        if (captionIndex >= 0) {
            // Update existing caption
            caption = children[captionIndex];
            caption.props.children = options.caption;
        } else {
            // Create new caption
            caption = {
                type: 'caption',
                namespace: 'dash_html_components',
                props: {
                    children: options.caption
                }
            };
            
            // Add caption to the children
            children.unshift(caption);
            tableComponent.props.children = children;
        }
    }
    
    // Recursively process table children to add appropriate roles
    function processTableChildren(element) {
        if (!element || typeof element !== 'object') return element;
        
        // Add appropriate role based on element type
        if (element.type === 'thead') {
            element.props.role = 'rowgroup';
        } else if (element.type === 'tbody') {
            element.props.role = 'rowgroup';
        } else if (element.type === 'tr') {
            element.props.role = 'row';
        } else if (element.type === 'th') {
            element.props.role = 'columnheader';
        } else if (element.type === 'td') {
            element.props.role = 'cell';
        }
        
        // Process children recursively
        if (element.props && element.props.children) {
            if (Array.isArray(element.props.children)) {
                element.props.children = element.props.children.map(processTableChildren);
            } else {
                element.props.children = processTableChildren(element.props.children);
            }
        }
        
        return element;
    }
    
    // Process children
    if (tableComponent.props.children) {
        if (Array.isArray(tableComponent.props.children)) {
            tableComponent.props.children = tableComponent.props.children.map(processTableChildren);
        } else {
            tableComponent.props.children = processTableChildren(tableComponent.props.children);
        }
    }
    
    return tableComponent;
}

// Export the utilities
export {
    addAriaLabelToIconButton,
    enhanceCheckbox,
    createScreenReaderOnly,
    enhanceDataTable
};
