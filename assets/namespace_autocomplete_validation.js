/**
 * Namespace Autocomplete - Input Validation
 *
 * Provides two validation functions used by both the Dash clientside
 * callback and the DOM input handlers:
 *
 *   window._nsa.validateInput(value, data, metric, field)
 *     -> HTML feedback string (empty = no input, no feedback needed)
 *
 *   window._nsa.isValidForSave(value, data)
 *     -> error string | null  (null = valid)
 *
 * Depends on: namespace_autocomplete_data.js (window._nsa must exist)
 */

window._nsa = window._nsa || {};

// ---------------------------------------------------------------------------
// Field type category maps (shared between both validators)
// ---------------------------------------------------------------------------

/** Expected type CATEGORY for each metric variable. */
window._nsa.FIELD_TYPE_CATEGORIES = {
  // DORA Metrics - datetime fields
  deployment_date: 'datetime',
  code_commit_date: 'datetime',
  incident_detected_at: 'datetime',
  incident_resolved_at: 'datetime',
  // General fields
  completed_date: 'datetime',
  created_date: 'datetime',
  updated_date: 'datetime',
  // DORA Metrics - boolean/option fields
  deployment_successful: 'option',
  change_failure: 'option',
  // DORA Metrics - selection fields
  affected_environment: 'option',
  target_environment: 'option',
  severity_level: 'option',
  // Flow Metrics
  flow_item_type: 'option',
  status: 'option',
  work_started_date: 'datetime',
  work_completed_date: 'datetime',
  effort_category: 'option',
  estimate: 'number',
  // Sprint Tracker
  sprint_field: 'option',
  // Active Work Timeline
  parent_field: 'any',
};

/** Maps JIRA field types to normalised categories. */
window._nsa.TYPE_TO_CATEGORY = {
  // Datetime types
  datetime: 'datetime',
  date: 'datetime',
  datepicker: 'datetime',
  // Option/selection types
  select: 'option',
  option: 'option',
  issuetype: 'option',
  priority: 'option',
  status: 'option',
  resolution: 'option',
  component: 'option',
  version: 'option',
  user: 'option',
  project: 'option',
  issuelinks: 'option',
  checkbox: 'option',
  radiobuttons: 'option',
  cascadingselect: 'option',
  multiselect: 'option',
  labels: 'option',
  // Number types
  number: 'number',
  float: 'number',
  integer: 'number',
  // Text types
  string: 'text',
  text: 'text',
  textarea: 'text',
  url: 'text',
  // Array types (usually work as option)
  array: 'option',
};

// ---------------------------------------------------------------------------
// validateInput: inline feedback while typing
// ---------------------------------------------------------------------------

/**
 * Validate a namespace input and return validation feedback HTML.
 *
 * @param {string} inputValue - Current input value
 * @param {Object} autocompleteData - Dataset from window._nsa.buildDataset
 * @param {string} _metric - Metric identifier (currently unused, kept for compat)
 * @param {string} field - Field identifier used to look up expected type
 * @returns {string} HTML string for inline feedback
 */
window._nsa.validateInput = function (inputValue, autocompleteData, _metric, field) {
  if (!inputValue || !inputValue.trim()) {
    return '';
  }

  if (!autocompleteData || !autocompleteData.fields) {
    return '<small class="text-muted"><i class="fas fa-info-circle me-1"></i>Loading field metadata...</small>';
  }

  var value = inputValue.trim();
  var expectedCategory = window._nsa.FIELD_TYPE_CATEGORIES[field] || null;

  // Check for complete changelog syntax with extractor FIRST
  var hasChangelogExtractor =
    value.includes(':') &&
    (value.endsWith('.DateTime') || value.endsWith('.Occurred') || value.endsWith('.Duration'));

  if (hasChangelogExtractor) {
    return '<small class="text-success"><i class="fas fa-check-circle me-1"></i>Changelog syntax (extracts datetime)</small>';
  }

  // Extract field ID from namespace syntax
  var fieldId = value;

  if (fieldId.includes('=')) {
    fieldId = fieldId.split('=')[0];
  }

  if (value.includes('.')) {
    var dotParts = value.split('.');
    fieldId = dotParts[dotParts.length - 1];
    if (['DateTime', 'Occurred', 'FirstValue', 'LastValue'].includes(fieldId)) {
      fieldId = dotParts[dotParts.length - 2];
    }
    if (fieldId.includes('=')) {
      fieldId = fieldId.split('=')[0];
    }
  }

  if (value.includes(':')) {
    var colonParts = value.split(':');
    fieldId = colonParts[0];
    if (fieldId.includes('.')) {
      fieldId = fieldId.split('.').pop();
    }
  }

  // Find field in metadata
  var fieldInfo = autocompleteData.fields.find(function (f) {
    return f.id === fieldId || f.name.toLowerCase() === fieldId.toLowerCase();
  });

  if (!fieldInfo) {
    if (value.includes(':')) {
      return '<small class="text-success"><i class="fas fa-check-circle me-1"></i>Changelog syntax (extracts datetime)</small>';
    }

    var builtInDateFields = [
      'created',
      'updated',
      'resolutiondate',
      'duedate',
      'lastViewed',
      'fixversions',
    ];
    var builtInOptionFields = [
      'status',
      'issuetype',
      'priority',
      'resolution',
      'assignee',
      'reporter',
      'project',
    ];

    if (
      builtInDateFields.some(function (f) {
        return fieldId.toLowerCase().includes(f);
      })
    ) {
      return '<small class="text-success"><i class="fas fa-check-circle me-1"></i>Built-in date field</small>';
    }
    if (
      builtInOptionFields.some(function (f) {
        return fieldId.toLowerCase().includes(f);
      })
    ) {
      return '<small class="text-success"><i class="fas fa-check-circle me-1"></i>Built-in field</small>';
    }
    return (
      '<small class="text-warning"><i class="fas fa-question-circle me-1"></i>Field "' +
      fieldId +
      '" not in metadata (may still work)</small>'
    );
  }

  var actualType = (fieldInfo.type || 'unknown').toLowerCase();
  var actualCategory = window._nsa.TYPE_TO_CATEGORY[actualType] || 'unknown';

  if (!expectedCategory) {
    return (
      '<small class="text-info"><i class="fas fa-info-circle me-1"></i>Field: ' +
      fieldInfo.name +
      ' (' +
      actualType +
      ')</small>'
    );
  }

  if (expectedCategory === 'any') {
    return (
      '<small class="text-success"><i class="fas fa-check-circle me-1"></i>Field: ' +
      fieldInfo.name +
      ' (' +
      actualType +
      ')</small>'
    );
  }

  if (actualCategory === expectedCategory) {
    if (value.includes('=')) {
      var filterValue = value.split('=')[1];
      return (
        '<small class="text-success"><i class="fas fa-check-circle me-1"></i>' +
        fieldInfo.name +
        ' with value filter "' +
        filterValue +
        '"</small>'
      );
    }
    return (
      '<small class="text-success"><i class="fas fa-check-circle me-1"></i>' +
      fieldInfo.name +
      ' (' +
      actualType +
      ')</small>'
    );
  }

  if (fieldId.toLowerCase() === 'fixversions' && expectedCategory === 'datetime') {
    return '<small class="text-success"><i class="fas fa-check-circle me-1"></i>fixVersions is valid (uses releaseDate automatically)</small>';
  }

  if (actualCategory === 'option' && expectedCategory === 'datetime') {
    return (
      '<small class="text-warning"><i class="fas fa-lightbulb me-1"></i>' +
      fieldInfo.name +
      ' is ' +
      actualType +
      '. Use changelog syntax: ' +
      fieldId +
      ':VALUE.DateTime</small>'
    );
  }

  return (
    '<small class="text-warning"><i class="fas fa-exclamation-triangle me-1"></i>' +
    fieldInfo.name +
    ' is ' +
    actualType +
    ', expected ' +
    expectedCategory +
    ' type</small>'
  );
};

// ---------------------------------------------------------------------------
// isValidForSave: strict validation before save
// ---------------------------------------------------------------------------

/** Valid extractor suffixes (case-sensitive). */
window._nsa.VALID_EXTRACTORS = ['DateTime', 'Occurred', 'Duration', 'FirstValue', 'LastValue'];

/** Built-in JIRA fields that don't require a metadata lookup. */
window._nsa.BUILT_IN_FIELDS = [
  'created',
  'updated',
  'resolutiondate',
  'duedate',
  'lastviewed',
  'status',
  'issuetype',
  'priority',
  'resolution',
  'assignee',
  'reporter',
  'project',
  'summary',
  'description',
  'labels',
  'components',
  'fixversions',
  'versions',
  'creator',
  'environment',
  'key',
  'id',
];

/**
 * Strictly validate a namespace value before saving.
 *
 * @param {string} value - Namespace value to validate
 * @param {Object} autocompleteData - Dataset from window._nsa.buildDataset
 * @returns {string|null} Error message, or null if valid
 */
window._nsa.isValidForSave = function (value, autocompleteData) {
  if (!value || !value.trim()) {
    return null; // Empty = valid (optional field)
  }

  var trimmed = value.trim();

  if (trimmed.endsWith(':')) {
    return 'Incomplete - add a value after ":"';
  }
  if (trimmed.endsWith('.')) {
    return 'Incomplete - select an extractor or field';
  }

  // 1. Detect extractor at end (.DateTime etc.)
  var extractor = null;
  window._nsa.VALID_EXTRACTORS.forEach(function (ext) {
    if (!extractor && trimmed.endsWith('.' + ext)) {
      extractor = ext;
    }
  });

  // Check for partial/wrong-case extractor
  var lastDotIndex = trimmed.lastIndexOf('.');
  if (lastDotIndex > 0 && !extractor) {
    var lastPart = trimmed.substring(lastDotIndex + 1);
    for (var ei = 0; ei < window._nsa.VALID_EXTRACTORS.length; ei++) {
      var ext = window._nsa.VALID_EXTRACTORS[ei];
      if (lastPart.toLowerCase() === ext.toLowerCase() && lastPart !== ext) {
        return 'Extractor must be exactly ".' + ext + '" (case-sensitive)';
      }
      if (
        ext.toLowerCase().startsWith(lastPart.toLowerCase()) &&
        lastPart.length > 0 &&
        lastPart.length < ext.length
      ) {
        return 'Incomplete extractor ".' + lastPart + '" - select ".' + ext + '" from suggestions';
      }
    }
  }

  var workingStr = extractor
    ? trimmed.substring(0, trimmed.length - extractor.length - 1)
    : trimmed;

  // 2. Changelog syntax (field:value)
  var changelogValue = null;
  var colonIndex = workingStr.indexOf(':');
  if (colonIndex > 0) {
    changelogValue = workingStr.substring(colonIndex + 1);
    workingStr = workingStr.substring(0, colonIndex);
    if (!changelogValue || !changelogValue.trim()) {
      return 'Incomplete - add a value after ":"';
    }
  }

  // 2b. Value filter (field=Value)
  var valueFilter = null;
  var equalsIndex = workingStr.indexOf('=');
  if (equalsIndex > 0) {
    valueFilter = workingStr.substring(equalsIndex + 1);
    workingStr = workingStr.substring(0, equalsIndex);
    if (!valueFilter || !valueFilter.trim()) {
      return 'Incomplete - add a value after "="';
    }
  }

  // 3. Project prefix (PROJECT.field)
  var projectPrefix = null;
  var fieldPart = null;
  var dotIndex = workingStr.indexOf('.');
  if (dotIndex > 0) {
    projectPrefix = workingStr.substring(0, dotIndex);
    fieldPart = workingStr.substring(dotIndex + 1);
  } else {
    fieldPart = workingStr;
  }

  // Validate project prefix
  if (projectPrefix && projectPrefix !== '*') {
    if (!autocompleteData || !autocompleteData.projects) {
      return 'Cannot validate project "' + projectPrefix + '" - metadata not loaded';
    }
    var validProject = autocompleteData.projects.find(function (p) {
      return p.key === projectPrefix || p.key.toUpperCase() === projectPrefix.toUpperCase();
    });
    if (!validProject) {
      var projectPartials = autocompleteData.projects.filter(function (p) {
        return (
          p.key.toUpperCase().startsWith(projectPrefix.toUpperCase()) ||
          p.name.toLowerCase().startsWith(projectPrefix.toLowerCase())
        );
      });
      if (projectPartials.length > 0) {
        return (
          'Unknown project "' + projectPrefix + '" - did you mean "' + projectPartials[0].key + '"?'
        );
      }
      return 'Unknown project "' + projectPrefix + '" - select from suggestions';
    }
  }

  if (!fieldPart) {
    return 'Missing field name';
  }

  var fieldLower = fieldPart.toLowerCase();
  var fieldValid = false;
  var fieldInfo = null;

  if (window._nsa.BUILT_IN_FIELDS.includes(fieldLower)) {
    fieldValid = true;
  }

  if (!fieldValid && autocompleteData && autocompleteData.fields) {
    fieldInfo = autocompleteData.fields.find(function (f) {
      return (
        f.id === fieldPart ||
        f.id.toLowerCase() === fieldLower ||
        f.name === fieldPart ||
        f.name.toLowerCase() === fieldLower
      );
    });
    if (fieldInfo) {
      fieldValid = true;
    }
  }

  if (!fieldValid && /^customfield_\d+$/i.test(fieldPart)) {
    fieldValid = true;
  }

  if (!fieldValid) {
    if (autocompleteData && autocompleteData.fields) {
      var fieldPartials = autocompleteData.fields.filter(function (f) {
        return (
          f.id.toLowerCase().startsWith(fieldLower) || f.name.toLowerCase().startsWith(fieldLower)
        );
      });
      if (fieldPartials.length > 0) {
        return (
          'Unknown field "' +
          fieldPart +
          '" - did you mean "' +
          fieldPartials[0].name +
          '" (' +
          fieldPartials[0].id +
          ')?'
        );
      }
    }
    return 'Unknown field "' + fieldPart + '" - select from autocomplete suggestions';
  }

  // Validate changelog value for known field types
  if (changelogValue) {
    if (fieldLower === 'status') {
      if (!autocompleteData || !autocompleteData.statuses) {
        return 'Cannot validate status "' + changelogValue + '" - metadata not loaded';
      }
      var validStatus = autocompleteData.statuses.find(function (s) {
        return s.name === changelogValue || s.name.toLowerCase() === changelogValue.toLowerCase();
      });
      if (!validStatus) {
        var statusPartials = autocompleteData.statuses.filter(function (s) {
          return s.name.toLowerCase().startsWith(changelogValue.toLowerCase());
        });
        if (statusPartials.length > 0) {
          return (
            'Unknown status "' +
            changelogValue +
            '" - did you mean "' +
            statusPartials[0].name +
            '"?'
          );
        }
        var similarStatuses = autocompleteData.statuses.filter(function (s) {
          return (
            s.name.toLowerCase().includes(changelogValue.toLowerCase()) ||
            changelogValue.toLowerCase().includes(s.name.toLowerCase().substring(0, 3))
          );
        });
        if (similarStatuses.length > 0) {
          return (
            'Unknown status "' + changelogValue + '" - similar: "' + similarStatuses[0].name + '"'
          );
        }
        return 'Unknown status "' + changelogValue + '" - select from autocomplete suggestions';
      }
    }

    if (fieldLower === 'issuetype') {
      if (!autocompleteData || !autocompleteData.issueTypes) {
        return 'Cannot validate issue type "' + changelogValue + '" - metadata not loaded';
      }
      var validType = autocompleteData.issueTypes.find(function (t) {
        return t.name === changelogValue || t.name.toLowerCase() === changelogValue.toLowerCase();
      });
      if (!validType) {
        var typePartials = autocompleteData.issueTypes.filter(function (t) {
          return t.name.toLowerCase().startsWith(changelogValue.toLowerCase());
        });
        if (typePartials.length > 0) {
          return (
            'Unknown issue type "' +
            changelogValue +
            '" - did you mean "' +
            typePartials[0].name +
            '"?'
          );
        }
        return 'Unknown issue type "' + changelogValue + '" - select from autocomplete suggestions';
      }
    }

    if (fieldLower === 'priority' && autocompleteData && autocompleteData.priorities) {
      var validPriority = autocompleteData.priorities.find(function (p) {
        return p.name === changelogValue || p.name.toLowerCase() === changelogValue.toLowerCase();
      });
      if (!validPriority) {
        var priorityPartials = autocompleteData.priorities.filter(function (p) {
          return p.name.toLowerCase().startsWith(changelogValue.toLowerCase());
        });
        if (priorityPartials.length > 0) {
          return (
            'Unknown priority "' +
            changelogValue +
            '" - did you mean "' +
            priorityPartials[0].name +
            '"?'
          );
        }
        return 'Unknown priority "' + changelogValue + '" - select from autocomplete suggestions';
      }
    }

    if (fieldLower === 'resolution' && autocompleteData && autocompleteData.resolutions) {
      var validResolution = autocompleteData.resolutions.find(function (r) {
        return r.name === changelogValue || r.name.toLowerCase() === changelogValue.toLowerCase();
      });
      if (!validResolution) {
        var resolutionPartials = autocompleteData.resolutions.filter(function (r) {
          return r.name.toLowerCase().startsWith(changelogValue.toLowerCase());
        });
        if (resolutionPartials.length > 0) {
          return (
            'Unknown resolution "' +
            changelogValue +
            '" - did you mean "' +
            resolutionPartials[0].name +
            '"?'
          );
        }
        return 'Unknown resolution "' + changelogValue + '" - select from autocomplete suggestions';
      }
    }
  }

  return null; // All validations passed
};
