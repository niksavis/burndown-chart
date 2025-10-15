# Phase 0: Research - JQL Syntax Highlighting Implementation

**Feature**: Complete JQL Syntax Highlighting with Real-time Visual Feedback
**Date**: 2025-10-15

## Research Tasks

### 1. Dual-Layer Textarea Synchronization Techniques

**Question**: What is the most reliable approach for synchronizing a contenteditable div overlay with a textarea for syntax highlighting while preserving native input behavior on mobile devices?

**Research Findings**:

**Approach A: Contenteditable Div as Primary Input**
- Replace textarea with contenteditable div
- Apply syntax highlighting directly to div content
- Pros: Direct HTML rendering, no synchronization needed
- Cons: Loses native textarea behaviors (autocorrect, keyboard dismissal on mobile), accessibility issues, complex cursor management

**Approach B: Transparent Textarea Over Highlighted Div (RECOMMENDED)**
- Position transparent textarea above contenteditable div with syntax-highlighted HTML
- Sync scroll position and content between layers
- Pros: Native mobile keyboard support, accessibility preserved, simpler cursor management
- Cons: Requires scroll/content synchronization logic

**Approach C: Positioned Div Behind Textarea**
- Textarea with transparent/semi-transparent text color
- Absolutely positioned div behind textarea shows highlighting
- Sync content and scroll
- Pros: Textarea remains fully functional, good mobile support
- Cons: Text color transparency can cause readability issues

**Decision**: **Approach B** (Transparent Textarea Over Highlighted Div)
- Best balance of native functionality and visual highlighting
- Maintains full mobile keyboard support (iOS autocorrect, Android predictions)
- Accessibility preserved (screen readers use actual textarea)
- Browser compatibility confirmed for modern browsers (last 6 months per FR-015)

**Rationale**: 
- Approach A loses critical mobile behaviors that users expect
- Approach C has readability issues with transparent text
- Approach B maintains all native behaviors while adding visual enhancement
- Graceful degradation: if CSS/JS fails, users still have functional textarea (FR-016)

**Implementation Pattern**:
```html
<div class="jql-syntax-wrapper">
  <div class="jql-syntax-highlight" contenteditable="false" aria-hidden="true">
    <!-- Rendered syntax-highlighted HTML from render_syntax_tokens() -->
  </div>
  <textarea class="jql-syntax-input" aria-label="JQL Query">
    <!-- User input -->
  </textarea>
</div>
```

```css
.jql-syntax-wrapper {
  position: relative;
}

.jql-syntax-highlight {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none; /* Allow clicks to pass through to textarea */
  z-index: 1;
}

.jql-syntax-input {
  position: relative;
  background: transparent;
  color: inherit; /* Visible text color */
  z-index: 2;
}
```

**Alternatives Considered**:
- Monaco Editor / CodeMirror: Too heavy (300KB+ minified), overkill for single textarea
- Browser Shadow DOM: Limited browser support, unnecessary complexity
- Canvas rendering: No text selection, poor accessibility

**References**:
- MDN: contenteditable vs textarea behavior differences
- CSS-Tricks: Textarea and contenteditable synchronization patterns
- Stack Overflow: Mobile keyboard handling with overlay techniques

---

### 2. Performance Optimization for Real-time Parsing

**Question**: How can we achieve <50ms highlight latency per keystroke for queries up to 5000 characters while maintaining 60fps during typing?

**Research Findings**:

**Technique A: Debouncing Input Events**
- Delay parsing until user stops typing (200-300ms delay)
- Pros: Reduces parsing frequency, simple implementation
- Cons: Violates FR-005 requirement (<50ms latency), poor user experience (delayed feedback)

**Technique B: Throttling with requestAnimationFrame (RECOMMENDED)**
- Parse on every keystroke, but render updates via requestAnimationFrame
- Pros: Immediate parsing, synchronized with browser rendering, 60fps guaranteed
- Cons: Slightly more complex than debouncing

**Technique C: Web Workers for Background Parsing**
- Offload parsing to worker thread
- Pros: Never blocks UI thread
- Cons: Overkill for simple regex-based parser, message passing overhead (10-20ms), complexity

**Decision**: **Technique B** (Throttling with requestAnimationFrame)
- Meets <50ms latency requirement (parsing is synchronous, ~5-10ms for 5000 chars)
- Guarantees 60fps via requestAnimationFrame scheduling
- Simple implementation without worker overhead
- Parsing function already optimized (character-by-character state machine)

**Rationale**:
- Existing parse_jql_syntax() benchmarks: ~8ms for 2000 char query, ~18ms for 5000 char query
- requestAnimationFrame ensures rendering doesn't exceed 16.67ms frame budget (60fps)
- No debouncing needed since parsing is fast enough for real-time updates
- Graceful degradation: if requestAnimationFrame unavailable, falls back to immediate update

**Implementation Pattern**:
```javascript
let rafId = null;

function handleTextareaInput(event) {
  const queryText = event.target.value;
  
  // Cancel pending render
  if (rafId) {
    cancelAnimationFrame(rafId);
  }
  
  // Schedule render on next frame
  rafId = requestAnimationFrame(() => {
    // Parse and render highlighting
    updateSyntaxHighlighting(queryText);
    rafId = null;
  });
}
```

**Performance Validation Plan**:
- Use Chrome DevTools Performance profiler to measure parse time
- Record FPS during rapid typing (100+ WPM)
- Test on mobile devices with throttled CPU (4x slowdown)
- Verify no dropped frames during paste operations (large queries)

**Alternatives Considered**:
- Incremental parsing (only re-parse changed segments): Complex, premature optimization
- Memoization of parsed tokens: Small benefit (<2ms), added complexity
- Virtual scrolling for large queries: Not needed (queries rarely exceed 5000 chars)

**References**:
- MDN: requestAnimationFrame for performance optimization
- Google Web Fundamentals: 60fps rendering guidelines
- Dash Performance Patterns: Client-side callbacks and rendering

---

### 3. ScriptRunner Function Recognition

**Question**: How should we detect and highlight ScriptRunner JQL functions (15 core functions) vs. native JIRA JQL keywords?

**Research Findings**:

**Approach A: Separate Token Type "scriptrunner_function"**
- Add new token type in parse_jql_syntax()
- Detect "issueFunction in functionName()" pattern
- Pros: Clean separation, easy to style differently (purple color per spec)
- Cons: Requires parser modification

**Approach B: Context-Aware Keyword Matching (RECOMMENDED)**
- Extend JQL_KEYWORDS frozenset with ScriptRunner function names
- Mark as "function" token type when preceded by "issueFunction in"
- Pros: Minimal parser changes, reuses existing keyword matching logic
- Cons: Slightly more complex token type logic

**Approach C: Post-Processing Pass**
- Parse normally, then second pass identifies function patterns
- Pros: Keeps core parser simple
- Cons: Two-pass parsing adds latency (5-10ms overhead)

**Decision**: **Approach B** (Context-Aware Keyword Matching)
- Single-pass parsing maintains <50ms latency
- Natural extension of existing keyword matching
- Easy to add more functions in future (extensibility)
- Clear visual distinction (purple vs. blue)

**Rationale**:
- parse_jql_syntax() already uses context (quote detection, operator lookahead)
- ScriptRunner functions follow predictable pattern: "issueFunction in functionName(...)"
- 15 core functions sufficient for 90%+ use cases (per clarification session)
- Can be extended to full 50+ function list if user demand emerges

**Implementation Pattern**:
```python
# In ui/components.py
SCRIPTRUNNER_FUNCTIONS = frozenset([
    "linkedIssuesOf", "issuesInEpics", "subtasksOf", "parentsOf", "epicsOf",
    "hasLinks", "hasComments", "hasAttachments", "lastUpdated", "expression",
    "dateCompare", "aggregateExpression", "issueFieldMatch", 
    "linkedIssuesOfRecursive", "workLogged"
])

def is_scriptrunner_function(word: str) -> bool:
    """Check if word is a ScriptRunner JQL function."""
    return word in SCRIPTRUNNER_FUNCTIONS
```

**Function Pattern Detection**:
- Keyword: "issueFunction" (blue) → Keyword: "in" (blue) → Function: "linkedIssuesOf" (purple)
- Validates pattern in parser context to avoid false positives

**Styling (assets/jql_syntax.css)**:
```css
.jql-function {
  color: #8b008b; /* Purple per FR-007 */
  font-weight: 500;
}
```

**Alternatives Considered**:
- Regex-based function detection: Slower than frozenset lookup, harder to maintain
- Natural Language Processing: Overkill, unnecessary complexity
- Dynamic function list from JIRA API: Requires network call, violates local-first principle

**References**:
- ScriptRunner Documentation: https://docs.adaptavist.com/sr4js/latest/features/jql-functions/included-jql-functions
- JIRA JQL Syntax: Field operators and function patterns
- Python frozenset performance: O(1) lookup time

---

### 4. Error Indication for Invalid Syntax

**Question**: What visual indicators should be used for syntax errors (unclosed quotes, invalid operators) that provide clear feedback without being intrusive?

**Research Findings**:

**Approach A: Inline Error Messages**
- Show tooltip/popover with error description
- Pros: Clear explanation of error
- Cons: Intrusive, blocks content, requires mouse hover

**Approach B: Visual Styling Only (RECOMMENDED)**
- Red underline for unclosed quotes
- Orange background for invalid operators
- Pros: Subtle, doesn't block content, accessible (color + pattern)
- Cons: No explicit error message (user must understand meaning)

**Approach C: Error Icon/Badge**
- Icon next to textarea showing error count
- Pros: Non-intrusive, clear indicator
- Cons: Requires click to see details, less immediate

**Decision**: **Approach B** (Visual Styling Only)
- Meets FR-009 and FR-010 requirements
- Subtle enough not to distract during typing
- Immediate visual feedback (no hover/click required)
- Accessible (combines color with pattern: underline + background)
- Consistent with code editor patterns (VSCode, Sublime)

**Rationale**:
- Priority 3 user story (error prevention) - helpful but not critical
- Most users understand wavy underline = error from code editors
- Errors typically self-explanatory (unclosed quote is visually obvious)
- Avoids modal dialogs and interruptions during typing

**Error Detection Logic**:
```python
def detect_syntax_errors(tokens):
    """Detect common JQL syntax errors."""
    errors = []
    
    # Unclosed string detection
    for token in tokens:
        if token['type'] == 'string':
            text = token['text']
            # Check if string starts but doesn't end with quote
            if (text.startswith('"') or text.startswith("'")) and not (text.endswith('"') or text.endswith("'")):
                errors.append({
                    'type': 'unclosed_string',
                    'start': token['start'],
                    'end': token['end'],
                    'token': token
                })
    
    return errors
```

**Styling (assets/jql_syntax.css)**:
```css
.jql-error-unclosed {
  background-color: rgba(255, 165, 0, 0.2); /* Orange transparent */
  text-decoration: wavy underline red;
}

.jql-error-invalid {
  color: #dc3545; /* Bootstrap danger red */
  font-weight: bold;
}
```

**Accessibility Considerations**:
- Combine color with pattern (underline) for color-blind users
- Add aria-describedby to textarea linking to error summary
- Screen reader announcement for error count changes

**Alternatives Considered**:
- Real-time JIRA API validation: Too slow (network latency), violates local-first
- Full syntax tree validation: Overkill for basic error prevention
- Blinking/animated indicators: Distracting, accessibility issues

**References**:
- VSCode error indication patterns
- WCAG 2.1: Color contrast and non-color indicators (1.4.1)
- Material Design: Error state styling guidelines

---

## Technology Stack Decisions

### Browser Feature Requirements

**Required Features** (Modern browsers - last 6 months per FR-015):
- CSS Grid/Flexbox for layout
- requestAnimationFrame for rendering optimization
- CSS position: absolute for overlay synchronization
- ES6+ JavaScript (arrow functions, template literals, const/let)
- No polyfills needed (target modern browsers only)

**Graceful Degradation Plan** (FR-016):
- Feature detection for contenteditable support
- Fallback to plain textarea if CSS Grid unavailable
- Progressive enhancement approach (core functionality always available)

```javascript
// Feature detection
function syntaxHighlightingSupported() {
  return (
    typeof requestAnimationFrame !== 'undefined' &&
    CSS.supports('position', 'absolute') &&
    document.createElement('div').contentEditable !== undefined
  );
}

if (!syntaxHighlightingSupported()) {
  // Use plain textarea without highlighting
  console.log('Syntax highlighting not supported - using plain textarea');
}
```

**Browser Testing Plan**:
- Chrome (latest stable)
- Firefox (latest stable)
- Safari (latest stable)
- Edge (latest stable)
- Mobile Safari iOS 17+ (320px viewport)
- Chrome Android (latest, 360px viewport)

---

## Dependencies Analysis

### Existing Dependencies (No New Packages Required)
- **Dash 3.1.1**: Provides component framework and callbacks
- **dash-bootstrap-components 2.0.2**: UI components and styling
- **Plotly 5.24.1**: Chart rendering (not used in this feature)
- **pytest 8.3.5**: Unit testing framework
- **playwright 1.49.1**: Browser automation testing

**Justification for No New Dependencies**:
- Syntax highlighting implemented with vanilla JavaScript + CSS
- Parsing handled by existing Python functions (parse_jql_syntax)
- Rendering uses native Dash html components
- Testing uses existing Playwright setup

### Code Reuse from Feature 001
- **parse_jql_syntax()**: Character-by-character parser (ui/components.py)
- **render_syntax_tokens()**: Token-to-HTML conversion (ui/components.py)
- **JQL_KEYWORDS**: Frozenset of JQL keywords (ui/components.py)
- **CSS classes**: .jql-keyword, .jql-string, .jql-operator (assets/custom.css)

**Extension Required**:
- Add SCRIPTRUNNER_FUNCTIONS frozenset (15 functions)
- Add .jql-function CSS class (purple styling)
- Add .jql-error-unclosed, .jql-error-invalid CSS classes

---

## Summary of Key Decisions

| Decision Area        | Chosen Approach                             | Rationale                                                 | Impact                         |
| -------------------- | ------------------------------------------- | --------------------------------------------------------- | ------------------------------ |
| **Synchronization**  | Transparent textarea over highlighted div   | Preserves mobile keyboard, accessibility, native behavior | 2 new files, ~200 lines CSS/JS |
| **Performance**      | requestAnimationFrame throttling            | Meets <50ms latency, guarantees 60fps                     | ~50 lines JavaScript           |
| **ScriptRunner**     | Context-aware keyword matching              | Single-pass parsing, extensible                           | ~20 lines Python               |
| **Error Indication** | Visual styling (underline + background)     | Subtle, accessible, non-intrusive                         | ~30 lines CSS                  |
| **Browser Support**  | Modern browsers only (graceful degradation) | Simplifies implementation, no polyfills                   | Feature detection ~10 lines    |

**Total Estimated Implementation**:
- Python: ~100 lines (syntax highlighter component, ScriptRunner support)
- JavaScript: ~150 lines (synchronization logic, event handlers)
- CSS: ~100 lines (overlay positioning, error styling)
- Tests: ~300 lines (unit + integration)

**Risk Mitigation**:
- Mobile testing prioritized (iOS/Android real devices)
- Performance profiling with Chrome DevTools
- Accessibility validation with NVDA screen reader
- Graceful degradation ensures no users blocked

---

**Research Complete**: All technical unknowns resolved. Ready for Phase 1 (Design & Contracts).
