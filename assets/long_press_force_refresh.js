/**
 * Long-press force refresh for Update Data button
 * Hold for 3s to trigger force refresh with animated progress
 */

window.dash_clientside = Object.assign({}, window.dash_clientside, {
  clientside: {
    setupLongPress: function () {
      // Wait for button to be available in DOM
      setTimeout(function () {
        const button = document.getElementById("update-data-unified");
        if (!button) {
          console.warn("Update Data button not found");
          return;
        }

        let progressInterval = null;
        let textChangeTimer = null;
        let startTime = null;
        let isReadyForForceRefresh = false;
        const originalText = "Update Data";
        const forceRefreshText = "Force Refresh";
        const LONG_PRESS_DURATION = 3000; // 3 seconds

        // Get text span inside button
        function getButtonTextElement() {
          // Button structure: <button><i class="fas..."></i> Update Data</button>
          const children = Array.from(button.childNodes);
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
            const progress = Math.min(
              (elapsed / LONG_PRESS_DURATION) * 100,
              100
            );
            button.style.setProperty("--progress-width", progress + "%");
          }, 16); // ~60fps

          // After 3s: Change text to indicate ready for force refresh
          textChangeTimer = setTimeout(function () {
            const textElement = getButtonTextElement();
            if (textElement) {
              textElement.textContent = " " + forceRefreshText;
            }
            isReadyForForceRefresh = true;
          }, LONG_PRESS_DURATION);
        }

        // Handle button release
        function handleRelease(e) {
          // If force refresh is ready, trigger it
          if (isReadyForForceRefresh) {
            // Set force refresh flag
            const store = document.getElementById("force-refresh-store");
            if (store) {
              // Trigger by changing store value
              const event = new CustomEvent("dash-force-refresh", {
                detail: { forceRefresh: true },
              });
              window.dispatchEvent(event);
            }

            // Click the button to trigger actual update
            // Use setTimeout to allow state reset first
            setTimeout(function () {
              button.click();
            }, 100);
          }

          // Reset state
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
            textElement.textContent = " " + originalText;
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
      }, 500); // Wait for DOM to be ready

      return window.dash_clientside.no_update;
    },
  },
});

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

// Listen for force refresh events
window.addEventListener("dash-force-refresh", function (e) {
  console.log("Force refresh triggered:", e.detail);
  // Store will be updated by callback
  const store = document.getElementById("force-refresh-store");
  if (store && store._dashprivate_layout && store._dashprivate_layout.props) {
    store._dashprivate_layout.props.data = true;
  }
});
