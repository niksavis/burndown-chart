/**
 * JQL Editor Initialization Script
 *
 * Initializes CodeMirror 6 editors for JQL syntax highlighting.
 * Bridges CodeMirror (client-side) with Dash dcc.Store (server-side).
 *
 * Architecture:
 *   1. Finds all .jql-editor-container elements on page
 *   2. Initializes CodeMirror EditorView in each container
 *   3. Applies jqlLanguageMode for syntax highlighting
 *   4. Syncs editor content to corresponding dcc.Store on every change
 *
 * Integration Flow:
 *   Python (ui/jql_editor.py) creates:
 *     → <div class="jql-editor-container" id="jira-jql-query-container">
 *     → <dcc.Store id="jira-jql-query">
 *
 *   This script:
 *     → Finds container by class
 *     → Extracts editor ID from container ID (remove "-container" suffix)
 *     → Initializes CodeMirror in container
 *     → Updates Store on every editor change
 *
 *   Dash callbacks:
 *     → Read from dcc.Store "data" property
 *     → Trigger on Input("jira-jql-query", "data")
 *
 * Dependencies:
 *   - CodeMirror 6 CDN must be loaded first
 *   - jql_language_mode.js must be loaded (defines window.jqlLanguageMode)
 *   - CSS token classes must be defined in custom.css
 *
 * Lifecycle:
 *   - Runs on DOMContentLoaded
 *   - Runs on Dash page updates (via MutationObserver)
 *   - Handles dynamic editor creation
 */

(function () {
  "use strict";

  // Store initialized editors to avoid double-initialization
  const initializedEditors = new WeakSet();

  // Retry configuration
  let retryCount = 0;
  const MAX_RETRIES = 50; // 50 * 100ms = 5 seconds max wait
  const RETRY_DELAY = 100; // milliseconds

  /**
   * Initialize all JQL editors on the page.
   * Safe to call multiple times - skips already initialized editors.
   */
  function initializeJQLEditors() {
    // Check if CodeMirror and jqlLanguageMode are available
    const jqlModeAvailable = typeof window.jqlLanguageMode !== "undefined";
    const codeMirrorAvailable =
      typeof CodeMirror !== "undefined" || typeof window.CM !== "undefined";

    if (jqlModeAvailable && codeMirrorAvailable) {
      console.log(
        "[JQL Editor] CodeMirror and jqlLanguageMode available - initializing full editor"
      );
    } else {
      console.warn(
        "[JQL Editor] CodeMirror or jqlLanguageMode not available - using textarea fallback"
      );
      console.log("  jqlLanguageMode:", jqlModeAvailable ? "✓" : "✗");
      console.log("  CodeMirror:", codeMirrorAvailable ? "✓" : "✗");
    }

    // Find all editor containers
    const containers = document.querySelectorAll(".jql-editor-container");
    console.log(`[JQL Editor] Found ${containers.length} editor container(s)`);

    containers.forEach((container) => {
      // Skip if already initialized
      if (initializedEditors.has(container)) {
        console.log(
          "[JQL Editor] Skipping already initialized container:",
          container.id
        );
        return;
      }

      // Also check if CodeMirror already exists in this container
      if (container._cmEditor || container.querySelector(".CodeMirror")) {
        console.log(
          "[JQL Editor] Skipping container with existing CodeMirror:",
          container.id
        );
        initializedEditors.add(container); // Mark as initialized
        return;
      }

      console.log(
        "[JQL Editor] Attempting to initialize container:",
        container.id
      );
      try {
        initializeEditor(container);
        initializedEditors.add(container);
        console.log(
          "[JQL Editor] Successfully initialized container:",
          container.id
        );
      } catch (error) {
        console.error("[JQL Editor] Failed to initialize editor:", error);
      }
    });
  }

  /**
   * Initialize a single CodeMirror editor in the given container.
   *
   * @param {HTMLElement} container - The .jql-editor-container element
   */
  function initializeEditor(container) {
    // Extract editor ID from container ID
    // Container ID format: "{editor_id}-container"
    // Store ID format: "{editor_id}"
    const containerId = container.id;
    if (!containerId) {
      console.error("[JQL Editor] Container missing ID attribute");
      return;
    }

    console.log("[JQL Editor] Container ID:", containerId);
    const editorId = containerId.replace("-container", "");
    console.log("[JQL Editor] Editor ID:", editorId);

    // Find corresponding dcc.Store element
    // dcc.Store might be rendered as a div or other element
    let storeElement = document.getElementById(editorId);

    if (!storeElement) {
      console.log(
        `[JQL Editor] Store not in DOM with ID: ${editorId} (expected for dcc.Store)`
      );
      console.log(
        "[JQL Editor] Attempting alternate Store detection methods..."
      );

      // Try finding by data-dash-store attribute or other methods
      storeElement =
        document.querySelector(`[id="${editorId}"]`) ||
        document.querySelector(`#${CSS.escape(editorId)}`);

      if (!storeElement) {
        console.log(
          "[JQL Editor] Store element not in DOM (this is normal for dcc.Store components)"
        );
        console.log(
          "[JQL Editor] Python callbacks will handle textarea ↔ Store synchronization"
        );
        // Don't return - we can still create an editable textarea
        // The Python callbacks in callbacks/jql_editor.py handle Store sync
      } else {
        console.log(
          "[JQL Editor] Found Store element using alternate selector"
        );
      }
    } else {
      console.log("[JQL Editor] Store element found:", editorId);
    }

    // Get initial value from container attributes or Store
    const initialValue =
      container.getAttribute("title") ||
      container.dataset.initialValue ||
      getStoreValue(storeElement) ||
      "";

    // Get placeholder from hidden textarea (fallback element)
    const hiddenTextarea = document.getElementById(`${editorId}-hidden`);
    const placeholder =
      (hiddenTextarea && hiddenTextarea.placeholder) ||
      container.dataset.placeholder ||
      "Enter JQL query...";

    console.log(
      "[JQL Editor] Initial value:",
      initialValue ? initialValue.substring(0, 50) : "(empty)"
    );
    console.log("[JQL Editor] Placeholder:", placeholder);

    // Create CodeMirror editor with JQL highlighting
    const editor = createCodeMirrorEditor(
      container,
      initialValue,
      placeholder,
      editorId,
      storeElement
    );

    // Store editor reference on container for potential future access
    container._cmEditor = editor;

    console.log(`[JQL Editor] Initialized editor: ${editorId}`);
  }

  /**
   * Create and configure CodeMirror EditorView.
   *
   * @param {HTMLElement} container - Mount point for editor
   * @param {string} initialValue - Initial editor content
   * @param {string} placeholder - Placeholder text
   * @param {string} editorId - Editor identifier
   * @param {HTMLElement} storeElement - Corresponding dcc.Store element
   * @returns {EditorView} CodeMirror editor instance
   */
  function createCodeMirrorEditor(
    container,
    initialValue,
    placeholder,
    editorId,
    storeElement
  ) {
    // Check if CodeMirror 5 is available
    if (typeof CodeMirror === "undefined" || !CodeMirror.fromTextArea) {
      console.warn(
        "[JQL Editor] CodeMirror 5 not available, using textarea fallback"
      );
      return createTextareaFallback(
        container,
        initialValue,
        placeholder,
        editorId,
        storeElement
      );
    }

    // Check if JQL mode is registered
    if (!window.jqlLanguageMode) {
      console.warn("[JQL Editor] JQL mode not loaded, using textarea fallback");
      return createTextareaFallback(
        container,
        initialValue,
        placeholder,
        editorId,
        storeElement
      );
    }

    console.log(
      "[JQL Editor] Creating CodeMirror 5 editor with JQL syntax highlighting"
    );

    // Find or create textarea for CodeMirror
    let textarea =
      container.querySelector("textarea") ||
      document.getElementById(`${editorId}-textarea`);

    if (!textarea) {
      console.log("[JQL Editor] Creating new textarea element for CodeMirror");
      textarea = document.createElement("textarea");
      textarea.id = `${editorId}-textarea`;
      textarea.value = initialValue;
      container.appendChild(textarea);
    } else {
      console.log("[JQL Editor] Using existing textarea:", textarea.id);
      // Update value if needed
      if (initialValue && !textarea.value) {
        textarea.value = initialValue;
      }
    }

    try {
      // Create CodeMirror editor from textarea
      const editor = CodeMirror.fromTextArea(textarea, {
        mode: "jql", // Use our custom JQL mode
        lineNumbers: false, // No line numbers for single queries
        lineWrapping: true, // Wrap long queries
        theme: "default", // Use default theme (styled via CSS)
        placeholder: placeholder,
        indentWithTabs: false,
        indentUnit: 2,
        tabSize: 2,
        autofocus: false,
        // Additional options for better UX
        extraKeys: {
          Tab: false, // Disable tab capture for accessibility
        },
      });

      console.log("[JQL Editor] CodeMirror editor created successfully");

      // Sync CodeMirror changes to textarea (Python callbacks handle textarea ↔ Store)
      if (storeElement) {
        // If Store element found (rare), sync directly
        editor.on("change", function (cm) {
          const value = cm.getValue();
          updateStoreValue(storeElement, value);
        });
        console.log("[JQL Editor] Direct Store sync enabled");
      } else {
        // Normal case: Python callbacks handle textarea → Store sync
        // CodeMirror.fromTextArea() automatically updates the hidden textarea
        console.log(
          "[JQL Editor] Textarea sync enabled (Python callbacks handle Store)"
        );
      }

      // Store editor reference
      container._cmEditor = editor;

      // Style the CodeMirror wrapper
      const cmWrapper = container.querySelector(".CodeMirror");
      if (cmWrapper) {
        cmWrapper.style.height = "auto";
        cmWrapper.style.minHeight = "100px";
        cmWrapper.style.border = "1px solid #ced4da";
        cmWrapper.style.borderRadius = "4px";
        cmWrapper.style.fontSize = "14px";
        console.log("[JQL Editor] CodeMirror wrapper styled");
      }

      return editor;
    } catch (error) {
      console.error("[JQL Editor] Error creating CodeMirror editor:", error);
      console.log("[JQL Editor] Falling back to plain textarea");
      return createTextareaFallback(
        container,
        initialValue,
        placeholder,
        editorId,
        storeElement
      );
    }
  }

  /**
   * Create a plain textarea fallback when CodeMirror is not available.
   */
  function createTextareaFallback(
    container,
    initialValue,
    placeholder,
    editorId,
    storeElement
  ) {
    console.log("[JQL Editor] Creating textarea fallback");

    // Find existing textarea or create new one
    let textarea =
      container.querySelector("textarea") ||
      document.getElementById(`${editorId}-textarea`);

    if (!textarea) {
      textarea = document.createElement("textarea");
      textarea.id = `${editorId}-textarea`;
      textarea.className = "jql-editor-textarea form-control";
      textarea.value = initialValue;
      textarea.placeholder = placeholder;
      textarea.style.fontFamily = "Monaco, Menlo, monospace";
      textarea.style.fontSize = "14px";
      textarea.style.minHeight = "100px";
      textarea.style.width = "100%";
      textarea.style.resize = "vertical";
      container.appendChild(textarea);
    }

    // Ensure textarea is visible and editable
    textarea.style.display = "block";
    textarea.readOnly = false;
    textarea.disabled = false;

    // Sync changes to dcc.Store
    if (storeElement) {
      textarea.addEventListener("input", function () {
        console.log("[JQL Editor] Textarea input - syncing to Store");
        updateStoreValue(storeElement, textarea.value);
      });
    }

    console.log("[JQL Editor] Textarea fallback created");
    return { textarea: textarea };
  }

  /**
   * Get current value from dcc.Store element.
   *
   * @param {HTMLElement} storeElement - dcc.Store DOM element (can be null)
   * @returns {string} Current store value
   */
  function getStoreValue(storeElement) {
    // Return empty string if no store element
    if (!storeElement) {
      return "";
    }

    try {
      // dcc.Store stores data in a data attribute
      const dataAttr = storeElement.getAttribute("data-dash-store-data");
      if (dataAttr) {
        const parsed = JSON.parse(dataAttr);
        return parsed || "";
      }
      return "";
    } catch (error) {
      console.error("[JQL Editor] Error reading Store value:", error);
      return "";
    }
  }

  /**
   * Update dcc.Store with new editor value.
   * Triggers Dash callbacks listening to this Store.
   *
   * @param {HTMLElement} storeElement - dcc.Store DOM element (can be null)
   * @param {string} value - New value to store
   */
  function updateStoreValue(storeElement, value) {
    // Skip if no store element
    if (!storeElement) {
      return;
    }

    try {
      // Update Store's data attribute
      storeElement.setAttribute("data-dash-store-data", JSON.stringify(value));

      // Dispatch change event to notify Dash
      const event = new CustomEvent("change", {
        bubbles: true,
        detail: { value: value },
      });
      storeElement.dispatchEvent(event);
    } catch (error) {
      console.error("[JQL Editor] Error updating Store value:", error);
    }
  }

  /**
   * Watch for dynamic content changes (Dash page updates).
   * Re-initialize editors when new containers appear.
   */
  function observeDOMChanges() {
    const observer = new MutationObserver(function (mutations) {
      let shouldReinitialize = false;

      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            // Check if added node is or contains editor containers
            if (
              node.classList &&
              node.classList.contains("jql-editor-container")
            ) {
              shouldReinitialize = true;
            } else if (node.querySelectorAll) {
              const containers = node.querySelectorAll(".jql-editor-container");
              if (containers.length > 0) {
                shouldReinitialize = true;
              }
            }
          }
        });
      });

      if (shouldReinitialize) {
        console.log("[JQL Editor] DOM changed, reinitializing editors...");
        initializeJQLEditors();
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  }

  // Initialize on page load
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initializeJQLEditors();
      observeDOMChanges();
    });
  } else {
    // DOM already loaded
    initializeJQLEditors();
    observeDOMChanges();
  }

  // Also try to initialize after a short delay (handles race conditions)
  setTimeout(initializeJQLEditors, 500);
})();
