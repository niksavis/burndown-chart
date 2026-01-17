/**
 * Auto-reconnect handler for Dash websocket disconnections during updates
 *
 * Detects when Dash websocket closes (e.g., during app updates), shows
 * reconnecting overlay, polls server every 2s, and auto-reloads page when
 * server comes back online.
 */

(function () {
  "use strict";

  // Configuration
  const POLL_INTERVAL_MS = 2000; // 2 seconds
  const INITIAL_RETRY_DELAY_MS = 1000; // 1 second before first retry
  const MAX_POLL_ATTEMPTS = 150; // Max 5 minutes (150 * 2s)

  // State
  let isReconnecting = false;
  let pollAttempts = 0;
  let pollIntervalId = null;
  let overlayElement = null;

  /**
   * Create and show reconnecting overlay
   */
  function showReconnectingOverlay() {
    if (overlayElement) return; // Already showing

    overlayElement = document.createElement("div");
    overlayElement.id = "reconnect-overlay";
    overlayElement.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.8);
      z-index: 10000;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      color: white;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    `;

    overlayElement.innerHTML = `
      <div style="text-align: center; padding: 2rem;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">
          <i class="fas fa-sync fa-spin"></i>
        </div>
        <h2 style="margin: 0 0 1rem 0; font-size: 1.5rem; font-weight: 500;">
          Reconnecting...
        </h2>
        <p style="margin: 0; opacity: 0.8; font-size: 1rem;\">\n          The application is restarting.\n        </p>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.6; font-size: 0.9rem;">
          This page will reconnect automatically in a few moments.
        </p>
        <div id="reconnect-status" style="margin-top: 2rem; font-size: 0.85rem; opacity: 0.7;">
          Checking server status...
        </div>
      </div>
    `;

    document.body.appendChild(overlayElement);
    console.log("[update_reconnect] Reconnecting overlay shown");
  }

  /**
   * Update status message in overlay
   */
  function updateOverlayStatus(message) {
    const statusElement = document.getElementById("reconnect-status");
    if (statusElement) {
      statusElement.textContent = message;
    }
  }

  /**
   * Hide reconnecting overlay
   */
  function hideReconnectingOverlay() {
    if (overlayElement) {
      overlayElement.remove();
      overlayElement = null;
      console.log("[update_reconnect] Reconnecting overlay hidden");
    }
  }

  /**
   * Poll server to check if it's back online
   */
  function pollServer() {
    pollAttempts++;
    console.log(
      `[update_reconnect] Polling server (attempt ${pollAttempts}/${MAX_POLL_ATTEMPTS})`
    );

    updateOverlayStatus(
      `Checking server status... (${pollAttempts}/${MAX_POLL_ATTEMPTS})`
    );

    // Try to fetch the root page
    fetch("/", {
      method: "HEAD",
      cache: "no-cache",
      headers: {
        "Cache-Control": "no-cache",
        Pragma: "no-cache",
      },
    })
      .then((response) => {
        if (response.ok) {
          console.log(
            "[update_reconnect] Server is back online - reloading page"
          );
          clearInterval(pollIntervalId);
          pollIntervalId = null;

          updateOverlayStatus("Server is back! Reloading...");

          // Small delay before reload to show message
          setTimeout(() => {
            window.location.reload();
          }, 500);
        } else {
          console.log(
            `[update_reconnect] Server responded with status ${response.status}`
          );
        }
      })
      .catch((error) => {
        console.log(
          "[update_reconnect] Server not available yet:",
          error.message
        );

        // Check if max attempts reached
        if (pollAttempts >= MAX_POLL_ATTEMPTS) {
          console.error(
            "[update_reconnect] Max poll attempts reached - giving up"
          );
          clearInterval(pollIntervalId);
          pollIntervalId = null;

          updateOverlayStatus(
            "Could not reconnect to server. Please refresh the page manually or restart the application."
          );
        }
      });
  }

  /**
   * Start reconnection process
   */
  function startReconnecting() {
    if (isReconnecting) return; // Already reconnecting

    console.log("[update_reconnect] Starting reconnection process");
    isReconnecting = true;
    pollAttempts = 0;

    showReconnectingOverlay();

    // Start polling after initial delay
    setTimeout(() => {
      // First immediate poll
      pollServer();

      // Then poll every POLL_INTERVAL_MS
      pollIntervalId = setInterval(pollServer, POLL_INTERVAL_MS);
    }, INITIAL_RETRY_DELAY_MS);
  }

  /**
   * Handle websocket close event
   */
  function handleWebSocketClose() {
    console.log("[update_reconnect] Dash websocket closed");
    startReconnecting();
  }

  /**
   * Handle fetch errors (connection failures during Dash requests)
   */
  function handleFetchError(error) {
    // Only handle connection errors during reconnect phase
    if (isReconnecting) {
      console.log("[update_reconnect] Fetch error during reconnect:", error);
      return;
    }

    // Check if it's a network error indicating server is down
    if (error instanceof TypeError && error.message.includes("fetch")) {
      console.log("[update_reconnect] Network fetch error detected");
      startReconnecting();
    }
  }

  /**
   * Monitor Dash websocket connection
   */
  function monitorDashWebSocket() {
    // Dash uses Socket.IO for real-time communication
    // We need to hook into the global error handlers

    // Monitor for websocket disconnections
    if (typeof io !== "undefined") {
      console.log(
        "[update_reconnect] Socket.IO detected, monitoring connection"
      );

      // Get Dash socket instance (may not be immediately available)
      const checkSocket = setInterval(() => {
        const socket = io.sockets?.[0];
        if (socket) {
          clearInterval(checkSocket);

          socket.on("disconnect", (reason) => {
            console.log(`[update_reconnect] Socket.IO disconnected: ${reason}`);

            // Only trigger reconnect for unexpected disconnections
            // (not user-initiated or normal navigation)
            if (reason === "transport close" || reason === "transport error") {
              handleWebSocketClose();
            }
          });

          console.log(
            "[update_reconnect] Socket.IO disconnect handler registered"
          );
        }
      }, 100);

      // Clear check after 10 seconds to avoid infinite polling
      setTimeout(() => clearInterval(checkSocket), 10000);
    }

    // Fallback: Monitor fetch failures as backup detection method
    const originalFetch = window.fetch;
    window.fetch = function (...args) {
      return originalFetch.apply(this, args).catch((error) => {
        handleFetchError(error);
        throw error; // Re-throw to maintain normal error handling
      });
    };

    console.log("[update_reconnect] Fetch error monitoring enabled");
  }

  /**
   * Initialize reconnection monitoring
   */
  function init() {
    // Wait for DOM to be ready
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", init);
      return;
    }

    console.log("[update_reconnect] Initializing auto-reconnect handler");

    // Start monitoring after a short delay to ensure Dash has initialized
    setTimeout(monitorDashWebSocket, 1000);
  }

  // Start initialization
  init();
})();
