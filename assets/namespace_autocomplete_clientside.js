/**
 * Namespace Autocomplete - Dash Clientside Callbacks
 *
 * Thin orchestrator: registers 5 methods on window.dash_clientside.namespace_autocomplete
 * and delegates to window._nsa.* helpers defined in:
 *   namespace_autocomplete_data.js       (buildDataset, filterSuggestions, ...)
 *   namespace_autocomplete_validation.js (validateInput, isValidForSave)
 *   namespace_autocomplete_rendering.js  (initAll, watchMetadataStore, ...)
 */

window.dash_clientside = window.dash_clientside || {};

window.dash_clientside.namespace_autocomplete = {
  /**
   * Build autocomplete dataset from JIRA metadata.
   * Called once when the modal opens; stores result globally for all inputs.
   *
   * Input: jira-metadata-store data
   * Output: namespace-autocomplete-data store
   */
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

  /**
   * Validate a namespace input and return validation HTML.
   * Called when a namespace input value changes.
   *
   * Input: input value, autocomplete data, metric, field
   * Output: Validation message HTML string
   */
  validateNamespaceInput: function (inputValue, autocompleteData, metric, field) {
    return window._nsa.validateInput(inputValue, autocompleteData, metric, field);
  },

  /**
   * Strict validation for save - returns an error string or null.
   *
   * Input: namespace value string, autocomplete data
   * Output: error string | null
   */
  isValidForSave: function (value, autocompleteData) {
    return window._nsa.isValidForSave(value, autocompleteData);
  },

  /**
   * Collect all namespace input values from the DOM.
   * Called when save/validate is clicked or when switching tabs.
   *
   * Since we use dcc.Input with DOM manipulation for autocomplete,
   * this function reads directly from the DOM to get the actual values
   * (including those set by autocomplete selection).
   *
   * Input: n_clicks from save button, n_clicks from validate button, active_tab string
   * Output: {trigger: "save"|"validate"|"tab_switch", values: {...}, validationErrors: [...]}
   */
  collectNamespaceValues: function (_saveClicks, _validateClicks, _activeTab) {
    // Determine which input triggered this callback
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

    // For tab switches, only collect if we're leaving the Fields tab
    // (inputs must exist in DOM to be collected)
    const inputs = document.querySelectorAll('.namespace-input-container input[type="text"]');

    // If no namespace inputs found (not on Fields tab or modal closed)
    // - For tab switches: skip (nothing to preserve)
    // - For save/validate: continue with empty values (validate other tabs)
    if (inputs.length === 0) {
      if (trigger === 'tab_switch') {
        console.log('[Autocomplete] No namespace inputs found, skipping tab switch collection');
        return window.dash_clientside.no_update;
      }
      // For save/validate, continue with empty field values
      // so other tabs (Status, Project, Issue Types) can still be validated
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
        // Parse the Dash pattern-matched ID
        const idStr = input.id;
        const idObj = JSON.parse(idStr);

        if (idObj.type === 'namespace-field-input') {
          const metric = idObj.metric;
          const field = idObj.field;
          const value = input.value ? input.value.trim() : '';

          if (value) {
            // Only validate on save or validate triggers (not tab switches)
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
                // Highlight the invalid input
                input.classList.add('is-invalid');
                // Find or create error message element
                let errorEl = input.parentElement.querySelector('.invalid-feedback');
                if (!errorEl) {
                  errorEl = document.createElement('div');
                  errorEl.className = 'invalid-feedback';
                  input.parentElement.appendChild(errorEl);
                }
                errorEl.textContent = error;
                errorEl.style.display = 'block';
              } else {
                // Valid - remove any error styling
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
        // Skip inputs with non-JSON IDs
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

  /**
   * Filter suggestions based on input value.
   * Pure client-side filtering - instant response with no server round-trips.
   *
   * Input: input value, autocomplete data, trigger count
   * Output: filtered suggestions HTML string
   */
  filterSuggestions: function (inputValue, autocompleteData, triggerCount) {
    void triggerCount;
    if (!inputValue || !autocompleteData || !autocompleteData.fields) {
      return '';
    }
    var suggestions = window._nsa.filterSuggestions(inputValue, autocompleteData);
    return window._nsa.renderSuggestionsHtml(suggestions);
  },
};
