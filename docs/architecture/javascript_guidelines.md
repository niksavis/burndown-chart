# JavaScript Architecture Guidelines

**Purpose**: Create maintainable, modular JavaScript that is easily understood and modified by both humans and AI agents. These guidelines enforce:

- **Code clarity**: Functions and files sized for quick comprehension
- **Modularity**: Independent, reusable components
- **Modern patterns**: ES6 modules, async/await, event handling best practices
- **Performance**: Optimized DOM manipulation and minimal repaints
- **Maintainability**: Clear separation of concerns for clientside callbacks (when used)
- **AI collaboration**: Structures optimized for AI-assisted development

## Terminology and Enforcement

- **MUST**: Required rule for all new/updated JavaScript in scope.
- **SHOULD**: Strong recommendation; deviations need a clear reason.
- **MAY**: Optional guidance for context-specific improvements.

Critical/hard limits in this document are **MUST** constraints.

## 2026 Standards Refresh (MDN-aligned)

Apply these as current defaults for new and updated JavaScript:

- Prefer ESM (`import`/`export`) and avoid introducing new global-script patterns.
- Use `async`/`await` with explicit error handling (`try`/`catch`) around network and async boundaries.
- Support cancellation in fetch/data workflows with `AbortController` for user-triggered refresh, navigation, or timeout paths.
- Use `addEventListener` options intentionally (`{ passive: true }` for scroll/touch where appropriate, `{ once: true }` for one-shot handlers).
- Default to `const`; use `let` only for reassignment; do not introduce `var`.
- Avoid deprecated patterns such as synchronous XHR and legacy implicit-global assignments.

## File Size Limits

**CRITICAL RULES**:

- **Maximum file size**: 400 lines (hard limit)
- **Target size**: 150-250 lines per file
- **Warning threshold**: 300 lines → refactor immediately

## File Organization (Airbnb Style Guide)

### Naming Conventions

Follow your repository naming rules. If your project defines file naming conventions in repo-level instructions, those take precedence.

```javascript
// Example patterns (adjust to your repo rules)
// files: feature_component.js or featureComponent.js
// exports: match default export name
export default class ComponentName {}
export default function buildComponent() { return null; }
```

### Structure Pattern

```
assets/
├── core/
│   ├── api.js              # API calls (< 200 lines)
│   └── storage.js          # Local storage (< 150 lines)
├── components/
│   ├── modal.js            # Modal component (< 250 lines)
│   └── toast.js            # Toast notifications (< 150 lines)
├── clientside/
│   ├── searchEditor.js     # Search editor logic (< 300 lines)
│   └── autocomplete.js     # Autocomplete logic (< 250 lines)
└── utils/
    └── helpers.js          # Utilities (< 100 lines)
```

## Module Pattern

### ES6 Modules (Preferred)

```javascript
// GOOD: Named exports for utilities
// helpers.js
export function formatDate(date) {
  return date.toISOString();
}

export function parseJSON(str) {
  try {
    return JSON.parse(str);
  } catch {
    return null;
  }
}

// GOOD: Default export for single component
// modal.js
export default class Modal {
  constructor(options) {
    this.options = options;
  }

  show() {
    // Implementation
  }

  hide() {
    // Implementation
  }
}
```

### Import Organization (Airbnb Style Guide)

```javascript
// 1. External dependencies
import React from 'react';
import { debounce, throttle } from 'lodash';

// 2. Internal modules (grouped, not duplicated)
import Modal, { ModalHeader } from './components/Modal';
import { formatDate, parseJSON } from './utils/helpers';

// 3. Styles (if applicable)
import './styles.css';

// All imports before other code
const API_URL = '/api/data';

function fetchData() {
  // Implementation
}
```

## Breaking Down Large Files

### Strategy 1: Feature-Based Split

**Before** (800 lines):

```
assets/search_editor_complete.js
```

**After**:

```
assets/search_editor/
├── core.js             # Core editor logic (< 250 lines)
├── autocomplete.js     # Autocomplete feature (< 200 lines)
├── syntax.js           # Syntax highlighting (< 200 lines)
└── validation.js       # Input validation (< 150 lines)
```

### Strategy 2: Responsibility Split

```javascript
// BEFORE: One god object (600 lines)
const appHandlers = {
  handleInput: function () {
    /* 100 lines */
  },
  handleSubmit: function () {
    /* 150 lines */
  },
  validateForm: function () {
    /* 120 lines */
  },
  formatOutput: function () {
    /* 80 lines */
  },
  // ... more functions
};

// AFTER: Split by responsibility
// input_handlers.js (< 200 lines)
export const inputHandlers = {
  handleInput: function () {
    /* 80 lines */
  },
  handleSubmit: function () {
    /* 100 lines */
  },
};

// validation.js (< 150 lines)
export const validationHandlers = {
  validateForm: function () {
    /* 100 lines */
  },
};

// formatting.js (< 150 lines)
export const formatHandlers = {
  formatOutput: function () {
    /* 70 lines */
  },
};
```

## Function Design

### Maximum Lines Per Function

- **Simple functions**: < 15 lines
- **Complex functions**: < 40 lines
- **Hard limit**: 60 lines → must refactor

### Early Returns (Airbnb Style Guide)

```javascript
// BAD: Nested conditionals (high cognitive complexity)
function processData(data) {
  if (data) {
    if (data.valid) {
      if (data.items.length > 0) {
        return data.items.map((item) => item.value);
      }
    }
  }
  return [];
}

// GOOD: Early returns
function processData(data) {
  if (!data) return [];
  if (!data.valid) return [];
  if (data.items.length === 0) return [];

  return data.items.map((item) => item.value);
}
```

### Function Decomposition

```javascript
// BAD: One large function (80 lines)
function initializeEditor(config) {
  // Parse config (15 lines)
  // Setup DOM (20 lines)
  // Bind events (25 lines)
  // Initialize plugins (20 lines)
}

// GOOD: Split into focused functions
function initializeEditor(config) {
  const parsedConfig = parseConfig(config);
  const editor = setupDOM(parsedConfig);
  bindEvents(editor);
  initializePlugins(editor, parsedConfig.plugins);
  return editor;
}

function parseConfig(config) {
  // 10 lines
}

function setupDOM(config) {
  // 15 lines
}

function bindEvents(editor) {
  // 20 lines
}

function initializePlugins(editor, plugins) {
  // 15 lines
}
```

## Framework-Specific Patterns (Optional)

### Clientside Namespace Example

```javascript
// Example for clientside callback namespaces (if applicable in your framework)
window.app = window.app || {};
window.app.feature = {
  handleInput: function (value) {
    if (!value) return { valid: false };
    return { valid: true };
  },
};

// Helper functions outside the namespace
function getSuggestions(value) {
  // 30 lines
}

function validateQuery(query) {
  // 25 lines
}
```

### Separate Files by Feature

```javascript
// search_input.js (< 200 lines)
window.app.searchInput = {
  handleKeyPress: function () {
    /* ... */
  },
  handlePaste: function () {
    /* ... */
  },
};

// search_autocomplete.js (< 250 lines)
window.app.searchAutocomplete = {
  showSuggestions: function () {
    /* ... */
  },
  selectSuggestion: function () {
    /* ... */
  },
};

// search_validation.js (< 150 lines)
window.app.searchValidation = {
  validateSyntax: function () {
    /* ... */
  },
  showErrors: function () {
    /* ... */
  },
};
```

## Code Style

### Constants

```javascript
// GOOD: Constants at top
const MAX_SUGGESTIONS = 10;
const DEBOUNCE_DELAY = 300;
const API_ENDPOINT = '/api/query/validate';

function fetchSuggestions(query) {
  return fetch(`${API_ENDPOINT}?q=${query}`);
}
```

### Grouping const and let

```javascript
// GOOD: Group const declarations first
const apiUrl = '/api/data';
const maxRetries = 3;
const timeout = 5000;

let currentPage = 1;
let results = [];
let isLoading = false;
```

### Object/Array Formatting

```javascript
// GOOD: Consistent formatting
const config = {
  url: '/api/data',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 5000,
};

const items = ['item1', 'item2', 'item3'];
```

## Error Handling

### Try-Catch Best Practices

```javascript
// GOOD: Specific error handling
function parseJSON(jsonString) {
  try {
    return JSON.parse(jsonString);
  } catch (error) {
    console.error('JSON parse error:', error.message);
    return null;
  }
}

// GOOD: Async error handling
async function fetchData(url) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  try {
    const response = await fetch(url, { signal: controller.signal });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (error.name === 'AbortError') {
      return { error: 'Request timed out or was cancelled' };
    }
    console.error('Fetch error:', error);
    return { error: error.message };
  } finally {
    clearTimeout(timeoutId);
  }
}
```

## Event Handling

### Debounce/Throttle

```javascript
// GOOD: Debounce user input
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Usage
const debouncedSearch = debounce(function (query) {
  // Expensive search operation
  performSearch(query);
}, 300);

input.addEventListener('input', (e) => {
  debouncedSearch(e.target.value);
});
```

### Event Delegation

```javascript
// GOOD: Event delegation for dynamic content
document.getElementById('list').addEventListener('click', (e) => {
  // Handle clicks on list items
  if (e.target.matches('.list-item')) {
    handleItemClick(e.target);
  }

  // Handle clicks on delete buttons
  if (e.target.matches('.delete-btn')) {
    handleDelete(e.target.closest('.list-item'));
  }
});
```

## DOM Manipulation

### Minimize Reflows

```javascript
// BAD: Multiple reflows
function addItems(items) {
  items.forEach((item) => {
    const div = document.createElement('div');
    div.textContent = item;
    container.appendChild(div); // Reflow on each append
  });
}

// GOOD: Single reflow
function addItems(items) {
  const fragment = document.createDocumentFragment();

  items.forEach((item) => {
    const div = document.createElement('div');
    div.textContent = item;
    fragment.appendChild(div);
  });

  container.appendChild(fragment); // Single reflow
}
```

### Query Selectors

```javascript
// GOOD: Cache selectors
const modal = document.getElementById('modal');
const modalTitle = modal.querySelector('.modal-title');
const modalBody = modal.querySelector('.modal-body');

function showModal(title, content) {
  modalTitle.textContent = title;
  modalBody.textContent = content;
  modal.classList.add('show');
}

// BAD: Repeated queries
function showModal(title, content) {
  document.querySelector('.modal-title').textContent = title;
  document.querySelector('.modal-body').textContent = content;
  document.getElementById('modal').classList.add('show');
}
```

## Asynchronous Code

### Async/Await (Preferred)

```javascript
// GOOD: Clean async/await
async function loadData() {
  const controller = new AbortController();

  try {
    const response = await fetch('/api/data', { signal: controller.signal });
    const data = await response.json();
    return processData(data);
  } catch (error) {
    if (error.name === 'AbortError') {
      return null;
    }
    console.error('Load error:', error);
    return null;
  }
}

// Sequential operations
async function processWorkflow() {
  const data = await fetchData();
  const validated = await validateData(data);
  const transformed = await transformData(validated);
  return transformed;
}

// Parallel operations
async function loadMultiple() {
  const [users, posts, comments] = await Promise.all([fetchUsers(), fetchPosts(), fetchComments()]);

  return { users, posts, comments };
}
```

## Comments and Documentation

### JSDoc Comments

```javascript
/**
 * Fetch items based on a query
 * @param {string} query - Query string
 * @param {number} [maxResults=100] - Maximum results to return
 * @param {Object} [options={}] - Additional options
 * @param {boolean} [options.includeFields=false] - Include all fields
 * @returns {Promise<Array<Object>>} Array of issue objects
 * @throws {Error} If query is invalid or API request fails
 */
async function fetchItems(query, maxResults = 100, options = {}) {
  // Implementation
}

/**
 * Modal component for displaying dialogs
 * @class
 */
class Modal {
  /**
   * Create a modal
   * @param {Object} options - Configuration options
   * @param {string} options.title - Modal title
   * @param {string} options.content - Modal content
   */
  constructor(options) {
    this.title = options.title;
    this.content = options.content;
  }

  /**
   * Show the modal
   * @returns {void}
   */
  show() {
    // Implementation
  }
}
```

### Inline Comments

```javascript
// GOOD: Explain why, not what
function calculateDiscount(price, userLevel) {
  // Premium users get 20% discount regardless of price
  if (userLevel === 'premium') {
    return price * 0.8;
  }

  // Regular users get tiered discounts based on price
  return price > 100 ? price * 0.9 : price * 0.95;
}

// BAD: Obvious comments
function calculateTotal(price) {
  // Multiply price by quantity
  return price * quantity;
}
```

## Testing Considerations

### Testable Functions

```javascript
// GOOD: Pure function (easy to test)
function calculateTotal(items) {
  return items.reduce((sum, item) => sum + item.price, 0);
}

// GOOD: Separate concerns
function updateUI(total) {
  document.getElementById('total').textContent = total;
}

// Use together
function displayTotal(items) {
  const total = calculateTotal(items);
  updateUI(total);
}
```

## Optional: Framework Callback Patterns

If your framework requires global namespaces or callback registries, keep one namespace per feature, keep helpers outside the namespace, and document parameters and return values.

## Performance Best Practices

### Minimize Bundle Size

```javascript
// GOOD: Import only what you need
import { debounce } from 'lodash/debounce';

// BAD: Import entire library
import _ from 'lodash';
```

### Lazy Loading

```javascript
// GOOD: Load heavy modules only when needed
async function loadEditor() {
  const { Editor } = await import('./components/Editor.js');
  return new Editor();
}

// Initialize only when user clicks
document.getElementById('editor-btn').addEventListener('click', async () => {
  const editor = await loadEditor();
  editor.show();
});
```

## Refactoring Checklist

When file exceeds 300 lines:

- [ ] Identify independent functions
- [ ] Extract utility functions to separate file
- [ ] Split by feature/responsibility
- [ ] Create focused modules
- [ ] Update imports
- [ ] Test functionality unchanged

## AI Agent Guidelines

### Before Creating New Code

1. Check existing file size using your editor line count or repo tooling
2. If target file > 250 lines → create new file
3. Name file to match feature/export

### File Naming

```javascript
// GOOD: Descriptive, matches content
searchAutocomplete.js; // Feature-based
modalComponent.js; // Component-based
apiHelpers.js; // Utility-based

// BAD: Generic names
utils.js; // Too vague
helpers.js; // Too vague
misc.js; // Never acceptable
```

## Summary

**Key Principles**:

1. Files < 400 lines (hard limit)
2. Functions < 40 lines (target)
3. Early returns over nested conditions
4. Single responsibility per module
5. ES6 modules (import/export)
6. JSDoc for public APIs
7. Async/await for promises
8. Debounce/throttle user input
9. Cache DOM queries
10. Test pure functions

**Optional: Framework Clientside Pattern**:

- One namespace per feature
- Keep callbacks < 200 lines
- Extract helpers outside the clientside namespace
- Document parameters and return values
