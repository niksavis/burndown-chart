# API Contracts: JQL Syntax Highlighting

**Feature**: Complete JQL Syntax Highlighting with Real-time Visual Feedback
**Date**: 2025-10-15

## Overview

This document defines the contracts (interfaces) for the JQL syntax highlighting feature. Since this is a Dash application (not a REST/GraphQL API), contracts are defined as Python function signatures and Dash callback signatures.

---

## Python Function Contracts

### 1. parse_jql_syntax (EXISTING - from feature 001)

**Purpose**: Parse JQL query string into syntax tokens.

**Signature**:
```python
def parse_jql_syntax(query: Optional[str]) -> List[Dict[str, Any]]:
    """
    Parse JQL query into syntax tokens for highlighting.
    
    Args:
        query: JQL query string (str or None)
        
    Returns:
        List[dict]: List of SyntaxToken dicts with keys: text, type, start, end
                   Returns empty list if query is None/empty
                   
    Example:
        >>> parse_jql_syntax('project = TEST AND status = "Done"')
        [
            {"text": "project", "type": "text", "start": 0, "end": 7},
            {"text": " ", "type": "text", "start": 7, "end": 8},
            {"text": "=", "type": "operator", "start": 8, "end": 9},
            ...
        ]
    """
```

**Contract Guarantees**:
- Always returns a list (never None)
- Empty input returns empty list
- Tokens cover entire input string (no gaps)
- Token positions are valid indices (0 <= start < end <= len(query))
- Token types are valid: "keyword", "string", "operator", "text", "function"

**Error Handling**:
- No exceptions raised for invalid input
- Invalid characters treated as "text" tokens
- Empty string or None handled gracefully

---

### 2. render_syntax_tokens (EXISTING - from feature 001)

**Purpose**: Convert syntax tokens to Dash HTML components with CSS classes.

**Signature**:
```python
def render_syntax_tokens(tokens: List[Dict[str, Any]]) -> List[Union[html.Mark, str]]:
    """
    Render syntax tokens to Dash HTML components.
    
    Args:
        tokens: List of SyntaxToken dicts
        
    Returns:
        list: List of html.Mark components or strings for rendering
        
    Example:
        >>> tokens = [{"text": "AND", "type": "keyword", "start": 0, "end": 3}]
        >>> render_syntax_tokens(tokens)
        [html.Mark("AND", className="jql-keyword")]
    """
```

**Contract Guarantees**:
- Always returns a list
- Empty tokens list returns empty list
- Each token mapped to html.Mark or plain string
- CSS classes match token types (.jql-keyword, .jql-string, .jql-operator, .jql-function)

**Error Handling**:
- Unknown token types rendered as plain text
- Missing keys in token dict handled gracefully (uses defaults)

---

### 3. detect_syntax_errors (NEW)

**Purpose**: Detect common JQL syntax errors in parsed tokens.

**Signature**:
```python
def detect_syntax_errors(tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect common JQL syntax errors (unclosed quotes, invalid operators).
    
    Args:
        tokens: List of SyntaxToken dicts from parse_jql_syntax()
        
    Returns:
        List[dict]: List of SyntaxError dicts with keys: error_type, start, end, token, message
                   Returns empty list if no errors detected
                   
    Example:
        >>> tokens = [{"text": '"Done', "type": "string", "start": 0, "end": 5}]
        >>> detect_syntax_errors(tokens)
        [
            {
                "error_type": "unclosed_string",
                "start": 0,
                "end": 5,
                "token": {"text": '"Done', "type": "string", "start": 0, "end": 5},
                "message": "Unclosed string literal"
            }
        ]
    """
```

**Contract Guarantees**:
- Always returns a list (never None)
- Error types are valid: "unclosed_string", "invalid_operator"
- Each error references the problematic token
- Position indices match token positions

**Error Handling**:
- Invalid token structure skipped (logged but not raised)
- Empty token list returns empty error list

---

### 4. is_scriptrunner_function (NEW)

**Purpose**: Check if a word is a recognized ScriptRunner JQL function.

**Signature**:
```python
def is_scriptrunner_function(word: str) -> bool:
    """
    Check if word is a ScriptRunner JQL function.
    
    Args:
        word: Word to check (case-sensitive)
        
    Returns:
        bool: True if word is in SCRIPTRUNNER_FUNCTIONS, False otherwise
        
    Example:
        >>> is_scriptrunner_function("linkedIssuesOf")
        True
        >>> is_scriptrunner_function("invalidFunction")
        False
    """
```

**Contract Guarantees**:
- Always returns bool (never None)
- Case-sensitive matching (exact match required)
- O(1) lookup time (uses frozenset)

**Error Handling**:
- Non-string input converted to string
- Empty string returns False

---

### 5. create_jql_syntax_highlighter (NEW)

**Purpose**: Create Dash component for syntax-highlighted JQL textarea.

**Signature**:
```python
def create_jql_syntax_highlighter(
    component_id: str,
    value: str = "",
    placeholder: str = "Enter JQL query...",
    rows: int = 5,
    disabled: bool = False,
    aria_label: str = "JQL Query Input"
) -> html.Div:
    """
    Create dual-layer syntax-highlighted JQL textarea component.
    
    Args:
        component_id: Unique component ID for Dash callbacks
        value: Initial query text
        placeholder: Placeholder text when empty
        rows: Number of visible textarea rows
        disabled: Disabled state
        aria_label: Accessibility label for screen readers
        
    Returns:
        html.Div: Wrapper div containing contenteditable div (highlighting) 
                 and textarea (input) with synchronization JavaScript
                 
    Example:
        >>> component = create_jql_syntax_highlighter(
        ...     component_id="jql-query",
        ...     value="project = TEST",
        ...     rows=5
        ... )
    """
```

**Contract Guarantees**:
- Returns valid Dash html.Div component
- Contains two child elements: contenteditable div and textarea
- JavaScript initialization included for synchronization
- Component ID is unique and used for callbacks

**Error Handling**:
- Invalid rows value clamped to 1-20 range
- Value exceeding 5000 chars truncated with warning

---

## Dash Callback Contracts

### 1. update_jql_syntax_highlighting

**Purpose**: Update syntax highlighting when query text changes.

**Signature**:
```python
@callback(
    Output("jql-syntax-highlight", "children"),
    Input("jql-query-input", "value"),
    prevent_initial_call=False
)
def update_jql_syntax_highlighting(query_value: Optional[str]) -> List[Union[html.Mark, str]]:
    """
    Parse and render syntax highlighting for JQL query.
    
    Args:
        query_value: Current JQL query text from textarea
        
    Returns:
        List of Dash components (html.Mark) for rendering in contenteditable div
        
    Performance:
        - Must complete in <50ms for queries up to 5000 chars (FR-005)
        - Triggered on every keystroke
    """
```

**Input Contract**:
- `query_value`: String or None from textarea value
- Triggered on every textarea change event

**Output Contract**:
- Returns list of Dash components
- Empty input returns empty list
- Syntax errors included with error styling

**Performance Requirements**:
- <50ms execution time (FR-005)
- No blocking operations
- requestAnimationFrame scheduled on client-side

---

### 2. update_character_count_with_highlighting

**Purpose**: Update character count display and syntax highlighting together (optimized batch update).

**Signature**:
```python
@callback(
    [
        Output("jql-character-count", "children"),
        Output("jql-syntax-highlight", "children")
    ],
    Input("jql-query-input", "value"),
    prevent_initial_call=False
)
def update_character_count_with_highlighting(
    query_value: Optional[str]
) -> Tuple[html.Div, List[Union[html.Mark, str]]]:
    """
    Batch update character count and syntax highlighting.
    
    Args:
        query_value: Current JQL query text
        
    Returns:
        Tuple of (character_count_component, highlighted_components)
        
    Performance:
        - Single callback reduces overhead vs separate callbacks
        - <50ms total execution time
    """
```

**Input Contract**:
- `query_value`: String or None from textarea

**Output Contract**:
- Returns tuple of (character count component, highlighting components)
- Character count follows existing format from feature 001
- Highlighting follows render_syntax_tokens format

**Performance Requirements**:
- Combined execution <50ms
- Prevents duplicate parsing (parse once, use twice)

---

### 3. track_syntax_highlighting_performance (Optional)

**Purpose**: Monitor parsing and rendering performance for optimization.

**Signature**:
```python
@callback(
    Output("jql-syntax-perf-store", "data"),
    Input("jql-query-input", "value"),
    State("jql-syntax-perf-store", "data"),
    prevent_initial_call=True
)
def track_syntax_highlighting_performance(
    query_value: Optional[str],
    current_metrics: Optional[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Track parsing and rendering performance metrics.
    
    Args:
        query_value: Current query text
        current_metrics: Previous performance metrics from dcc.Store
        
    Returns:
        Updated performance metrics dict with keys:
            - last_parse_time_ms: Last parse duration
            - avg_parse_time_ms: Moving average parse time
            - max_parse_time_ms: Maximum observed parse time
            - sample_count: Number of samples collected
    """
```

**Input Contract**:
- `query_value`: Current query text
- `current_metrics`: Previous metrics from dcc.Store or None

**Output Contract**:
- Returns dict with performance metrics
- Metrics updated incrementally (moving averages)

**Performance Requirements**:
- Minimal overhead (<5ms)
- Only runs if performance tracking enabled (optional feature)

---

## Client-Side JavaScript Contracts

### 1. syncScrollPosition

**Purpose**: Synchronize scroll position between textarea and contenteditable div.

**Signature**:
```javascript
function syncScrollPosition(textareaElement, highlightElement) {
    /**
     * Sync scroll position from textarea to highlight div.
     * 
     * @param {HTMLTextAreaElement} textareaElement - The textarea input
     * @param {HTMLDivElement} highlightElement - The contenteditable highlight div
     * 
     * Performance: Must complete in <5ms to maintain 60fps
     */
}
```

**Contract Guarantees**:
- Scroll positions (top, left) kept in sync
- Called on textarea scroll event
- No visual lag or jitter

**Error Handling**:
- Null element checks
- Invalid scroll values clamped to valid range

---

### 2. initializeSyntaxHighlighting

**Purpose**: Initialize event listeners and synchronization for syntax highlighting component.

**Signature**:
```javascript
function initializeSyntaxHighlighting(componentId) {
    /**
     * Initialize syntax highlighting for JQL textarea.
     * 
     * @param {string} componentId - Component ID for textarea and highlight div
     * 
     * Sets up:
     * - Scroll synchronization
     * - requestAnimationFrame throttling
     * - Feature detection and graceful degradation
     * 
     * Returns: void
     */
}
```

**Contract Guarantees**:
- Event listeners registered on component mount
- Cleanup on component unmount
- Feature detection prevents errors on unsupported browsers

**Error Handling**:
- Feature detection fallback to plain textarea
- Missing elements logged but don't throw exceptions

---

## CSS Contract

### Required CSS Classes

**Purpose**: Define visual styling for syntax highlighting tokens.

**Classes**:

```css
/* Keyword styling (AND, OR, IN, etc.) */
.jql-keyword {
  color: #0066cc;       /* Blue per FR-002 */
  font-weight: bold;
}

/* String literal styling ("Done", 'In Progress') */
.jql-string {
  color: #22863a;       /* Green per FR-003 */
}

/* Operator styling (=, !=, <, >, ~) */
.jql-operator {
  color: #6c757d;       /* Gray per FR-004 */
  font-weight: 500;
}

/* ScriptRunner function styling */
.jql-function {
  color: #8b008b;       /* Purple per FR-007 */
  font-weight: 500;
}

/* Error styling - unclosed string */
.jql-error-unclosed {
  background-color: rgba(255, 165, 0, 0.2);  /* Orange background per FR-009 */
  text-decoration: wavy underline red;
}

/* Error styling - invalid operator */
.jql-error-invalid {
  color: #dc3545;       /* Red per FR-010 */
  font-weight: bold;
}
```

**Contract Guarantees**:
- Colors meet WCAG 2.1 AA contrast requirements (4.5:1 minimum)
- Mobile-responsive (no fixed pixel sizes)
- Consistent with existing .jql-keyword, .jql-string, .jql-operator styles

---

## Component Lifecycle

### Initialization Flow

1. `create_jql_syntax_highlighter()` called to create component
2. Dash renders html.Div with textarea and contenteditable div
3. `initializeSyntaxHighlighting()` JavaScript runs on mount
4. Event listeners registered (scroll, input)
5. Initial highlighting applied (if value provided)

### Update Flow

1. User types in textarea → onChange event
2. JavaScript schedules update via requestAnimationFrame
3. Dash callback `update_jql_syntax_highlighting()` triggered
4. Query parsed → tokens generated → errors detected
5. Tokens rendered to HTML components
6. Contenteditable div updated with new highlighting
7. Scroll position synchronized

### Cleanup Flow

1. Component unmounted from Dash layout
2. JavaScript cleanup listeners removed
3. requestAnimationFrame IDs cancelled
4. No memory leaks (event listeners cleaned up)

---

## Error Handling Contract

### Function-Level Error Handling

All public functions MUST:
- Accept None/null inputs gracefully (return safe defaults)
- Log errors to console (not raise exceptions that crash app)
- Return valid types matching signature (never undefined/None when list expected)
- Validate inputs and clamp to safe ranges (e.g., max query length 5000)

### Callback-Level Error Handling

All Dash callbacks MUST:
- Use try/except blocks for external calls (parsing, rendering)
- Return Dash `no_update` if error prevents valid output
- Log exceptions with context (query length, token count, error type)
- Never crash the entire application (isolated error handling)

### Client-Side Error Handling

All JavaScript functions MUST:
- Check for element existence before DOM operations
- Use feature detection before modern API calls
- Provide fallback for unsupported browsers (graceful degradation per FR-016)
- Log errors to console (not alert dialogs)

---

## Testing Contracts

### Unit Test Requirements

Each function MUST have tests covering:
- **Happy path**: Valid inputs with expected outputs
- **Edge cases**: Empty input, None input, max length input
- **Error cases**: Invalid token structure, malformed queries
- **Performance**: Execution time <50ms for max length queries

### Integration Test Requirements

Each user story MUST have Playwright tests covering:
- **Visual verification**: Highlighting appears correctly
- **Interaction**: Typing, pasting, selecting text
- **Mobile**: Touch interactions, viewport responsiveness
- **Accessibility**: Keyboard navigation, screen reader compatibility

---

## Version Compatibility

### Backward Compatibility

- **Feature 001 functions**: parse_jql_syntax(), render_syntax_tokens() unchanged
- **Existing CSS classes**: .jql-keyword, .jql-string, .jql-operator remain valid
- **Character count**: Existing functionality unaffected

### Forward Compatibility

- **Extensibility**: SCRIPTRUNNER_FUNCTIONS can be expanded without breaking changes
- **New token types**: Future token types (e.g., "variable") can be added to TOKEN_TYPES
- **New error types**: Future error types can be added to ERROR_TYPES

---

## Summary

**Total Contracts Defined**: 11
- Python Functions: 5 (3 new, 2 existing)
- Dash Callbacks: 3
- JavaScript Functions: 2
- CSS Classes: 6

**Key Guarantees**:
- <50ms parse time for queries up to 5000 chars
- 60fps rendering during typing
- Graceful error handling (no crashes)
- Backward compatible with feature 001
- Mobile-first responsive design
