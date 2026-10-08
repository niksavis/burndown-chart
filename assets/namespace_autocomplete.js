(function () {
  'use strict';

  const autocompleteState = new Map();

  function initAutocomplete(input) {
    if (!input || input.dataset.autocompleteInit) return;
    input.dataset.autocompleteInit = 'true';

    const inputId = JSON.parse(input.id);
    const metric = inputId.metric;
    const field = inputId.field;

    const suggestionsId = JSON.stringify({
      type: 'namespace-suggestions',
      metric: metric,
      field: field,
    });
    const suggestionsContainer = document.querySelector(`[id='${suggestionsId}']`);

    if (!suggestionsContainer) {
      console.warn('Suggestions container not found for', inputId);
      return;
    }

    autocompleteState.set(input.id, {
      selectedIndex: -1,
      suggestions: [],
      visible: false,
    });

    input.addEventListener('input', (_e) => {
      resetSelection(input);
    });

    input.addEventListener('keydown', (e) => {
      const state = autocompleteState.get(input.id);
      const items = suggestionsContainer.querySelectorAll('.list-group-item');

      if (items.length === 0) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          state.selectedIndex = Math.min(state.selectedIndex + 1, items.length - 1);
          updateHighlight(items, state.selectedIndex);
          break;

        case 'ArrowUp':
          e.preventDefault();
          state.selectedIndex = Math.max(state.selectedIndex - 1, 0);
          updateHighlight(items, state.selectedIndex);
          break;

        case 'Enter':
        case 'Tab':
          if (state.selectedIndex >= 0 && state.selectedIndex < items.length) {
            e.preventDefault();
            selectItem(input, items[state.selectedIndex], suggestionsContainer);
          }
          break;

        case 'Escape':
          e.preventDefault();
          hideSuggestions(suggestionsContainer);
          state.selectedIndex = -1;
          break;
      }
    });

    suggestionsContainer.addEventListener('click', (e) => {
      const item = e.target.closest('.list-group-item');
      if (item) {
        e.preventDefault();
        e.stopPropagation();
        selectItem(input, item, suggestionsContainer);
      }
    });

    suggestionsContainer.addEventListener('mousedown', (e) => {
      e.preventDefault();
    });
  }

  function updateHighlight(items, selectedIndex) {
    items.forEach((item, idx) => {
      if (idx === selectedIndex) {
        item.classList.add('active');
        item.scrollIntoView({ block: 'nearest' });
      } else {
        item.classList.remove('active');
      }
    });
  }

  function resetSelection(input) {
    const state = autocompleteState.get(input.id);
    if (state) {
      state.selectedIndex = -1;
    }
  }

  function selectItem(input, item, suggestionsContainer) {
    const wrapper = item.closest('div');
    const valueDiv = wrapper ? wrapper.querySelector('[id*="namespace-suggestion-value"]') : null;

    if (valueDiv) {
      const value = valueDiv.textContent;
      input.value = value;

      input.dispatchEvent(new Event('input', { bubbles: true }));

      input.dispatchEvent(new Event('change', { bubbles: true }));

      console.log('[Autocomplete] Selected:', value);
    }

    hideSuggestions(suggestionsContainer);

    input.focus();
  }

  function hideSuggestions(container) {
    container.innerHTML = '';
  }

  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE) {
          const inputs = node.querySelectorAll
            ? node.querySelectorAll('input[id*="namespace-field-input"]')
            : [];
          inputs.forEach(initAutocomplete);

          if (node.matches && node.matches('input[id*="namespace-field-input"]')) {
            initAutocomplete(node);
          }
        }
      });
    });
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('input[id*="namespace-field-input"]').forEach(initAutocomplete);
  });

  window.initNamespaceAutocomplete = function () {
    document.querySelectorAll('input[id*="namespace-field-input"]').forEach(initAutocomplete);
  };
})();
