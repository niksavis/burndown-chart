# Data Model: JQL Syntax Highlighting

**Feature**: Complete JQL Syntax Highlighting with Real-time Visual Feedback
**Date**: 2025-10-15

## Overview

This document defines the data structures and entities for implementing real-time JQL syntax highlighting. The feature extends existing entities from feature 001-add-jql-query (SyntaxToken, JQL_KEYWORDS) and introduces new entities for visual rendering and error detection.

---

## Entity Definitions

### 1. SyntaxToken (EXISTING - from feature 001)

**Purpose**: Represents a parsed segment of JQL query with type and position information.

**Schema**:
```python
{
    "text": str,       # The actual text content of the token
    "type": str,       # Token type: "keyword", "string", "operator", "text", "function", "error"
    "start": int,      # Start index in original query string (0-based)
    "end": int         # End index in original query string (exclusive)
}
```

**Validation Rules**:
- `text`: Non-empty string, must match `query[start:end]`
- `type`: Must be one of: "keyword", "string", "operator", "text", "function", "error"
- `start`: Non-negative integer, less than query length
- `end`: Greater than `start`, not exceeding query length

**Constraints**:
- Tokens must not overlap (token[i].end <= token[i+1].start)
- All tokens together must cover entire query string (no gaps)

**Example**:
```python
{
    "text": "AND",
    "type": "keyword",
    "start": 15,
    "end": 18
}
```

**State Transitions**: None (immutable after parsing)

**Relationships**:
- Belongs to: JQL Query (as list of tokens)
- Used by: render_syntax_tokens() for HTML generation

---

### 2. JQLQuery (EXISTING - Extended)

**Purpose**: Container for JQL query text and associated metadata (character count, parsed tokens).

**Schema**:
```python
{
    "query_text": str,               # Raw JQL query string
    "character_count": int,          # Total character count (from count_jql_characters)
    "tokens": List[SyntaxToken],     # Parsed syntax tokens
    "errors": List[SyntaxError],     # Detected syntax errors (NEW)
    "last_parsed": float             # Timestamp of last parse (NEW)
}
```

**Validation Rules**:
- `query_text`: String, max 5000 characters (performance constraint per FR-011)
- `character_count`: Must equal `len(query_text)`
- `tokens`: List of valid SyntaxToken objects
- `errors`: List of SyntaxError objects (can be empty)
- `last_parsed`: Unix timestamp (seconds since epoch)

**Example**:
```python
{
    "query_text": "project = TEST AND status = \"Done\"",
    "character_count": 35,
    "tokens": [
        {"text": "project", "type": "text", "start": 0, "end": 7},
        {"text": " ", "type": "text", "start": 7, "end": 8},
        {"text": "=", "type": "operator", "start": 8, "end": 9},
        # ... more tokens
    ],
    "errors": [],
    "last_parsed": 1729012345.67
}
```

---

### 3. SyntaxError (NEW)

**Purpose**: Represents a detected syntax error in JQL query with position and type information.

**Schema**:
```python
{
    "error_type": str,      # Error type: "unclosed_string", "invalid_operator"
    "start": int,           # Start index of error in query string
    "end": int,             # End index of error in query string
    "token": SyntaxToken,   # The problematic token
    "message": str          # Human-readable error description
}
```

**Validation Rules**:
- `error_type`: Must be one of: "unclosed_string", "invalid_operator"
- `start`, `end`: Valid indices matching token position
- `token`: Valid SyntaxToken object
- `message`: Non-empty descriptive string

**Example**:
```python
{
    "error_type": "unclosed_string",
    "start": 20,
    "end": 25,
    "token": {
        "text": "\"Done",
        "type": "string",
        "start": 20,
        "end": 25
    },
    "message": "Unclosed string literal"
}
```

**State Transitions**: None (immutable after detection)

---

### 4. HighlightedComponent (NEW)

**Purpose**: Dash component for rendering syntax-highlighted JQL textarea with dual-layer overlay.

**Schema** (Component Props):
```python
{
    "id": str,                      # Unique component ID
    "value": str,                   # Current query text
    "placeholder": str,             # Placeholder text
    "rows": int,                    # Textarea rows
    "maxLength": int,               # Max character limit (5000)
    "disabled": bool,               # Disabled state
    "className": str,               # Additional CSS classes
    "style": dict,                  # Inline styles
    "aria_label": str               # Accessibility label
}
```

**Internal State** (Client-side):
```javascript
{
    highlightedHtml: string,        // Rendered syntax-highlighted HTML
    scrollTop: number,              // Current scroll position
    scrollLeft: number,             // Horizontal scroll position
    cursorPosition: number,         # Cursor index in text
    rafId: number | null,           // requestAnimationFrame ID
    lastParsedText: string          // Last parsed query text (for change detection)
}
```

**Validation Rules**:
- `id`: Required, unique within page
- `value`: String, max 5000 characters
- `rows`: Positive integer, typically 3-10
- `maxLength`: Must be 5000 (performance constraint)

**Example**:
```python
HighlightedComponent(
    id="jql-query-input",
    value="project = TEST",
    placeholder="Enter JQL query...",
    rows=5,
    maxLength=5000,
    aria_label="JQL Query Input"
)
```

---

### 5. ScriptRunnerFunction (NEW)

**Purpose**: Extended JQL function from ScriptRunner plugin with metadata.

**Schema**:
```python
{
    "name": str,            # Function name (e.g., "linkedIssuesOf")
    "category": str,        # Function category (e.g., "Issue Links", "Date")
    "syntax": str,          # Function syntax pattern (e.g., "issueFunction in linkedIssuesOf('KEY')")
    "description": str      # Brief function description (optional, for future enhancement)
}
```

**Validation Rules**:
- `name`: Non-empty string, must match Python identifier rules
- `category`: String, typically one of ScriptRunner categories
- `syntax`: Non-empty string showing usage pattern

**Constants** (Python):
```python
SCRIPTRUNNER_FUNCTIONS = frozenset([
    "linkedIssuesOf", "issuesInEpics", "subtasksOf", "parentsOf", "epicsOf",
    "hasLinks", "hasComments", "hasAttachments", "lastUpdated", "expression",
    "dateCompare", "aggregateExpression", "issueFieldMatch",
    "linkedIssuesOfRecursive", "workLogged"
])

SCRIPTRUNNER_CATEGORIES = {
    "linkedIssuesOf": "Issue Links",
    "issuesInEpics": "Issue Links",
    "subtasksOf": "Issue Links",
    "parentsOf": "Issue Links",
    "epicsOf": "Issue Links",
    "hasLinks": "Issue Links",
    "hasComments": "Comments",
    "hasAttachments": "Attachments",
    "lastUpdated": "Date",
    "expression": "Calculations",
    "dateCompare": "Date",
    "aggregateExpression": "Calculations",
    "issueFieldMatch": "Match Functions",
    "linkedIssuesOfRecursive": "Issue Links",
    "workLogged": "Worklogs"
}
```

**Example**:
```python
{
    "name": "linkedIssuesOf",
    "category": "Issue Links",
    "syntax": "issueFunction in linkedIssuesOf('KEY')",
    "description": "Returns issues linked to specified issue"
}
```

---

## Data Flow

### 1. Query Input → Parsing → Rendering

```
User Types
    ↓
Textarea onChange Event
    ↓
JavaScript Event Handler (debounced with requestAnimationFrame)
    ↓
Dash Callback: update_jql_highlighting()
    ↓
parse_jql_syntax(query_text) → List[SyntaxToken]
    ↓
detect_syntax_errors(tokens) → List[SyntaxError]
    ↓
render_syntax_tokens(tokens, errors) → List[Dash components]
    ↓
Update Contenteditable Div (highlighting overlay)
    ↓
Sync Scroll Position (JavaScript)
```

### 2. Syntax Highlighting Rendering Pipeline

```
SyntaxToken List
    ↓
Group by type (keyword, string, operator, function, error)
    ↓
Map to CSS classes:
    - keyword → .jql-keyword (blue)
    - string → .jql-string (green)
    - operator → .jql-operator (gray)
    - function → .jql-function (purple)
    - error → .jql-error-unclosed / .jql-error-invalid (red underline/orange bg)
    ↓
Wrap in html.Mark components
    ↓
Return list of Dash html components
    ↓
Render in contenteditable div (aria-hidden="true")
```

### 3. Error Detection Flow

```
Parsed Tokens
    ↓
Iterate through tokens
    ↓
For each string token:
    Check if starts with quote but doesn't end with matching quote
        → Create SyntaxError(type="unclosed_string")
    ↓
For each operator token:
    Check if operator is in VALID_OPERATORS set
    If not → Create SyntaxError(type="invalid_operator")
    ↓
Return List[SyntaxError]
    ↓
Apply error styling to tokens
```

---

## State Management

### Client-Side State (dcc.Store)

**jql-syntax-state** (NEW):
```python
{
    "last_parsed_query": str,      # Last successfully parsed query (for change detection)
    "parse_timestamp": float,      # Unix timestamp of last parse
    "error_count": int,            # Number of detected errors
    "performance_metrics": {       # Performance tracking
        "last_parse_time_ms": float,
        "avg_parse_time_ms": float,
        "frame_rate": float        # Rendering FPS
    }
}
```

**Purpose**: Track parsing state and performance metrics for optimization.

**Validation Rules**:
- `last_parsed_query`: String, max 5000 characters
- `parse_timestamp`: Valid Unix timestamp
- `error_count`: Non-negative integer
- `performance_metrics`: All values non-negative floats

---

## Constants

### Token Types
```python
TOKEN_TYPES = ["keyword", "string", "operator", "text", "function", "error"]
```

### Error Types
```python
ERROR_TYPES = ["unclosed_string", "invalid_operator"]
```

### Valid Operators (JQL Specification)
```python
VALID_OPERATORS = frozenset(["=", "!=", "<", ">", "<=", ">=", "~", "!~", "IN", "NOT IN", "IS", "IS NOT", "WAS", "WAS IN", "WAS NOT", "WAS NOT IN"])
```

### Performance Thresholds
```python
MAX_PARSE_TIME_MS = 50           # FR-005: Max latency per keystroke
MIN_FRAME_RATE = 60              # FR-011: Maintain 60fps during typing
MAX_QUERY_LENGTH = 5000          # FR-011: Performance tested up to 5000 chars
PASTE_RENDER_TIME_MS = 300       # SC-007: Paste operation render time
```

---

## Validation Functions

### validate_syntax_token(token: dict) -> bool
```python
def validate_syntax_token(token: dict) -> bool:
    """
    Validate SyntaxToken structure and constraints.
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(token, dict):
        return False
    
    required_keys = ["text", "type", "start", "end"]
    if not all(key in token for key in required_keys):
        return False
    
    if token["type"] not in TOKEN_TYPES:
        return False
    
    if not isinstance(token["start"], int) or not isinstance(token["end"], int):
        return False
    
    if token["start"] < 0 or token["end"] <= token["start"]:
        return False
    
    if token["text"] != token["text"][token["start"]:token["end"]]:
        return False
    
    return True
```

### validate_syntax_error(error: dict) -> bool
```python
def validate_syntax_error(error: dict) -> bool:
    """
    Validate SyntaxError structure and constraints.
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(error, dict):
        return False
    
    required_keys = ["error_type", "start", "end", "token", "message"]
    if not all(key in error for key in required_keys):
        return False
    
    if error["error_type"] not in ERROR_TYPES:
        return False
    
    if not validate_syntax_token(error["token"]):
        return False
    
    return True
```

---

## Schema Evolution

### Backward Compatibility

**Feature 001 Compatibility**:
- Existing `parse_jql_syntax()` and `render_syntax_tokens()` functions remain unchanged
- New token type "function" added without breaking existing "keyword", "string", "operator", "text"
- Existing CSS classes (.jql-keyword, .jql-string, .jql-operator) remain valid
- Character count functionality (count_jql_characters, should_show_character_warning) unaffected

**Migration Path**:
- No data migration required (no persisted data structures)
- Feature toggle: If syntax highlighting disabled, falls back to plain textarea
- Graceful degradation: If browser lacks required features, plain textarea used

### Future Extensions

**Potential Schema Additions** (Out of Scope for Feature 002):
- **AutocompleteSuggestion**: For future autocomplete feature
  ```python
  {
      "text": str,
      "type": str,  # "field", "value", "function"
      "insert_position": int,
      "description": str
  }
  ```

- **SemanticValidationError**: For future JIRA API validation
  ```python
  {
      "error_type": "invalid_field" | "invalid_value",
      "field_name": str,
      "suggestion": str
  }
  ```

---

## Summary

**Core Entities**:
1. **SyntaxToken**: Parsed query segment (EXISTING, extended with "function" type)
2. **JQLQuery**: Query container (EXISTING, extended with errors and timestamp)
3. **SyntaxError**: Detected syntax error (NEW)
4. **HighlightedComponent**: Dual-layer textarea component (NEW)
5. **ScriptRunnerFunction**: ScriptRunner function metadata (NEW)

**Key Relationships**:
- JQLQuery → contains → List[SyntaxToken]
- JQLQuery → contains → List[SyntaxError]
- SyntaxError → references → SyntaxToken
- HighlightedComponent → renders → JQLQuery with highlighting

**Validation Constraints**:
- Max query length: 5000 characters
- Max parse time: 50ms
- Token type enumeration enforced
- Position indices validated (no overlaps, no gaps)

**Data Flow**:
1. User input → Parsing → Token list
2. Token list → Error detection → Error list
3. Token + Error lists → Rendering → Highlighted HTML
4. Performance metrics tracked in client-side state
