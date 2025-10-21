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
    console.log(`[JQL Editor] Found ${textareas.length} textarea(s)`);

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
        console.log(
          "[JQL Editor] Skipping textarea with existing CodeMirror:",
          textarea.id
        );
        initializedTextareas.add(textarea);
        return;
      }

      console.log(
        "[JQL Editor] Initializing CodeMirror for textarea:",
        textarea.id
      );

      try {
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

        // Mark as initialized
        initializedTextareas.add(textarea);

        // Store reference for potential future access
        textarea._cmEditor = editor;

        // AGGRESSIVE APPROACH: Override textarea's value property to always sync
        let originalValue = textarea.value;
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
                console.log(
                  "[JQL Editor] Value getter - returning CodeMirror value:",
                  cmValue.substring(0, 30)
                );
                return cmValue;
              }
            }
            return originalValue;
          },
          set: function (val) {
            console.log(
              "[JQL Editor] Value setter - setting both textarea and CodeMirror:",
              val.substring(0, 30)
            );
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
            const oldValue = textarea._originalValue;
            const newValue = editor.getValue();
            console.log(
              `[JQL Editor] Force sync - old: "${oldValue.substring(
                0,
                30
              )}" new: "${newValue.substring(0, 30)}"`
            );
            syncCodeMirrorToTextarea();
            console.log("[JQL Editor] Forced sync completed");
            return editor.getValue();
          };

          // Enhanced debug function to check all values
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

        // CRITICAL: Ensure bidirectional sync between CodeMirror and textarea
        // This is essential for Dash callbacks to work properly

        // 1. CodeMirror → Textarea sync (when user types in CodeMirror)
        const syncCodeMirrorToTextarea = function () {
          const value = editor.getValue();
          const oldValue = textarea._originalValue;

          if (oldValue !== value) {
            console.log(
              "[JQL Editor] Syncing CodeMirror to textarea:",
              `"${oldValue.substring(0, 30)}" → "${value.substring(0, 30)}"`
            );

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

            console.log("[JQL Editor] Sync completed - events dispatched");
          } else {
            console.log("[JQL Editor] Values already synced, no update needed");
          }
        };

        editor.on("change", function (cm) {
          // Immediate sync on every change
          syncCodeMirrorToTextarea();

          // Also set a flag to force sync before any potential callback
          textarea._pendingSync = true;

          // Clear the flag after a short delay
          setTimeout(() => {
            textarea._pendingSync = false;
          }, 100);
        });

        // CRITICAL: Force sync when focus leaves CodeMirror (before callbacks fire)
        editor.on("blur", function (cm) {
          console.log("[JQL Editor] CodeMirror blur - forcing sync");
          syncCodeMirrorToTextarea();
        });

        // Also sync on key events that might trigger callbacks
        editor.on("keydown", function (cm, event) {
          // Force sync on Enter key (common trigger for forms)
          if (event.key === "Enter" || event.keyCode === 13) {
            setTimeout(syncCodeMirrorToTextarea, 10); // Small delay to let CodeMirror update
          }
        });

        // 2. Textarea → CodeMirror sync (when Dash updates textarea programmatically)
        const syncTextareaToCodeMirror = function () {
          const textareaValue = textarea.value || "";
          const editorValue = editor.getValue() || "";

          if (textareaValue !== editorValue) {
            console.log(
              "[JQL Editor] Syncing textarea to CodeMirror:",
              textareaValue.substring(0, 50)
            );
            // Use setValue without triggering change event to avoid infinite loop
            editor.setValue(textareaValue);
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
        let lastKnownValue = textarea.value || "";
        const pollInterval = setInterval(function () {
          const currentValue = textarea.value || "";
          if (currentValue !== lastKnownValue) {
            lastKnownValue = currentValue;
            syncTextareaToCodeMirror();
          }
        }, 200); // Poll every 200ms

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

        // Set initial sync
        syncTextareaToCodeMirror();

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
                console.log(
                  `[JQL Editor] ${buttonId} clicked - forcing immediate sync`
                );
                // Force sync immediately and synchronously
                syncCodeMirrorToTextarea();

                // Also force a second sync after a tiny delay to handle any race conditions
                setTimeout(() => {
                  syncCodeMirrorToTextarea();
                  console.log(
                    `[JQL Editor] ${buttonId} - secondary sync completed`
                  );
                }, 1);
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
                        console.log(
                          `[JQL Editor] ${buttonId} clicked (dynamic) - forcing sync`
                        );
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

        console.log("[JQL Editor] Successfully initialized:", textarea.id);
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
        console.log("[JQL Editor] DOM changed, re-initializing editors");
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
          console.log(
            `[JQL Editor] Critical button ${target.id} clicked - forcing global sync`
          );
          const currentValue = window.forceJQLSync();
          console.log(
            `[JQL Editor] Synced value: "${currentValue.substring(0, 50)}..."`
          );

          // Extra aggressive sync for Update Data button specifically
          if (target.id === "update-data-unified") {
            console.log(
              "[JQL Editor] Update Data clicked - performing extra sync"
            );

            // Force immediate sync one more time after a tiny delay
            setTimeout(() => {
              const doubleCheckValue = window.forceJQLSync();
              console.log(
                `[JQL Editor] Update Data double-check sync: "${doubleCheckValue.substring(
                  0,
                  50
                )}..."`
              );
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
        console.log("[JQL Editor] Update Data mousedown - pre-emptive sync");
        if (window.forceJQLSync) {
          const syncValue = window.forceJQLSync();
          console.log(
            `[JQL Editor] Pre-click sync value: "${syncValue.substring(
              0,
              50
            )}..."`
          );
        }
      });

      updateButton.addEventListener("click", function (e) {
        console.log("[JQL Editor] Update Data click - immediate sync");
        if (window.forceJQLSync) {
          const syncValue = window.forceJQLSync();
          console.log(
            `[JQL Editor] Click sync value: "${syncValue.substring(0, 50)}..."`
          );
        }
      });

      console.log("[JQL Editor] Update Data button sync listeners added");
    }
  }

  // Set up Update Data sync when ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupUpdateDataSync);
  } else {
    setupUpdateDataSync();
  }

  // Test sync function
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

    console.log("🧪 Testing JQL Editor sync with value:", testValue);

    // Test CodeMirror → Textarea
    console.log("  Setting CodeMirror value...");
    editor.setValue(testValue);

    setTimeout(() => {
      console.log("  Textarea value after CodeMirror update:", textarea.value);
      console.log(
        "  ✅ CodeMirror → Textarea sync:",
        textarea.value === testValue ? "WORKS" : "FAILED"
      );

      // Test Textarea → CodeMirror
      const reverseTest = testValue + " REVERSE";
      console.log("  Setting textarea value to:", reverseTest);
      textarea.value = reverseTest;
      textarea.dispatchEvent(new Event("input", { bubbles: true }));

      setTimeout(() => {
        console.log(
          "  CodeMirror value after textarea update:",
          editor.getValue()
        );
        console.log(
          "  ✅ Textarea → CodeMirror sync:",
          editor.getValue() === reverseTest ? "WORKS" : "FAILED"
        );
      }, 100);
    }, 100);
  };
})();
