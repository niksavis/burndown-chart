/**
 * Namespace Autocomplete - IDE-style autocomplete for namespace syntax inputs
 *
 * Features:
 * - Shows suggestions as you type (no focus loss)
 * - Arrow keys to navigate
 * - Enter/Tab to select
 * - Click to select
 * - Escape to dismiss
 */

(function () {
  "use strict";

  // Track active autocomplete state per input
  const autocompleteState = new Map();

  /**
   * Initialize autocomplete for a namespace input field
   */
  function initAutocomplete(input) {
    if (!input || input.dataset.autocompleteInit) return;
    input.dataset.autocompleteInit = "true";

    const inputId = JSON.parse(input.id);
    const metric = inputId.metric;
    const field = inputId.field;

    // Find the suggestions container
    const suggestionsId = JSON.stringify({
      type: "namespace-suggestions",
      metric: metric,
      field: field,
    });
    const suggestionsContainer = document.querySelector(
      `[id='${suggestionsId}']`
    );

    if (!suggestionsContainer) {
      console.warn("Suggestions container not found for", inputId);
      return;
    }

    // Initialize state
    autocompleteState.set(input.id, {
      selectedIndex: -1,
      suggestions: [],
      visible: false,
    });

    // Handle input events
    input.addEventListener("input", (e) => {
      // Suggestions will be populated by Dash callback
      // We just need to handle navigation/selection
      resetSelection(input);
    });

    // Handle keydown for navigation
    input.addEventListener("keydown", (e) => {
      const state = autocompleteState.get(input.id);
      const items = suggestionsContainer.querySelectorAll(".list-group-item");

      if (items.length === 0) return;

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          state.selectedIndex = Math.min(
            state.selectedIndex + 1,
            items.length - 1
          );
          updateHighlight(items, state.selectedIndex);
          break;

        case "ArrowUp":
          e.preventDefault();
          state.selectedIndex = Math.max(state.selectedIndex - 1, 0);
          updateHighlight(items, state.selectedIndex);
          break;

        case "Enter":
        case "Tab":
          if (state.selectedIndex >= 0 && state.selectedIndex < items.length) {
            e.preventDefault();
            selectItem(input, items[state.selectedIndex], suggestionsContainer);
          }
          break;

        case "Escape":
          e.preventDefault();
          hideSuggestions(suggestionsContainer);
          state.selectedIndex = -1;
          break;
      }
    });

    // Handle click on suggestions
    suggestionsContainer.addEventListener("click", (e) => {
      const item = e.target.closest(".list-group-item");
      if (item) {
        e.preventDefault();
        e.stopPropagation();
        selectItem(input, item, suggestionsContainer);
      }
    });

    // Prevent blur when clicking suggestions
    suggestionsContainer.addEventListener("mousedown", (e) => {
      e.preventDefault(); // Prevent input from losing focus
    });
  }

  /**
   * Update visual highlight on suggestion items
   */
  function updateHighlight(items, selectedIndex) {
    items.forEach((item, idx) => {
      if (idx === selectedIndex) {
        item.classList.add("active");
        item.scrollIntoView({ block: "nearest" });
      } else {
        item.classList.remove("active");
      }
    });
  }

  /**
   * Reset selection state
   */
  function resetSelection(input) {
    const state = autocompleteState.get(input.id);
    if (state) {
      state.selectedIndex = -1;
    }
  }

  /**
   * Select an item and populate the input
   */
  function selectItem(input, item, suggestionsContainer) {
    // Find the hidden value div (sibling of the list item)
    const wrapper = item.closest("div");
    const valueDiv = wrapper
      ? wrapper.querySelector('[id*="namespace-suggestion-value"]')
      : null;

    if (valueDiv) {
      const value = valueDiv.textContent;
      input.value = value;

      // Trigger Dash callback by dispatching input event
      input.dispatchEvent(new Event("input", { bubbles: true }));

      // Also trigger change for debounced inputs
      input.dispatchEvent(new Event("change", { bubbles: true }));

      console.log("[Autocomplete] Selected:", value);
    }

    // Hide suggestions
    hideSuggestions(suggestionsContainer);

    // Keep focus on input
    input.focus();
  }

  /**
   * Hide suggestions dropdown
   */
  function hideSuggestions(container) {
    container.innerHTML = "";
  }

  /**
   * Observer to detect when new namespace inputs are added to the DOM
   */
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE) {
          // Find all namespace inputs in the added node
          const inputs = node.querySelectorAll
            ? node.querySelectorAll('input[id*="namespace-field-input"]')
            : [];
          inputs.forEach(initAutocomplete);

          // Also check if the node itself is an input
          if (
            node.matches &&
            node.matches('input[id*="namespace-field-input"]')
          ) {
            initAutocomplete(node);
          }
        }
      });
    });
  });

  // Start observing
  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });

  // Initialize existing inputs on page load
  document.addEventListener("DOMContentLoaded", () => {
    document
      .querySelectorAll('input[id*="namespace-field-input"]')
      .forEach(initAutocomplete);
  });

  // Re-initialize when modal opens (Dash dynamic content)
  window.initNamespaceAutocomplete = function () {
    document
      .querySelectorAll('input[id*="namespace-field-input"]')
      .forEach(initAutocomplete);
  };
})();
