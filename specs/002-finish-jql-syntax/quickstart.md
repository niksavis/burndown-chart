# Quickstart Guide: JQL Syntax Highlighting Implementation

**Feature**: Complete JQL Syntax Highlighting with Real-time Visual Feedback
**Branch**: `002-finish-jql-syntax`
**Date**: 2025-10-15

## Overview

This guide provides a quick reference for implementing the JQL syntax highlighting feature. It covers the architecture, key files, development workflow, and testing approach.

---

## Architecture Overview

### Dual-Layer Textarea Approach

```
┌─────────────────────────────────────┐
│   JQL Syntax Highlighter Component  │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Textarea (Z-index: 2)       │  │ ← User Input
│  │  - Transparent background    │  │
│  │  - Native keyboard handling  │  │
│  │  - Screen reader accessible  │  │
│  └──────────────────────────────┘  │
│           ↓                         │
│  ┌──────────────────────────────┐  │
│  │  Contenteditable Div (Z-1)   │  │ ← Visual Display
│  │  - Syntax-highlighted HTML   │  │
│  │  - aria-hidden="true"        │  │
│  │  - Scroll synced to textarea │  │
│  └──────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```

### Data Flow

```
User Types
    ↓
Textarea onChange Event
    ↓
JavaScript: requestAnimationFrame throttle
    ↓
Dash Callback: update_jql_syntax_highlighting()
    ↓
Python: parse_jql_syntax(query) → tokens
    ↓
Python: detect_syntax_errors(tokens) → errors
    ↓
Python: render_syntax_tokens(tokens, errors) → HTML
    ↓
Update Contenteditable Div (highlighting overlay)
    ↓
JavaScript: syncScrollPosition()
```

---

## Key Files

### New Files (Create)

1. **ui/jql_syntax_highlighter.py** (~100 lines)
   - `create_jql_syntax_highlighter()` - Main component factory
   - `detect_syntax_errors()` - Error detection logic
   - `is_scriptrunner_function()` - ScriptRunner function checker
   - Constants: SCRIPTRUNNER_FUNCTIONS frozenset

2. **assets/jql_syntax.css** (~100 lines)
   - `.jql-syntax-wrapper` - Container positioning
   - `.jql-syntax-input` - Textarea styling (transparent, z-index: 2)
   - `.jql-syntax-highlight` - Contenteditable div styling (z-index: 1)
   - `.jql-function` - ScriptRunner function color (purple)
   - `.jql-error-unclosed`, `.jql-error-invalid` - Error styling

3. **assets/jql_syntax.js** (~150 lines)
   - `initializeSyntaxHighlighting()` - Component initialization
   - `syncScrollPosition()` - Scroll synchronization
   - `handleTextareaInput()` - requestAnimationFrame throttling
   - Feature detection and graceful degradation

4. **tests/unit/ui/test_jql_syntax_highlighter.py** (~200 lines)
   - Test `create_jql_syntax_highlighter()` rendering
   - Test `detect_syntax_errors()` for unclosed quotes
   - Test `is_scriptrunner_function()` matching
   - Performance tests (<50ms parse time)

5. **tests/integration/dashboard/test_jql_highlighting_workflow.py** (~100 lines)
   - Playwright tests for visual feedback
   - Cursor position preservation tests
   - Mobile viewport tests (320px)
   - Error indication tests

### Modified Files (Update)

1. **ui/components.py**
   - Add `SCRIPTRUNNER_FUNCTIONS` frozenset (15 functions)
   - Modify `parse_jql_syntax()` to detect "function" token type
   - Modify `render_syntax_tokens()` to handle "function" and "error" types
   - Update `JQL_KEYWORDS` if needed (no changes expected)

2. **callbacks/settings.py**
   - Add `update_jql_syntax_highlighting()` callback
   - Add `update_character_count_with_highlighting()` (batch update)
   - Optional: Add `track_syntax_highlighting_performance()` callback

3. **assets/custom.css**
   - Add `.jql-function` class (purple color: #8b008b)
   - Add `.jql-error-unclosed`, `.jql-error-invalid` classes
   - Verify existing `.jql-keyword`, `.jql-string`, `.jql-operator` classes

---

## Development Workflow

### Step 1: Create Component Structure (TDD - Red Phase)

**Write failing tests first** (TDD Red):

```python
# tests/unit/ui/test_jql_syntax_highlighter.py

def test_create_jql_syntax_highlighter_returns_div():
    """Test component returns valid Dash div."""
    component = create_jql_syntax_highlighter("test-id")
    assert isinstance(component, html.Div)
    assert component.id == "test-id-wrapper"

def test_detect_unclosed_string_error():
    """Test detection of unclosed string."""
    tokens = [{"text": '"Done', "type": "string", "start": 0, "end": 5}]
    errors = detect_syntax_errors(tokens)
    
    assert len(errors) == 1
    assert errors[0]["error_type"] == "unclosed_string"
```

Run tests (should fail):
```powershell
.\.venv\Scripts\activate; pytest tests/unit/ui/test_jql_syntax_highlighter.py -v
```

**Implement minimum code to pass** (TDD Green):

```python
# ui/jql_syntax_highlighter.py

from dash import html
from typing import List, Dict, Any

SCRIPTRUNNER_FUNCTIONS = frozenset([
    "linkedIssuesOf", "issuesInEpics", "subtasksOf", "parentsOf", "epicsOf",
    "hasLinks", "hasComments", "hasAttachments", "lastUpdated", "expression",
    "dateCompare", "aggregateExpression", "issueFieldMatch",
    "linkedIssuesOfRecursive", "workLogged"
])

def create_jql_syntax_highlighter(
    component_id: str,
    value: str = "",
    placeholder: str = "Enter JQL query...",
    rows: int = 5,
    disabled: bool = False,
    aria_label: str = "JQL Query Input"
) -> html.Div:
    """Create dual-layer syntax-highlighted JQL textarea."""
    return html.Div(
        [
            # Contenteditable div for highlighting
            html.Div(
                id=f"{component_id}-highlight",
                className="jql-syntax-highlight",
                contentEditable="false",
                **{"aria-hidden": "true"}
            ),
            # Textarea for input
            html.Textarea(
                id=component_id,
                className="jql-syntax-input",
                value=value,
                placeholder=placeholder,
                rows=rows,
                disabled=disabled,
                **{"aria-label": aria_label}
            )
        ],
        id=f"{component_id}-wrapper",
        className="jql-syntax-wrapper"
    )

def detect_syntax_errors(tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect unclosed strings and invalid operators."""
    errors = []
    
    for token in tokens:
        # Check for unclosed strings
        if token.get("type") == "string":
            text = token.get("text", "")
            if text and text[0] in ('"', "'"):
                if len(text) < 2 or text[-1] != text[0]:
                    errors.append({
                        "error_type": "unclosed_string",
                        "start": token["start"],
                        "end": token["end"],
                        "token": token,
                        "message": "Unclosed string literal"
                    })
    
    return errors

def is_scriptrunner_function(word: str) -> bool:
    """Check if word is a ScriptRunner function."""
    return word in SCRIPTRUNNER_FUNCTIONS
```

Run tests (should pass):
```powershell
.\.venv\Scripts\activate; pytest tests/unit/ui/test_jql_syntax_highlighter.py -v
```

---

### Step 2: Add CSS Styling (TDD - Red Phase)

**Write visual tests first** (Playwright):

```python
# tests/integration/dashboard/test_jql_highlighting_workflow.py

def test_keyword_highlighting_appears(live_server):
    """Test keywords highlighted in blue."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(live_server)
        
        # Type query with keyword
        page.fill("#jql-query-input", "project = TEST AND status")
        page.wait_for_timeout(100)  # Wait for highlighting
        
        # Verify keyword highlighted
        keyword = page.locator(".jql-keyword").filter(has_text="AND")
        assert keyword.count() == 1
        
        # Verify color (should be blue #0066cc)
        color = keyword.evaluate("el => getComputedStyle(el).color")
        assert "0, 102, 204" in color  # RGB for #0066cc
        
        browser.close()
```

**Implement CSS** (assets/jql_syntax.css):

```css
/* Wrapper positioning */
.jql-syntax-wrapper {
    position: relative;
    width: 100%;
}

/* Highlight layer (behind) */
.jql-syntax-highlight {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    padding: 8px 12px;
    border: 1px solid transparent;
    border-radius: 4px;
    overflow: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
    pointer-events: none;
    z-index: 1;
    font-family: monospace;
    font-size: 14px;
    line-height: 1.5;
}

/* Input layer (front) */
.jql-syntax-input {
    position: relative;
    width: 100%;
    padding: 8px 12px;
    border: 1px solid #ced4da;
    border-radius: 4px;
    background: transparent;
    color: inherit;
    z-index: 2;
    font-family: monospace;
    font-size: 14px;
    line-height: 1.5;
    resize: vertical;
}

/* ScriptRunner function styling */
.jql-function {
    color: #8b008b;
    font-weight: 500;
}

/* Error styling */
.jql-error-unclosed {
    background-color: rgba(255, 165, 0, 0.2);
    text-decoration: wavy underline red;
}

.jql-error-invalid {
    color: #dc3545;
    font-weight: bold;
}
```

---

### Step 3: Add JavaScript Synchronization (TDD - Red Phase)

**Write interaction tests first**:

```python
def test_scroll_synchronization(live_server):
    """Test scroll position syncs between layers."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(live_server)
        
        # Fill with long query
        long_query = "project = TEST AND " * 50  # Force scrollbar
        page.fill("#jql-query-input", long_query)
        
        # Scroll textarea
        page.evaluate("""
            document.querySelector('#jql-query-input').scrollTop = 100;
        """)
        
        page.wait_for_timeout(100)
        
        # Verify highlight div scrolled
        highlight_scroll = page.evaluate("""
            document.querySelector('#jql-query-input-highlight').scrollTop
        """)
        assert highlight_scroll == 100
        
        browser.close()
```

**Implement JavaScript** (assets/jql_syntax.js):

```javascript
function initializeSyntaxHighlighting(componentId) {
    const textarea = document.getElementById(componentId);
    const highlightDiv = document.getElementById(`${componentId}-highlight`);
    
    if (!textarea || !highlightDiv) {
        console.warn(`Syntax highlighting elements not found for ${componentId}`);
        return;
    }
    
    // Sync scroll position
    function syncScrollPosition() {
        highlightDiv.scrollTop = textarea.scrollTop;
        highlightDiv.scrollLeft = textarea.scrollLeft;
    }
    
    // Attach scroll listener
    textarea.addEventListener('scroll', syncScrollPosition);
    
    // Initial sync
    syncScrollPosition();
}

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    const textareas = document.querySelectorAll('.jql-syntax-input');
    textareas.forEach(textarea => {
        initializeSyntaxHighlighting(textarea.id);
    });
});
```

---

### Step 4: Add Dash Callbacks (TDD - Red Phase)

**Write callback tests first**:

```python
def test_update_highlighting_callback(dash_app):
    """Test callback updates highlighting on text change."""
    # Simulate textarea input
    query = "project = TEST AND status = Done"
    
    # Trigger callback manually
    result = update_jql_syntax_highlighting(query)
    
    # Verify result contains html.Mark components
    assert len(result) > 0
    assert any(isinstance(item, html.Mark) for item in result)
    
    # Verify keyword highlighted
    keyword_marks = [
        item for item in result 
        if isinstance(item, html.Mark) and item.className == "jql-keyword"
    ]
    assert len(keyword_marks) >= 1  # Should have "AND"
```

**Implement callback** (callbacks/settings.py):

```python
from dash import callback, Output, Input
from ui.components import parse_jql_syntax, render_syntax_tokens
from ui.jql_syntax_highlighter import detect_syntax_errors

@callback(
    Output("jql-query-input-highlight", "children"),
    Input("jql-query-input", "value"),
    prevent_initial_call=False
)
def update_jql_syntax_highlighting(query_value):
    """Update syntax highlighting on query change."""
    if not query_value:
        return []
    
    # Parse query
    tokens = parse_jql_syntax(query_value)
    
    # Detect errors
    errors = detect_syntax_errors(tokens)
    
    # Apply error styling to tokens
    for error in errors:
        for token in tokens:
            if token["start"] == error["start"]:
                token["type"] = f"error_{error['error_type']}"
    
    # Render to HTML
    return render_syntax_tokens(tokens)
```

---

### Step 5: Mobile Testing (Playwright)

**Write mobile tests**:

```python
def test_mobile_viewport_highlighting(live_server):
    """Test highlighting works on mobile viewport."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # iPhone SE viewport (320px)
        context = browser.new_context(viewport={"width": 320, "height": 568})
        page = context.new_page()
        page.goto(live_server)
        
        # Type query
        page.fill("#jql-query-input", "project = TEST")
        page.wait_for_timeout(100)
        
        # Verify textarea visible and responsive
        textarea = page.locator("#jql-query-input")
        box = textarea.bounding_box()
        assert box["width"] <= 320
        
        # Verify highlighting visible
        keyword = page.locator(".jql-keyword").filter(has_text="project")
        assert keyword.count() == 0  # "project" is text, not keyword
        
        browser.close()
```

---

## Testing Strategy

### Unit Tests (pytest)

**Run unit tests**:
```powershell
.\.venv\Scripts\activate; pytest tests/unit/ui/test_jql_syntax_highlighter.py -v
```

**Test Coverage**:
- `create_jql_syntax_highlighter()` - component structure
- `detect_syntax_errors()` - error detection logic
- `is_scriptrunner_function()` - function matching
- Performance: parse time <50ms for 5000 char queries

### Integration Tests (Playwright)

**Run integration tests**:
```powershell
.\.venv\Scripts\activate; pytest tests/integration/dashboard/test_jql_highlighting_workflow.py -v
```

**Test Coverage**:
- Keyword highlighting (blue)
- String highlighting (green)
- Operator highlighting (gray)
- ScriptRunner function highlighting (purple)
- Error indication (unclosed quotes)
- Scroll synchronization
- Cursor position preservation
- Mobile viewport (320px)

### Performance Testing

**Measure parse time**:
```powershell
.\.venv\Scripts\activate; python -c "
import time
from ui.components import parse_jql_syntax

query = 'project = TEST AND ' * 500  # ~5000 chars

start = time.time()
tokens = parse_jql_syntax(query)
duration = (time.time() - start) * 1000

print(f'Parse time: {duration:.2f}ms (target: <50ms)')
assert duration < 50
"
```

---

## Common Patterns

### Pattern 1: Adding New ScriptRunner Function

```python
# ui/jql_syntax_highlighter.py
SCRIPTRUNNER_FUNCTIONS = frozenset([
    # ... existing functions
    "newFunctionName",  # Add here
])
```

### Pattern 2: Adding New Error Type

```python
# ui/jql_syntax_highlighter.py
def detect_syntax_errors(tokens):
    errors = []
    
    # ... existing error detection
    
    # New error type
    for token in tokens:
        if token["type"] == "operator" and token["text"] not in VALID_OPERATORS:
            errors.append({
                "error_type": "invalid_operator",
                "start": token["start"],
                "end": token["end"],
                "token": token,
                "message": f"Invalid operator: {token['text']}"
            })
    
    return errors
```

### Pattern 3: Performance Profiling

```python
# Add to callback for debugging
import time

@callback(Output("jql-query-input-highlight", "children"), Input("jql-query-input", "value"))
def update_jql_syntax_highlighting(query_value):
    start = time.time()
    
    tokens = parse_jql_syntax(query_value)
    parse_time = (time.time() - start) * 1000
    
    errors = detect_syntax_errors(tokens)
    detect_time = (time.time() - start) * 1000 - parse_time
    
    rendered = render_syntax_tokens(tokens)
    render_time = (time.time() - start) * 1000 - parse_time - detect_time
    
    print(f"Parse: {parse_time:.2f}ms, Detect: {detect_time:.2f}ms, Render: {render_time:.2f}ms")
    
    return rendered
```

---

## Debugging Tips

### Issue: Highlighting Not Appearing

**Check**:
1. CSS classes applied correctly (`jql-keyword`, etc.)?
2. JavaScript initialized (`initializeSyntaxHighlighting()` called)?
3. Callback triggered (check Dash debug console)?
4. Tokens generated correctly (`parse_jql_syntax()` returns non-empty list)?

**Debug Steps**:
```powershell
# Test parsing
.\.venv\Scripts\activate; python -c "
from ui.components import parse_jql_syntax
tokens = parse_jql_syntax('project = TEST AND status')
print(tokens)
"

# Check CSS loaded
# Open browser DevTools → Network tab → Verify jql_syntax.css loaded

# Check JavaScript errors
# Open browser DevTools → Console tab → Look for errors
```

### Issue: Scroll Not Synchronized

**Check**:
1. JavaScript event listener attached?
2. Element IDs match (textarea and highlight div)?
3. CSS overflow properties correct?

**Debug Steps**:
```javascript
// Browser console
const textarea = document.getElementById('jql-query-input');
const highlight = document.getElementById('jql-query-input-highlight');

console.log('Textarea:', textarea);
console.log('Highlight:', highlight);
console.log('Scroll:', textarea.scrollTop, highlight.scrollTop);
```

### Issue: Performance Slow (<50ms not met)

**Profile**:
```powershell
.\.venv\Scripts\activate; python -m cProfile -s cumtime -c "
from ui.components import parse_jql_syntax
query = 'project = TEST AND ' * 500
for _ in range(100):
    parse_jql_syntax(query)
" | Select-String -Pattern "parse_jql_syntax"
```

---

## Deployment Checklist

Before merging to main:

- [ ] All unit tests pass (pytest tests/unit/ -v)
- [ ] All integration tests pass (pytest tests/integration/ -v)
- [ ] Performance tests pass (<50ms parse time)
- [ ] Mobile testing completed (320px, 768px viewports)
- [ ] Accessibility testing (keyboard navigation, screen reader)
- [ ] Browser testing (Chrome, Firefox, Safari, Edge - latest versions)
- [ ] No console errors or warnings
- [ ] Code reviewed and approved
- [ ] Documentation updated (README.md, CHANGELOG.md)
- [ ] Graceful degradation verified (unsupported browsers)

---

## Quick Reference Commands

```powershell
# Run application
.\.venv\Scripts\activate; python app.py

# Run unit tests
.\.venv\Scripts\activate; pytest tests/unit/ui/test_jql_syntax_highlighter.py -v

# Run integration tests
.\.venv\Scripts\activate; pytest tests/integration/dashboard/test_jql_highlighting_workflow.py -v

# Run all tests with coverage
.\.venv\Scripts\activate; pytest --cov=ui --cov=callbacks --cov-report=html

# Performance profiling
.\.venv\Scripts\activate; pytest tests/ -k "performance" -v --durations=10

# Lint code
.\.venv\Scripts\activate; pylint ui/jql_syntax_highlighter.py callbacks/settings.py
```

---

**Ready to Implement**: Follow TDD workflow (Red → Green → Refactor) for each user story.
