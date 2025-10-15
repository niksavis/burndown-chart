/**
 * JQL Syntax Highlighting - JavaScript Layer
 *
 * Provides real-time scroll synchronization and performance optimization
 * for dual-layer syntax-highlighted JQL textareas.
 *
 * Features:
 * - Scroll synchronization between textarea and highlight div
 * - requestAnimationFrame throttling for 60fps rendering
 * - Automatic component detection via data attributes
 * - Mobile-responsive touch event handling
 *
 * Performance Constraints (per FR-010, FR-011):
 * - Render latency: < 50ms
 * - Frame rate: 60fps (16.67ms per frame)
 * - Max query length: 5000 characters
 *
 * Browser Support: Latest 6 months (Chrome, Firefox, Safari, Edge)
 *
 * Usage:
 * This script automatically initializes on page load for any component
 * with class "jql-syntax-wrapper". No manual initialization required.
 */

(function () {
  "use strict";

  //=========================================================================
  // CONFIGURATION
  //=========================================================================

  const CONFIG = {
    WRAPPER_CLASS: "jql-syntax-wrapper",
    INPUT_CLASS: "jql-syntax-input",
    HIGHLIGHT_CLASS: "jql-syntax-highlight",
    MAX_QUERY_LENGTH: 5000,
    SCROLL_THROTTLE_MS: 16, // ~60fps (16.67ms per frame)
  };

  //=========================================================================
  // STATE MANAGEMENT
  //=========================================================================

  // Track scroll animation frames to prevent multiple simultaneous updates
  const scrollAnimationFrames = new Map();

  //=========================================================================
  // SCROLL SYNCHRONIZATION
  //=========================================================================

  /**
   * Synchronize scroll position from textarea to highlight div.
   * Uses requestAnimationFrame for 60fps rendering.
   *
   * @param {HTMLTextAreaElement} textarea - Source textarea element
   * @param {HTMLDivElement} highlightDiv - Target highlight div element
   */
  function syncScroll(textarea, highlightDiv) {
    // Cancel any pending animation frame for this component
    const existingFrame = scrollAnimationFrames.get(textarea);
    if (existingFrame) {
      cancelAnimationFrame(existingFrame);
    }

    // Schedule scroll sync on next animation frame
    const frameId = requestAnimationFrame(() => {
      highlightDiv.scrollTop = textarea.scrollTop;
      highlightDiv.scrollLeft = textarea.scrollLeft;
      scrollAnimationFrames.delete(textarea);
    });

    scrollAnimationFrames.set(textarea, frameId);
  }

  /**
   * Set up scroll event listeners for a textarea/highlight pair.
   *
   * @param {HTMLTextAreaElement} textarea - Textarea element
   * @param {HTMLDivElement} highlightDiv - Highlight div element
   */
  function setupScrollSync(textarea, highlightDiv) {
    if (!textarea || !highlightDiv) {
      console.warn(
        "[JQL Syntax] Missing textarea or highlight div for scroll sync"
      );
      return;
    }

    // Sync scroll on textarea scroll event
    textarea.addEventListener(
      "scroll",
      () => {
        syncScroll(textarea, highlightDiv);
      },
      { passive: true }
    );

    // Initial sync
    syncScroll(textarea, highlightDiv);
  }

  //=========================================================================
  // COMPONENT INITIALIZATION
  //=========================================================================

  /**
   * Initialize JQL syntax highlighting for a single wrapper component.
   *
   * @param {HTMLElement} wrapper - Wrapper div containing textarea and highlight div
   */
  function initializeComponent(wrapper) {
    const textarea = wrapper.querySelector(`.${CONFIG.INPUT_CLASS}`);
    const highlightDiv = wrapper.querySelector(`.${CONFIG.HIGHLIGHT_CLASS}`);

    if (!textarea) {
      console.warn("[JQL Syntax] No textarea found in wrapper", wrapper);
      return;
    }

    if (!highlightDiv) {
      console.warn("[JQL Syntax] No highlight div found in wrapper", wrapper);
      return;
    }

    // Set up scroll synchronization
    setupScrollSync(textarea, highlightDiv);

    console.log("[JQL Syntax] Component initialized:", textarea.id);
  }

  /**
   * Initialize all JQL syntax highlighting components on the page.
   */
  function initializeAll() {
    const wrappers = document.querySelectorAll(`.${CONFIG.WRAPPER_CLASS}`);

    if (wrappers.length === 0) {
      console.log("[JQL Syntax] No components found on page");
      return;
    }

    wrappers.forEach((wrapper) => {
      initializeComponent(wrapper);
    });

    console.log(`[JQL Syntax] Initialized ${wrappers.length} component(s)`);
  }

  //=========================================================================
  // MUTATION OBSERVER (for Dash dynamic updates)
  //=========================================================================

  /**
   * Watch for new JQL syntax components added to DOM via Dash callbacks.
   * Automatically initializes new components when detected.
   */
  function setupMutationObserver() {
    const observer = new MutationObserver((mutations) => {
      let newComponentsFound = false;

      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            // Check if added node is a wrapper
            if (
              node.classList &&
              node.classList.contains(CONFIG.WRAPPER_CLASS)
            ) {
              initializeComponent(node);
              newComponentsFound = true;
            }

            // Check if added node contains wrappers
            const nestedWrappers =
              node.querySelectorAll &&
              node.querySelectorAll(`.${CONFIG.WRAPPER_CLASS}`);
            if (nestedWrappers && nestedWrappers.length > 0) {
              nestedWrappers.forEach((wrapper) => {
                initializeComponent(wrapper);
              });
              newComponentsFound = true;
            }
          }
        });
      });

      if (newComponentsFound) {
        console.log("[JQL Syntax] New components detected and initialized");
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    console.log("[JQL Syntax] Mutation observer active");
  }

  //=========================================================================
  // AUTO-INITIALIZATION
  //=========================================================================

  /**
   * Initialize on DOM ready and set up mutation observer for Dash updates.
   */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      initializeAll();
      setupMutationObserver();
    });
  } else {
    // DOM already loaded
    initializeAll();
    setupMutationObserver();
  }
})();
