window._nsa = window._nsa || {};

window._nsa.watchMetadataStore = function () {
  var metadataStore = document.getElementById('jira-metadata-store');
  if (!metadataStore || metadataStore.dataset.watching) return;

  metadataStore.dataset.watching = 'true';

  window._nsa.tryBuildFromMetadata();

  var storeObserver = new MutationObserver(function () {
    window._nsa.tryBuildFromMetadata();
  });

  storeObserver.observe(metadataStore, {
    childList: true,
    characterData: true,
    subtree: true,
  });

  console.log('[Autocomplete] Watching metadata store for changes');
};

window._nsa.tryBuildFromMetadata = function () {
  if (
    window._namespaceAutocompleteData &&
    window._namespaceAutocompleteData.fields &&
    window._namespaceAutocompleteData.fields.length > 0
  ) {
    return;
  }

  var metadataStore = document.getElementById('jira-metadata-store');
  if (!metadataStore) return;

  try {
    var rawData = metadataStore.textContent || metadataStore.innerText;
    if (rawData && rawData.trim() && rawData !== 'null') {
      var metadata = JSON.parse(rawData);
      if (metadata && !metadata.error && metadata.fields) {
        window.dash_clientside.namespace_autocomplete.buildAutocompleteData(metadata);
        console.log('[Autocomplete] Built data from metadata store on change');
      }
    }
  } catch (e) {
    void e;
  }
};

window._nsa.updateSuggestions = function (inputValue, dropdown, input) {
  var autocompleteData = window._namespaceAutocompleteData;

  if (!autocompleteData || !autocompleteData.fields || autocompleteData.fields.length === 0) {
    var metadataStore = document.getElementById('jira-metadata-store');
    if (metadataStore) {
      try {
        var rawData = metadataStore.textContent || metadataStore.innerText;
        if (rawData && rawData.trim()) {
          var metadata = JSON.parse(rawData);
          if (metadata && !metadata.error) {
            autocompleteData =
              window.dash_clientside.namespace_autocomplete.buildAutocompleteData(metadata);
            console.log('[Autocomplete] Built data from metadata store');
          }
        }
      } catch (_e) {
        console.log('[Autocomplete] Could not parse metadata store:', _e.message);
      }
    }
  }

  if (!autocompleteData || !autocompleteData.fields || autocompleteData.fields.length === 0) {
    console.log('[Autocomplete] No autocomplete data available yet');
    return;
  }

  var suggestions = window._nsa.filterSuggestions(inputValue, autocompleteData);
  dropdown.innerHTML = window._nsa.renderSuggestionsHtml(suggestions);
  window._nsa.positionDropdown(dropdown, input);
};

window._nsa.positionDropdown = function (dropdown, input) {
  if (!dropdown || !input) return;

  if (!dropdown.innerHTML || !dropdown.innerHTML.trim()) {
    if (dropdown.parentElement !== input.parentElement) {
      input.parentElement.appendChild(dropdown);
    }
    return;
  }

  if (dropdown.parentElement !== document.body) {
    document.body.appendChild(dropdown);
  }

  var rect = input.getBoundingClientRect();
  dropdown.style.position = 'fixed';
  dropdown.style.top = rect.bottom + 2 + 'px';
  dropdown.style.left = rect.left + 'px';
  dropdown.style.width = rect.width + 'px';
  dropdown.style.zIndex = '1200';
};

window._nsa.hideDropdown = function (dropdown, input) {
  if (!dropdown || !input) return;
  dropdown.innerHTML = '';
  if (dropdown.parentElement === document.body) {
    input.parentElement.appendChild(dropdown);
  }
};

window._nsa.updateSelection = function (items, selectedIndex) {
  items.forEach(function (item, idx) {
    if (idx === selectedIndex) {
      item.classList.add('active');
      item.scrollIntoView({ block: 'nearest' });
    } else {
      item.classList.remove('active');
    }
  });
};

window._nsa.selectItem = function (input, item, dropdown) {
  var value = item.dataset.value;
  if (!value) return;

  console.log('[Autocomplete] Selecting:', value, 'current input:', input.value);
  input.dataset.programmaticUpdate = 'true';
  window._nsa.hideDropdown(dropdown, input);

  try {
    var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype,
      'value'
    ).set;

    nativeInputValueSetter.call(input, value);

    input.dispatchEvent(
      new InputEvent('input', {
        bubbles: true,
        cancelable: true,
        inputType: 'insertText',
        data: value,
      })
    );
    input.dispatchEvent(new Event('change', { bubbles: true }));

    input.blur();

    setTimeout(function () {
      input.dataset.programmaticUpdate = 'true';
      nativeInputValueSetter.call(input, value);
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.focus();
      input.setSelectionRange(value.length, value.length);
      console.log('[Autocomplete] Selection complete, value:', input.value);
      setTimeout(function () {
        delete input.dataset.programmaticUpdate;
      }, 100);
    }, 10);
  } catch (_e) {
    console.warn('[Autocomplete] Event dispatch failed:', _e);
    input.value = value;
    delete input.dataset.programmaticUpdate;
  }

  setTimeout(function () {
    if (!input.id) return;
    try {
      var idObj = JSON.parse(input.id);
      if (idObj.metric && idObj.field) {
        var validationContainer = document.getElementById(
          'validation-' + idObj.metric + '-' + idObj.field
        );
        if (validationContainer && window._namespaceAutocompleteData) {
          validationContainer.innerHTML = window._nsa.validateInput(
            value,
            window._namespaceAutocompleteData,
            idObj.metric,
            idObj.field
          );
        }
      }
    } catch (e) {
      void e;
    }
  }, 50);

  input.focus();
};

window._nsa.initContainer = function (container) {
  if (container.dataset.initialized) return;
  container.dataset.initialized = 'true';

  var input = container.querySelector('input');
  var dropdown = container.querySelector('.namespace-suggestions-dropdown');
  if (!input || !dropdown) return;

  var validationContainer = null;
  try {
    var idObj = JSON.parse(input.id);
    if (idObj.type === 'namespace-field-input') {
      var validationId = JSON.stringify({
        field: idObj.field,
        metric: idObj.metric,
        type: 'field-validation-message',
      });
      validationContainer = document.querySelector("[id='" + validationId + "']");
      console.log(
        '[Autocomplete] Looking for validation container:',
        validationId,
        'found:',
        !!validationContainer
      );
    }
  } catch (_e) {
    console.log('[Autocomplete] Error finding validation container:', _e);
  }

  var selectedIndex = -1;
  var validationTimeout = null;

  function runValidation() {
    if (validationTimeout) clearTimeout(validationTimeout);
    validationTimeout = setTimeout(function () {
      if (validationContainer && window._namespaceAutocompleteData) {
        try {
          var _idObj = JSON.parse(input.id);
          validationContainer.innerHTML = window._nsa.validateInput(
            input.value,
            window._namespaceAutocompleteData,
            _idObj.metric,
            _idObj.field
          );
        } catch (_e) {
          console.log('[Autocomplete] Validation error:', _e);
        }
      }
    }, 300);
  }

  input.addEventListener('input', function () {
    if (input.dataset.programmaticUpdate === 'true') {
      console.log('[Autocomplete] Skipping update - programmatic change');
      return;
    }
    selectedIndex = -1;
    window._nsa.updateSuggestions(input.value, dropdown, input);
    runValidation();

    var statusDiv = document.getElementById('field-mapping-status');
    if (statusDiv && statusDiv.innerHTML.trim()) {
      statusDiv.innerHTML = '';
      console.log('[Autocomplete] Cleared validation status on input');
    }
    input.classList.remove('is-invalid');
    var errorEl = input.parentElement.querySelector('.invalid-feedback');
    if (errorEl) {
      errorEl.style.display = 'none';
      errorEl.textContent = '';
    }
  });

  input.addEventListener('blur', function () {
    if (validationTimeout) clearTimeout(validationTimeout);
    if (validationContainer && window._namespaceAutocompleteData) {
      try {
        var _idObj = JSON.parse(input.id);
        validationContainer.innerHTML = window._nsa.validateInput(
          input.value,
          window._namespaceAutocompleteData,
          _idObj.metric,
          _idObj.field
        );
      } catch (_e) {
        console.log('[Autocomplete] Validation error on blur:', _e);
      }
    }

    var timeSinceSelection = input._selectionTimestamp
      ? Date.now() - input._selectionTimestamp
      : Infinity;
    if (input._lastSelectedValue && timeSinceSelection < 500) {
      setTimeout(function () {
        if (
          input.value !== input._lastSelectedValue &&
          Date.now() - input._selectionTimestamp < 1000
        ) {
          console.log(
            '[Autocomplete] Restoring reverted value:',
            input._lastSelectedValue,
            'current:',
            input.value
          );
          var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype,
            'value'
          ).set;
          nativeInputValueSetter.call(input, input._lastSelectedValue);
          input.dispatchEvent(new Event('input', { bubbles: true }));
        }
      }, 50);
    }

    setTimeout(function () {
      if (!container.contains(document.activeElement)) {
        window._nsa.hideDropdown(dropdown, input);
        selectedIndex = -1;
      }
    }, 200);
  });

  if (input.value && input.value.trim()) {
    setTimeout(runValidation, 500);
  }

  input.addEventListener('keydown', function (e) {
    var items = dropdown.querySelectorAll('.list-group-item');
    if (items.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
      window._nsa.updateSelection(items, selectedIndex);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedIndex = Math.max(selectedIndex - 1, 0);
      window._nsa.updateSelection(items, selectedIndex);
    } else if (e.key === 'Enter' || e.key === 'Tab') {
      if (selectedIndex >= 0 && selectedIndex < items.length) {
        e.preventDefault();
        window._nsa.selectItem(input, items[selectedIndex], dropdown);
        input._lastSelectedValue = items[selectedIndex].dataset.value;
        input._selectionTimestamp = Date.now();
      }
    } else if (e.key === 'Escape') {
      window._nsa.hideDropdown(dropdown, input);
      selectedIndex = -1;
    }
  });

  dropdown.removeEventListener('click', dropdown._nsaClickHandler);
  dropdown._nsaClickHandler = function (e) {
    var item = e.target.closest('.list-group-item');
    if (item) {
      e.preventDefault();
      input._lastSelectedValue = item.dataset.value;
      input._selectionTimestamp = Date.now();
      window._nsa.selectItem(input, item, dropdown);
    }
  };
  dropdown.addEventListener('click', dropdown._nsaClickHandler);

  dropdown.addEventListener('mousedown', function (e) {
    e.preventDefault();
  });

  setInterval(function () {
    if (input._selectionTimestamp && Date.now() - input._selectionTimestamp > 2000) {
      input._lastSelectedValue = null;
    }
  }, 1000);

  input.addEventListener('focus', function () {
    if (input.dataset.programmaticUpdate === 'true') {
      console.log('[Autocomplete] Skipping focus suggestions - programmatic update');
      return;
    }
    if (input.value.trim().length > 0) {
      window._nsa.updateSuggestions(input.value, dropdown, input);
    }
  });

  var repositionDropdown = function () {
    if (
      dropdown.innerHTML &&
      dropdown.innerHTML.trim() &&
      dropdown.parentElement === document.body
    ) {
      window._nsa.positionDropdown(dropdown, input);
    }
  };
  window.addEventListener('scroll', repositionDropdown, true);
  window.addEventListener('resize', repositionDropdown);

  console.log('[Autocomplete] Initialized container for:', input.id);
};

window._nsa.initAll = function () {
  document.querySelectorAll('.namespace-input-container').forEach(function (container) {
    window._nsa.initContainer(container);
  });
};

document.addEventListener('DOMContentLoaded', function () {
  window._nsa.initAll();
  window._nsa.watchMetadataStore();
});

window._nsa.observer = new MutationObserver(function (mutations) {
  mutations.forEach(function (mutation) {
    if (mutation.addedNodes.length) {
      window._nsa.initAll();
      window._nsa.watchMetadataStore();
    }
  });
});

window._nsa.observer.observe(document.body, { childList: true, subtree: true });
