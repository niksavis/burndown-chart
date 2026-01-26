/**
 * Direct click handler for Update button to trigger overlay immediately
 *
 * Attaches native click event listener to bypass Dash's callback queue,
 * ensuring overlay appears synchronously before Python callback executes.
 */

(function () {
  "use strict";

  console.log("[update_button_handler] Initializing direct click handler");

  /**
   * Attach click handler to Update button when it appears in DOM
   */
  function attachUpdateButtonHandler() {
    // Use MutationObserver to watch for button appearing in DOM
    const observer = new MutationObserver(() => {
      const updateButton = document.getElementById("install-update-button");

      if (updateButton && !updateButton.dataset.handlerAttached) {
        console.log(
          "[update_button_handler] Found Update button - attaching handler",
        );

        // Mark as handled to avoid duplicate listeners
        updateButton.dataset.handlerAttached = "true";

        // Add CAPTURE phase listener to fire before Dash's bubbling listeners
        updateButton.addEventListener(
          "click",
          function (event) {
            console.log(
              "[update_button_handler] CLICK CAPTURED - triggering overlay",
            );

            // Dispatch overlay trigger event IMMEDIATELY
            const overlayEvent = new CustomEvent("trigger-update-overlay");
            window.dispatchEvent(overlayEvent);

            console.log(
              "[update_button_handler] Overlay event dispatched, Dash callback will follow",
            );

            // Don't prevent default - let Dash callback proceed
          },
          true, // Use capture phase for earliest execution
        );

        console.log(
          "[update_button_handler] Click handler attached in capture phase",
        );
      }
    });

    // Start observing
    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    console.log("[update_button_handler] MutationObserver started");
  }

  // Initialize when DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", attachUpdateButtonHandler);
  } else {
    attachUpdateButtonHandler();
  }
})();
