(function () {
  'use strict';

  const POLL_INTERVAL_MS = 2000;
  const INITIAL_RETRY_DELAY_MS = 1000;
  const MAX_POLL_ATTEMPTS = 150;
  const DISCONNECT_TIMEOUT_MS = 10000;

  let isReconnecting = false;
  let pollAttempts = 0;
  let pollIntervalId = null;
  let overlayElement = null;
  let isUpdateFlow = false;
  let waitingForDisconnect = false;
  let disconnectTimeoutId = null;
  let toastBlocker = null;

  function showReconnectingOverlay() {
    if (overlayElement) return;

    overlayElement = document.createElement('div');
    overlayElement.id = 'reconnect-overlay';
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
        <p style="margin: 0; opacity: 0.8; font-size: 1rem;">\n          The application is restarting.\n        </p>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.6; font-size: 0.9rem;">
          This page will reconnect automatically in a few moments.
        </p>
        <div id="reconnect-status" style="margin-top: 2rem; font-size: 0.85rem; opacity: 0.7;">
          Checking server status...
        </div>
      </div>
    `;

    document.body.appendChild(overlayElement);
    console.log('[update_reconnect] Reconnecting overlay shown');
  }

  function updateOverlayStatus(message) {
    const statusElement = document.getElementById('reconnect-status');
    if (statusElement) {
      statusElement.textContent = message;
    }
  }

  function hideReconnectingOverlay() {
    if (overlayElement) {
      overlayElement.remove();
      overlayElement = null;
      console.log('[update_reconnect] Reconnecting overlay hidden');
    }
  }

  function parseJsonResponse(response, contextLabel) {
    return response.text().then((rawText) => {
      const contentType = response.headers.get('content-type') || '';
      const payload = rawText || '';

      if (!response.ok) {
        const snippet = payload.slice(0, 120).replace(/\s+/g, ' ').trim();
        throw new Error(
          `${contextLabel}: HTTP ${response.status} ${response.statusText} (content-type: ${contentType || 'unknown'}, body: ${snippet || '<empty>'})`
        );
      }

      if (!payload.trim()) {
        throw new Error(`${contextLabel}: Empty response body`);
      }

      try {
        return JSON.parse(payload);
      } catch (_parseError) {
        const snippet = payload.slice(0, 120).replace(/\s+/g, ' ').trim();
        throw new Error(
          `${contextLabel}: Invalid JSON response (content-type: ${contentType || 'unknown'}, body: ${snippet || '<empty>'})`
        );
      }
    });
  }

  function showUpdateSuccessToast(version) {
    console.log('[update_reconnect] Showing update success toast for version', version);

    const showToast = () => {
      const notificationsContainer = document.getElementById('app-notifications');
      if (!notificationsContainer) {
        console.warn('[update_reconnect] Notifications container not found');
        return;
      }

      const existingToasts = notificationsContainer.querySelectorAll('.toast');
      if (existingToasts.length > 0) {
        console.warn(
          `[update_reconnect] Clearing ${existingToasts.length} existing toast(s) before showing success`
        );
        existingToasts.forEach((toast) => {
          const header = toast.querySelector('.toast-header strong');
          const body = toast.querySelector('.toast-body');
          console.log('[update_reconnect] Removing toast:', {
            header: header ? header.textContent : 'unknown',
            body: body ? body.textContent.substring(0, 50) : 'unknown',
          });
          toast.remove();
        });
      }

      const toastElement = document.createElement('div');
      toastElement.className = 'fade toast show app-toast';
      toastElement.setAttribute('role', 'alert');
      toastElement.setAttribute('aria-live', 'assertive');
      toastElement.setAttribute('aria-atomic', 'true');
      toastElement.innerHTML = `
      <div class="toast-header">
        <i class="fas fa-check-circle text-success me-2" style="font-size: 1.2rem;"></i>
        <strong class="me-auto">Success</strong>
        <button type="button" class="btn-close" aria-label="Close" data-dismiss="toast"></button>
      </div>
      <div class="toast-body">
        Successfully updated to v${version}!
      </div>
    `;

      notificationsContainer.appendChild(toastElement);

      const autoDismissId = setTimeout(() => {
        if (
          window.update_reconnect_helpers &&
          window.update_reconnect_helpers.remove_toast_element
        ) {
          window.update_reconnect_helpers.remove_toast_element(toastElement);
          return;
        }

        toastElement.classList.remove('show');
        setTimeout(() => {
          toastElement.remove();
        }, 300);
      }, 5000);

      if (window.update_reconnect_helpers && window.update_reconnect_helpers.attach_toast_dismiss) {
        window.update_reconnect_helpers.attach_toast_dismiss(toastElement, autoDismissId);
      }

      console.log('[update_reconnect] Success toast displayed');
    };

    if (toastBlocker) {
      console.log(
        '[update_reconnect] Waiting for toast blocker to be removed before showing success toast'
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

  function pollServer() {
    pollAttempts++;
    console.log(`[update_reconnect] Polling server (attempt ${pollAttempts}/${MAX_POLL_ATTEMPTS})`);

    updateOverlayStatus(`Checking server status... (${pollAttempts}/${MAX_POLL_ATTEMPTS})`);

    fetch('/', {
      method: 'HEAD',
      cache: 'no-cache',
      headers: {
        'Cache-Control': 'no-cache',
        Pragma: 'no-cache',
      },
    })
      .then((response) => {
        if (response.ok) {
          console.log('[update_reconnect] Server is back online');

          clearInterval(pollIntervalId);
          pollIntervalId = null;

          updateOverlayStatus('Server is back! Finalizing...');

          if (isUpdateFlow) {
            console.log('[update_reconnect] Update flow detected - fetching new version');

            fetch('/api/version', {
              cache: 'no-cache',
              headers: {
                'Cache-Control': 'no-cache',
                Pragma: 'no-cache',
              },
            })
              .then((versionResponse) => parseJsonResponse(versionResponse, 'version-check'))
              .then((versionData) => {
                console.log('[update_reconnect] New version:', versionData.version);

                const notificationsContainer = document.getElementById('app-notifications');
                if (notificationsContainer) {
                  const existingToasts = notificationsContainer.querySelectorAll('.toast');
                  if (existingToasts.length > 0) {
                    console.log(
                      `[update_reconnect] Pre-clearing ${existingToasts.length} toast(s) before overlay removal`
                    );
                    existingToasts.forEach((toast) => toast.remove());
                  }

                  console.log('[update_reconnect] Installing toast blocker for 2 seconds');
                  toastBlocker = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                      mutation.addedNodes.forEach((node) => {
                        if (
                          node.nodeType === 1 &&
                          node.classList &&
                          node.classList.contains('toast')
                        ) {
                          console.warn(
                            '[update_reconnect] Blocking unwanted toast during update reconnect',
                            node
                          );
                          node.remove();
                        }
                      });
                    });
                  });
                  toastBlocker.observe(notificationsContainer, {
                    childList: true,
                  });

                  setTimeout(() => {
                    if (toastBlocker) {
                      toastBlocker.disconnect();
                      toastBlocker = null;
                      console.log('[update_reconnect] Toast blocker removed');
                    }
                  }, 2000);
                }

                hideReconnectingOverlay();

                console.log(
                  '[update_reconnect] Update complete - forcing page reload to show success'
                );
                window.location.reload();
              })
              .catch((error) => {
                console.error('[update_reconnect] Failed to fetch version:', error);
                hideReconnectingOverlay();
                setTimeout(() => {
                  window.location.reload();
                }, 500);
              });
          } else {
            console.log('[update_reconnect] Normal reconnect - hiding overlay');
            hideReconnectingOverlay();
          }
        } else {
          console.log(`[update_reconnect] Server responded with status ${response.status}`);
        }
      })
      .catch((error) => {
        console.log('[update_reconnect] Server not available yet:', error.message);

        if (pollAttempts >= MAX_POLL_ATTEMPTS) {
          console.error('[update_reconnect] Max poll attempts reached - giving up');
          clearInterval(pollIntervalId);
          pollIntervalId = null;

          updateOverlayStatus(
            'Could not reconnect to server. Please refresh the page manually or restart the application.'
          );
        }
      });
  }

  function startReconnecting(isUpdate = false) {
    if (isReconnecting) return;

    console.log('[update_reconnect] Starting reconnection process (isUpdate:', isUpdate, ')');
    isReconnecting = true;
    isUpdateFlow = isUpdate;
    pollAttempts = 0;

    showReconnectingOverlay();

    if (isUpdate) {
      waitingForDisconnect = true;
      updateOverlayStatus('Waiting for update to start...');

      console.log('[update_reconnect] Update flow - waiting for disconnect signal before polling');

      disconnectTimeoutId = setTimeout(() => {
        if (waitingForDisconnect) {
          console.warn('[update_reconnect] Disconnect timeout - starting polling anyway');
          waitingForDisconnect = false;
          beginPolling();
        }
      }, DISCONNECT_TIMEOUT_MS);

      return;
    }

    beginPolling();
  }

  function beginPolling() {
    console.log('[update_reconnect] Beginning server polling');
    updateOverlayStatus('Checking server status...');

    setTimeout(() => {
      pollServer();

      pollIntervalId = setInterval(pollServer, POLL_INTERVAL_MS);
    }, INITIAL_RETRY_DELAY_MS);
  }

  function handleWebSocketClose() {
    console.log('[update_reconnect] Dash websocket closed');

    if (waitingForDisconnect) {
      console.log('[update_reconnect] Disconnect detected during update - starting polling now');
      waitingForDisconnect = false;

      if (disconnectTimeoutId) {
        clearTimeout(disconnectTimeoutId);
        disconnectTimeoutId = null;
      }

      beginPolling();
      return;
    }

    startReconnecting();
  }

  function handleFetchError(error) {
    if (isReconnecting) {
      console.log('[update_reconnect] Fetch error during reconnect:', error);
      return;
    }

    if (error instanceof TypeError && error.message.includes('fetch')) {
      console.log('[update_reconnect] Network fetch error detected');
      startReconnecting();
    }
  }

  function monitorDashWebSocket() {
    if (typeof io !== 'undefined') {
      console.log('[update_reconnect] Socket.IO detected, monitoring connection');

      const checkSocket = setInterval(() => {
        const socket = io.sockets?.[0];
        if (socket) {
          clearInterval(checkSocket);

          socket.on('disconnect', (reason) => {
            console.log(`[update_reconnect] Socket.IO disconnected: ${reason}`);

            if (reason === 'transport close' || reason === 'transport error') {
              handleWebSocketClose();
            }
          });

          console.log('[update_reconnect] Socket.IO disconnect handler registered');
        }
      }, 100);

      setTimeout(() => clearInterval(checkSocket), 10000);
    }

    const originalFetch = window.fetch;
    window.fetch = function (...args) {
      return originalFetch.apply(this, args).catch((error) => {
        handleFetchError(error);
        throw error;
      });
    };

    console.log('[update_reconnect] Fetch error monitoring enabled');
  }

  function init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
      return;
    }

    console.log('[update_reconnect] Initializing auto-reconnect handler');

    fetch('/api/version', {
      cache: 'no-cache',
      headers: {
        'Cache-Control': 'no-cache',
        Pragma: 'no-cache',
      },
    })
      .then((response) => parseJsonResponse(response, 'post-update-version-check'))
      .then((versionData) => {
        const version = versionData && versionData.version ? versionData.version : 'unknown';
        const postUpdate = Boolean(versionData && versionData.post_update);
        console.log(
          `[update_reconnect] Version check: version=${version}, post_update=${postUpdate}`
        );

        if (versionData.post_update) {
          console.log('[update_reconnect] Post-update restart detected - showing success toast');
          isUpdateFlow = true;

          const footerVersionElement = document.getElementById('footer-version-text');
          if (footerVersionElement) {
            footerVersionElement.textContent = 'v' + versionData.version;
            console.log('[update_reconnect] Footer version confirmed:', versionData.version);
          }

          setTimeout(() => {
            showUpdateSuccessToast(versionData.version);
          }, 1000);

          fetch('/api/clear-post-update', {
            method: 'POST',
            cache: 'no-cache',
          })
            .then((response) => parseJsonResponse(response, 'clear-post-update'))
            .then((result) => {
              if (result.success) {
                console.log('[update_reconnect] Post-update flag cleared successfully');
              } else {
                console.warn('[update_reconnect] Failed to clear post-update flag:', result.error);
              }
            })
            .catch((error) => {
              console.error('[update_reconnect] Error clearing post-update flag:', error);
            });
        }
      })
      .catch((error) => {
        const errorMessage = error instanceof Error ? error.message : String(error);
        const isHtmlFallbackResponse =
          errorMessage.includes('Invalid JSON response') &&
          errorMessage.includes('content-type: text/html');

        if (isHtmlFallbackResponse) {
          console.info(
            '[update_reconnect] Version endpoint returned HTML during startup; skipping post-update check'
          );
          return;
        }

        console.warn(
          '[update_reconnect] Failed to check version/post-update status:',
          errorMessage
        );
      });

    window.addEventListener('trigger-update-overlay', function () {
      console.log('[update_reconnect] Received trigger-update-overlay event');
      startReconnecting(true);
    });

    setTimeout(monitorDashWebSocket, 1000);
  }

  init();
})();
