---
name: 'frontend-javascript-quality'
description: 'Implement reliable and maintainable JavaScript/clientside callback changes'
---

# Skill: Frontend JavaScript Quality

Use this skill when working in `assets/` with JavaScript files, clientside callbacks, or CSS.

## Goals

- Maintain React-compatible clientside callback patterns
- Ensure cross-browser compatibility and performance
- Keep JavaScript modular, testable, and well-documented
- Prevent memory leaks and performance degradation

## Workflow

1. **Identify scope**: Determine which clientside callbacks or UI behaviors need changes
2. **Read context**: Load relevant JS files and related Python callback files
3. **Apply patterns**: Follow Dash clientside callback conventions and repository standards
4. **Test**: Verify in browser, check console for errors, validate performance
5. **Validate**: Run `get_errors` and check for linting issues

## Key files to consider

### Clientside callbacks

- `assets/namespace_autocomplete_clientside.js` - Complex autocomplete behavior
- `assets/viewport_detection.js` - Responsive layout detection
- `assets/jql_editor_*.js` - JQL editor clientside logic
- `assets/update_*.js` - Update UI handling
- `assets/modal_keyboard_fix.js` - A11y improvements

### CSS modules

- `assets/custom.css` - Global styles
- `assets/components/*.css` - Component-specific styles
- `assets/layout/*.css` - Layout patterns

### Python callback coordinators

- `callbacks/*.py` - Server callbacks that work with clientside callbacks

## Enforcement points

### JavaScript patterns

**Namespace registration**:

```javascript
// ✓ GOOD: Namespaced with clear purpose
window.dash_clientside = window.dash_clientside || {};
window.dash_clientside.namespace_autocomplete = {
  buildAutocompleteData: function(metadata) { ... }
};

// ❌ BAD: Global pollution
function myFunction() { ... }
```

**Event handlers**:

```javascript
// ✓ GOOD: Clean up before adding
element.removeEventListener('click', handler);
element.addEventListener('click', handler);

// ❌ BAD: Memory leak (duplicate handlers)
element.addEventListener('click', handler);
```

**React controlled inputs**:

```javascript
// ✓ GOOD: Use native setters + dispatch events
const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
  window.HTMLInputElement.prototype,
  'value'
).set;
nativeInputValueSetter.call(input, newValue);
input.dispatchEvent(new Event('input', { bubbles: true }));

// ❌ BAD: Direct assignment (React won't detect)
input.value = newValue;
```

**Performance**:

```javascript
// ✓ GOOD: Debounce expensive operations
function debounce(func, wait) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

// Use for resize, scroll, input
window.addEventListener('resize', debounce(handler, 150));
```

### CSS patterns

**BEM naming**:

```css
/* ✓ GOOD: Scoped, semantic */
.namespace-autocomplete-dropdown {
}
.namespace-autocomplete__item--active {
}

/* ❌ BAD: Generic, conflicts */
.dropdown {
}
.active {
}
```

**CSS custom properties**:

```css
/* ✓ GOOD: DRY, themeable */
:root {
  --primary-color: #007bff;
  --spacing-unit: 8px;
}
.button {
  background: var(--primary-color);
}

/* ❌ BAD: Hardcoded values everywhere */
.button {
  background: #007bff;
}
```

### Performance targets

| Metric          | Target | Measurement         |
| --------------- | ------ | ------------------- |
| Event handler   | <16ms  | Browser profiler    |
| DOM query cache | Always | Cache selectors     |
| Debounce input  | 150ms  | User input handlers |

## Guardrails

- No emoji in JS code or comments
- Always clean up event listeners and timeouts
- Test in both desktop and mobile viewports
- Validate A11y with keyboard navigation
- Check browser console for errors
- Never expose credentials or API keys in frontend code
- Use sanitized test data in comments/examples

## Suggested validations

- `get_errors` for changed files
- Browser console check (no errors/warnings)
- Test keyboard navigation
- Test mobile viewport behavior
- Performance profiling for expensive operations

## Related files often modified together

When changing clientside callbacks in `assets/`, also review:

- Corresponding Python callback in `callbacks/`
- UI component builder in `ui/`
- Related CSS in `assets/` or `assets/components/`

## Documentation references

- `docs/architecture/javascript_guidelines.md` - JavaScript coding standards
- `docs/architecture/css_guidelines.md` - CSS coding standards
- `docs/design_system.md` - Design system and UI patterns
