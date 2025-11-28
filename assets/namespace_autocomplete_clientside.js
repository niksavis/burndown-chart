/**
 * Namespace Autocomplete - Pure Clientside Implementation
 *
 * All data is pre-loaded into a dcc.Store when the modal opens.
 * This script filters suggestions entirely in the browser - no server round-trips.
 */

// Register clientside callbacks with Dash
if (window.dash_clientside === undefined) {
  window.dash_clientside = {};
}

window.dash_clientside.namespace_autocomplete = {
  /**
   * Build autocomplete dataset from JIRA metadata
   * Called once when modal opens, stores result for all inputs to use
   *
   * Input: jira-metadata-store data
   * Output: namespace-autocomplete-data store
   */
  buildAutocompleteData: function (metadata) {
    console.log(
      "[Autocomplete] buildAutocompleteData CALLED with:",
      metadata ? "data" : "null"
    );

    if (!metadata || metadata.error) {
      console.log("[Autocomplete] No metadata or error, returning empty");
      window._namespaceAutocompleteData = {
        fields: [],
        projects: [],
        statuses: [],
      };
      return window._namespaceAutocompleteData;
    }

    const result = {
      // Fields with type info for validation
      fields: (metadata.fields || []).map((f) => ({
        id: f.id || f.field_id || "",
        name: f.name || f.id || "",
        type: f.type || f.schema?.type || f.field_type || "unknown",
        searchText: ((f.name || "") + " " + (f.id || "")).toLowerCase(),
      })),
      // Projects for namespace prefix
      projects: (metadata.projects || []).map((p) => ({
        key: p.key || "",
        name: p.name || "",
        searchText: ((p.key || "") + " " + (p.name || "")).toLowerCase(),
      })),
      // Statuses for changelog syntax
      statuses: (metadata.statuses || []).map((s) => ({
        name: s.name || "",
        category: s.statusCategory?.name || "",
        searchText: (s.name || "").toLowerCase(),
      })),
      // Issue types
      issueTypes: (metadata.issue_types || []).map((t) => ({
        name: t.name || "",
        searchText: (t.name || "").toLowerCase(),
      })),
    };

    // Store globally for JavaScript access
    window._namespaceAutocompleteData = result;

    console.log(
      "[Autocomplete] Built dataset:",
      result.fields.length,
      "fields,",
      result.projects.length,
      "projects,",
      result.statuses.length,
      "statuses"
    );

    return result;
  },

  /**
   * Validate a namespace input and return validation HTML
   * Called when namespace input value changes
   *
   * Checks:
   * 1. Field exists in metadata
   * 2. Field type is compatible with expected usage for the metric variable
   *
   * Input: input value, autocomplete data, metric, field
   * Output: Validation message HTML string
   */
  validateNamespaceInput: function (
    inputValue,
    autocompleteData,
    metric,
    field
  ) {
    // Expected field type CATEGORIES for each metric variable
    // Using categories instead of exact types because JIRA has many type variants
    const FIELD_TYPE_CATEGORIES = {
      // DORA Metrics - datetime fields
      deployment_date: "datetime",
      code_commit_date: "datetime",
      deployed_to_production_date: "datetime",
      incident_detected_at: "datetime",
      incident_resolved_at: "datetime",
      // DORA Metrics - boolean/option fields
      deployment_successful: "option",
      change_failure: "option",
      // DORA Metrics - selection fields
      affected_environment: "option",
      target_environment: "option",
      severity_level: "option",
      // Flow Metrics
      flow_item_type: "option", // issuetype, select, etc.
      status: "option",
      work_started_date: "datetime",
      work_completed_date: "datetime",
      effort_category: "option",
      estimate: "number",
    };

    // Map JIRA field types to categories
    // This handles the many variants JIRA uses
    const TYPE_TO_CATEGORY = {
      // Datetime types
      datetime: "datetime",
      date: "datetime",
      datepicker: "datetime",
      // Option/selection types
      select: "option",
      option: "option",
      issuetype: "option",
      priority: "option",
      status: "option",
      resolution: "option",
      component: "option",
      version: "option",
      user: "option",
      project: "option",
      issuelinks: "option",
      checkbox: "option",
      radiobuttons: "option",
      cascadingselect: "option",
      multiselect: "option",
      labels: "option",
      // Number types
      number: "number",
      float: "number",
      integer: "number",
      // Text types
      string: "text",
      text: "text",
      textarea: "text",
      url: "text",
      // Array types (usually work as option)
      array: "option",
    };

    if (!inputValue || !inputValue.trim()) {
      return ""; // No input, no validation needed
    }

    if (!autocompleteData || !autocompleteData.fields) {
      return '<small class="text-muted"><i class="fas fa-info-circle me-1"></i>Loading field metadata...</small>';
    }

    const value = inputValue.trim();
    const expectedCategory = FIELD_TYPE_CATEGORIES[field] || null;

    // Check for complete changelog syntax with extractor FIRST
    // Format: field:value.DateTime or Project.field:value.DateTime
    const hasChangelogExtractor =
      value.includes(":") &&
      (value.endsWith(".DateTime") ||
        value.endsWith(".Occurred") ||
        value.endsWith(".Duration"));

    if (hasChangelogExtractor) {
      // This is valid changelog syntax that extracts datetime
      return `<small class="text-success"><i class="fas fa-check-circle me-1"></i>Changelog syntax (extracts datetime)</small>`;
    }

    // Extract field ID from namespace syntax
    // Formats: "fieldId", "PROJECT.fieldId", "*.fieldId", "Status:value.DateTime"
    let fieldId = value;
    if (value.includes(".")) {
      const parts = value.split(".");
      fieldId = parts[parts.length - 1]; // Last part is usually field ID
      // Handle special extractors
      if (
        ["DateTime", "Occurred", "FirstValue", "LastValue"].includes(fieldId)
      ) {
        fieldId = parts[parts.length - 2]; // Go one level up
      }
    }
    if (value.includes(":")) {
      // Changelog syntax - first part before colon is the field
      const colonParts = value.split(":");
      fieldId = colonParts[0];
      if (fieldId.includes(".")) {
        fieldId = fieldId.split(".").pop(); // Get field after project prefix
      }
    }

    // Find field in metadata
    const fieldInfo = autocompleteData.fields.find(
      (f) => f.id === fieldId || f.name.toLowerCase() === fieldId.toLowerCase()
    );

    if (!fieldInfo) {
      // Field not found - could be custom syntax or built-in field
      if (value.includes(":")) {
        // Changelog syntax - assume it's valid datetime extraction
        return `<small class="text-success"><i class="fas fa-check-circle me-1"></i>Changelog syntax (extracts datetime)</small>`;
      }
      // Could be a built-in field like "created", "updated", etc.
      const builtInDateFields = [
        "created",
        "updated",
        "resolutiondate",
        "duedate",
        "lastViewed",
      ];
      const builtInOptionFields = [
        "status",
        "issuetype",
        "priority",
        "resolution",
        "assignee",
        "reporter",
        "project",
      ];
      if (builtInDateFields.some((f) => fieldId.toLowerCase().includes(f))) {
        return `<small class="text-success"><i class="fas fa-check-circle me-1"></i>Built-in date field</small>`;
      }
      if (builtInOptionFields.some((f) => fieldId.toLowerCase().includes(f))) {
        return `<small class="text-success"><i class="fas fa-check-circle me-1"></i>Built-in field</small>`;
      }
      return `<small class="text-warning"><i class="fas fa-question-circle me-1"></i>Field "${fieldId}" not in metadata (may still work)</small>`;
    }

    const actualType = (fieldInfo.type || "unknown").toLowerCase();
    const actualCategory = TYPE_TO_CATEGORY[actualType] || "unknown";

    // If we don't have expected type for this field, just show info
    if (!expectedCategory) {
      return `<small class="text-info"><i class="fas fa-info-circle me-1"></i>Field: ${fieldInfo.name} (${actualType})</small>`;
    }

    // Check category match
    if (actualCategory === expectedCategory) {
      return `<small class="text-success"><i class="fas fa-check-circle me-1"></i>${fieldInfo.name} (${actualType})</small>`;
    }

    // Special case: option field for datetime requirement - suggest changelog syntax
    if (actualCategory === "option" && expectedCategory === "datetime") {
      return `<small class="text-warning"><i class="fas fa-lightbulb me-1"></i>${fieldInfo.name} is ${actualType}. Use changelog syntax: ${fieldId}:VALUE.DateTime</small>`;
    }

    // Category mismatch - warning but not error
    return `<small class="text-warning"><i class="fas fa-exclamation-triangle me-1"></i>${fieldInfo.name} is ${actualType}, expected ${expectedCategory} type</small>`;
  },

  /**
   * Check if a namespace value is complete and valid for saving.
   * Returns an error message if invalid, or null if valid.
   *
   * STRICT VALIDATION - ALL parts must be valid:
   * 1. Project prefix (if present) must exist in metadata
   * 2. Field must exist in metadata OR be a built-in field
   * 3. Changelog value (if present) must be a valid status/value from metadata
   * 4. Extractor (if present) must be one of: DateTime, Occurred, Duration, FirstValue, LastValue
   *
   * NO partial values, NO misspellings, NO arbitrary text allowed.
   */
  isValidForSave: function (value, autocompleteData) {
    if (!value || !value.trim()) {
      return null; // Empty is valid (optional field)
    }

    const trimmed = value.trim();

    // Valid extractors (case-sensitive, exact match required)
    const VALID_EXTRACTORS = [
      "DateTime",
      "Occurred",
      "Duration",
      "FirstValue",
      "LastValue",
    ];

    // Built-in JIRA fields that don't need metadata lookup
    const BUILT_IN_FIELDS = [
      "created",
      "updated",
      "resolutiondate",
      "duedate",
      "lastviewed",
      "status",
      "issuetype",
      "priority",
      "resolution",
      "assignee",
      "reporter",
      "project",
      "summary",
      "description",
      "labels",
      "components",
      "fixversions",
      "versions",
      "creator",
      "environment",
      "key",
      "id",
    ];

    // Check for obvious incomplete syntax
    if (trimmed.endsWith(":")) {
      return 'Incomplete - add a value after ":"';
    }
    if (trimmed.endsWith(".")) {
      return "Incomplete - select an extractor or field";
    }

    // Parse the namespace syntax into components
    let projectPrefix = null;
    let fieldPart = null;
    let changelogValue = null;
    let extractor = null;

    // Step 1: Check for extractor at the end (e.g., .DateTime)
    for (const ext of VALID_EXTRACTORS) {
      if (trimmed.endsWith("." + ext)) {
        extractor = ext;
        break;
      }
    }

    // Check for partial/wrong-case extractor
    const lastDotIndex = trimmed.lastIndexOf(".");
    if (lastDotIndex > 0 && !extractor) {
      const lastPart = trimmed.substring(lastDotIndex + 1);
      for (const ext of VALID_EXTRACTORS) {
        // Wrong case
        if (lastPart.toLowerCase() === ext.toLowerCase() && lastPart !== ext) {
          return `Extractor must be exactly ".${ext}" (case-sensitive)`;
        }
        // Partial match
        if (
          ext.toLowerCase().startsWith(lastPart.toLowerCase()) &&
          lastPart.length > 0 &&
          lastPart.length < ext.length
        ) {
          return `Incomplete extractor ".${lastPart}" - select ".${ext}" from suggestions`;
        }
      }
    }

    // Remove extractor from working string
    let workingStr = extractor
      ? trimmed.substring(0, trimmed.length - extractor.length - 1)
      : trimmed;

    // Step 2: Check for changelog syntax (field:value)
    const colonIndex = workingStr.indexOf(":");
    if (colonIndex > 0) {
      changelogValue = workingStr.substring(colonIndex + 1);
      workingStr = workingStr.substring(0, colonIndex);

      // Changelog value cannot be empty
      if (!changelogValue || !changelogValue.trim()) {
        return 'Incomplete - add a value after ":"';
      }
    }

    // Step 3: Check for project prefix (PROJECT.field)
    const dotIndex = workingStr.indexOf(".");
    if (dotIndex > 0) {
      projectPrefix = workingStr.substring(0, dotIndex);
      fieldPart = workingStr.substring(dotIndex + 1);
    } else {
      fieldPart = workingStr;
    }

    // Now validate each component

    // Validate project prefix
    if (projectPrefix && projectPrefix !== "*") {
      if (!autocompleteData?.projects) {
        return `Cannot validate project "${projectPrefix}" - metadata not loaded`;
      }
      const validProject = autocompleteData.projects.find(
        (p) =>
          p.key === projectPrefix || // Exact match for project key
          p.key.toUpperCase() === projectPrefix.toUpperCase() // Case-insensitive for keys
      );
      if (!validProject) {
        // Check for partial match
        const partialMatches = autocompleteData.projects.filter(
          (p) =>
            p.key.toUpperCase().startsWith(projectPrefix.toUpperCase()) ||
            p.name.toLowerCase().startsWith(projectPrefix.toLowerCase())
        );
        if (partialMatches.length > 0) {
          return `Unknown project "${projectPrefix}" - did you mean "${partialMatches[0].key}"?`;
        }
        return `Unknown project "${projectPrefix}" - select from suggestions`;
      }
    }

    // Validate field part
    if (!fieldPart) {
      return "Missing field name";
    }

    const fieldLower = fieldPart.toLowerCase();
    let fieldValid = false;
    let fieldInfo = null;

    // Check built-in fields (case-insensitive)
    if (BUILT_IN_FIELDS.includes(fieldLower)) {
      fieldValid = true;
    }

    // Check against metadata (exact match on ID or name)
    if (!fieldValid && autocompleteData?.fields) {
      fieldInfo = autocompleteData.fields.find(
        (f) =>
          f.id === fieldPart || // Exact ID match
          f.id.toLowerCase() === fieldLower || // Case-insensitive ID
          f.name === fieldPart || // Exact name match
          f.name.toLowerCase() === fieldLower // Case-insensitive name
      );
      if (fieldInfo) {
        fieldValid = true;
      }
    }

    // Check customfield pattern
    if (!fieldValid && /^customfield_\d+$/i.test(fieldPart)) {
      fieldValid = true;
    }

    if (!fieldValid) {
      // Check for partial match to give helpful error
      if (autocompleteData?.fields) {
        const partialMatches = autocompleteData.fields.filter(
          (f) =>
            f.id.toLowerCase().startsWith(fieldLower) ||
            f.name.toLowerCase().startsWith(fieldLower)
        );
        if (partialMatches.length > 0) {
          return `Unknown field "${fieldPart}" - did you mean "${partialMatches[0].name}" (${partialMatches[0].id})?`;
        }
      }
      return `Unknown field "${fieldPart}" - select from autocomplete suggestions`;
    }

    // Validate changelog value (status, issuetype, etc.)
    if (changelogValue) {
      // For status field, validate against known statuses
      if (fieldLower === "status") {
        if (!autocompleteData?.statuses) {
          return `Cannot validate status "${changelogValue}" - metadata not loaded`;
        }
        const validStatus = autocompleteData.statuses.find(
          (s) =>
            s.name === changelogValue || // Exact match
            s.name.toLowerCase() === changelogValue.toLowerCase() // Case-insensitive
        );
        if (!validStatus) {
          // Check for partial match
          const partialMatches = autocompleteData.statuses.filter((s) =>
            s.name.toLowerCase().startsWith(changelogValue.toLowerCase())
          );
          if (partialMatches.length > 0) {
            return `Unknown status "${changelogValue}" - did you mean "${partialMatches[0].name}"?`;
          }
          // Check for similar (typo detection)
          const similarMatches = autocompleteData.statuses.filter(
            (s) =>
              s.name.toLowerCase().includes(changelogValue.toLowerCase()) ||
              changelogValue
                .toLowerCase()
                .includes(s.name.toLowerCase().substring(0, 3))
          );
          if (similarMatches.length > 0) {
            return `Unknown status "${changelogValue}" - similar: "${similarMatches[0].name}"`;
          }
          return `Unknown status "${changelogValue}" - select from autocomplete suggestions`;
        }
      }

      // For issuetype field, validate against known issue types
      if (fieldLower === "issuetype") {
        if (!autocompleteData?.issueTypes) {
          return `Cannot validate issue type "${changelogValue}" - metadata not loaded`;
        }
        const validType = autocompleteData.issueTypes.find(
          (t) =>
            t.name === changelogValue ||
            t.name.toLowerCase() === changelogValue.toLowerCase()
        );
        if (!validType) {
          const partialMatches = autocompleteData.issueTypes.filter((t) =>
            t.name.toLowerCase().startsWith(changelogValue.toLowerCase())
          );
          if (partialMatches.length > 0) {
            return `Unknown issue type "${changelogValue}" - did you mean "${partialMatches[0].name}"?`;
          }
          return `Unknown issue type "${changelogValue}" - select from autocomplete suggestions`;
        }
      }

      // For priority field, validate against known priorities
      if (fieldLower === "priority") {
        if (autocompleteData?.priorities) {
          const validPriority = autocompleteData.priorities.find(
            (p) =>
              p.name === changelogValue ||
              p.name.toLowerCase() === changelogValue.toLowerCase()
          );
          if (!validPriority) {
            const partialMatches = autocompleteData.priorities.filter((p) =>
              p.name.toLowerCase().startsWith(changelogValue.toLowerCase())
            );
            if (partialMatches.length > 0) {
              return `Unknown priority "${changelogValue}" - did you mean "${partialMatches[0].name}"?`;
            }
            return `Unknown priority "${changelogValue}" - select from autocomplete suggestions`;
          }
        }
        // If no priorities metadata, allow (can't validate)
      }

      // For resolution field, validate against known resolutions
      if (fieldLower === "resolution") {
        if (autocompleteData?.resolutions) {
          const validResolution = autocompleteData.resolutions.find(
            (r) =>
              r.name === changelogValue ||
              r.name.toLowerCase() === changelogValue.toLowerCase()
          );
          if (!validResolution) {
            const partialMatches = autocompleteData.resolutions.filter((r) =>
              r.name.toLowerCase().startsWith(changelogValue.toLowerCase())
            );
            if (partialMatches.length > 0) {
              return `Unknown resolution "${changelogValue}" - did you mean "${partialMatches[0].name}"?`;
            }
            return `Unknown resolution "${changelogValue}" - select from autocomplete suggestions`;
          }
        }
      }

      // For custom fields with changelog syntax, we can't validate the values
      // without fetching the field's allowed values (which we don't have)
      // So we allow them if the field itself is valid
    }

    // All validations passed
    return null;
  },

  /**
   * Collect all namespace input values from the DOM
   * Called when save or validate button is clicked to gather values.
   *
   * Since we use dcc.Input with DOM manipulation for autocomplete,
   * this function reads directly from DOM to get the actual values
   * (including those set by autocomplete selection).
   *
   * Input: n_clicks from save button, n_clicks from validate button
   * Output: Dict with {trigger: "save"|"validate", values: {...}, validationErrors: [...]}
   */
  collectNamespaceValues: function (saveClicks, validateClicks) {
    // Check if any trigger is active
    if (!saveClicks && !validateClicks) {
      return window.dash_clientside.no_update;
    }

    // Determine which button triggered this
    const ctx = window.dash_clientside.callback_context;
    let trigger = "unknown";
    if (ctx && ctx.triggered && ctx.triggered.length > 0) {
      const triggeredId = ctx.triggered[0].prop_id.split(".")[0];
      if (triggeredId === "field-mapping-save-button") {
        trigger = "save";
      } else if (triggeredId === "validate-mappings-button") {
        trigger = "validate";
      }
    }

    const values = {};
    const validationErrors = [];
    const autocompleteData = window._namespaceAutocompleteData || null;
    const inputs = document.querySelectorAll(
      '.namespace-input-container input[type="text"]'
    );

    inputs.forEach((input) => {
      try {
        // Parse the Dash pattern-matched ID
        const idStr = input.id;
        const idObj = JSON.parse(idStr);

        if (idObj.type === "namespace-field-input") {
          const metric = idObj.metric;
          const field = idObj.field;
          const value = input.value ? input.value.trim() : "";

          if (value) {
            // Validate on save OR validate trigger
            if (trigger === "save" || trigger === "validate") {
              const error =
                window.dash_clientside.namespace_autocomplete.isValidForSave(
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
                input.classList.add("is-invalid");
                // Find or create error message element
                let errorEl =
                  input.parentElement.querySelector(".invalid-feedback");
                if (!errorEl) {
                  errorEl = document.createElement("div");
                  errorEl.className = "invalid-feedback";
                  input.parentElement.appendChild(errorEl);
                }
                errorEl.textContent = error;
                errorEl.style.display = "block";
              } else {
                // Valid - remove any error styling
                input.classList.remove("is-invalid");
                const errorEl =
                  input.parentElement.querySelector(".invalid-feedback");
                if (errorEl) {
                  errorEl.style.display = "none";
                }
              }
            }

            if (!values[metric]) {
              values[metric] = {};
            }
            values[metric][field] = value;
            console.log(
              "[Autocomplete] Collected:",
              metric + "." + field,
              "=",
              value
            );
          }
        }
      } catch (e) {
        // Skip inputs with non-JSON IDs
      }
    });

    console.log(
      "[Autocomplete] Collected namespace values (trigger=" + trigger + "):",
      values,
      "errors:",
      validationErrors
    );

    return {
      trigger: trigger,
      values: values,
      validationErrors: validationErrors,
    };
  },

  /**
   * Filter suggestions based on input value
   * Pure client-side filtering - instant response
   *
   * Inputs: input value, autocomplete data
   * Output: filtered suggestions HTML
   */
  filterSuggestions: function (inputValue, autocompleteData, triggerCount) {
    // Return empty if no input or no data
    if (!inputValue || !autocompleteData || !autocompleteData.fields) {
      return "";
    }

    const query = inputValue.toLowerCase().trim();
    if (query.length < 1) {
      return "";
    }

    const suggestions = [];
    const maxResults = 15;

    // Determine what type of suggestions to show based on input pattern
    const parts = inputValue.split(".");

    if (parts.length === 1 && !inputValue.includes(":")) {
      // User is typing the first part - could be project or field
      // Show projects first, then fields

      // Add wildcard option
      if ("*".startsWith(query) || query === "") {
        suggestions.push({
          label: "* (All Projects)",
          value: "*.",
          description: "Match from any project",
          type: "project",
        });
      }

      // Filter projects
      autocompleteData.projects.forEach((p) => {
        if (p.searchText.includes(query) && suggestions.length < maxResults) {
          suggestions.push({
            label: p.key,
            value: p.key + ".",
            description: p.name,
            type: "project",
          });
        }
      });

      // Filter fields (direct field without project prefix)
      autocompleteData.fields.forEach((f) => {
        if (f.searchText.includes(query) && suggestions.length < maxResults) {
          suggestions.push({
            label: f.name,
            value: f.id,
            description: f.id + " (" + f.type + ")",
            type: "field",
            fieldType: f.type,
          });
        }
      });
    } else if (parts.length >= 2) {
      // User has typed "Project." or "*.field" - suggest fields
      const fieldQuery = parts[parts.length - 1].toLowerCase();
      const prefix = parts.slice(0, -1).join(".") + ".";

      autocompleteData.fields.forEach((f) => {
        if (
          f.searchText.includes(fieldQuery) &&
          suggestions.length < maxResults
        ) {
          suggestions.push({
            label: f.name,
            value: prefix + f.id,
            description: f.id + " (" + f.type + ")",
            type: "field",
            fieldType: f.type,
          });
        }
      });
    }

    // Also check for changelog syntax (Status:value)
    if (inputValue.includes(":")) {
      const colonParts = inputValue.split(":");
      const afterColon = colonParts[colonParts.length - 1];

      // Check if user is typing extractor after changelog value (e.g., "Status:Done.")
      if (afterColon.includes(".")) {
        // User typed "Status:Done." - suggest extractors
        const dotParts = afterColon.split(".");
        const extractorQuery = dotParts[dotParts.length - 1].toLowerCase();
        const baseValue = colonParts[0] + ":" + dotParts[0];

        const extractors = [
          {
            name: "DateTime",
            description: "Extract timestamp when this transition occurred",
          },
          {
            name: "Occurred",
            description: "Boolean: true if this transition ever happened",
          },
          {
            name: "Duration",
            description: "Time spent in this state (future)",
          },
        ];

        extractors.forEach((e) => {
          if (
            e.name.toLowerCase().startsWith(extractorQuery) &&
            suggestions.length < maxResults
          ) {
            suggestions.push({
              label: e.name,
              value: baseValue + "." + e.name,
              description: e.description,
              type: "extractor",
            });
          }
        });
      } else {
        // User is typing status value after colon
        const statusQuery = afterColon.toLowerCase();

        autocompleteData.statuses.forEach((s) => {
          if (
            s.searchText.includes(statusQuery) &&
            suggestions.length < maxResults
          ) {
            suggestions.push({
              label: s.name,
              value: colonParts[0] + ":" + s.name,
              description:
                "Status: " +
                (s.category || "Unknown") +
                " (add .DateTime for timestamp)",
              type: "status",
            });
          }
        });
      }
    }

    if (suggestions.length === 0) {
      return "";
    }

    // Build HTML for suggestions dropdown
    let html = '<div class="list-group">';
    suggestions.forEach((s, idx) => {
      const typeIcon =
        s.type === "project"
          ? "📁"
          : s.type === "field"
          ? "📋"
          : s.type === "status"
          ? "🔄"
          : s.type === "extractor"
          ? "⏱️"
          : "📄";
      html += `
                <button type="button" 
                        class="list-group-item list-group-item-action py-2" 
                        data-value="${escapeHtml(s.value)}"
                        data-index="${idx}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <span class="me-1">${typeIcon}</span>
                            <strong>${escapeHtml(s.label)}</strong>
                        </div>
                        ${
                          s.fieldType
                            ? `<span class="badge bg-secondary">${escapeHtml(
                                s.fieldType
                              )}</span>`
                            : ""
                        }
                    </div>
                    <small class="text-muted">${escapeHtml(
                      s.description
                    )}</small>
                </button>
            `;
    });
    html += "</div>";

    return html;
  },
};

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Initialize autocomplete behavior for namespace inputs
 * Handles keyboard navigation and selection
 */
document.addEventListener("DOMContentLoaded", function () {
  initNamespaceAutocomplete();
  watchMetadataStore();
});

// Re-initialize when Dash updates the DOM
const observer = new MutationObserver(function (mutations) {
  mutations.forEach(function (mutation) {
    if (mutation.addedNodes.length) {
      initNamespaceAutocomplete();
      // Also check if metadata store was added
      watchMetadataStore();
    }
  });
});

observer.observe(document.body, { childList: true, subtree: true });

/**
 * Watch for metadata store changes and build autocomplete data
 */
function watchMetadataStore() {
  const metadataStore = document.getElementById("jira-metadata-store");
  if (!metadataStore || metadataStore.dataset.watching) return;

  metadataStore.dataset.watching = "true";

  // Try to build data immediately if store has content
  tryBuildFromMetadata();

  // Watch for changes to the store
  const storeObserver = new MutationObserver(function () {
    tryBuildFromMetadata();
  });

  storeObserver.observe(metadataStore, {
    childList: true,
    characterData: true,
    subtree: true,
  });

  console.log("[Autocomplete] Watching metadata store for changes");
}

/**
 * Try to build autocomplete data from metadata store
 */
function tryBuildFromMetadata() {
  if (
    window._namespaceAutocompleteData &&
    window._namespaceAutocompleteData.fields &&
    window._namespaceAutocompleteData.fields.length > 0
  ) {
    return; // Already have data
  }

  const metadataStore = document.getElementById("jira-metadata-store");
  if (!metadataStore) return;

  try {
    const rawData = metadataStore.textContent || metadataStore.innerText;
    if (rawData && rawData.trim() && rawData !== "null") {
      const metadata = JSON.parse(rawData);
      if (metadata && !metadata.error && metadata.fields) {
        window.dash_clientside.namespace_autocomplete.buildAutocompleteData(
          metadata
        );
        console.log("[Autocomplete] Built data from metadata store on change");
      }
    }
  } catch (e) {
    // Ignore parse errors - store might not be ready yet
  }
}

function initNamespaceAutocomplete() {
  // Find all namespace input containers
  document
    .querySelectorAll(".namespace-input-container")
    .forEach((container) => {
      if (container.dataset.initialized) return;
      container.dataset.initialized = "true";

      const input = container.querySelector("input");
      const dropdown = container.querySelector(
        ".namespace-suggestions-dropdown"
      );

      if (!input || !dropdown) return;

      // Find validation message container (sibling of input container)
      let validationContainer = null;
      try {
        const idStr = input.id;
        const idObj = JSON.parse(idStr);
        if (idObj.type === "namespace-field-input") {
          // Dash serializes pattern-matched IDs with keys in alphabetical order
          // So we need to match that: field, metric, type
          const validationId = JSON.stringify({
            field: idObj.field,
            metric: idObj.metric,
            type: "field-validation-message",
          });
          validationContainer = document.querySelector(
            `[id='${validationId}']`
          );
          console.log(
            "[Autocomplete] Looking for validation container:",
            validationId,
            "found:",
            !!validationContainer
          );
        }
      } catch (e) {
        console.log("[Autocomplete] Error finding validation container:", e);
      }

      let selectedIndex = -1;

      // Debounced validation
      let validationTimeout = null;
      function runValidation() {
        if (validationTimeout) clearTimeout(validationTimeout);
        validationTimeout = setTimeout(() => {
          if (validationContainer && window._namespaceAutocompleteData) {
            try {
              const idObj = JSON.parse(input.id);
              const validationHtml =
                window.dash_clientside.namespace_autocomplete.validateNamespaceInput(
                  input.value,
                  window._namespaceAutocompleteData,
                  idObj.metric,
                  idObj.field
                );
              validationContainer.innerHTML = validationHtml;
            } catch (e) {
              console.log("[Autocomplete] Validation error:", e);
            }
          }
        }, 300); // 300ms debounce
      }

      // Handle input changes - filter suggestions and validate
      input.addEventListener("input", function (e) {
        // Skip if this is a programmatic update from selectItem
        if (input.dataset.programmaticUpdate === "true") {
          console.log("[Autocomplete] Skipping update - programmatic change");
          return;
        }
        selectedIndex = -1;
        updateSuggestions(input.value, dropdown);
        runValidation();

        // Clear any save validation error when user starts typing
        // 1. Clear the global status message
        const statusDiv = document.getElementById("field-mapping-status");
        if (statusDiv && statusDiv.innerHTML.trim()) {
          statusDiv.innerHTML = "";
          console.log("[Autocomplete] Cleared validation status on input");
        }

        // 2. Clear the inline validation error on this specific input
        input.classList.remove("is-invalid");
        const errorEl = input.parentElement.querySelector(".invalid-feedback");
        if (errorEl) {
          errorEl.style.display = "none";
          errorEl.textContent = "";
        }
      });

      // Also validate on blur (when user finishes typing)
      input.addEventListener("blur", function (e) {
        // Run validation immediately on blur
        if (validationTimeout) clearTimeout(validationTimeout);
        if (validationContainer && window._namespaceAutocompleteData) {
          try {
            const idObj = JSON.parse(input.id);
            const validationHtml =
              window.dash_clientside.namespace_autocomplete.validateNamespaceInput(
                input.value,
                window._namespaceAutocompleteData,
                idObj.metric,
                idObj.field
              );
            validationContainer.innerHTML = validationHtml;
          } catch (e) {
            console.log("[Autocomplete] Validation error on blur:", e);
          }
        }
      });

      // Run initial validation if input has value
      if (input.value && input.value.trim()) {
        setTimeout(runValidation, 500); // Delay to let metadata load
      }

      // Handle keyboard navigation
      input.addEventListener("keydown", function (e) {
        const items = dropdown.querySelectorAll(".list-group-item");
        if (items.length === 0) return;

        switch (e.key) {
          case "ArrowDown":
            e.preventDefault();
            selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
            updateSelection(items, selectedIndex);
            break;
          case "ArrowUp":
            e.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, 0);
            updateSelection(items, selectedIndex);
            break;
          case "Enter":
          case "Tab":
            if (selectedIndex >= 0 && selectedIndex < items.length) {
              e.preventDefault();
              selectItem(input, items[selectedIndex], dropdown);
            }
            break;
          case "Escape":
            dropdown.innerHTML = "";
            selectedIndex = -1;
            break;
        }
      });

      // Handle click on suggestions
      dropdown.addEventListener("click", function (e) {
        const item = e.target.closest(".list-group-item");
        if (item) {
          e.preventDefault();
          selectItem(input, item, dropdown);
        }
      });

      // Prevent dropdown clicks from stealing focus
      dropdown.addEventListener("mousedown", function (e) {
        e.preventDefault();
      });

      // Track the last programmatically selected value
      // This helps us restore it if React tries to revert
      let lastSelectedValue = null;
      let selectionTimestamp = 0;

      // Store reference to selectItem wrapper that tracks selection
      const originalSelectItem = selectItem;
      const wrappedSelectItem = function (inp, itm, dd) {
        const val = itm.dataset.value;
        if (val) {
          lastSelectedValue = val;
          selectionTimestamp = Date.now();
        }
        originalSelectItem(inp, itm, dd);
      };

      // Override click handler to use wrapped selectItem
      dropdown.removeEventListener("click", dropdown._clickHandler);
      dropdown._clickHandler = function (e) {
        const item = e.target.closest(".list-group-item");
        if (item) {
          e.preventDefault();
          wrappedSelectItem(input, item, dropdown);
        }
      };
      dropdown.addEventListener("click", dropdown._clickHandler);

      // Protect against React reverting the value on blur
      // If value changes within 500ms of selection, restore it
      input.addEventListener("blur", function () {
        const timeSinceSelection = Date.now() - selectionTimestamp;
        if (lastSelectedValue && timeSinceSelection < 500) {
          // React might try to revert - schedule a check
          setTimeout(() => {
            if (
              input.value !== lastSelectedValue &&
              timeSinceSelection < 1000
            ) {
              console.log(
                "[Autocomplete] Restoring reverted value:",
                lastSelectedValue,
                "current:",
                input.value
              );
              const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype,
                "value"
              ).set;
              nativeInputValueSetter.call(input, lastSelectedValue);
              input.dispatchEvent(new Event("input", { bubbles: true }));
            }
          }, 50);
        }
      });

      // Clear selection tracking after a delay
      setInterval(() => {
        if (Date.now() - selectionTimestamp > 2000) {
          lastSelectedValue = null;
        }
      }, 1000);

      // Hide dropdown on blur (after a short delay to allow clicks)
      input.addEventListener("blur", function () {
        setTimeout(() => {
          if (!container.contains(document.activeElement)) {
            dropdown.innerHTML = "";
            selectedIndex = -1;
          }
        }, 200);
      });

      // Show suggestions on focus if input has value (but not after programmatic selection)
      input.addEventListener("focus", function () {
        // Don't reopen dropdown if we just completed a selection
        if (input.dataset.programmaticUpdate === "true") {
          console.log(
            "[Autocomplete] Skipping focus suggestions - programmatic update"
          );
          return;
        }
        if (input.value.trim().length > 0) {
          updateSuggestions(input.value, dropdown);
        }
      });

      console.log("[Autocomplete] Initialized container for:", input.id);
    });
}

/**
 * Update suggestions dropdown based on input value
 */
function updateSuggestions(inputValue, dropdown) {
  // First try the global variable (set by clientside callback)
  let autocompleteData = window._namespaceAutocompleteData;

  // If not available, try to build it from jira-metadata-store
  if (
    !autocompleteData ||
    !autocompleteData.fields ||
    autocompleteData.fields.length === 0
  ) {
    const metadataStore = document.getElementById("jira-metadata-store");
    if (metadataStore) {
      try {
        // Dash stores keep data in a specific format - try to extract it
        const rawData = metadataStore.textContent || metadataStore.innerText;
        if (rawData && rawData.trim()) {
          const metadata = JSON.parse(rawData);
          if (metadata && !metadata.error) {
            // Build autocomplete data from metadata
            autocompleteData =
              window.dash_clientside.namespace_autocomplete.buildAutocompleteData(
                metadata
              );
            console.log("[Autocomplete] Built data from metadata store");
          }
        }
      } catch (e) {
        console.log(
          "[Autocomplete] Could not parse metadata store:",
          e.message
        );
      }
    }
  }

  if (
    !autocompleteData ||
    !autocompleteData.fields ||
    autocompleteData.fields.length === 0
  ) {
    console.log("[Autocomplete] No autocomplete data available yet");
    return;
  }

  // Filter and display suggestions
  const html = window.dash_clientside.namespace_autocomplete.filterSuggestions(
    inputValue,
    autocompleteData,
    0 // trigger count (unused, for callback signature)
  );

  dropdown.innerHTML = html;
}

function updateSelection(items, selectedIndex) {
  items.forEach((item, idx) => {
    if (idx === selectedIndex) {
      item.classList.add("active");
      item.scrollIntoView({ block: "nearest" });
    } else {
      item.classList.remove("active");
    }
  });
}

function selectItem(input, item, dropdown) {
  const value = item.dataset.value;
  if (value) {
    console.log(
      "[Autocomplete] Selecting:",
      value,
      "current input:",
      input.value
    );

    // Set flag BEFORE any value changes to prevent input handler from reopening dropdown
    input.dataset.programmaticUpdate = "true";

    // Clear dropdown FIRST to prevent any race conditions
    dropdown.innerHTML = "";

    // For dcc.Input (React controlled), we need to properly update React's state
    // The key is to use the native setter AND dispatch the right events
    // React listens for 'input' events to update controlled components
    try {
      // Get the native value setter
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype,
        "value"
      ).set;

      // Set the value using native setter
      nativeInputValueSetter.call(input, value);

      // Create and dispatch an input event that React will recognize
      // Using InputEvent with inputType helps React recognize it as user input
      const inputEvent = new InputEvent("input", {
        bubbles: true,
        cancelable: true,
        inputType: "insertText",
        data: value,
      });
      input.dispatchEvent(inputEvent);

      // Also dispatch change event for completeness
      const changeEvent = new Event("change", { bubbles: true });
      input.dispatchEvent(changeEvent);

      // Force a blur and refocus to ensure React processes the change
      // This is a workaround for React's synthetic event system
      const activeElement = document.activeElement;
      input.blur();

      // Small delay before refocus to let React process
      setTimeout(() => {
        // Keep flag set during refocus to prevent dropdown reopening
        input.dataset.programmaticUpdate = "true";

        // Set value again after blur in case React reset it
        nativeInputValueSetter.call(input, value);
        input.dispatchEvent(new Event("input", { bubbles: true }));

        // Refocus
        input.focus();

        // Move cursor to end
        input.setSelectionRange(value.length, value.length);

        console.log("[Autocomplete] Selection complete, value:", input.value);

        // Clear flag after everything is done
        setTimeout(() => {
          delete input.dataset.programmaticUpdate;
        }, 100);
      }, 10);
    } catch (e) {
      console.warn("[Autocomplete] Event dispatch failed:", e);
      // Last resort fallback
      input.value = value;
      delete input.dataset.programmaticUpdate;
    }

    // Run validation after selection
    setTimeout(() => {
      const inputId = input.id;
      if (inputId) {
        // Extract metric and field from input ID pattern (JSON format)
        try {
          const idObj = JSON.parse(inputId);
          if (idObj.metric && idObj.field) {
            const validationContainer = document.getElementById(
              `validation-${idObj.metric}-${idObj.field}`
            );
            if (validationContainer && window._autocompleteData) {
              const validationResult =
                window.dash_clientside.namespace_autocomplete.validateNamespaceInput(
                  value,
                  window._autocompleteData,
                  idObj.metric,
                  idObj.field
                );
              validationContainer.innerHTML = validationResult;
              console.log(
                "[Autocomplete] Validation after select for",
                inputId
              );
            }
          }
        } catch (e) {
          // Non-JSON ID format, try old pattern
          const match = inputId.match(/namespace-(.+)-(.+)/);
          if (match) {
            const metric = match[1];
            const field = match[2];
            const validationContainer = document.getElementById(
              `validation-${metric}-${field}`
            );
            if (validationContainer && window._autocompleteData) {
              const validationResult =
                window.dash_clientside.namespace_autocomplete.validateNamespaceInput(
                  value,
                  window._autocompleteData,
                  metric,
                  field
                );
              validationContainer.innerHTML = validationResult;
            }
          }
        }
      }
      // Note: programmaticUpdate flag is cleared in the selection setTimeout chain above
    }, 50);

    // Keep focus
    input.focus();
  }
}
