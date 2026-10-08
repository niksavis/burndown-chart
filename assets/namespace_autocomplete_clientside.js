window.dash_clientside = window.dash_clientside || {};

window.dash_clientside.namespace_autocomplete = {
  buildAutocompleteData: function (metadata) {
    console.log('[Autocomplete] buildAutocompleteData CALLED with:', metadata ? 'data' : 'null');

    if (!metadata || metadata.error) {
      console.log('[Autocomplete] No metadata or error, returning empty');
      window._namespaceAutocompleteData = { fields: [], projects: [], statuses: [] };
      return window._namespaceAutocompleteData;
    }

    var result = window._nsa.buildDataset(metadata);
    window._namespaceAutocompleteData = result;

    console.log(
      '[Autocomplete] Built dataset:',
      result.fields.length,
      'fields,',
      result.projects.length,
      'projects,',
      result.statuses.length,
      'statuses'
    );

    return result;
  },

  validateNamespaceInput: function (inputValue, autocompleteData, metric, field) {
    return window._nsa.validateInput(inputValue, autocompleteData, metric, field);
  },

  isValidForSave: function (value, autocompleteData) {
    return window._nsa.isValidForSave(value, autocompleteData);
  },

  collectNamespaceValues: function (_saveClicks, _validateClicks, _activeTab) {
    const ctx = window.dash_clientside.callback_context;
    let trigger = 'unknown';
    if (ctx && ctx.triggered && ctx.triggered.length > 0) {
      const triggeredId = ctx.triggered[0].prop_id.split('.')[0];
      if (triggeredId === 'field-mapping-save-button') {
        trigger = 'save';
      } else if (triggeredId === 'validate-mappings-button') {
        trigger = 'validate';
      } else if (triggeredId === 'mappings-tabs') {
        trigger = 'tab_switch';
      }
    }

    const inputs = document.querySelectorAll('.namespace-input-container input[type="text"]');

    if (inputs.length === 0) {
      if (trigger === 'tab_switch') {
        console.log('[Autocomplete] No namespace inputs found, skipping tab switch collection');
        return window.dash_clientside.no_update;
      }
      console.log(
        '[Autocomplete] No namespace inputs found, continuing with empty field values for ' +
          trigger
      );
    }

    const values = {};
    const validationErrors = [];
    const autocompleteData = window._namespaceAutocompleteData || null;

    inputs.forEach((input) => {
      try {
        const idStr = input.id;
        const idObj = JSON.parse(idStr);

        if (idObj.type === 'namespace-field-input') {
          const metric = idObj.metric;
          const field = idObj.field;
          const value = input.value ? input.value.trim() : '';

          if (value) {
            if (trigger === 'save' || trigger === 'validate') {
              const error = window.dash_clientside.namespace_autocomplete.isValidForSave(
                value,
                autocompleteData
              );
              if (error) {
                validationErrors.push({
                  metric: metric,
                  field: field,
                  value: value,
                  error: error,
                });
                input.classList.add('is-invalid');
                let errorEl = input.parentElement.querySelector('.invalid-feedback');
                if (!errorEl) {
                  errorEl = document.createElement('div');
                  errorEl.className = 'invalid-feedback';
                  input.parentElement.appendChild(errorEl);
                }
                errorEl.textContent = error;
                errorEl.style.display = 'block';
              } else {
                input.classList.remove('is-invalid');
                const errorEl = input.parentElement.querySelector('.invalid-feedback');
                if (errorEl) {
                  errorEl.style.display = 'none';
                }
              }
            }

            if (!values[metric]) {
              values[metric] = {};
            }
            values[metric][field] = value;
            console.log('[Autocomplete] Collected:', metric + '.' + field, '=', value);
          }
        }
      } catch (e) {
        void e;
      }
    });

    console.log(
      '[Autocomplete] Collected namespace values (trigger=' + trigger + '):',
      values,
      'errors:',
      validationErrors
    );

    return {
      trigger: trigger,
      values: values,
      validationErrors: validationErrors,
    };
  },

  filterSuggestions: function (inputValue, autocompleteData, triggerCount) {
    void triggerCount;
    if (!inputValue || !autocompleteData || !autocompleteData.fields) {
      return '';
    }
    var suggestions = window._nsa.filterSuggestions(inputValue, autocompleteData);
    return window._nsa.renderSuggestionsHtml(suggestions);
  },
};
