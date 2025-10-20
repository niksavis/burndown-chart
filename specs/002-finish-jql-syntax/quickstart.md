# Developer Quickstart: JQL Syntax Highlighting with CodeMirror 6

**Feature**: Complete JQL Syntax Highlighting with Real-time Visual Feedback  
**Branch**: `002-finish-jql-syntax`  
**Last Updated**: 2025-10-20

## Overview

This guide helps developers implement JQL syntax highlighting using **CodeMirror 6 via CDN** (JavaScript library, NOT a Python package).

**CRITICAL**: No `dash-codemirror` Python package exists. This feature uses standard web integration: CDN-loaded JavaScript library + client-side initialization.

**Time to Implementation**: ~2-4 hours for MVP (User Story 1)

---

## Prerequisites

✅ **Required**:
- Python 3.11+ with virtual environment activated
- Dash 2.x already installed (existing project dependency)
- Modern browser (Chrome/Firefox/Safari/Edge - latest 6 months)
- Playwright installed for integration testing

❌ **NOT Required**:
- No new Python packages to install
- No custom React component build process
- No npm/node.js setup

---

## Installation Steps

### Step 1: No Python Package Installation Needed

**Previous (incorrect) assumption**:
```bash
# ❌ This package doesn't exist
pip install dash-codemirror
```

**Reality**:
```bash
# ✅ No pip install needed - CodeMirror loads via CDN
# Just verify existing dependencies work
.\.venv\Scripts\activate; python -c "import dash; print(f'Dash {dash.__version__} ready')"
```

### Step 2: Include CodeMirror 6 via CDN

**Option A**: Use `external_scripts` in `app.py` (Recommended):

```python
from dash import Dash

app = Dash(
    __name__,
    external_scripts=[
        # CodeMirror 6 core library (ESM bundle)
        "https://cdn.jsdelivr.net/npm/codemirror@6/dist/index.min.js",
    ]
)
```

**Option B**: Load in custom JavaScript file (`assets/jql_editor_init.js`):

```javascript
// Dynamically load CodeMirror from CDN
const script = document.createElement('script');
script.src = 'https://cdn.jsdelivr.net/npm/codemirror@6/dist/index.min.js';
script.type = 'module';
document.head.appendChild(script);
```

### Step 3: Install Playwright for Integration Testing

```powershell
.\.venv\Scripts\activate; pip install pytest-playwright
.\.venv\Scripts\activate; playwright install chromium
```

---

## Architecture Overview

### Component Stack

```
┌─────────────────────────────────────────┐
│  User Types in Browser                  │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  CodeMirror 6 Editor (JavaScript)       │
│  - Loaded from CDN                      │
│  - Custom JQL language mode             │
│  - Real-time tokenization (<50ms)       │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  JavaScript Initialization Logic        │
│  (assets/jql_editor_init.js)            │
│  - Attaches CodeMirror to container div │
│  - Syncs value to dcc.Store()           │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│  Dash Components (Python)               │
│  - html.Div() container                 │
│  - dcc.Store() for state sync           │
│  - Existing callbacks unchanged         │
└─────────────────────────────────────────┘
```

### File Organization

```
ui/
├── jql_editor.py           # NEW: Returns html.Div() + dcc.Store()

assets/
├── jql_language_mode.js    # NEW: Custom JQL tokenizer (StreamLanguage)
├── jql_editor_init.js      # NEW: CodeMirror initialization + sync logic
└── custom.css              # MODIFIED: Add .cm-jql-* token styles

app.py                      # MODIFIED: Replace dbc.Textarea with create_jql_editor()

tests/integration/dashboard/
└── test_jql_editor_workflow.py  # NEW: Playwright visual tests
```

---

## TDD Workflow

### Phase 1: Write Failing Tests (Red)

**Create Playwright test for keyword highlighting**:

```python
# tests/integration/dashboard/test_jql_editor_workflow.py
from playwright.sync_api import sync_playwright

def test_keyword_highlighting():
    """Test that JQL keywords appear in blue color."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8050")
        
        # Find editor container
        editor = page.locator('.jql-editor-container')
        
        # Type keyword
        editor.type("AND")
        
        # Verify blue color (#0066cc)
        keyword_span = page.locator('.cm-jql-keyword')
        color = keyword_span.evaluate('el => getComputedStyle(el).color')
        assert color == 'rgb(0, 102, 204)'  # #0066cc in RGB
        
        browser.close()
```

**Run test** (should FAIL - editor not created yet):

```powershell
.\.venv\Scripts\activate; pytest tests/integration/dashboard/test_jql_editor_workflow.py::test_keyword_highlighting -v
# Expected: FAILED - Element not found
```

### Phase 2: Make Test Pass (Green)

**Step 1**: Create Python container component:

```python
# ui/jql_editor.py
from dash import html, dcc

def create_jql_editor(editor_id, value="", placeholder="Enter JQL query...", 
                      aria_label="JQL Query Editor", height="200px"):
    """Create container for CodeMirror editor with Dash state sync."""
    return html.Div([
        # Container that JavaScript will turn into CodeMirror editor
        html.Div(
            id=f"{editor_id}-codemirror-container",
            className="jql-editor-container",
            **{"aria-label": aria_label, "role": "textbox", "data-placeholder": placeholder}
        ),
        
        # Hidden store for Dash callback synchronization
        dcc.Store(id=editor_id, data=value),
        
        # Hidden textarea for accessibility fallback
        html.Textarea(
            id=f"{editor_id}-hidden",
            value=value,
            style={"display": "none"},
            **{"aria-label": aria_label}
        )
    ], style={"height": height})
```

**Step 2**: Create JQL language mode:

```javascript
// assets/jql_language_mode.js

// JQL keywords (case-insensitive)
const JQL_KEYWORDS = /\b(AND|OR|NOT|IN|IS|WAS|EMPTY|NULL|ORDER|BY|ASC|DESC)\b/i;

// Define JQL language mode using StreamLanguage
const jqlLanguageMode = {
    startState: () => ({ inString: false }),
    
    token: (stream, state) => {
        // Skip whitespace
        if (stream.eatSpace()) return null;
        
        // Keywords
        if (stream.match(JQL_KEYWORDS)) {
            return "jql-keyword";
        }
        
        // Default: consume character
        stream.next();
        return null;
    }
};

// Export for use in initialization
window.jqlLanguageMode = jqlLanguageMode;
```

**Step 3**: Create initialization script:

```javascript
// assets/jql_editor_init.js

document.addEventListener('DOMContentLoaded', function() {
    // Wait for CodeMirror to load from CDN
    if (typeof EditorView === 'undefined') {
        console.error('CodeMirror not loaded from CDN');
        return;
    }
    
    // Find all editor containers
    const containers = document.querySelectorAll('.jql-editor-container');
    
    containers.forEach(container => {
        // Get configuration from data attributes
        const placeholder = container.dataset.placeholder || "";
        const storeId = container.id.replace('-codemirror-container', '');
        const store = document.getElementById(storeId);
        const initialValue = store ? store.dataset.data || "" : "";
        
        // Initialize CodeMirror editor
        const editor = new EditorView({
            doc: initialValue,
            extensions: [
                basicSetup,
                StreamLanguage.define(window.jqlLanguageMode),
                lineWrapping(),
                placeholder(placeholder),
                
                // Sync changes to Dash Store
                EditorView.updateListener.of((update) => {
                    if (update.docChanged && store) {
                        const value = update.state.doc.toString();
                        store.setAttribute('data-data', value);
                        // Trigger Dash callback
                        store.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                })
            ],
            parent: container
        });
        
        // Store editor reference for debugging
        container._editorView = editor;
    });
});
```

**Step 4**: Add CSS token styles:

```css
/* assets/custom.css */

/* CodeMirror JQL Token Styles (WCAG AA compliant) */
.cm-jql-keyword {
    color: #0066cc;           /* Blue - 4.78:1 contrast ratio */
    font-weight: bold;
}

.cm-jql-string {
    color: #22863a;           /* Green - 4.98:1 contrast ratio */
}

.cm-jql-operator {
    color: #6c757d;           /* Gray - 4.54:1 contrast ratio */
}

.cm-jql-function,
.cm-jql-scriptrunner {
    color: #8b008b;           /* Purple - 6.38:1 contrast ratio */
    font-style: italic;
}

.cm-jql-error {
    text-decoration: wavy underline red;
    background-color: #ffebee;
}

/* Mobile-first responsive editor container */
.jql-editor-container {
    border: 1px solid #dee2e6;
    border-radius: 4px;
    padding: 8px;
    min-height: 100px;
}

@media (max-width: 768px) {
    .jql-editor-container {
        font-size: 16px;      /* Prevent iOS zoom on focus */
        padding: 12px;        /* Larger touch targets */
    }
}
```

**Step 5**: Update app layout:

```python
# app.py
from ui.jql_editor import create_jql_editor

# Replace existing dbc.Textarea with new editor
layout = html.Div([
    # ... other components
    
    # OLD (remove):
    # dbc.Textarea(id="jira-jql-query", value="", placeholder="Enter JQL...")
    
    # NEW:
    create_jql_editor(
        editor_id="jira-jql-query",
        value="",
        placeholder="Enter JQL query (e.g., project = TEST AND status = Open)",
        aria_label="JIRA JQL Query Editor",
        height="200px"
    ),
    
    # ... other components
])
```

**Run test again** (should PASS):

```powershell
.\.venv\Scripts\activate; pytest tests/integration/dashboard/test_jql_editor_workflow.py::test_keyword_highlighting -v
# Expected: PASSED
```

### Phase 3: Refactor (if needed)

- Extract common patterns
- Improve performance
- Add comments
- Validate WCAG AA compliance

---

## Key Files Reference

### New Files

| File                                                      | Purpose                     | Lines | Complexity |
| --------------------------------------------------------- | --------------------------- | ----- | ---------- |
| `ui/jql_editor.py`                                        | Container component factory | ~30   | Low        |
| `assets/jql_language_mode.js`                             | JQL tokenizer               | ~100  | Medium     |
| `assets/jql_editor_init.js`                               | CodeMirror initialization   | ~50   | Medium     |
| `tests/integration/dashboard/test_jql_editor_workflow.py` | Playwright tests            | ~200  | Medium     |

### Modified Files

| File                    | Changes                                              | Risk |
| ----------------------- | ---------------------------------------------------- | ---- |
| `app.py`                | Replace `dbc.Textarea` with `create_jql_editor()`    | Low  |
| `assets/custom.css`     | Add `.cm-jql-*` token styles                         | Low  |
| `callbacks/settings.py` | Verify existing callbacks work (NO CHANGES expected) | Low  |

### Deprecated Files (Remove)

| File                                       | Reason                              |
| ------------------------------------------ | ----------------------------------- |
| `assets/jql_syntax.css`                    | Replaced by CodeMirror + custom.css |
| `assets/jql_syntax.js`                     | Replaced by jql_editor_init.js      |
| `ui/components.py::parse_jql_syntax()`     | Replaced by CodeMirror tokenizer    |
| `ui/components.py::render_syntax_tokens()` | No longer needed                    |

---

## Testing Strategy

### Unit Tests: NONE (Per Constitution)

**Reasoning**: UI component wrappers don't require unit tests per project constitution. Visual behavior is validated via Playwright.

### Integration Tests: Playwright (Visual Validation)

**Test Categories**:

1. **Syntax Highlighting** (6 tests):
   - Keyword highlighting (blue)
   - String highlighting (green)
   - Operator highlighting (gray)
   - Function highlighting (purple)
   - ScriptRunner highlighting (purple)
   - Error highlighting (red underline)

2. **Performance** (3 tests):
   - Keystroke latency <50ms
   - Paste performance <300ms for 1000 chars
   - 60fps typing (no dropped frames)

3. **Mobile Responsiveness** (2 tests):
   - 320px viewport (iPhone SE)
   - Touch interaction (cursor positioning)

4. **Accessibility** (2 tests):
   - Keyboard navigation
   - Screen reader compatibility

**Run all tests**:

```powershell
.\.venv\Scripts\activate; pytest tests/integration/dashboard/test_jql_editor_workflow.py -v
```

---

## Performance Targets Checklist

✅ **Keystroke Latency**: <50ms from keypress to visual update  
✅ **Paste Performance**: <300ms for 1000-character query  
✅ **Frame Rate**: 60fps during typing (no dropped frames)  
✅ **Bundle Size**: CodeMirror 6 ~100KB gzipped (CDN cached)  
✅ **Memory Usage**: <1MB for editor instance  
✅ **Mobile Performance**: Works on 320px viewport (iPhone SE)

**Validation**:

```javascript
// Chrome DevTools Performance profiler
// 1. Open DevTools > Performance tab
// 2. Start recording
// 3. Type in JQL editor
// 4. Stop recording
// 5. Check "Main" thread - should see <50ms between events
```

---

## Troubleshooting

### Issue: CodeMirror not loading from CDN

**Symptom**: Editor container remains empty, console error "CodeMirror not loaded"

**Solution**:
```javascript
// Check CDN availability
console.log(typeof EditorView); // Should NOT be 'undefined'

// Verify script tag in HTML
document.querySelector('script[src*="codemirror"]'); // Should exist
```

### Issue: Syntax highlighting not working

**Symptom**: Keywords typed but no color changes

**Solution**:
```css
/* Verify CSS classes exist */
.cm-jql-keyword { color: #0066cc; } /* Check in DevTools */

/* Verify tokenizer is attached */
console.log(window.jqlLanguageMode); // Should be defined
```

### Issue: Dash callbacks not receiving value

**Symptom**: Typing in editor doesn't trigger callbacks

**Solution**:
```javascript
// Check Store synchronization
const store = document.getElementById('jira-jql-query');
console.log(store.dataset.data); // Should match editor content

// Verify event dispatching
store.addEventListener('change', () => console.log('Store changed'));
```

### Issue: Mobile keyboard not appearing

**Symptom**: Tapping editor on mobile doesn't show keyboard

**Solution**:
```css
/* Ensure input is focusable */
.cm-content {
    -webkit-user-select: text;
    user-select: text;
}
```

---

## Next Steps

1. **Implement MVP** (User Story 1): Basic keyword/string/operator highlighting
2. **Add ScriptRunner** (User Story 2): Extend tokenizer with ScriptRunner functions
3. **Add Error Detection** (User Story 3): Implement unclosed quote detection
4. **Validate Performance**: Run Chrome DevTools profiler
5. **Mobile Testing**: Test on real iPhone/Android devices

---

## Additional Resources

- **CodeMirror 6 Docs**: https://codemirror.net/docs/
- **StreamLanguage API**: https://codemirror.net/docs/ref/#language.StreamLanguage
- **Playwright Docs**: https://playwright.dev/python/
- **WCAG Color Contrast**: https://webaim.org/resources/contrastchecker/

---

**Document Version**: 1.0 (2025-10-20 - Updated for CDN reality check)
