/**
 * JQL Editor Initialization Script
 *
 * Initializes CodeMirror 5 editors for JQL syntax highlighting.
 * Uses CodeMirror.fromTextArea() for automatic synchronization with Dash callbacks.
 *
 * Architecture:
 *   1. Find all textareas with class "jql-editor-textarea"
 *   2. Use CodeMirror.fromTextArea() to create editor
 *   3. CodeMirror automatically syncs changes back to textarea
 *   4. Dash callbacks read from textarea.value (no additional sync needed)
 *
 * Integration Flow:
 *   Python (ui/jql_editor.py) creates:
 *     → <textarea id="jira-jql-query" class="jql-editor-textarea">
 *
 *   This script:
 *     → Finds textarea by class
 *     → Calls CodeMirror.fromTextArea(textarea, {...})
 *     → CodeMirror handles all synchronization automatically
 *
 *   Dash callbacks:
 *     → Read from Input("jira-jql-query", "value")
 *     → Write to Output("jira-jql-query", "value")
 *     → Everything works like a normal textarea!
 *
 * Dependencies:
 *   - CodeMirror 5 CDN must be loaded first
 *   - jql_language_mode.js must be loaded (defines JQL mode)
 *   - CSS token classes must be defined in custom.css
 */

(function () {
  "use strict";

  // Store initialized textareas to avoid double-initialization
  const initializedTextareas = new WeakSet();

  /**
   * Hide JQL test results when user starts typing or loads new query
   */
  let testResultsLocked = false; // Flag to prevent hiding when test is in progress

  function hideJQLTestResults() {
    // Don't hide if test results are locked (test in progress or results showing)
    if (testResultsLocked) {
      console.log("[JQL Test] Hide blocked - lock is TRUE");
      return;
    }

    console.log("[JQL Test] Hiding test results - lock is FALSE");
    const testResultsDiv = document.getElementById("jql-test-results");
    if (testResultsDiv) {
      // Use className to hide (CSS will override inline style with !important)
      // DON'T clear innerHTML - let Dash manage the content
      testResultsDiv.className = "jql-test-results-hidden";
    }
  }

  // Expose functions globally for the test button callback
  window.setJQLTestResultsLock = function (locked) {
    console.log("[JQL Test] Lock changed:", testResultsLocked, "→", locked);
    testResultsLocked = locked;
  };

  /**
   * Initialize CodeMirror on all JQL editor textareas.
   * Safe to call multiple times - skips already initialized textareas.
   */
  function initializeJQLEditors() {
    // Check if CodeMirror and jqlLanguageMode are available
    const jqlModeAvailable = typeof window.jqlLanguageMode !== "undefined";
    const codeMirrorAvailable =
      typeof CodeMirror !== "undefined" &&
      typeof CodeMirror.fromTextArea === "function";

    if (!codeMirrorAvailable) {
      console.warn(
        "[JQL Editor] CodeMirror 5 not available - using plain textareas"
      );
      return;
    }

    if (!jqlModeAvailable) {
      console.warn(
        "[JQL Editor] JQL language mode not loaded - syntax highlighting disabled"
      );
    }

    // Find all JQL editor textareas
    const textareas = document.querySelectorAll("textarea.jql-editor-textarea");
    // Reduced logging: only log if no textareas found or more than expected
    if (textareas.length === 0 || textareas.length > 2) {
      console.log(`[JQL Editor] Found ${textareas.length} textarea(s)`);
    }

    textareas.forEach((textarea) => {
      // Skip if already initialized
      if (initializedTextareas.has(textarea)) {
        return;
      }

      // Skip if CodeMirror already attached
      if (
        textarea.nextSibling &&
        textarea.nextSibling.classList &&
        textarea.nextSibling.classList.contains("CodeMirror")
      ) {
        // Reduced logging: only log in debug mode
        initializedTextareas.add(textarea);
        return;
      }

      // Reduced logging: only log initialization attempts
      if (window.location.search.includes("debug=true")) {
        console.log(
          "[JQL Editor] Initializing CodeMirror for textarea:",
          textarea.id
        );
      }

      try {
        // CRITICAL FIX: Capture initial value BEFORE CodeMirror hides textarea
        // Get the REAL DOM value, not our custom property
        const domValue = Object.getOwnPropertyDescriptor(
          HTMLTextAreaElement.prototype,
          "value"
        ).get.call(textarea);
        const initialValue = domValue || "";

        console.log(
          `[JQL Editor] Init ${textarea.id}: captured value length =`,
          initialValue.length,
          initialValue ? `(${initialValue.substring(0, 30)}...)` : "(empty)"
        );

        // Create CodeMirror from textarea
        const editor = CodeMirror.fromTextArea(textarea, {
          mode: jqlModeAvailable ? "jql" : "text/plain",
          lineNumbers: false,
          lineWrapping: true,
          theme: "default",
          placeholder: textarea.placeholder || "Enter JQL query...",
          indentWithTabs: false,
          indentUnit: 2,
          tabSize: 2,
          autofocus: false,
          extraKeys: {
            Tab: false, // Don't capture Tab key (accessibility)
          },
        });

        console.log(
          `[JQL Editor] After fromTextArea(): CodeMirror value length =`,
          editor.getValue().length
        );

        // CRITICAL FIX: Explicitly set the initial value in CodeMirror
        // fromTextArea() should do this automatically, but it fails when
        // the textarea is inside a collapsed Bootstrap panel
        if (initialValue && editor.getValue() !== initialValue) {
          console.log(`[JQL Editor] Manually setting value in CodeMirror`);
          editor.setValue(initialValue);
        }

        // Mark as initialized
        initializedTextareas.add(textarea);

        // Store reference for potential future access
        textarea._cmEditor = editor;

        // AGGRESSIVE APPROACH: Override textarea's value property to always sync
        let originalValue = initialValue;
        Object.defineProperty(textarea, "_originalValue", {
          get: function () {
            return originalValue;
          },
          set: function (val) {
            originalValue = val;
          },
        });

        Object.defineProperty(textarea, "value", {
          get: function () {
            // Always return CodeMirror value if it exists and differs
            if (editor) {
              const cmValue = editor.getValue();
              if (cmValue !== originalValue) {
                return cmValue;
              }
            }
            return originalValue;
          },
          set: function (val) {
            // PERFORMANCE FIX: Removed verbose logging that was slowing down input
            originalValue = val;
            if (editor && editor.getValue() !== val) {
              editor.setValue(val);
            }
          },
        });

        // Add global debug reference (only for the main JQL editor)
        if (textarea.id === "jira-jql-query") {
          window.jqlEditor = editor;

          // Global force sync function for critical operations
          window.forceJQLSync = function () {
            syncCodeMirrorToTextarea();
            return editor.getValue();
          };

          // Enhanced debug function to check all values (only available in debug mode)
          if (window.location.search.includes("debug=true")) {
            window.checkAllValues = function () {
              console.log("=== ALL VALUES CHECK ===");
              console.log("CodeMirror value:", editor.getValue());
              console.log(
                "Textarea DOM value:",
                Object.getOwnPropertyDescriptor(
                  HTMLTextAreaElement.prototype,
                  "value"
                ).get.call(textarea)
              );
              console.log("Textarea custom value:", textarea.value);
              console.log("Textarea _originalValue:", textarea._originalValue);
              console.log(
                "Textarea attribute value:",
                textarea.getAttribute("value")
              );
              console.log("========================");
            };
          }

          // Debug functions (only available in debug mode)
          if (window.location.search.includes("debug=true")) {
            window.debugJQL = {
              getTextareaValue: () => textarea.value,
              getCodeMirrorValue: () => editor.getValue(),
              setTextareaValue: (val) => {
                textarea.value = val;
                console.log("Set textarea to:", val);
              },
              setCodeMirrorValue: (val) => {
                editor.setValue(val);
                console.log("Set CodeMirror to:", val);
              },
              checkSync: () => {
                const ta = textarea.value;
                const cm = editor.getValue();
                console.log(
                  "Sync check - Textarea:",
                  ta,
                  "CodeMirror:",
                  cm,
                  "Match:",
                  ta === cm
                );
                return ta === cm;
              },
              forceSync: () => {
                syncCodeMirrorToTextarea();
                console.log("Forced sync from CodeMirror to textarea");
              },
              syncFromTextarea: () => {
                const ta = textarea.value;
                editor.setValue(ta);
                console.log("Forced sync from textarea to CodeMirror");
              },
            };
            console.log(
              "[JQL Editor] Debug functions available at window.debugJQL"
            );
          }
        }

        // CRITICAL: Ensure bidirectional sync between CodeMirror and textarea
        // This is essential for Dash callbacks to work properly

        // 1. CodeMirror → Textarea sync (when user types in CodeMirror)
        const syncCodeMirrorToTextarea = function () {
          const value = editor.getValue();
          const oldValue = textarea._originalValue;

          if (oldValue !== value) {
            // PERFORMANCE FIX: Removed verbose logging to reduce lag

            // Update both the original value and DOM value
            textarea._originalValue = value;

            // Force update DOM attribute as well (for React)
            textarea.setAttribute("value", value);

            // Update the DOM property directly
            Object.getOwnPropertyDescriptor(
              HTMLTextAreaElement.prototype,
              "value"
            ).set.call(textarea, value);

            // Dispatch input event to notify Dash of the change
            const inputEvent = new Event("input", { bubbles: true });
            textarea.dispatchEvent(inputEvent);

            // Also dispatch change event for backward compatibility
            const changeEvent = new Event("change", { bubbles: true });
            textarea.dispatchEvent(changeEvent);
          }
        };

        // PERFORMANCE FIX: Optimized change handling with minimal throttling
        let syncTimeout;
        editor.on("change", function (cm, changeObj) {
          // Minimal throttle to reduce lag while maintaining responsiveness for character count
          clearTimeout(syncTimeout);
          syncTimeout = setTimeout(syncCodeMirrorToTextarea, 50); // Reduced from 150ms to 50ms

          // Only hide test results on user input (not programmatic changes)
          // Check if this is a user-initiated change
          if (changeObj.origin && changeObj.origin !== "setValue") {
            // When user starts typing, unlock the test results first
            if (typeof window.setJQLTestResultsLock === "function") {
              window.setJQLTestResultsLock(false);
            }
            // Then hide them (hideJQLTestResults will check the lock internally)
            hideJQLTestResults();
          }
        });

        // CRITICAL: Force sync when focus leaves CodeMirror (before callbacks fire)
        editor.on("blur", function (cm) {
          // Clear any pending throttled sync and do immediate sync
          clearTimeout(syncTimeout);
          syncCodeMirrorToTextarea();
        });

        // Force immediate sync on Enter key (common callback trigger)
        editor.on("keydown", function (cm, event) {
          if (event.key === "Enter" || event.keyCode === 13) {
            clearTimeout(syncTimeout);
            setTimeout(syncCodeMirrorToTextarea, 10);
          }
        });

        // 2. Textarea → CodeMirror sync (when Dash updates textarea programmatically)
        const syncTextareaToCodeMirror = function () {
          const textareaValue = textarea.value || "";
          const editorValue = editor.getValue() || "";

          if (textareaValue !== editorValue) {
            // PERFORMANCE FIX: Removed verbose logging
            // Use setValue without triggering change event to avoid infinite loop
            editor.setValue(textareaValue);

            // Don't hide test results on programmatic changes - only on user input
          }
        };

        // Watch for external changes to textarea (from Dash callbacks)
        // Dash uses React which can update DOM properties without events

        // Method 1: MutationObserver for attribute changes
        const attrObserver = new MutationObserver(function (mutations) {
          mutations.forEach(function (mutation) {
            if (
              mutation.type === "attributes" &&
              mutation.attributeName === "value"
            ) {
              syncTextareaToCodeMirror();
            }
          });
        });

        attrObserver.observe(textarea, {
          attributes: true,
          attributeFilter: ["value"],
        });

        // Method 2: Poll for value changes (handles React property updates)
        // CRITICAL FIX: Use faster polling to catch Dash callback updates quickly
        let lastKnownValue = textarea.value || "";
        const pollInterval = setInterval(function () {
          const currentValue = textarea.value || "";
          if (currentValue !== lastKnownValue) {
            lastKnownValue = currentValue;
            syncTextareaToCodeMirror();
          }
        }, 100); // CRITICAL FIX: Reduced to 100ms to catch Dash updates quickly on initial load

        // Method 3: Listen for standard DOM events
        textarea.addEventListener("input", syncTextareaToCodeMirror);
        textarea.addEventListener("change", syncTextareaToCodeMirror);

        // Method 4: Listen for Dash-specific events if they exist
        textarea.addEventListener("dash-update", syncTextareaToCodeMirror);

        // Store cleanup function on the textarea
        textarea._cleanup = function () {
          clearInterval(pollInterval);
          attrObserver.disconnect();
        };

        // CRITICAL FIX: Set initial sync with delay to ensure textarea value is populated
        // First sync immediately
        syncTextareaToCodeMirror();

        // Then sync again after short delays to catch async Dash updates
        setTimeout(syncTextareaToCodeMirror, 50);
        setTimeout(syncTextareaToCodeMirror, 200);
        setTimeout(syncTextareaToCodeMirror, 500);

        // Add click listeners to critical buttons to force sync before callbacks
        const criticalButtons = [
          "save-jql-query-button", // CRITICAL: This opens the modal with JQL preview
          "confirm-save-query-button",
          "update-data-unified",
          "calculate-scope",
          "save-query-button", // Legacy button ID (kept for compatibility)
        ];

        criticalButtons.forEach((buttonId) => {
          const button = document.getElementById(buttonId);
          if (button) {
            button.addEventListener(
              "click",
              function (e) {
                // PERFORMANCE FIX: Removed verbose logging
                // Force sync immediately and synchronously
                clearTimeout(syncTimeout); // Clear any pending throttled sync
                syncCodeMirrorToTextarea();

                // Secondary sync with small delay for race conditions
                setTimeout(syncCodeMirrorToTextarea, 1);
              },
              true
            ); // Use capture phase to run before other handlers
          }
        });

        // Use MutationObserver to add listeners to buttons that appear later
        const buttonObserver = new MutationObserver(function (mutations) {
          mutations.forEach(function (mutation) {
            mutation.addedNodes.forEach(function (node) {
              if (node.nodeType === 1) {
                // Element node
                criticalButtons.forEach((buttonId) => {
                  const button =
                    node.id === buttonId
                      ? node
                      : node.querySelector &&
                        node.querySelector(`#${buttonId}`);
                  if (
                    button &&
                    !button.hasAttribute("data-jql-sync-listener")
                  ) {
                    button.setAttribute("data-jql-sync-listener", "true");
                    button.addEventListener(
                      "click",
                      function (e) {
                        // PERFORMANCE FIX: Removed verbose logging
                        clearTimeout(syncTimeout);
                        syncCodeMirrorToTextarea();
                      },
                      true
                    );
                  }
                });
              }
            });
          });
        });

        buttonObserver.observe(document.body, {
          childList: true,
          subtree: true,
        });

        // Style the CodeMirror wrapper
        const cmWrapper = textarea.nextSibling;
        if (cmWrapper && cmWrapper.classList.contains("CodeMirror")) {
          cmWrapper.style.border = "1px solid #ced4da";
          cmWrapper.style.borderRadius = "0.25rem";
          cmWrapper.style.fontSize = "14px";
          cmWrapper.style.fontFamily =
            "Monaco, Menlo, 'Ubuntu Mono', Consolas, monospace";
          cmWrapper.style.minHeight = "100px";
          cmWrapper.style.maxHeight = "400px";
        }

        // PERFORMANCE FIX: Only log in debug mode
        if (window.location.search.includes("debug=true")) {
          console.log("[JQL Editor] Successfully initialized:", textarea.id);
        }
      } catch (error) {
        console.error("[JQL Editor] Failed to initialize editor:", error);
      }
    });
  }

  /**
   * Watch for dynamic content changes (Dash page updates).
   * Re-initialize editors when new textareas appear.
   */
  function observeDOMChanges() {
    const observer = new MutationObserver(function (mutations) {
      let shouldReinitialize = false;

      mutations.forEach(function (mutation) {
        mutation.addedNodes.forEach(function (node) {
          if (node.nodeType === 1) {
            // Element node
            // Check if added node is a JQL textarea or contains one
            if (
              (node.classList &&
                node.classList.contains("jql-editor-textarea")) ||
              (node.querySelector &&
                node.querySelector("textarea.jql-editor-textarea"))
            ) {
              shouldReinitialize = true;
            }
          }
        });
      });

      if (shouldReinitialize) {
        // PERFORMANCE FIX: Only log in debug mode
        if (window.location.search.includes("debug=true")) {
          console.log("[JQL Editor] DOM changed, re-initializing editors");
        }
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

  // Also try to initialize after a short delay (handles race conditions with Dash)
  setTimeout(function () {
    initializeJQLEditors();
  }, 500);

  /**
   * Watch for settings panel collapse events and sync CodeMirror.
   * This ensures the JQL editor shows the correct value when panel opens.
   */
  function watchSettingsPanelCollapse() {
    const settingsCollapse = document.getElementById("settings-collapse");

    console.log("[JQL Editor] Looking for settings-collapse...");
    console.log(
      "[JQL Editor] Found settings-collapse:",
      settingsCollapse ? "YES" : "NO"
    );

    if (settingsCollapse) {
      // Test if Bootstrap collapse is working
      console.log("[JQL Editor] Settings collapse element:", settingsCollapse);
      console.log(
        "[JQL Editor] Is open?",
        settingsCollapse.classList.contains("show")
      );

      // Bootstrap 5 collapse events
      settingsCollapse.addEventListener("shown.bs.collapse", function () {
        console.log(
          "[JQL Editor] ⭐ Settings panel shown.bs.collapse EVENT FIRED!"
        );
        refreshSettingsPanelEditor();
      });

      // CRITICAL FIX: Dash controls collapse via is_open property, not Bootstrap events
      // Use MutationObserver to detect when 'show' class is added (panel opens)
      const observer = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
          if (
            mutation.type === "attributes" &&
            mutation.attributeName === "class"
          ) {
            const isOpen = settingsCollapse.classList.contains("show");

            // Only trigger when panel becomes visible (gets 'show' class)
            if (isOpen) {
              console.log(
                "[JQL Editor] ⭐ Settings panel OPENED (detected via class change)!"
              );
              refreshSettingsPanelEditor();
            }
          }
        });
      });

      // Start observing class changes on the collapse element
      observer.observe(settingsCollapse, {
        attributes: true,
        attributeFilter: ["class"],
      });

      console.log(
        "[JQL Editor] Watching settings-collapse for class changes (Dash-compatible)"
      );

      console.log(
        "[JQL Editor] Watching settings panel collapse for sync events"
      );
    } else {
      // Retry if collapse not found yet
      setTimeout(watchSettingsPanelCollapse, 500);
    }
  }

  /**
   * Refresh the JQL editor when settings panel opens
   */
  function refreshSettingsPanelEditor() {
    const textarea = document.getElementById("jira-jql-query");
    if (textarea) {
      // CRITICAL FIX: Initialize CodeMirror if not already done
      // This handles cases where textarea was rendered while panel collapsed
      if (!textarea._cmEditor) {
        console.log(
          "[JQL Editor] Initializing CodeMirror on settings panel open"
        );
        initializeJQLEditors();
        // Wait for initialization to complete
        setTimeout(function () {
          refreshSettingsPanelEditor(); // Retry sync after init
        }, 100);
        return;
      }

      const editor = textarea._cmEditor;
      const textareaValue = textarea.value || "";

      console.log(
        "[JQL Editor] Panel opened - CodeMirror value:",
        editor.getValue().length,
        "Textarea value:",
        textareaValue.length
      );

      // Force update CodeMirror with current textarea value
      if (editor.getValue() !== textareaValue) {
        console.log("[JQL Editor] Syncing textarea to CodeMirror");
        editor.setValue(textareaValue);
      }

      // CRITICAL FIX: CodeMirror can't render properly when parent is display:none
      // When panel becomes visible, we must refresh to recalculate dimensions
      console.log("[JQL Editor] Forcing refresh after panel opens");

      // Immediate refresh
      editor.refresh();

      // Additional refresh after animation completes (Bootstrap collapse takes ~350ms)
      setTimeout(function () {
        console.log("[JQL Editor] Second refresh after animation");
        editor.refresh();
      }, 400);
    }
  }

  // Start watching for settings panel collapse
  watchSettingsPanelCollapse();

  // Expose debug function globally for troubleshooting
  window.debugJQLEditor = function (editorId = "jira-jql-query") {
    const textarea = document.getElementById(editorId);
    if (!textarea) {
      console.log("❌ Textarea not found:", editorId);
      return;
    }

    const editor = textarea._cmEditor;
    if (!editor) {
      console.log("❌ CodeMirror not initialized on textarea:", editorId);
      return;
    }

    console.log("🔍 JQL Editor Debug Info:");
    console.log("  Textarea ID:", textarea.id);
    console.log("  Textarea value:", textarea.value);
    console.log("  CodeMirror value:", editor.getValue());
    console.log("  Values match:", textarea.value === editor.getValue());
    console.log(
      "  CodeMirror initialized:",
      initializedTextareas.has(textarea)
    );

    return {
      textarea: textarea,
      editor: editor,
      textareaValue: textarea.value,
      codeMirrorValue: editor.getValue(),
      valuesMatch: textarea.value === editor.getValue(),
    };
  };

  // MANUAL REFRESH FUNCTION - Call this from console to force refresh
  window.refreshJQLEditor = function (editorId = "jira-jql-query") {
    const textarea = document.getElementById(editorId);
    if (!textarea || !textarea._cmEditor) {
      console.log("❌ Cannot refresh - editor not found");
      return false;
    }

    const editor = textarea._cmEditor;
    console.log("🔄 Forcing CodeMirror refresh...");
    console.log("  Before: CodeMirror has", editor.getValue().length, "chars");

    // Force set value from textarea
    const textareaValue = Object.getOwnPropertyDescriptor(
      HTMLTextAreaElement.prototype,
      "value"
    ).get.call(textarea);

    if (textareaValue && editor.getValue() !== textareaValue) {
      console.log("  Setting value:", textareaValue.substring(0, 50), "...");
      editor.setValue(textareaValue);
    }

    editor.refresh();
    console.log("  After: CodeMirror has", editor.getValue().length, "chars");
    console.log("✅ Refresh complete!");
    return true;
  };

  // Global click interceptor to force sync before any callback
  document.addEventListener(
    "click",
    function (e) {
      // Check if clicked element might trigger a Dash callback
      const target = e.target;

      // More specific targeting for critical buttons
      const isCriticalButton =
        target &&
        target.id &&
        (target.id === "save-jql-query-button" || // Save modal trigger
          target.id === "confirm-save-query-button" || // Save confirmation
          target.id === "update-data-unified" || // Update data
          target.id === "calculate-scope" || // Calculate scope
          target.id.includes("save") || // Any save button
          target.id.includes("update") || // Any update button
          target.id.includes("calculate") || // Any calculate button
          target.id.includes("confirm")); // Any confirm button

      if (isCriticalButton) {
        // Force sync if JQL editor exists
        if (window.forceJQLSync) {
          // PERFORMANCE FIX: Removed verbose logging
          window.forceJQLSync();

          // Extra sync for Update Data button specifically
          if (target.id === "update-data-unified") {
            setTimeout(() => {
              window.forceJQLSync();
            }, 10);
          }
        }
      }
    },
    true
  ); // Use capture phase

  // Add specific event listener for Update Data button
  function setupUpdateDataSync() {
    const updateButton = document.getElementById("update-data-unified");
    if (updateButton) {
      updateButton.addEventListener("mousedown", function (e) {
        if (window.forceJQLSync) {
          window.forceJQLSync();
        }
      });

      updateButton.addEventListener("click", function (e) {
        if (window.forceJQLSync) {
          window.forceJQLSync();
        }
      });

      // PERFORMANCE FIX: Only log in debug mode
      if (window.location.search.includes("debug=true")) {
        console.log("[JQL Editor] Update Data button sync listeners added");
      }
    }
  }

  // Set up Update Data sync when ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupUpdateDataSync);
  } else {
    setupUpdateDataSync();
  }

  // Test sync function (simplified logging)
  window.testJQLEditorSync = function (
    testValue = "project = SYNCTEST",
    editorId = "jira-jql-query"
  ) {
    const textarea = document.getElementById(editorId);
    const editor = textarea && textarea._cmEditor;

    if (!editor) {
      console.log("❌ Editor not ready for sync test");
      return false;
    }

    console.log("🧪 Testing JQL Editor sync");

    // Test CodeMirror → Textarea
    editor.setValue(testValue);

    setTimeout(() => {
      console.log(
        "  ✅ CodeMirror → Textarea sync:",
        textarea.value === testValue ? "WORKS" : "FAILED"
      );

      // Test Textarea → CodeMirror
      const reverseTest = testValue + " REVERSE";
      textarea.value = reverseTest;
      textarea.dispatchEvent(new Event("input", { bubbles: true }));

      setTimeout(() => {
        console.log(
          "  ✅ Textarea → CodeMirror sync:",
          editor.getValue() === reverseTest ? "WORKS" : "FAILED"
        );
      }, 100);
    }, 100);
  };
})();
