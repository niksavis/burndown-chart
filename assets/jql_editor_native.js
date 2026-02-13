/**
 * Native JQL Editor Initialization Script
 *
 * Creates native CodeMirror editors (not from textarea) for JQL syntax highlighting.
 * Syncs CodeMirror value to hidden input for Dash callbacks.
 *
 * Architecture:
 *   1. Find all containers with class "jql-codemirror-container"
 *   2. Create native CodeMirror instance inside container
 *   3. Sync changes to hidden input with matching ID
 *   4. Dash callbacks read from hidden input value
 *
 * Integration Flow:
 *   Python (ui/jql_editor.py) creates:
 *     → <div class="jql-codemirror-container" data-editor-id="query-jql-editor">
 *     → <input type="hidden" id="query-jql-editor" value="...">
 *
 *   This script:
 *     → Finds container by class
 *     → Creates CodeMirror(container, {...})
 *     → Syncs CodeMirror.getValue() → hidden input.value
 *
 *   Dash callbacks:
 *     → Read from Input("query-jql-editor", "value")
 *     → Write to Output("query-jql-editor", "value")
 */

(function () {
  "use strict";

  /**
   * Ensure JQL mode is registered with the active CodeMirror instance.
   */
  function ensureJqlModeRegistered() {
    if (typeof CodeMirror === "undefined" || !CodeMirror.defineMode) {
      return;
    }

    if (CodeMirror.modes && CodeMirror.modes.jql) {
      return;
    }

    if (typeof window !== "undefined" && window.jqlLanguageMode) {
      CodeMirror.defineMode("jql", function () {
        return window.jqlLanguageMode;
      });
    }
  }

  /**
   * Check if JQL mode is registered with CodeMirror
   */
  function isJqlModeAvailable() {
    if (typeof CodeMirror === "undefined") {
      return false;
    }

    ensureJqlModeRegistered();

    try {
      const testMode = CodeMirror.getMode({}, "jql");
      return testMode && testMode.name === "jql";
    } catch (e) {
      return false;
    }
  }

  /**
   * Initialize all native CodeMirror editors
   */
  function initializeNativeEditors() {
    const codeMirrorAvailable =
      typeof CodeMirror !== "undefined" && typeof CodeMirror === "function";

    if (!codeMirrorAvailable) {
      console.error("[Native JQL] CodeMirror not loaded");
      return;
    }

    // Check if JQL mode is available
    const jqlModeAvailable = isJqlModeAvailable();

    if (!jqlModeAvailable) {
      console.warn("[Native JQL] JQL mode not loaded - using plain text");
    }

    // Find all native editor containers
    const containers = document.querySelectorAll(".jql-codemirror-container");

    if (containers.length === 0) {
      return;
    }

    console.log(`[Native JQL] Initializing ${containers.length} editor(s)`);

    containers.forEach((container) => {
      // Skip if already initialized
      if (container._cmEditor) {
        return;
      }

      const editorId = container.getAttribute("data-editor-id");
      const initialValue = container.getAttribute("data-initial-value") || "";
      const placeholder =
        container.getAttribute("data-placeholder") || "Enter JQL query...";

      // Find hidden input
      const hiddenInput = document.getElementById(editorId);
      if (!hiddenInput) {
        console.error(`[Native JQL] Hidden input not found: ${editorId}`);
        return;
      }

      // CRITICAL: Use hidden input value if it exists (Dash may update it)
      const actualInitialValue = hiddenInput.value || initialValue;

      console.log(
        `[Native JQL] Creating editor for ${editorId} with value: "${actualInitialValue.substring(
          0,
          50,
        )}..."`,
      );

      // Create native CodeMirror
      const editor = CodeMirror(container, {
        value: actualInitialValue,
        mode: jqlModeAvailable ? "jql" : "text/plain",
        lineNumbers: false,
        lineWrapping: true,
        theme: "default",
        placeholder: placeholder,
        indentWithTabs: false,
        indentUnit: 2,
        tabSize: 2,
        autofocus: false,
        viewportMargin: Infinity, // Render all lines (prevents height issues)
        extraKeys: {
          Tab: false,
        },
      });

      // Store reference
      container._cmEditor = editor;

      // CRITICAL: Check if container is visible, if not, mark for refresh
      const isVisible = container.offsetParent !== null;
      if (!isVisible) {
        console.log(
          `[Native JQL] ${editorId} initialized in hidden tab, will refresh on tab show`,
        );
        container.setAttribute("data-needs-refresh", "true");
      }

      // Refresh editor to fix display (fixes hidden tab issue)
      setTimeout(function () {
        editor.refresh();
      }, 1);

      // Sync CodeMirror → hidden input
      editor.on("change", function () {
        const value = editor.getValue();
        if (hiddenInput.value !== value) {
          hiddenInput.value = value;
          // Trigger change event for Dash
          const event = new Event("input", { bubbles: true });
          hiddenInput.dispatchEvent(event);
        }
      });

      // Sync hidden input → CodeMirror (for Dash updates)
      // Use the correct prototype based on element type
      const elementPrototype =
        hiddenInput.tagName === "TEXTAREA"
          ? HTMLTextAreaElement.prototype
          : HTMLInputElement.prototype;

      const originalDescriptor = Object.getOwnPropertyDescriptor(
        elementPrototype,
        "value",
      );

      Object.defineProperty(hiddenInput, "value", {
        get: function () {
          return originalDescriptor.get.call(this);
        },
        set: function (val) {
          originalDescriptor.set.call(this, val);
          if (editor && editor.getValue() !== val) {
            editor.setValue(val || "");
          }
        },
      });

      console.log(
        `[Native JQL] Initialized ${editorId} with ${
          actualInitialValue.length
        } chars: "${actualInitialValue.substring(0, 50)}..."`,
      );
    });
  }

  // Initialize on DOMContentLoaded
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeNativeEditors);
  } else {
    initializeNativeEditors();
  }

  // Retry initialization every 500ms for first 5 seconds (catches Dash dynamic content)
  let retryCount = 0;
  const maxRetries = 10;
  const retryInterval = setInterval(function () {
    const uninitializedContainers = Array.from(
      document.querySelectorAll(".jql-codemirror-container"),
    ).filter((c) => !c._cmEditor);

    if (uninitializedContainers.length > 0) {
      console.log(
        `[Native JQL] Retry ${retryCount + 1}: Found ${
          uninitializedContainers.length
        } uninitialized container(s)`,
      );
      initializeNativeEditors();
    }

    retryCount++;
    if (retryCount >= maxRetries) {
      clearInterval(retryInterval);
      console.log("[Native JQL] Stopped retry polling");
    }
  }, 500);

  // Watch for dynamically added containers (Dash adds content after page load)
  const observer = new MutationObserver(function (mutations) {
    let shouldReinit = false;
    mutations.forEach(function (mutation) {
      mutation.addedNodes.forEach(function (node) {
        if (node.nodeType === 1) {
          // Element node
          if (
            node.classList &&
            node.classList.contains("jql-codemirror-container")
          ) {
            shouldReinit = true;
          } else if (node.querySelectorAll) {
            const containers = node.querySelectorAll(
              ".jql-codemirror-container",
            );
            if (containers.length > 0) {
              shouldReinit = true;
            }
          }
        }
      });
    });

    if (shouldReinit) {
      console.log("[Native JQL] New containers detected, reinitializing...");
      setTimeout(initializeNativeEditors, 50);
    }
  });

  // Start observing the document body for changes
  if (document.body) {
    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  } else {
    document.addEventListener("DOMContentLoaded", function () {
      observer.observe(document.body, {
        childList: true,
        subtree: true,
      });
    });
  }

  // Refresh CodeMirror when tabs change (multiple event strategies)
  // Strategy 1: Bootstrap native event
  document.addEventListener("shown.bs.tab", function (event) {
    console.log("[Native JQL] Bootstrap tab shown event");
    refreshAllEditors();
  });

  // Strategy 2: Click on tab navigation (Dash Bootstrap Components)
  document.addEventListener("click", function (event) {
    const target = event.target;
    // Check if click is on Queries tab
    if (
      target &&
      (target.textContent?.includes("Queries") ||
        target.closest('[tab_id="queries-tab"]') ||
        (target.classList && target.classList.contains("nav-link")))
    ) {
      console.log("[Native JQL] Queries tab clicked, will refresh editors");
      setTimeout(refreshAllEditors, 150);
    }
  });

  // Helper function to refresh all editors
  function refreshAllEditors() {
    console.log("[Native JQL] Refreshing all editors...");

    // First, try to initialize any uninitialized editors
    initializeNativeEditors();

    // Then refresh any existing editors
    setTimeout(function () {
      const containers = document.querySelectorAll(".jql-codemirror-container");
      containers.forEach(function (container) {
        if (container._cmEditor) {
          const needsRefresh =
            container.getAttribute("data-needs-refresh") === "true";

          if (needsRefresh) {
            console.log(
              `[Native JQL] Refreshing ${container.getAttribute(
                "data-editor-id",
              )} (was hidden on init)`,
            );
            container.removeAttribute("data-needs-refresh");
          }

          container._cmEditor.refresh();

          // Double refresh for stubborn cases
          setTimeout(function () {
            container._cmEditor.refresh();
          }, 100);
        }
      });
    }, 50);
  }

  // Re-initialize on Dash page load (for dynamic content)
  document.addEventListener("DOMContentLoaded", function () {
    if (window.dash_clientside) {
      window.dash_clientside = window.dash_clientside || {};
      window.dash_clientside.reinit_jql = function () {
        setTimeout(initializeNativeEditors, 100);
        return window.dash_clientside.no_update;
      };
    }
  });

  // Global re-init for debugging
  window.reinitJQLEditors = initializeNativeEditors;
})();
