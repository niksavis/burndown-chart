/**
 * Namespace Autocomplete - Data Preparation
 *
 * Builds and normalises the autocomplete dataset from JIRA metadata,
 * and provides pure filtering/rendering helpers.
 *
 * Exposed on window._nsa (internal cross-file namespace):
 *   window._nsa.buildDataset(metadata)         -> dataset object
 *   window._nsa.filterSuggestions(input, data) -> suggestion array
 *   window._nsa.renderSuggestionsHtml(arr)      -> HTML string
 *   window._nsa.escapeHtml(text)                -> safe HTML string
 */

window._nsa = window._nsa || {};

/**
 * Build the autocomplete dataset from raw JIRA metadata.
 *
 * @param {Object|null} metadata - JIRA metadata from jira-metadata-store
 * @returns {Object} Normalised dataset with fields, projects, statuses, issueTypes
 */
window._nsa.buildDataset = function (metadata) {
  if (!metadata || metadata.error) {
    return { fields: [], projects: [], statuses: [], issueTypes: [] };
  }

  return {
    fields: (metadata.fields || []).map(function (f) {
      return {
        id: f.id || f.field_id || '',
        name: f.name || f.id || '',
        type: f.type || (f.schema && f.schema.type) || f.field_type || 'unknown',
        searchText: ((f.name || '') + ' ' + (f.id || '')).toLowerCase(),
      };
    }),
    projects: (metadata.projects || []).map(function (p) {
      return {
        key: p.key || '',
        name: p.name || '',
        searchText: ((p.key || '') + ' ' + (p.name || '')).toLowerCase(),
      };
    }),
    statuses: (metadata.statuses || []).map(function (s) {
      return {
        name: s.name || '',
        category: (s.statusCategory && s.statusCategory.name) || '',
        searchText: (s.name || '').toLowerCase(),
      };
    }),
    issueTypes: (metadata.issue_types || []).map(function (t) {
      return {
        name: t.name || '',
        searchText: (t.name || '').toLowerCase(),
      };
    }),
  };
};

/**
 * Filter the autocomplete dataset and return suggestion objects.
 *
 * @param {string} inputValue - Current input value
 * @param {Object} autocompleteData - Dataset from buildDataset
 * @returns {Array} Suggestion objects with label, value, description, type
 */
window._nsa.filterSuggestions = function (inputValue, autocompleteData) {
  if (!inputValue || !autocompleteData || !autocompleteData.fields) {
    return [];
  }

  var query = inputValue.toLowerCase().trim();
  if (query.length < 1) {
    return [];
  }

  var suggestions = [];
  var maxResults = 15;
  var parts = inputValue.split('.');

  if (parts.length === 1 && !inputValue.includes(':')) {
    // First token: could be project prefix or bare field

    if ('*'.startsWith(query) || query === '') {
      suggestions.push({
        label: '* (All Projects)',
        value: '*.',
        description: 'Match from any project',
        type: 'project',
      });
    }

    autocompleteData.projects.forEach(function (p) {
      if (p.searchText.includes(query) && suggestions.length < maxResults) {
        suggestions.push({
          label: p.key,
          value: p.key + '.',
          description: p.name,
          type: 'project',
        });
      }
    });

    autocompleteData.fields.forEach(function (f) {
      if (f.searchText.includes(query) && suggestions.length < maxResults) {
        suggestions.push({
          label: f.name,
          value: f.id,
          description: f.id + ' (' + f.type + ')',
          type: 'field',
          fieldType: f.type,
        });
      }
    });
  } else if (parts.length >= 2) {
    // "Project." typed - suggest fields
    var fieldQuery = parts[parts.length - 1].toLowerCase();
    var prefix = parts.slice(0, -1).join('.') + '.';

    autocompleteData.fields.forEach(function (f) {
      if (f.searchText.includes(fieldQuery) && suggestions.length < maxResults) {
        suggestions.push({
          label: f.name,
          value: prefix + f.id,
          description: f.id + ' (' + f.type + ')',
          type: 'field',
          fieldType: f.type,
        });
      }
    });
  }

  // Changelog syntax (Status:value)
  if (inputValue.includes(':')) {
    var colonParts = inputValue.split(':');
    var afterColon = colonParts[colonParts.length - 1];

    if (afterColon.includes('.')) {
      // "Status:Done." - suggest extractors
      var dotParts = afterColon.split('.');
      var extractorQuery = dotParts[dotParts.length - 1].toLowerCase();
      var baseValue = colonParts[0] + ':' + dotParts[0];

      var extractors = [
        { name: 'DateTime', description: 'Extract timestamp when this transition occurred' },
        { name: 'Occurred', description: 'Boolean: true if this transition ever happened' },
        { name: 'Duration', description: 'Time spent in this state (future)' },
      ];

      extractors.forEach(function (e) {
        if (e.name.toLowerCase().startsWith(extractorQuery) && suggestions.length < maxResults) {
          suggestions.push({
            label: e.name,
            value: baseValue + '.' + e.name,
            description: e.description,
            type: 'extractor',
          });
        }
      });
    } else {
      // Typing status value after colon
      var statusQuery = afterColon.toLowerCase();

      autocompleteData.statuses.forEach(function (s) {
        if (s.searchText.includes(statusQuery) && suggestions.length < maxResults) {
          suggestions.push({
            label: s.name,
            value: colonParts[0] + ':' + s.name,
            description: 'Status: ' + (s.category || 'Unknown') + ' (add .DateTime for timestamp)',
            type: 'status',
          });
        }
      });
    }
  }

  return suggestions;
};

/**
 * Render a suggestions array as an HTML string for the dropdown.
 *
 * @param {Array} suggestions - Output of filterSuggestions
 * @returns {string} HTML string, or empty string if no suggestions
 */
window._nsa.renderSuggestionsHtml = function (suggestions) {
  if (!suggestions || suggestions.length === 0) {
    return '';
  }

  var html = '<div class="list-group">';
  suggestions.forEach(function (s, idx) {
    var typeIcon =
      s.type === 'project'
        ? '\uD83D\uDCC1'
        : s.type === 'field'
          ? '\uD83D\uDCCB'
          : s.type === 'status'
            ? '\uD83D\uDD04'
            : s.type === 'extractor'
              ? '\u23F1\uFE0F'
              : '\uD83D\uDCC4';
    html +=
      '<button type="button"' +
      ' class="list-group-item list-group-item-action py-2"' +
      ' data-value="' +
      window._nsa.escapeHtml(s.value) +
      '"' +
      ' data-index="' +
      idx +
      '">' +
      '<div class="d-flex justify-content-between align-items-start">' +
      '<div>' +
      '<span class="me-1">' +
      typeIcon +
      '</span>' +
      '<strong>' +
      window._nsa.escapeHtml(s.label) +
      '</strong>' +
      '</div>' +
      (s.fieldType
        ? '<span class="badge bg-secondary">' + window._nsa.escapeHtml(s.fieldType) + '</span>'
        : '') +
      '</div>' +
      '<small class="text-muted">' +
      window._nsa.escapeHtml(s.description) +
      '</small>' +
      '</button>';
  });
  html += '</div>';
  return html;
};

/**
 * Escape HTML to prevent XSS.
 *
 * @param {string} text - Raw text
 * @returns {string} HTML-safe string
 */
window._nsa.escapeHtml = function (text) {
  if (!text) return '';
  var div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
};
