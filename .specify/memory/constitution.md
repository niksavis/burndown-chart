<!--
Sync Impact Report:
Version: 1.0.1 (Test Isolation Clarification)
Modified Principles: N/A
Added Sections: Test Isolation requirements in Testing Gate (Phase -1) and Test Coverage Gate (Implementation)
Removed Sections: N/A
Templates Requiring Updates:
  - ✅ plan-template.md: Already enforces Phase -1 gates
  - ✅ spec-template.md: Already references constitutional requirements
  - ✅ tasks-template.md: Already validates against quality gates
  - ✅ copilot-instructions.md: Updated with detailed test isolation patterns and examples
Follow-up TODOs: None - test isolation requirements documented
-->

# Burndown Chart Constitution

**Project**: Burndown Chart - Agile Project Forecasting Tool  
**Type**: Locally-run Python Dash Web Application  
**Purpose**: Mobile-first burndown chart visualization with JIRA integration

## Core Principles

### I. Mobile-First Design (NON-NEGOTIABLE)

All features MUST work flawlessly on mobile devices (320px+) before any desktop optimization.

**Requirements**:
- Design and implement all UI components for 320px+ mobile screens first
- Use progressive enhancement to add features for tablet (768px+) and desktop (1024px+)
- Maintain 44px minimum touch target size for all interactive elements
- Test responsive behavior at breakpoints: 320px, 768px, 1024px, 1440px
- Full feature parity across all devices - no mobile-degraded functionality

**Rationale**: Mobile users represent a significant portion of agile team workflows. Features that work on mobile screens inherently work on larger screens, but the reverse is not true.

**Validation**: Every feature specification must include mobile viewport designs and acceptance criteria for 320px+ screens.

### II. Performance Standards (NON-NEGOTIABLE)

All features MUST meet these measurable performance targets before merging to main.

**Mandatory Targets**:
- **Initial Page Load**: < 2 seconds (from navigation to interactive state)
- **Chart Rendering**: < 500ms (from data availability to visual completion)
- **User Interactions**: < 100ms response time (button clicks, form inputs, navigation)
- **Mobile Data Usage**: Minimize API payload size, implement efficient caching

**Rationale**: Performance directly impacts user satisfaction and adoption. Agile teams need rapid access to project metrics without waiting for slow interfaces.

**Validation**: Performance testing required before code review. Use browser DevTools Performance profiler and Lighthouse metrics. Failing to meet targets requires optimization work or feature re-scoping.

### III. Test-First Development (NON-NEGOTIABLE)

Test-Driven Development (TDD) is mandatory for all feature work using the Red-Green-Refactor cycle.

**Process**:
1. Write failing tests that specify desired behavior
2. Obtain user approval of test scenarios
3. Verify tests fail (RED)
4. Implement minimum code to pass tests (GREEN)
5. Refactor for quality and maintainability (REFACTOR)
6. No implementation code before corresponding tests exist

**Technology Requirements**:
- **Playwright-First**: All browser automation tests MUST use Playwright (NOT Selenium)
- **pytest Framework**: All unit and integration tests use pytest
- **Test Structure**: 
  - `tests/unit/` for isolated component tests
  - `tests/integration/` for end-to-end workflow tests
- **Coverage Requirement**: All acceptance criteria must have corresponding test cases

**Rationale**: TDD ensures code correctness, prevents regressions, and serves as living documentation. Playwright offers superior performance and reliability compared to Selenium for Dash applications.

**Validation**: Pull requests without tests for new features will be rejected. Test files must exist before implementation files in commit history.

### IV. Windows Development Environment (CRITICAL)

All development assumes Windows OS with PowerShell as the default shell.

**Mandatory Practices**:
- **PowerShell Commands Only**: Never use Unix commands (find, grep, ls, cat, sed, awk)
- **Virtual Environment Activation**: ALWAYS prefix Python commands with `.\.venv\Scripts\activate;`
- **Command Pattern**: `.\.venv\Scripts\activate; python [script.py]` or `.\.venv\Scripts\activate; pytest [test_file.py]`
- **Path Separators**: Use backslashes `\` for Windows file paths
- **Command Chaining**: Use semicolon `;` for sequential commands (not `&&` or `||`)

**PowerShell Equivalents**:
```powershell
# File operations
Get-ChildItem -Recurse -Filter "*.py"           # Instead of: find . -name "*.py"
Get-Content "file.txt" | Select-Object -First 10 # Instead of: head -10 file.txt
Select-String -Path "*.py" -Pattern "function"   # Instead of: grep "function" *.py

# Process and system
Get-Process | Where-Object { $_.ProcessName -like "*python*" }  # Instead of: ps aux | grep python
Get-Location                                     # Instead of: pwd
```

**Rationale**: Consistency across development environments prevents bugs from environment-specific tooling. Windows represents the primary development platform for this project.

**Validation**: All documentation, scripts, and instructions must use PowerShell syntax. Unix commands in specs or plans will be rejected during review.

### V. Local-First Architecture

Application runs entirely locally without cloud deployment or remote service dependencies.

**Requirements**:
- **Persistence**: JSON files only (app_settings.json, jira_query_profiles.json, jira_cache.json)
- **No Remote Services**: No database servers, authentication services, or cloud APIs (except JIRA integration)
- **File-Based Caching**: Simple timestamp-based cache validation using local JSON files
- **Portability**: Application must run on any Windows machine with Python 3.11+ and no additional infrastructure
- **No Build Step**: Direct Python execution via `python app.py` - no compilation, bundling, or transpilation

**Rationale**: Local-first ensures data privacy, eliminates deployment complexity, and provides instant startup. Users maintain full control of their data without vendor lock-in.

**Validation**: Feature specifications proposing remote services or databases will be rejected unless exceptional justification provided.

### VI. Technology Stack Constraints

Minimize dependencies to maintain simplicity and reduce maintenance burden.

**Approved Stack**:
- **Python**: 3.11+ (language version standard)
- **Dash**: Core UI framework (dash, dash-bootstrap-components)
- **Plotly**: Chart visualization library
- **Playwright**: Browser automation for testing
- **pytest**: Testing framework
- **JIRA API**: External integration for issue data (only approved remote service)

**Dependency Policy**:
- **No New Dependencies Without Justification**: Adding new packages requires written rationale in feature specification explaining:
  - Why existing stack cannot solve the problem
  - Maintenance status and community health of new dependency
  - License compatibility (must be permissive OSS)
  - Impact on application size and performance

**Rationale**: Every dependency adds maintenance burden, security risk, and potential compatibility issues. Existing stack provides comprehensive functionality for project requirements.

**Validation**: Pull requests adding dependencies without specification approval will be rejected.

### VII. Accessibility (NON-NEGOTIABLE)

WCAG 2.1 Level AA compliance required for all user-facing components.

**Mandatory Requirements**:
- **Keyboard Navigation**: All interactive elements accessible via keyboard (Tab, Enter, Space, Arrow keys)
- **Screen Readers**: Proper ARIA labels, semantic HTML elements, meaningful alt text for images
- **Color Contrast**: 
  - Minimum 4.5:1 ratio for normal text
  - Minimum 3:1 ratio for large text and UI components
- **Focus Management**: Visible focus indicators, logical tab order, focus trapping in modals
- **Testing**: Keyboard navigation tests for all new interactive features

**Rationale**: Accessibility is a legal requirement and ethical imperative. Many agile team members rely on assistive technologies. Accessible design benefits all users through improved usability.

**Validation**: Features without accessibility testing will be rejected. Use browser DevTools Accessibility Inspector and screen reader testing (NVDA or Windows Narrator) before code review.

## Development Standards

### Dash Best Practices

**Component Organization**:
- `ui/` - Reusable UI components (cards, buttons, layouts, modals)
- `callbacks/` - Dash callback functions for interactivity
- `visualization/` - Chart generation and data visualization logic
- `data/` - Data fetching, processing, and persistence
- `configuration/` - App settings, server config, help content

**State Management**:
- Use `dcc.Store` for client-side state caching (avoid server round-trips)
- Minimize callback chains - batch related updates
- Implement proper loading states for all async operations
- Use `prevent_initial_call=True` to avoid unnecessary initial renders

**Callback Pattern**:
```python
from dash import callback, Output, Input, State, no_update

@callback(
    [Output("result", "children"), Output("loading", "is_open")],
    Input("action", "n_clicks"),
    State("input", "value"),
    prevent_initial_call=True
)
def handle_action(n_clicks, input_value):
    if not input_value:
        return no_update, False
    # Process action
    return result, False  # Hide loading
```

**Bootstrap Components**:
- Prefer `dbc.*` components for consistent styling
- Use Bootstrap grid system (Container, Row, Col) with mobile-first breakpoints
- Follow InputGroup pattern for form field consistency
- Use Bootstrap color palette (primary, secondary, success, danger, warning, info)

### Code Quality Standards

**Simplicity First (YAGNI - You Aren't Gonna Need It)**:
- Start with simplest solution that solves the problem
- Avoid premature abstraction and speculative generalization
- Prefer duplication over wrong abstraction
- Refactor only when patterns emerge through actual use

**File Structure**:
- Follow existing directory organization patterns
- Keep related functionality in same module
- Maximum file size: ~500 lines (split if larger)
- Use descriptive, unambiguous file names

**Error Handling**:
- User-friendly error messages (explain what happened and how to fix)
- Proper Python logging (use logging module, not print statements)
- Graceful degradation - feature failure shouldn't crash entire app
- Validate user input before processing

**Documentation**:
- Docstrings for all public functions (Google style)
- Inline comments for complex logic (explain "why", not "what")
- Type hints for function signatures
- Update README.md for significant feature additions

**Type Hints**:
```python
from typing import Dict, List, Optional, Any

def process_jira_data(
    issues: List[Dict[str, Any]], 
    field_name: str = "customfield_10002"
) -> Optional[Dict[str, Any]]:
    """
    Process JIRA issue data and extract story points.
    
    Args:
        issues: List of JIRA issue dictionaries
        field_name: Custom field name for story points
        
    Returns:
        Processed data dictionary or None if processing fails
    """
    # Implementation
    pass
```

### Data Architecture

**JSON Schema Validation**:
- Use `data/schema.py` for data structure validation
- Define explicit schemas for all persisted data
- Validate data before saving to JSON files
- Provide clear error messages for schema violations

**JIRA Integration**:
- `data/jira_simple.py` - Direct JIRA API calls with error handling
- `data/jira_query_manager.py` - Query profile management (CRUD operations)
- `data/jira_scope_calculator.py` - Scope metrics calculation
- All JIRA functions must handle network errors and invalid responses

**Processing Pipeline**:
- `data/processing.py` - Data transformations and calculations
- `data/persistence.py` - File I/O operations (load/save JSON)
- Separate concerns: fetching → validation → transformation → persistence
- Use pure functions where possible (no side effects)

**Caching Strategy**:
- Simple file-based caching with timestamp validation (caching.py)
- Cache key: combination of JIRA URL + JQL query
- Default cache TTL: 1 hour (configurable in settings)
- Manual cache invalidation via "Clear Cache" button

## Quality Gates

### Pre-Implementation Gates (Phase -1)

Before writing ANY implementation code, validate these gates. Failing any gate requires revision of the feature specification or implementation plan.

#### Simplicity Gate
- [ ] **≤3 New Files**: Feature requires 3 or fewer new files/modules?
- [ ] **No Future-Proofing**: Not anticipating hypothetical future requirements?
- [ ] **Explainable**: Can explain entire implementation in < 5 sentences?
- [ ] **No Premature Abstraction**: Not creating abstractions without concrete use cases?

**Rejection Criteria**: Features requiring >3 new files or introducing speculative abstractions without clear immediate need.

#### Mobile-First Gate
- [ ] **320px+ Design**: All UI components designed for 320px+ viewports first?
- [ ] **Progressive Enhancement**: Documented how larger screens add features (not lose them)?
- [ ] **Touch Targets**: All interactive elements ≥ 44px?
- [ ] **Responsive Verification**: Design mockups exist for 320px, 768px, 1024px breakpoints?

**Rejection Criteria**: Desktop-first designs or features that degrade on mobile screens.

#### Performance Gate
- [ ] **Impact Analysis**: Performance impact analyzed for page load, rendering, interactions?
- [ ] **Caching Strategy**: Expensive operations use caching or lazy loading?
- [ ] **Non-Blocking**: No blocking operations in UI thread (use background callbacks)?
- [ ] **Lazy Loading**: Heavy components load on-demand, not on initial page load?

**Rejection Criteria**: Features with unanalyzed performance impact or known performance regressions without mitigation plan.

#### Testing Gate
- [ ] **Test Strategy**: Unit and integration test approach documented?
- [ ] **Playwright Approach**: Browser automation uses Playwright (with specific selectors and scenarios)?
- [ ] **Test Files Identified**: Exact test file paths listed in implementation plan?
- [ ] **Acceptance Criteria Testable**: Each acceptance criterion translates to executable test case?
- [ ] **Test Isolation**: Tests use temporary files/directories and clean up all created resources (no pollution of project root)?

**Rejection Criteria**: Features without clear test strategy or non-testable acceptance criteria.

#### Accessibility Gate
- [ ] **Keyboard Navigation**: Approach for keyboard-only usage documented?
- [ ] **ARIA Labels**: Plan for dynamic content announcements to screen readers?
- [ ] **Color Contrast**: Design mockups verified for 4.5:1 text contrast?
- [ ] **Screen Reader Compatibility**: Semantic HTML and ARIA roles planned?

**Rejection Criteria**: Features without accessibility considerations or plans for WCAG 2.1 AA compliance.

### Implementation Gates (During Development)

These gates MUST pass before submitting code for review. Failing any gate requires additional work before review.

#### Test Coverage Gate
- [ ] **All Criteria Tested**: Every acceptance criterion has corresponding test case?
- [ ] **Unit Tests Pass**: `.\.venv\Scripts\activate; pytest tests/unit/ -v` passes?
- [ ] **Integration Tests Pass**: `.\.venv\Scripts\activate; pytest tests/integration/ -v` passes?
- [ ] **No Skipped Tests**: All tests enabled unless documented exception approved?
- [ ] **Test Isolation Verified**: Tests can run in any order and in isolation without failing (no shared state, proper cleanup)?

**Rejection Criteria**: Pull requests with failing tests, skipped tests without approval, missing test coverage for acceptance criteria, or tests that pollute the project workspace.

#### Code Quality Gate
- [ ] **No Lint Errors**: `.\.venv\Scripts\activate; pylint [changed_files]` passes?
- [ ] **Type Hints Present**: All public functions have type hints?
- [ ] **Docstrings Present**: All public functions have Google-style docstrings?
- [ ] **No Hardcoded Values**: Configuration uses settings files (app_settings.json)?

**Rejection Criteria**: Linting errors, missing documentation, hardcoded configuration values.

#### Runtime Performance Validation
- [ ] **Page Load Verified**: Initial page load measured < 2s (Chrome DevTools Performance)?
- [ ] **Chart Rendering Verified**: Chart render time measured < 500ms?
- [ ] **No Console Errors**: Browser console shows no errors or warnings?
- [ ] **Mobile Performance**: Tested on throttled connection (Fast 3G in DevTools)?

**Rejection Criteria**: Performance regressions without documented justification and optimization plan.

#### Accessibility Validation
- [ ] **Keyboard Navigation Tested**: All features usable with keyboard only (Tab, Enter, Space)?
- [ ] **Screen Reader Tested**: Content readable with NVDA or Windows Narrator?
- [ ] **Color Contrast Verified**: DevTools Accessibility Inspector shows no contrast violations?
- [ ] **ARIA Labels Present**: Dynamic content and interactions have proper ARIA attributes?

**Rejection Criteria**: Accessibility failures without documented remediation plan.

## Governance

### Constitutional Authority

This constitution supersedes all other development practices, guidelines, and documentation.

**Binding Requirements**:
- Every line of code, specification, plan, and task MUST comply with constitutional principles
- Phase -1 and implementation gates are mandatory checkpoints
- No exceptions without written justification documented in feature specification
- All feature specifications must reference relevant constitutional principles

**Hierarchy**:
1. **Constitution** (this document) - Immutable principles and quality gates
2. **Feature Specifications** (`specs/*/spec.md`) - WHAT to build and WHY
3. **Implementation Plans** (`specs/*/plan.md`) - HOW to build (must comply with constitution)
4. **Runtime Guidance** (`.github/copilot-instructions.md`) - Detailed patterns and examples

### Amendment Process

Constitution may be amended through documented, justified process with version control.

**Process**:
1. **Proposal**: Create amendment document in `memory/amendments/YYYY-MM-DD-amendment-name.md`
2. **Rationale**: Document why existing principle is insufficient or incorrect
3. **Impact Analysis**: Assess impact on existing features, pending work, and technical debt
4. **Migration Plan**: Define how existing code will be updated to comply with amendment
5. **Ratification**: Update `constitution.md` with amendment, increment version, update dates
6. **Communication**: Update all related documentation (SPECKIT_GUIDE.md, README.md, copilot-instructions.md)

**Version Increment Rules** (Semantic Versioning):
- **MAJOR** (X.0.0): Backward-incompatible changes - principle removal, redefinition of gates, fundamental policy shift
- **MINOR** (x.Y.0): New principles added, expanded guidance, new quality gates
- **PATCH** (x.y.Z): Clarifications, wording improvements, typo fixes, non-semantic refinements

**Amendment Example**:
```markdown
# Amendment 2025-10-20: Cloud Deployment Support

## Rationale
User demand for cloud-hosted version requires relaxing Local-First Architecture (Principle V).

## Proposed Change
Principle V: Add exception allowing optional cloud deployment via Azure App Service while maintaining local-run capability.

## Impact
- Affects: Principle V (Local-First Architecture)
- Version: 1.0.0 → 2.0.0 (MAJOR - backward incompatible principle change)
- Migration: No code changes required - local operation remains default
```

### Compliance Verification

All feature implementations must verify constitutional compliance at multiple checkpoints.

**Pre-Implementation Checkpoint**:
- Phase -1 gates in `plan.md` must be checked and passed before writing implementation code
- Gate failures require plan revision and re-approval
- No coding begins until all Phase -1 gates pass

**Implementation Checkpoint**:
- Implementation gates in `tasks.md` must be verified before requesting code review
- Gate failures require additional work - pull request will be rejected
- Automated CI checks can enforce some gates (linting, test coverage)

**Code Review Checkpoint**:
- Reviewer must verify constitutional compliance as part of review checklist
- Constitutional violations block merge even if code technically works
- Complexity or gate violations require documented exception with rationale

**Exception Documentation Template**:
```markdown
## Constitutional Exception: [Gate Name]

**Principle Violated**: [Principle Number and Name]
**Gate Failed**: [Specific gate requirement]
**Rationale**: [Why compliance is not feasible or appropriate]
**Mitigation**: [How risk is reduced despite violation]
**Approval**: [Reviewer name and date]
```

### Complexity Justification

Any feature that fails the Simplicity Gate (>3 new files, premature abstraction) requires explicit justification.

**Required Documentation**:
- Why simpler approaches were rejected
- Concrete use cases requiring complexity
- Alternative approaches considered
- Long-term maintenance plan

**Tracking**: Document complexity decisions in feature specification under "Design Decisions" section.

### Runtime Development Guidance

For day-to-day development decisions not explicitly covered by constitutional principles:

**Reference Hierarchy**:
1. **Primary**: `.github/copilot-instructions.md` - Detailed patterns, examples, code snippets
2. **Secondary**: Existing codebase patterns - Follow established conventions
3. **Tertiary**: Official Dash, Plotly, Playwright documentation for framework-specific questions

**When Guidance Conflicts**:
- Constitution overrides all other guidance
- Runtime guidance provides implementation details within constitutional constraints
- Existing code patterns should be followed unless they violate constitution

---

**Version**: 1.0.1  
**Ratified**: 2025-10-15  
**Last Amended**: 2025-10-15 (Test Isolation Clarification - PATCH)  
**Approver**: Project Owner  
**Next Review**: 2026-01-15 (Quarterly review cycle)

## Amendment History

### Version 1.0.1 (2025-10-15) - PATCH

**Change**: Added test isolation requirements to quality gates

**Details**:
- Added test isolation checkpoint to Testing Gate (Phase -1)
- Added test isolation verification to Test Coverage Gate (Implementation)
- Documented mandatory use of `tempfile` for test file operations
- Added requirement that tests must run in any order without failures

**Rationale**: Prevent test pollution of project workspace and ensure tests can run independently. Tests creating files in project root directory cause false failures when run in parallel or in different orders.

**Impact**: No code changes required - existing tests already follow these patterns using `tempfile.TemporaryDirectory()` and `tempfile.NamedTemporaryFile()` fixtures.
