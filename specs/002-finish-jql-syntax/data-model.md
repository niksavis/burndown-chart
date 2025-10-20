# Data Model: JQL Syntax Highlighting Runtime Entities

**Feature**: Complete JQL Syntax Highlighting with Real-time Visual Feedback
**Branch**: `002-finish-jql-syntax`
**Last Updated**: 2025-10-20

## Overview

This document defines the runtime data structures and entities for JQL syntax highlighting using **CodeMirror 6** library. No persistent storage is required - all entities exist in browser memory during editor operation.

**Architecture**: Client-side JavaScript (CodeMirror 6) with Python Dash wrapper component.

## Core Entities

### 1. JQL Editor Component (Python Dash)

**Purpose**: Dash wrapper component that embeds CodeMirror editor with JQL language mode.

**Implementation**: `ui/jql_editor.py::create_jql_editor()`

**Attributes**:

```python
{
    "id": str,                    # Dash component ID (e.g., "jira-jql-query")
    "value": str,                 # Current query text
    "placeholder": str,           # Placeholder text
    "mode": "jql",                # Custom language mode identifier
    "theme": "light",             # Editor theme
    "lineNumbers": bool,          # Show line numbers (default: False for mobile)
    "lineWrapping": bool,         # Wrap long lines (default: True)
    "readOnly": bool,             # Editor readonly state
    "maxLength": int,             # Character limit (default: 5000)
    "height": str,                # Editor height (e.g., "200px", "auto")
    "className": str,             # Additional CSS classes
    "ariaLabel": str              # Accessibility label
}
```

**Example**:

```python
from ui.jql_editor import create_jql_editor

editor = create_jql_editor(
    editor_id="jira-jql-query",
    value="project = TEST AND status = Open",
    placeholder="Enter JQL query (e.g., project = TEST)",
    aria_label="JQL Query Editor"
)
```

**Lifecycle**:
- Created: When app layout initializes
- Updated: On user typing (browser-side, no server round-trip)
- Destroyed: When tab/page closes

### 2. JQL Language Mode (JavaScript)

**Purpose**: Custom CodeMirror language mode that defines JQL syntax tokenization rules.

**Implementation**: `assets/jql_language_mode.js`

**Token Types**:

```javascript
{
    keyword: {
        pattern: /\b(AND|OR|NOT|IN|IS|WAS|...)\b/i,
        style: "jql-keyword",     // CSS class: color #0066cc
        examples: ["AND", "OR", "NOT", "IN", "IS", "WAS"]
    },
    
    operator: {
        pattern: /[=!<>~]+/,
        style: "jql-operator",    // CSS class: color #6c757d
        examples: ["=", "!=", "~", ">", "<="]
    },
    
    string: {
        pattern: /"[^"]*"?|'[^']*'?/,
        style: "jql-string",      // CSS class: color #22863a
        examples: ['"Done"', "'In Progress'"]
    },
    
    function: {
        pattern: /\b(currentUser|now|startOfDay|...)\(\)/,
        style: "jql-function",    // CSS class: color #8b008b
        examples: ["currentUser()", "now()", "startOfDay()"]
    },
    
    scriptrunner_function: {
        pattern: /\b(linkedIssuesOf|issueFunction|...)\(/,
        style: "jql-scriptrunner", // CSS class: color #8b008b
        examples: ["linkedIssuesOf(", "issueFunction("]
    },
    
    field: {
        pattern: /\b[a-zA-Z_][a-zA-Z0-9_]*\b(?=\s*[=!<>~])/,
        style: "jql-field",       // CSS class: color #24292e
        examples: ["project", "status", "assignee"]
    },
    
    error: {
        pattern: /"[^"]*$|'[^']*$/,  // Unclosed quotes
        style: "jql-error",       // CSS class: red underline
        examples: ['"unclosed', "'missing quote"]
    }
}
```

**Tokenizer State Machine**:

```javascript
const jqlLanguageMode = {
    startState: () => ({ inString: false, stringDelimiter: null }),
    
    token: (stream, state) => {
        // Error detection: unclosed strings
        if (state.inString && stream.eol()) {
            state.inString = false;
            return "jql-error";
        }
        
        // String literals (highest priority)
        if (stream.match(/^"[^"]*"/)) return "jql-string";
        if (stream.match(/^'[^']*'/)) return "jql-string";
        
        // ScriptRunner functions (before generic keywords)
        if (stream.match(/\b(linkedIssuesOf|issueFunction|...)\(/i)) {
            return "jql-scriptrunner";
        }
        
        // JQL keywords
        if (stream.match(/\b(AND|OR|NOT|IN|...)\b/i)) {
            return "jql-keyword";
        }
        
        // Operators
        if (stream.match(/[=!<>~]+/)) return "jql-operator";
        
        // Default: advance stream
        stream.next();
        return null;
    }
};
```

**Lifecycle**:
- Created: On page load (loaded from `assets/jql_language_mode.js`)
- Updated: Never (static tokenizer rules)
- Destroyed: On page unload

### 3. Query Text (Runtime State)

**Purpose**: Current JQL query text being edited.

**Storage**: Browser memory (CodeMirror editor internal state)

**Attributes**:

```javascript
{
    text: string,                 // Full query text
    cursorPosition: number,       // Character offset of cursor
    selectionStart: number,       // Selection start offset
    selectionEnd: number,         // Selection end offset
    length: number,               // Character count
    tokens: Array<Token>          // Tokenized representation (internal)
}
```

**Lifecycle**:
- Created: When editor initializes with value
- Updated: On every keystroke (debounced highlighting <50ms)
- Destroyed: On editor unmount

### 4. Editor Configuration (Runtime)

**Purpose**: CodeMirror editor configuration passed from Dash component.

**Storage**: Browser memory (component props)

**Attributes**:

```javascript
{
    mode: "jql",                  // Language mode identifier
    theme: "default",             // Visual theme
    lineNumbers: false,           // Mobile-first: no line numbers
    lineWrapping: true,           // Mobile-first: wrap long lines
    indentUnit: 2,                // Indent size
    tabSize: 2,                   // Tab width
    readOnly: false,              // Editable by default
    maxLength: 5000,              // Character limit
    placeholder: string,          // Placeholder text
    autofocus: false,             // Focus on mount
    ariaLabel: string             // Accessibility label
}
```

**Lifecycle**:
- Created: On component mount
- Updated: On prop changes from Dash
- Destroyed: On component unmount

## Token Types Reference

### Keyword Token

**Syntax**: JQL reserved words (case-insensitive)
**Style**: Bold, blue (#0066cc)
**Examples**: `AND`, `OR`, `NOT`, `IN`, `IS`, `WAS`, `EMPTY`, `NULL`
**Count**: ~50 keywords

### Operator Token

**Syntax**: Comparison and logical operators
**Style**: Gray (#6c757d)
**Examples**: `=`, `!=`, `~`, `!~`, `>`, `<`, `>=`, `<=`
**Count**: ~10 operators

### String Token

**Syntax**: Double-quoted or single-quoted text
**Style**: Green (#22863a)
**Examples**: `"Done"`, `'In Progress'`, `"Epic: PROJ-123"`
**Validation**: Unclosed quotes trigger error state

### Function Token

**Syntax**: Standard JQL functions with parentheses
**Style**: Purple (#8b008b)
**Examples**: `currentUser()`, `now()`, `startOfDay()`, `endOfWeek()`
**Count**: ~20 built-in functions

### ScriptRunner Function Token

**Syntax**: ScriptRunner plugin functions with parentheses
**Style**: Purple (#8b008b, same as standard functions)
**Examples**: `linkedIssuesOf()`, `issueFunction()`, `hasSubtasks()`
**Count**: ~15 ScriptRunner functions (initial support)

### Field Token

**Syntax**: Field names (detected before operators)
**Style**: Default text color (#24292e)
**Examples**: `project`, `status`, `assignee`, `customfield_10001`
**Validation**: None (any valid identifier)

### Error Token

**Syntax**: Malformed syntax (unclosed quotes)
**Style**: Red wavy underline
**Examples**: `"unclosed`, `'missing end quote`
**Detection**: Real-time as user types

## Data Flow

### User Types → Highlighting

```
User keystroke
    ↓
Browser captures event
    ↓
CodeMirror updates internal state
    ↓
JQL Language Mode tokenizes text (<50ms)
    ↓
CodeMirror applies CSS classes to tokens
    ↓
Browser renders highlighted text (60fps)
```

**Performance Requirements**:
- Keystroke to highlight: <50ms (FR-005, SC-001)
- Typing at 100 WPM: Zero dropped keystrokes (FR-010)
- Mobile devices: 60fps rendering (FR-011)

### Dash Callback → Query Validation

```
User clicks "Update Data"
    ↓
Dash callback fires with editor value
    ↓
Python receives query text
    ↓
Validate query syntax (optional)
    ↓
Send to JIRA API
    ↓
Display results or error
```

**Note**: Syntax highlighting is visual-only. Query validation happens server-side in existing `data/jira_simple.py` logic.

## No Persistent Storage

**Key Design Decision**: Syntax highlighting is ephemeral - no data persists between sessions.

**What is NOT stored**:
- ❌ Tokenized query representation
- ❌ Cursor position
- ❌ Editor configuration
- ❌ Highlighting state

**What IS stored** (existing functionality, unchanged):
- ✅ JQL query text in `app_settings.json` (via existing settings callback)
- ✅ JIRA cached results in `jira_cache.json` (via existing caching logic)

## Performance Considerations

### Memory Usage

**Estimated Memory**:
- CodeMirror library: ~500KB (gzipped: ~100KB)
- JQL language mode: ~5KB
- Query text (5000 chars): ~10KB
- Token array (worst case): ~50KB
- **Total**: ~565KB in browser memory

**Mobile Impact**: Acceptable for devices with ≥1GB RAM (target: 2GB+ devices per constitution)

### CPU Usage

**Tokenization Complexity**: O(n) where n = query length
- Average query: 200 characters → <5ms
- Large query: 2000 characters → <50ms (within target)
- Paste operation: 1000 characters → <300ms (SC-007)

**Debouncing**: CodeMirror handles internal debouncing/throttling automatically.

## Error Handling

### Syntax Errors (Client-Side)

**Detection**: JQL language mode tokenizer identifies unclosed quotes
**Display**: Red wavy underline (CSS class: `.jql-error`)
**User Feedback**: Visual indicator only (no blocking errors)

### Validation Errors (Server-Side)

**Detection**: Existing JIRA API error responses
**Display**: Existing error toast/banner in Dash UI
**Location**: `callbacks/settings.py` (unchanged)

## Integration Points

### Dash Component Integration

**Location**: `app.py` layout
**Change**: Replace `dbc.Textarea` with `create_jql_editor()`

**Before**:
```python
dbc.Textarea(
    id="jira-jql-query",
    placeholder="Enter JQL query",
    value=app_settings.get("jira_jql_query", "")
)
```

**After**:
```python
from ui.jql_editor import create_jql_editor

create_jql_editor(
    editor_id="jira-jql-query",
    value=app_settings.get("jira_jql_query", ""),
    placeholder="Enter JQL query (e.g., project = TEST AND status = Open)",
    aria_label="JQL Query Editor"
)
```

### Callback Integration

**Location**: `callbacks/settings.py`
**Change**: None required - callback already receives `Input("jira-jql-query", "value")`

**Existing Callback** (unchanged):
```python
@callback(
    Output("jira-cache-status", "children"),
    Input("update-data-unified", "n_clicks"),
    State("jira-jql-query", "value"),
    ...
)
def update_jira_data(n_clicks, jql_query, ...):
    # Query validation and JIRA API call (unchanged)
    ...
```

## Accessibility Data

### Screen Reader Announcements

**Query Text**: Announced via `role="textbox"` and `aria-label="JQL Query Editor"`
**Character Count**: Announced via existing ARIA live region (unchanged)
**Syntax Errors**: Visual-only (no ARIA announcements to avoid noise)

### Keyboard Navigation

**Supported Keys**:
- Arrow keys: Move cursor (handled by CodeMirror)
- Tab: Navigate to next form field (handled by browser)
- Ctrl+A: Select all text (handled by CodeMirror)
- Backspace/Delete: Edit text (handled by CodeMirror)

**Not Supported**:
- Screen reader text navigation (CodeMirror limitation - will document in quickstart)

## Testing Data

### Unit Test Fixtures

**Location**: `tests/unit/ui/test_jql_editor.py`

**Sample Queries**:
```python
SAMPLE_QUERIES = {
    "simple": "project = TEST",
    "complex": 'project = TEST AND status = "In Progress" AND assignee = currentUser()',
    "scriptrunner": "project = TEST AND issueFunction in linkedIssuesOf('PROJ-123')",
    "error": 'project = TEST AND summary ~ "unclosed',
    "long": "project = TEST AND " + " OR ".join([f"status = {i}" for i in range(100)])
}
```

### Integration Test Scenarios

**Location**: `tests/integration/dashboard/test_jql_editor_workflow.py`

**Playwright Selectors**:
```python
SELECTORS = {
    "editor": "[data-testid='jql-editor'] .CodeMirror",
    "keyword_token": ".cm-jql-keyword",
    "string_token": ".cm-jql-string",
    "error_token": ".cm-jql-error",
    "character_count": "#jql-character-count"
}
```

**Performance Measurement**:
```javascript
// Measure keystroke latency with Performance API
performance.mark("keystroke-start");
editor.type("AND");
performance.mark("highlight-complete");
performance.measure("latency", "keystroke-start", "highlight-complete");
```

## Migration from Legacy Implementation

### Deprecated Entities

**Functions to Remove**:
- `ui/components.py::parse_jql_syntax()` - Custom regex-based tokenizer
- `ui/components.py::render_syntax_tokens()` - HTML generation for highlighted spans

**Assets to Remove**:
- `assets/jql_syntax.css` - Custom syntax highlighting styles
- `assets/jql_syntax.js` - Dual-layer textarea synchronization logic

### Data Structure Changes

**No breaking changes**: Editor component maintains same Dash callback interface (`id`, `value` props).

**Migration Path**:
1. Install dash-codemirror: `pip install dash-codemirror`
2. Create `ui/jql_editor.py` with `create_jql_editor()` wrapper
3. Create `assets/jql_language_mode.js` with tokenizer rules
4. Update `app.py` layout to use new component
5. Remove deprecated functions and assets
6. Update tests

## Appendix: CodeMirror 6 Data Structures (Internal)

**Note**: These are library internals - provided for reference only. Our code does not directly manipulate these structures.

### EditorState

```typescript
interface EditorState {
    doc: Text;              // Document text
    selection: Selection;   // Cursor/selection state
    facets: FacetState;     // Configuration
    values: StateField[];   // Plugin state
}
```

### Token

```typescript
interface Token {
    type: string;           // Token type (e.g., "jql-keyword")
    from: number;           // Start position
    to: number;             // End position
    value: string;          // Token text
}
```

### ViewUpdate

```typescript
interface ViewUpdate {
    startState: EditorState;
    state: EditorState;
    transactions: Transaction[];
    changes: ChangeSet;
    geometryChanged: boolean;
    focusChanged: boolean;
}
```

**Usage**: Our `create_jql_editor()` wrapper configures these via dash-codemirror props, but does not directly access internal state.
