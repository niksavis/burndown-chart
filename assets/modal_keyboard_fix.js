/**
 * Modal keyboard event handler fix
 *
 * 1. Prevents ESC key from closing modals with backdrop="static"
 * 2. Prevents SPACE key from activating buttons when focus is not on inputs
 * 3. Auto-focuses the first input when modal opens
 */

(function () {
  "use strict";

  console.log("[Modal Fix] Script loaded");

  // Wait for DOM to be ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initModalKeyboardFix);
  } else {
    initModalKeyboardFix();
  }

  function initModalKeyboardFix() {
    console.log("[Modal Fix] Initializing modal keyboard handling");

    // Prevent ESC and SPACE from causing modal issues
    document.addEventListener(
      "keydown",
      function (e) {
        // Find all open modals with static backdrop
        const staticModals = document.querySelectorAll(
          '.modal.show[data-bs-backdrop="static"]'
        );

        if (staticModals.length === 0) return;

        // Prevent ESC from closing static backdrop modals
        if (e.key === "Escape" || e.key === "Esc") {
          console.log(
            "[Modal Fix] Preventing ESC key from closing static backdrop modal"
          );
          e.preventDefault();
          e.stopPropagation();
          e.stopImmediatePropagation();
          return false;
        }

        // Prevent SPACE from activating buttons when not in an input
        if (e.key === " " || e.code === "Space") {
          const activeElement = document.activeElement;
          const isInput =
            activeElement &&
            (activeElement.tagName === "INPUT" ||
              activeElement.tagName === "TEXTAREA" ||
              activeElement.tagName === "SELECT" ||
              activeElement.isContentEditable);

          // If not in an input field and SPACE is pressed, check if on a button
          if (!isInput && activeElement && activeElement.tagName === "BUTTON") {
            console.log(
              "[Modal Fix] Preventing SPACE key from clicking button"
            );
            e.preventDefault();
            e.stopPropagation();
            return false;
          }
        }
      },
      true
    ); // Use capture phase to intercept early

    // Auto-focus first input when modal opens
    const observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        if (
          mutation.type === "attributes" &&
          mutation.attributeName === "class"
        ) {
          const modal = mutation.target;
          if (
            modal.classList.contains("modal") &&
            modal.classList.contains("show")
          ) {
            // Modal just opened - focus first input after a short delay
            setTimeout(function () {
              const firstInput = modal.querySelector(
                'input:not([type="hidden"]), textarea'
              );
              if (firstInput) {
                firstInput.focus();
                console.log("[Modal Fix] Auto-focused first input in modal");
              }
            }, 100);
          }
        }
      });
    });

    // Observe all modals for class changes
    document.querySelectorAll(".modal").forEach(function (modal) {
      observer.observe(modal, { attributes: true, attributeFilter: ["class"] });
    });

    // Also observe document body for dynamically added modals
    const bodyObserver = new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        mutation.addedNodes.forEach(function (node) {
          if (
            node.nodeType === 1 &&
            node.classList &&
            node.classList.contains("modal")
          ) {
            observer.observe(node, {
              attributes: true,
              attributeFilter: ["class"],
            });
          }
        });
      });
    });
    bodyObserver.observe(document.body, { childList: true, subtree: true });

    console.log("[Modal Fix] Keyboard handling initialized");
  }
})();
