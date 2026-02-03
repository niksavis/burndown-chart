/**
 * Long-press force refresh for Update Data button
 * Hold for 3s to trigger force refresh with animated progress
 */

// Ensure dash_clientside exists
window.dash_clientside = window.dash_clientside || {};
// Ensure clientside namespace exists (may have been created by other scripts)
window.dash_clientside.clientside = window.dash_clientside.clientside || {};
// Add our function to the clientside namespace (merges with existing)
window.dash_clientside.clientside.setupLongPress = function () {
  // Retry finding button with exponential backoff (button may be in collapsed panel)
  let attempts = 0;
  const maxAttempts = 10;

  function tryInitialize() {
    const button = document.getElementById("update-data-unified");
    if (!button) {
      attempts++;
      if (attempts < maxAttempts) {
        // Retry with exponential backoff: 100ms, 200ms, 400ms, 800ms, etc.
        setTimeout(tryInitialize, 100 * Math.pow(2, Math.min(attempts - 1, 4)));
      } else {
        console.warn(
          "Update Data button not found after",
          maxAttempts,
          "attempts",
        );
      }
      return;
    }

    // Button found, initialize long press

    let progressInterval = null;
    let textChangeTimer = null;
    let startTime = null;
    let isReadyForForceRefresh = false;
    let processingForceRefresh = false;
    let allowNextClick = false;
    const originalText = "Update Data";
    const forceRefreshText = "Force Refresh";
    const LONG_PRESS_DURATION = 2000; // 2 seconds

    // Get text span inside button
    function getButtonTextElement() {
      // Button structure: <button><i class="fas..."></i><span>Update Data</span></button>
      // OR: <button><i class="fas..."></i> Update Data</button>
      const children = Array.from(button.childNodes);

      // First, try to find a span element
      for (let child of children) {
        if (child.nodeType === Node.ELEMENT_NODE && child.tagName === "SPAN") {
          return child;
        }
      }

      // Fallback: find direct text node
      for (let child of children) {
        if (child.nodeType === Node.TEXT_NODE) {
          return child;
        }
      }

      return null;
    }

    // Start long press
    function startPress(e) {
      // Prevent default to avoid text selection
      e.preventDefault();

      startTime = Date.now();
      isReadyForForceRefresh = false;
      button.classList.add("long-press-active");

      // Initialize progress width to 0%
      button.style.setProperty("--progress-width", "0%");

      // Update progress animation by changing CSS custom property
      progressInterval = setInterval(function () {
        const elapsed = Date.now() - startTime;
        const progress = Math.min((elapsed / LONG_PRESS_DURATION) * 100, 100);
        button.style.setProperty("--progress-width", progress + "%");
      }, 16); // ~60fps

      // After 3s: Change text to indicate ready for force refresh
      textChangeTimer = setTimeout(function () {
        const textElement = getButtonTextElement();
        if (textElement) {
          textElement.textContent = forceRefreshText;
        }
        isReadyForForceRefresh = true;
      }, LONG_PRESS_DURATION);
    }

    // Handle button release
    function handleRelease(e) {
      // If force refresh is ready, trigger it
      if (isReadyForForceRefresh) {
        console.log("🔄 Force refresh activated!");

        // Store flag globally BEFORE allowing the click to propagate
        window._forceRefreshPending = true;
        console.log("✅ Set global _forceRefreshPending flag");

        // Don't prevent the event - let it propagate naturally
        // This ensures clientside callbacks see the flag before server callbacks execute

        // Reset visual state immediately
        cancelPress();

        // Note: Flag is cleared by the clientside callback after it reads it
        return;
      }

      // Reset state for normal clicks
      cancelPress();
    }

    // Cancel/reset long press state
    function cancelPress() {
      if (textChangeTimer) {
        clearTimeout(textChangeTimer);
        textChangeTimer = null;
      }
      if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
      }

      button.classList.remove("long-press-active");
      isReadyForForceRefresh = false;

      // Reset progress width
      button.style.setProperty("--progress-width", "0%");

      // Reset text
      const textElement = getButtonTextElement();
      if (textElement) {
        textElement.textContent = originalText;
      }
    }

    // Event listeners for mouse
    button.addEventListener("mousedown", startPress);
    button.addEventListener("mouseup", handleRelease);
    button.addEventListener("mouseleave", cancelPress);

    // Event listeners for touch (mobile)
    button.addEventListener("touchstart", startPress, { passive: false });
    button.addEventListener("touchend", handleRelease);
    button.addEventListener("touchcancel", cancelPress);

    console.log("Long-press force refresh initialized");
  }

  // Start trying to initialize
  tryInitialize();

  return window.dash_clientside.no_update;
};

// Initialize on page load
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", function () {
    if (window.dash_clientside && window.dash_clientside.clientside) {
      window.dash_clientside.clientside.setupLongPress();
    }
  });
} else {
  // DOM already loaded
  if (window.dash_clientside && window.dash_clientside.clientside) {
    window.dash_clientside.clientside.setupLongPress();
  }
}

// Clientside callback to update the store when button is clicked
// This runs BEFORE the server-side callback
window.dash_clientside = Object.assign({}, window.dash_clientside, {
  forceRefresh: {
    updateStore: function (n_clicks) {
      // Check if force refresh is pending
      if (window._forceRefreshPending) {
        console.log(
          "✅ Clientside callback: Force refresh detected, returning TRUE",
        );
        // Clear flag immediately after reading to prevent interference with next click
        window._forceRefreshPending = false;
        return true;
      }
      console.log("✅ Clientside callback: Normal click, returning FALSE");
      return false;
    },
  },
});
