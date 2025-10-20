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
    // NOTE: Currently using textarea fallback, not full CodeMirror integration
    // We don't wait for CodeMirror/jqlLanguageMode - proceed directly with textarea

    // Log availability for debugging
    const jqlModeAvailable = typeof window.jqlLanguageMode !== "undefined";
    const codeMirrorAvailable =
      (typeof CodeMirror !== "undefined" && CodeMirror.EditorView) ||
      (typeof window.CodeMirror !== "undefined" &&
        window.CodeMirror.EditorView) ||
      typeof CM !== "undefined";

    if (jqlModeAvailable && codeMirrorAvailable) {
      console.log(
        "[JQL Editor] Both jqlLanguageMode and CodeMirror available - full editor possible"
      );
    } else if (jqlModeAvailable) {
      console.log(
        "[JQL Editor] jqlLanguageMode available, CodeMirror not loaded - using textarea fallback"
      );
    } else {
      console.log(
        "[JQL Editor] Using plain textarea fallback (CodeMirror/jqlLanguageMode not loaded)"
      );
    }

    // Find all editor containers
    const containers = document.querySelectorAll(".jql-editor-container");

    containers.forEach((container) => {
      // Skip if already initialized
      if (initializedEditors.has(container)) {
        console.log(
          "[JQL Editor] Skipping already initialized container:",
          container.id
        );
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
      console.warn(`[JQL Editor] Store element not found with ID: ${editorId}`);
      console.log("[JQL Editor] Searching for Store by selector...");

      // Try finding by data-dash-store attribute or other methods
      storeElement =
        document.querySelector(`[id="${editorId}"]`) ||
        document.querySelector(`#${CSS.escape(editorId)}`);

      if (!storeElement) {
        console.error(
          "[JQL Editor] Could not find Store element by any method"
        );
        console.log(
          "[JQL Editor] Proceeding without Store sync (textarea will still be editable)"
        );
        // Don't return - we can still create an editable textarea
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
    // Note: This is a simplified implementation
    // Full CodeMirror 6 initialization requires proper imports and extensions
    // This is a placeholder that demonstrates the integration pattern

    // STRATEGY: Instead of creating a new textarea, use the existing hidden one
    // This prevents Dash from removing our dynamically created element
    console.log(
      "[JQL Editor] Looking for hidden textarea:",
      `${editorId}-hidden`
    );
    const hiddenTextarea = document.getElementById(`${editorId}-hidden`);

    if (hiddenTextarea) {
      console.log("[JQL Editor] Found hidden textarea, making it visible...");

      // Move it into the container
      container.appendChild(hiddenTextarea);

      // Make it visible and style it
      hiddenTextarea.style.display = "block";
      hiddenTextarea.style.width = "100%";
      hiddenTextarea.style.minHeight = "100px";
      hiddenTextarea.style.fontFamily = "Monaco, Menlo, monospace";
      hiddenTextarea.style.fontSize = "14px";
      hiddenTextarea.style.padding = "8px";
      hiddenTextarea.style.border = "1px solid #ced4da";
      hiddenTextarea.style.borderRadius = "4px";
      hiddenTextarea.style.resize = "vertical";
      hiddenTextarea.className = "jql-editor-textarea";

      console.log(
        "[JQL Editor] Hidden textarea readOnly:",
        hiddenTextarea.readOnly
      );
      console.log(
        "[JQL Editor] Hidden textarea disabled:",
        hiddenTextarea.disabled
      );
      console.log("[JQL Editor] Hidden textarea value:", hiddenTextarea.value);

      // Sync changes to dcc.Store (if available)
      if (storeElement) {
        hiddenTextarea.addEventListener("input", function () {
          console.log("[JQL Editor] Textarea input event - syncing to Store");
          updateStoreValue(storeElement, hiddenTextarea.value);
        });
      } else {
        console.warn(
          "[JQL Editor] No Store element found - textarea editable but won't sync to Dash callbacks"
        );
      }

      console.log("[JQL Editor] Textarea moved to container and made visible");
      return { textarea: hiddenTextarea };
    }

    // Fallback: create a new textarea if hidden one not found
    console.log("[JQL Editor] Hidden textarea not found, creating new one...");
    const textarea = document.createElement("textarea");
    textarea.className = "jql-editor-textarea";
    textarea.value = initialValue;
    textarea.placeholder = placeholder;
    textarea.style.width = "100%";
    textarea.style.minHeight = "100px";
    textarea.style.fontFamily = "Monaco, Menlo, monospace";
    textarea.style.fontSize = "14px";
    textarea.style.padding = "8px";
    textarea.style.border = "1px solid #ced4da";
    textarea.style.borderRadius = "4px";
    textarea.style.resize = "vertical";

    console.log("[JQL Editor] Textarea readonly:", textarea.readOnly);
    console.log("[JQL Editor] Textarea disabled:", textarea.disabled);

    // Sync changes to dcc.Store (if available)
    if (storeElement) {
      textarea.addEventListener("input", function () {
        console.log("[JQL Editor] Textarea input event - syncing to Store");
        updateStoreValue(storeElement, textarea.value);
      });
    } else {
      console.warn(
        "[JQL Editor] No Store element found - textarea editable but won't sync to Dash callbacks"
      );
    }

    container.appendChild(textarea);
    console.log(
      "[JQL Editor] Textarea appended to container, children count:",
      container.children.length
    );

    return { textarea }; // Return object for consistency
  }

  /**
   * Get current value from dcc.Store element.
   *
   * @param {HTMLElement} storeElement - dcc.Store DOM element
   * @returns {string} Current store value
   */
  function getStoreValue(storeElement) {
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
   * @param {HTMLElement} storeElement - dcc.Store DOM element
   * @param {string} value - New value to store
   */
  function updateStoreValue(storeElement, value) {
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
