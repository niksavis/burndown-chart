/**
 * Auto-reconnect handler for Dash websocket disconnections during updates
 *
 * Detects when Dash websocket closes (e.g., during app updates), shows
 * reconnecting overlay, polls server every 2s, and when server comes back:
 * - Removes overlay
 * - Fetches new version from /api/version
 * - Updates footer version display
 * - Shows success toast
 * - No page reload required!
 */

(function () {
  "use strict";

  // Configuration
  const POLL_INTERVAL_MS = 2000; // 2 seconds
  const INITIAL_RETRY_DELAY_MS = 1000; // 1 second before first retry
  const MAX_POLL_ATTEMPTS = 150; // Max 5 minutes (150 * 2s)
  const DISCONNECT_TIMEOUT_MS = 10000; // Max 10s to wait for disconnect during update

  // State
  let isReconnecting = false;
  let pollAttempts = 0;
  let pollIntervalId = null;
  let overlayElement = null;
  let isUpdateFlow = false; // Track if this is an update (vs normal disconnect)
  let waitingForDisconnect = false; // Track if we're waiting for server to die
  let disconnectTimeoutId = null; // Timeout for disconnect detection  let toastBlocker = null; // MutationObserver to block toasts during update reconnect
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
   * Show success toast after update completes
   */
  function showUpdateSuccessToast(version) {
    console.log(
      "[update_reconnect] Showing update success toast for version",
      version,
    );

    // Wait for toast blocker to be removed (if active)
    const showToast = () => {
      // Create toast element directly in the notifications container
      const notificationsContainer =
        document.getElementById("app-notifications");
      if (!notificationsContainer) {
        console.warn("[update_reconnect] Notifications container not found");
        return;
      }

      // CRITICAL: Clear any existing toasts before showing success toast
      // This prevents duplicate/stale toasts from Dash callbacks firing on reconnect
      const existingToasts = notificationsContainer.querySelectorAll(".toast");
      if (existingToasts.length > 0) {
        console.warn(
          `[update_reconnect] Clearing ${existingToasts.length} existing toast(s) before showing success`,
        );
        existingToasts.forEach((toast) => {
          const header = toast.querySelector(".toast-header strong");
          const body = toast.querySelector(".toast-body");
          console.log("[update_reconnect] Removing toast:", {
            header: header ? header.textContent : "unknown",
            body: body ? body.textContent.substring(0, 50) : "unknown",
          });
          toast.remove();
        });
      }

      // Create toast HTML (matching Dash Bootstrap Components style)
      const toastElement = document.createElement("div");
      toastElement.className = "toast fade show";
      toastElement.setAttribute("role", "alert");
      toastElement.innerHTML = `
      <div class="toast-header bg-success text-white">
        <i class="fas fa-check-circle me-2"></i>
        <strong class="me-auto">Update Complete</strong>
        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
      <div class="toast-body">
        Successfully updated to v${version}!
      </div>
    `;

      // Add to container
      notificationsContainer.appendChild(toastElement);

      // Auto-dismiss after 5 seconds
      setTimeout(() => {
        toastElement.classList.remove("show");
        setTimeout(() => {
          toastElement.remove();
        }, 300); // Wait for fade animation
      }, 5000);

      console.log("[update_reconnect] Success toast displayed");
    };

    // If toast blocker is active, wait for it to be removed
    if (toastBlocker) {
      console.log(
        "[update_reconnect] Waiting for toast blocker to be removed before showing success toast",
      );
      const checkBlocker = setInterval(() => {
        if (!toastBlocker) {
          clearInterval(checkBlocker);
          showToast();
        }
      }, 100);
    } else {
      showToast();
    }
  }

  /**
   * Poll server to check if it's back online
   */
  function pollServer() {
    pollAttempts++;
    console.log(
      `[update_reconnect] Polling server (attempt ${pollAttempts}/${MAX_POLL_ATTEMPTS})`,
    );

    updateOverlayStatus(
      `Checking server status... (${pollAttempts}/${MAX_POLL_ATTEMPTS})`,
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
          console.log("[update_reconnect] Server is back online");

          // Server back - proceed with reconnect
          clearInterval(pollIntervalId);
          pollIntervalId = null;

          updateOverlayStatus("Server is back! Finalizing...");

          // If this was an update flow, fetch new version and update UI
          if (isUpdateFlow) {
            console.log(
              "[update_reconnect] Update flow detected - fetching new version",
            );

            // Fetch new version from API
            fetch("/api/version", {
              cache: "no-cache",
              headers: {
                "Cache-Control": "no-cache",
                Pragma: "no-cache",
              },
            })
              .then((versionResponse) => versionResponse.json())
              .then((versionData) => {
                console.log(
                  "[update_reconnect] New version:",
                  versionData.version,
                );

                // CRITICAL: Clear any toasts BEFORE removing overlay
                // This prevents Dash callbacks from showing toasts during reconnect
                const notificationsContainer =
                  document.getElementById("app-notifications");
                if (notificationsContainer) {
                  const existingToasts =
                    notificationsContainer.querySelectorAll(".toast");
                  if (existingToasts.length > 0) {
                    console.log(
                      `[update_reconnect] Pre-clearing ${existingToasts.length} toast(s) before overlay removal`,
                    );
                    existingToasts.forEach((toast) => toast.remove());
                  }

                  // Install toast blocker to prevent Dash from adding toasts during critical window
                  console.log(
                    "[update_reconnect] Installing toast blocker for 2 seconds",
                  );
                  toastBlocker = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                      mutation.addedNodes.forEach((node) => {
                        if (
                          node.nodeType === 1 &&
                          node.classList &&
                          node.classList.contains("toast")
                        ) {
                          console.warn(
                            "[update_reconnect] Blocking unwanted toast during update reconnect",
                            node,
                          );
                          node.remove();
                        }
                      });
                    });
                  });
                  toastBlocker.observe(notificationsContainer, {
                    childList: true,
                  });

                  // Remove blocker after 2 seconds (enough time for Dash callbacks to settle)
                  setTimeout(() => {
                    if (toastBlocker) {
                      toastBlocker.disconnect();
                      toastBlocker = null;
                      console.log("[update_reconnect] Toast blocker removed");
                    }
                  }, 2000);
                }

                // Remove overlay
                hideReconnectingOverlay();

                // Update footer version
                const footerVersionElement = document.getElementById(
                  "footer-version-text",
                );
                if (footerVersionElement) {
                  footerVersionElement.textContent = "v" + versionData.version;
                  console.log(
                    "[update_reconnect] Footer version updated to",
                    versionData.version,
                  );
                } else {
                  console.warn(
                    "[update_reconnect] Footer version element not found",
                  );
                }

                // Show success toast
                showUpdateSuccessToast(versionData.version);

                // Reset update flow flag
                isUpdateFlow = false;
              })
              .catch((error) => {
                console.error(
                  "[update_reconnect] Failed to fetch version:",
                  error,
                );
                // Fallback: just hide overlay and reload
                hideReconnectingOverlay();
                setTimeout(() => {
                  window.location.reload();
                }, 500);
              });
          } else {
            // Normal reconnect (not update) - just hide overlay
            // Dash will automatically reconnect and refresh components
            console.log("[update_reconnect] Normal reconnect - hiding overlay");
            hideReconnectingOverlay();
          }
        } else {
          console.log(
            `[update_reconnect] Server responded with status ${response.status}`,
          );
        }
      })
      .catch((error) => {
        console.log(
          "[update_reconnect] Server not available yet:",
          error.message,
        );

        // Check if max attempts reached
        if (pollAttempts >= MAX_POLL_ATTEMPTS) {
          console.error(
            "[update_reconnect] Max poll attempts reached - giving up",
          );
          clearInterval(pollIntervalId);
          pollIntervalId = null;

          updateOverlayStatus(
            "Could not reconnect to server. Please refresh the page manually or restart the application.",
          );
        }
      });
  }

  /**
   * Start reconnection process
   */
  function startReconnecting(isUpdate = false) {
    if (isReconnecting) return; // Already reconnecting

    console.log(
      "[update_reconnect] Starting reconnection process (isUpdate:",
      isUpdate,
      ")",
    );
    isReconnecting = true;
    isUpdateFlow = isUpdate; // Track if this is an update
    pollAttempts = 0;

    showReconnectingOverlay();

    // For update flows, WAIT for disconnect signal before polling
    // This prevents race condition where server is still alive
    if (isUpdate) {
      waitingForDisconnect = true;
      updateOverlayStatus("Waiting for update to start...");

      console.log(
        "[update_reconnect] Update flow - waiting for disconnect signal before polling",
      );

      // Safety timeout: If disconnect doesn't happen in 10s, start polling anyway
      disconnectTimeoutId = setTimeout(() => {
        if (waitingForDisconnect) {
          console.warn(
            "[update_reconnect] Disconnect timeout - starting polling anyway",
          );
          waitingForDisconnect = false;
          beginPolling();
        }
      }, DISCONNECT_TIMEOUT_MS);

      return; // Don't start polling yet!
    }

    // Normal reconnect (not update) - start polling immediately
    beginPolling();
  }

  /**
   * Begin polling for server availability
   */
  function beginPolling() {
    console.log("[update_reconnect] Beginning server polling");
    updateOverlayStatus("Checking server status...");

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

    // If we were waiting for disconnect (update flow), start polling now!
    if (waitingForDisconnect) {
      console.log(
        "[update_reconnect] Disconnect detected during update - starting polling now",
      );
      waitingForDisconnect = false;

      // Clear safety timeout
      if (disconnectTimeoutId) {
        clearTimeout(disconnectTimeoutId);
        disconnectTimeoutId = null;
      }

      beginPolling();
      return;
    }

    // Normal disconnect (not during update wait) - start reconnect flow
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
        "[update_reconnect] Socket.IO detected, monitoring connection",
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
            "[update_reconnect] Socket.IO disconnect handler registered",
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

    // Check if this is a post-update restart (flag persisted in database)
    fetch("/api/version", {
      cache: "no-cache",
      headers: {
        "Cache-Control": "no-cache",
        Pragma: "no-cache",
      },
    })
      .then((response) => response.json())
      .then((versionData) => {
        console.log("[update_reconnect] Version check:", versionData);

        // If post_update flag is set, this is a post-update restart
        if (versionData.post_update) {
          console.log(
            "[update_reconnect] Post-update restart detected - showing success toast",
          );
          isUpdateFlow = true; // Mark as update flow (prevents reload)

          // Update footer version (defense in depth - server already rendered correct version)
          const footerVersionElement = document.getElementById(
            "footer-version-text",
          );
          if (footerVersionElement) {
            footerVersionElement.textContent = "v" + versionData.version;
            console.log(
              "[update_reconnect] Footer version confirmed:",
              versionData.version,
            );
          }

          // Show success toast immediately (app already restarted, no blocker needed)
          // Wait a bit for Dash to initialize
          setTimeout(() => {
            showUpdateSuccessToast(versionData.version);
          }, 1000);

          // Clear the flag so it doesn't show again
          fetch("/api/clear-post-update", {
            method: "POST",
            cache: "no-cache",
          })
            .then((response) => response.json())
            .then((result) => {
              if (result.success) {
                console.log(
                  "[update_reconnect] Post-update flag cleared successfully",
                );
              } else {
                console.warn(
                  "[update_reconnect] Failed to clear post-update flag:",
                  result.error,
                );
              }
            })
            .catch((error) => {
              console.error(
                "[update_reconnect] Error clearing post-update flag:",
                error,
              );
            });
        }
      })
      .catch((error) => {
        console.warn(
          "[update_reconnect] Failed to check version/post-update status:",
          error,
        );
      });

    // Listen for custom event from update button callback
    window.addEventListener("trigger-update-overlay", function () {
      console.log("[update_reconnect] Received trigger-update-overlay event");
      startReconnecting(true); // true = this is an update flow
    });

    // Start monitoring after a short delay to ensure Dash has initialized
    setTimeout(monitorDashWebSocket, 1000);
  }

  // Start initialization
  init();
})();
