# Data Model: JQL Query Enhancements

**Feature**: 001-add-jql-query  
**Date**: 2025-10-15  
**Phase**: Phase 1 - Design & Contracts

## Entities

### 1. Character Count State

**Purpose**: Track real-time character count for JQL query textareas to provide user feedback and warning states.

**Storage**: Client-side only (`dcc.Store` component)

**Schema**:
```python
from typing import TypedDict

class CharacterCountState(TypedDict):
    """
    Character count state stored in dcc.Store.
    
    Attributes:
        count: Current character count (including whitespace, unicode)
        warning: True if count exceeds warning threshold (1800)
        textarea_id: ID of the textarea being tracked ("main" or "dialog")
        last_updated: Timestamp of last update (for debugging)
    """
    count: int
    warning: bool
    textarea_id: str
    last_updated: float  # Unix timestamp
```

**Example**:
```json
{
    "count": 1850,
    "warning": true,
    "textarea_id": "main",
    "last_updated": 1697385600.0
}
```

**Validation Rules**:
- `count` ≥ 0 (never negative)
- `warning` = `True` if `count > 1800`, else `False`
- `textarea_id` ∈ {"main", "dialog"}
- `last_updated` = current Unix timestamp when state updates

**State Transitions**:
```
Initial State → User Types → Count Updates → Warning Activated (if > 1800)
     ↓              ↓              ↓                    ↓
  count: 0      count: 1850    warning: True      Display: Warning Color
```

---

### 2. JQL Syntax Tokens

**Purpose**: Parsed representation of JQL query for syntax highlighting rendering.

**Storage**: Ephemeral (generated in callback, not persisted)

**Schema**:
```python
from typing import Literal, TypedDict
from dash import html

TokenType = Literal["keyword", "string", "field", "operator", "text"]

class SyntaxToken(TypedDict):
    """
    Individual token from JQL query parsing.
    
    Attributes:
        text: The actual text of the token
        type: Token classification for CSS styling
        start: Starting position in original query (for debugging)
        end: Ending position in original query (for debugging)
    """
    text: str
    type: TokenType
    start: int
    end: int
```

**Example**:
```python
# Query: 'project = TEST AND status IN ("Done", "In Progress")'
tokens = [
    {"text": "project", "type": "field", "start": 0, "end": 7},
    {"text": " = ", "type": "operator", "start": 7, "end": 10},
    {"text": "TEST", "type": "text", "start": 10, "end": 14},
    {"text": " AND ", "type": "keyword", "start": 14, "end": 19},
    {"text": "status", "type": "field", "start": 19, "end": 25},
    {"text": " IN ", "type": "keyword", "start": 25, "end": 29},
    {"text": '"Done"', "type": "string", "start": 30, "end": 36},
    # ... etc
]
```

**Rendering to HTML**:
```python
def render_syntax_tokens(tokens: List[SyntaxToken]) -> List[html.Mark | str]:
    """Convert tokens to Dash HTML components with CSS classes."""
    return [
        html.Mark(token["text"], className=f"jql-{token['type']}")
        if token["type"] != "text"
        else token["text"]
        for token in tokens
    ]
```

---

### 3. JQL Keywords Registry

**Purpose**: Canonical list of JQL keywords for syntax highlighting recognition.

**Storage**: Python constant (no persistence required)

**Schema**:
```python
from typing import FrozenSet

JQL_KEYWORDS: FrozenSet[str] = frozenset([
    # Logical Operators
    "AND", "OR", "NOT",
    
    # Comparison Operators
    "IN", "NOT IN",
    
    # State Operators
    "IS", "IS NOT", "WAS", "WAS NOT",
    
    # Special Values
    "EMPTY", "NULL",
    
    # List Operators
    "CONTAINS", "NOT CONTAINS",
    
    # Ordering
    "ORDER BY", "ASC", "DESC"
])
```

**Usage**:
```python
def is_jql_keyword(word: str) -> bool:
    """Check if word is a JQL keyword (case-insensitive)."""
    return word.upper() in JQL_KEYWORDS
```

---

### 4. Warning Threshold Configuration

**Purpose**: Define character count thresholds for user warnings.

**Storage**: Python constants (configurable via app_settings.json in future)

**Schema**:
```python
from typing import TypedDict

class CharacterCountConfig(TypedDict):
    """
    Character count warning configuration.
    
    Attributes:
        warning_threshold: Character count to trigger warning display (1800)
        max_reference: Maximum character count shown to user (2000)
        debounce_ms: Milliseconds to debounce count updates (300)
    """
    warning_threshold: int
    max_reference: int
    debounce_ms: int
```

**Constants**:
```python
CHARACTER_COUNT_CONFIG: CharacterCountConfig = {
    "warning_threshold": 1800,
    "max_reference": 2000,
    "debounce_ms": 300
}
```

**Rationale for Values**:
- **1800 warning threshold**: Gives user 200-character buffer before JIRA limit (~2000)
- **2000 max reference**: Common JIRA instance limit (may vary, but standard)
- **300ms debounce**: Balances responsiveness with performance (per spec FR-002)

---

## Data Flows

### Flow 1: Character Count Update

```
User Types in Textarea
         ↓
Textarea "value" property changes
         ↓
Callback: store_character_count()
    - Input: textarea value
    - Process: len(value)
    - Output: CharacterCountState
         ↓
dcc.Store updated
         ↓
Callback: render_character_count()
    - Input: CharacterCountState
    - Process: Format display with warning styling
    - Output: html.Div with count + warning indicator
         ↓
UI Updated (300ms debounced)
```

### Flow 2: Syntax Highlighting Render

```
User Types in Textarea
         ↓
Textarea "value" property changes
         ↓
Callback: highlight_jql_syntax()
    - Input: Raw JQL query string
    - Process: Parse into SyntaxTokens
    - Output: List[html.Mark | str]
         ↓
Textarea children updated with highlighted HTML
         ↓
CSS applies .jql-keyword, .jql-string classes
         ↓
User sees colored syntax highlighting
```

### Flow 3: Warning State Activation

```
Character Count > 1800
         ↓
CharacterCountState.warning = True
         ↓
render_character_count() callback
    - Adds "text-warning" CSS class
    - Adds warning icon (fa-exclamation-triangle)
    - Sets aria-live="polite" announcement
         ↓
Screen Reader Announces: "Warning: 1850 of 2000 characters used"
         ↓
Visual Warning Displayed (amber/orange color)
```

---

## Validation Functions

### Character Count Validation

```python
def validate_character_count_state(state: dict) -> bool:
    """
    Validate CharacterCountState structure.
    
    Args:
        state: Dictionary to validate against CharacterCountState schema
        
    Returns:
        True if valid, False otherwise
        
    Raises:
        ValueError: If validation fails with descriptive error
    """
    if not isinstance(state.get("count"), int) or state["count"] < 0:
        raise ValueError("count must be non-negative integer")
    
    if not isinstance(state.get("warning"), bool):
        raise ValueError("warning must be boolean")
    
    if state.get("textarea_id") not in ("main", "dialog"):
        raise ValueError("textarea_id must be 'main' or 'dialog'")
    
    # Validate warning state matches count
    expected_warning = state["count"] > 1800
    if state["warning"] != expected_warning:
        raise ValueError(f"warning state mismatch: count={state['count']}, warning={state['warning']}")
    
    return True
```

### Syntax Token Validation

```python
def validate_syntax_token(token: dict) -> bool:
    """
    Validate SyntaxToken structure.
    
    Args:
        token: Dictionary to validate against SyntaxToken schema
        
    Returns:
        True if valid, False otherwise
        
    Raises:
        ValueError: If validation fails with descriptive error
    """
    if not isinstance(token.get("text"), str):
        raise ValueError("text must be string")
    
    valid_types = {"keyword", "string", "field", "operator", "text"}
    if token.get("type") not in valid_types:
        raise ValueError(f"type must be one of {valid_types}")
    
    if not isinstance(token.get("start"), int) or token["start"] < 0:
        raise ValueError("start must be non-negative integer")
    
    if not isinstance(token.get("end"), int) or token["end"] < token["start"]:
        raise ValueError("end must be >= start")
    
    return True
```

---

## State Lifecycle

### Character Count State Lifecycle

1. **Initialization**: `{"count": 0, "warning": False, "textarea_id": "main", "last_updated": 0.0}`
2. **User Typing**: State updates on each change (debounced at 300ms)
3. **Warning Activation**: When `count > 1800`, `warning` becomes `True`
4. **Warning Deactivation**: When `count <= 1800`, `warning` becomes `False`
5. **Reset**: When textarea cleared, state returns to initialization values

### Syntax Tokens Lifecycle

1. **Parsing**: Raw query string → List[SyntaxToken]
2. **Rendering**: Tokens → List[html.Mark | str]
3. **Display**: HTML components rendered in textarea
4. **Discarded**: Not persisted, regenerated on each query change

---

## Performance Considerations

**Character Count State**:
- **Update Frequency**: Debounced to 300ms (max ~3 updates/second)
- **Size**: ~100 bytes per state object (negligible)
- **Storage**: Client-side only, no server round-trips

**Syntax Tokens**:
- **Parsing Time**: ~5-10ms for 2000-character query (string operations only)
- **Memory**: ~50 bytes per token, ~100 tokens for complex query = 5KB (negligible)
- **Rendering**: Dash HTML generation <5ms

**Conclusion**: ✅ No performance concerns, well within 60fps requirement (16.7ms per frame)

---

## Schema Evolution

**Future Enhancements** (Out of Scope for 001):
- **Customizable Thresholds**: Store `warning_threshold` and `max_reference` in `app_settings.json`
- **Query History**: Persist character count trends for analytics
- **Error Tokens**: Add `"error"` token type for invalid JQL syntax (requires syntax validation)

**Backward Compatibility**:
- Adding new fields to CharacterCountState: ✅ Safe (provide defaults)
- Adding new TokenType values: ✅ Safe (render as "text" if unknown)
- Changing threshold values: ✅ Safe (constants, no breaking changes)
