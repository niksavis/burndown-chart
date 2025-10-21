<!--
Sync Impact Report:
Version: 1.2.0 (Pragmatic Development Gates)
Modified Principles: Multiple quality gates relaxed to reduce AI agent overhead
Added Sections: Flexible validation approach for gates, "good enough" thresholds
Removed Sections: Overly strict gate requirements that block development without clear benefit
Templates Requiring Updates:
  - ✅ plan-template.md: Gates already flexible
  - ✅ spec-template.md: Already allows pragmatic approaches
  - ✅ tasks-template.md: Gate validation flexible
  - ✅ copilot-instructions.md: Reflects pragmatic development
Follow-up TODOs: None - pragmatic gates documented
-->

# Burndown Chart Constitution

**Project**: Burndown Chart - Agile Project Forecasting Tool  
**Type**: Locally-run Python Dash Web Application  
**Purpose**: Mobile-first burndown chart visualization with JIRA integration

## Core Principles

### I. Mobile-First Design (IMPORTANT)

Features should work well on mobile devices (320px+), but perfection is not required before desktop work.

**Requirements**:
- Consider mobile screens (320px+) during design and implementation
- Use responsive design patterns (Bootstrap grid, media queries)
- Aim for 44px minimum touch target size for interactive elements
- Test on mobile during or after implementation - doesn't need to be perfect upfront
- Full feature parity preferred, but acceptable degradation if documented

**Rationale**: Mobile users are important. Mobile-friendly design improves usability for everyone. However, requiring flawless mobile implementation before any desktop work creates unnecessary delays.

**Validation**: Feature should be usable on mobile screens. Desktop-only features require explicit justification.

### II. Performance Standards (ASPIRATIONAL TARGETS)

Features should feel responsive, but exact millisecond targets are guidelines, not gates.

**Performance Goals**:
- **Initial Page Load**: Should feel fast (aim for < 2 seconds)
- **Chart Rendering**: Should feel instant (aim for < 500ms)
- **User Interactions**: Should respond immediately (aim for < 100ms)
- **Mobile Data Usage**: Be mindful of payload size, use caching where sensible

**Rationale**: Performance matters, but obsessing over exact milliseconds wastes time. Focus on making features feel responsive during normal usage. Performance optimization can happen iteratively if issues arise.

**Validation**: Manual testing during development. If it feels slow, investigate. Formal performance profiling happens when there's a real problem, not as routine gatekeeping.

### III. Test-First Development (FLEXIBLE APPROACH)

Testing is mandatory but follows a pragmatic approach that balances quality with development velocity.

**Testing Strategy**:
1. **Unit Tests**: Required during implementation for isolated components and business logic
   - Write unit tests before or alongside implementation code
   - Test pure functions, data transformations, calculations
   - Use pytest with proper test isolation (tempfile, cleanup)
   
2. **Integration Tests**: Required as final validation before merge, optional during implementation
   - Playwright-based browser automation tests verify end-to-end workflows
   - Can be written after implementation is complete
   - Should run as final checkpoint before code review/merge
   - Focus on user-visible behavior and acceptance criteria

**Technology Requirements**:
- **Playwright-First**: All browser automation tests MUST use Playwright (NOT Selenium)
- **pytest Framework**: All unit and integration tests use pytest
- **Test Structure**: 
  - `tests/unit/` for isolated component tests (required during implementation)
  - `tests/integration/` for end-to-end workflow tests (required before merge)
- **Coverage Requirement**: All acceptance criteria must have corresponding test cases (unit or integration)

**Rationale**: Unit tests provide rapid feedback during development. Integration tests with Playwright can be time-consuming to set up and may block progress if required too early. Running integration tests as a final validation step ensures quality without slowing development.

**Validation**: Pull requests must have passing unit tests for new logic and integration tests for user-facing features. Integration tests may be written after implementation but must pass before merge approval.

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

### VII. Accessibility (IMPORTANT)

Features should be accessible, with WCAG 2.1 Level AA as the goal, not a blocking gate.

**Accessibility Guidelines**:
- **Keyboard Navigation**: Interactive elements should work with keyboard (Tab, Enter, Space)
- **Screen Readers**: Use semantic HTML, add labels to form fields
- **Color Contrast**: Aim for readable contrast (4.5:1 for text)
- **Focus Management**: Visible focus indicators on interactive elements
- **Testing**: Quick keyboard navigation test during development

**Rationale**: Accessibility is important and beneficial. However, requiring perfect WCAG compliance before merge creates delays. Aim for good accessibility, fix issues when found, improve iteratively.

**Validation**: Features should pass basic keyboard navigation tests. Use DevTools Accessibility Inspector to catch obvious issues. Comprehensive accessibility audits can happen periodically, not per-feature.

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
- All Markdown files must comply with [markdownlint rules](https://github.com/DavidAnson/markdownlint/tree/main/doc)

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

#### Simplicity Gate (GUIDANCE, NOT BLOCKING)
- [ ] **Reasonable Scope**: Feature scope is proportional to value delivered?
- [ ] **No Future-Proofing**: Not anticipating hypothetical future requirements?
- [ ] **Explainable**: Can explain the general approach in a paragraph?
- [ ] **No Premature Abstraction**: Not creating abstractions without concrete use cases?

**Guidance**: Prefer simple solutions. If a feature genuinely requires >3 new files due to logical separation of concerns, that's acceptable. Focus on avoiding unnecessary complexity, not counting files.

**Rejection Criteria**: Features with unjustified complexity or speculative abstractions without clear immediate need.

#### Mobile-First Gate (VALIDATE DURING IMPLEMENTATION)
- [ ] **Mobile Consideration**: Feature approach considers mobile screens (320px+)?
- [ ] **Progressive Enhancement**: Plan won't break mobile functionality?
- [ ] **Touch Targets**: Interactive elements will be appropriately sized (≥ 44px)?

**Validation Timing**: Design mockups and multi-breakpoint testing can be done during/after implementation. The goal is mobile-friendly results, not upfront bureaucracy.

**Rejection Criteria**: Desktop-only designs that explicitly exclude or break mobile usage.

#### Performance Gate (AWARENESS, NOT DETAILED ANALYSIS)
- [ ] **Performance Awareness**: Considered whether feature might impact performance?
- [ ] **Obvious Optimizations**: Heavy operations will use caching or lazy loading if clearly needed?
- [ ] **Non-Blocking**: Long-running operations won't freeze the UI?

**Validation Timing**: Detailed performance analysis and measurement happens after implementation, not before. Focus on avoiding obvious performance mistakes.

**Rejection Criteria**: Features with known severe performance issues (e.g., loading 10MB on page load) without mitigation.

#### Testing Gate (PRAGMATIC APPROACH)
- [ ] **Testing Approach**: General idea of how feature will be tested (unit, integration, or manual)?
- [ ] **Acceptance Criteria Testable**: Feature requirements are verifiable (not vague)?
- [ ] **Test Isolation Awareness**: Know that tests should clean up after themselves?

**Validation Timing**: Detailed test plans, specific selectors, and comprehensive test scenarios can be developed during implementation. The goal is testable features, not upfront test design documents.

**Rejection Criteria**: Features with no idea how they'll be validated or fundamentally untestable requirements.

**Note**: Integration tests with Playwright may be written after implementation. Unit tests for complex business logic are recommended during implementation but not strictly required upfront.

#### Accessibility Gate (AWARENESS, NOT DETAILED PLANNING)
- [ ] **Accessibility Awareness**: Considered that feature should be accessible (keyboard, screen readers)?
- [ ] **Semantic HTML**: Will use appropriate HTML elements (buttons, links, headings)?

**Validation Timing**: Specific ARIA labels, color contrast verification, and detailed accessibility testing happen during/after implementation. Use browser DevTools to catch issues.

**Rejection Criteria**: Features that fundamentally break accessibility (e.g., mouse-only interactions, text-in-images without alt text).

### Implementation Gates (During Development)

These gates MUST pass before submitting code for review. Failing any gate requires additional work before review.

#### Test Coverage Gate
- [ ] **All Criteria Tested**: Every acceptance criterion has corresponding test case (unit or integration)?
- [ ] **Unit Tests Pass**: `.\.venv\Scripts\activate; pytest tests/unit/ -v` passes?
- [ ] **Integration Tests Pass**: `.\.venv\Scripts\activate; pytest tests/integration/ -v` passes (execute as final validation)?
- [ ] **No Skipped Tests**: All tests enabled unless documented exception approved?
- [ ] **Test Isolation Verified**: Tests can run in any order and in isolation without failing (no shared state, proper cleanup)?

**Rejection Criteria**: Pull requests with failing tests, skipped tests without approval, missing test coverage for acceptance criteria, or tests that pollute the project workspace.

**Flexible Execution**: Integration tests may be written and executed after implementation is complete, as the final checkpoint before merge approval. This prevents Playwright setup complexity from blocking development progress. However, all tests must pass before code review approval.

#### Code Quality Gate (REASONABLE STANDARDS)
- [ ] **No Critical Lint Errors**: Major linting issues resolved (unused imports, obvious bugs)?
- [ ] **Key Functions Documented**: Complex or public-facing functions have docstrings?
- [ ] **Type Hints for Complex Code**: Type hints added where they improve code clarity?
- [ ] **No Hardcoded Secrets**: Sensitive values (tokens, passwords) not in code?
- [ ] **Markdown Readable**: Markdown files are well-formatted (markdownlint optional)?

**Pragmatic Approach**: Focus on code quality that matters. Pedantic linting rules (line length, import order) can be relaxed. Type hints are helpful but not mandatory for every function. Documentation where it adds value.

**Rejection Criteria**: Code with serious bugs, security issues, or completely undocumented complex logic.

#### Runtime Performance Validation (SUBJECTIVE TESTING)
- [ ] **Performance Feels Reasonable**: Feature doesn't feel sluggish or broken during manual testing?
- [ ] **No Console Errors**: Browser console shows no critical errors?

**Pragmatic Approach**: Exact millisecond measurements (< 2s, < 500ms) are aspirational targets, not blocking gates. If the feature feels responsive during manual testing, that's sufficient. Performance optimization can happen iteratively.

**Validation Timing**: Detailed performance profiling with DevTools happens if there's a noticeable problem, not as a routine gate.

**Rejection Criteria**: Features with obvious performance issues that make the app unusable (e.g., 30-second load times, frozen UI).

#### Accessibility Validation (BASIC COMPLIANCE)
- [ ] **Keyboard Navigation Works**: Feature can be used with keyboard (Tab, Enter)?
- [ ] **No Obvious Accessibility Issues**: Quick check with DevTools Accessibility Inspector shows no critical violations?

**Pragmatic Approach**: Comprehensive screen reader testing and detailed ARIA attribute verification are aspirational goals, not blocking gates. Focus on avoiding obvious accessibility mistakes (keyboard traps, invisible focus, missing labels on form fields).

**Validation Timing**: Detailed accessibility audit happens if accessibility issues are reported or for high-impact features. Basic accessibility is validated during manual testing.

**Rejection Criteria**: Features that fundamentally break keyboard navigation or screen reader compatibility.

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

**Version**: 1.2.0  
**Ratified**: 2025-10-15  
**Last Amended**: 2025-10-21 (Pragmatic Development Gates - MINOR)  
**Approver**: Project Owner  
**Next Review**: 2026-01-15 (Quarterly review cycle)

## Amendment History

### Version 1.2.0 (2025-10-21) - MINOR

**Change**: Relaxed multiple quality gates to reduce AI agent overhead and improve development velocity

**Details**:
- **Simplicity Gate**: Removed arbitrary "≤3 new files" rule, changed to guidance about reasonable scope
- **Mobile-First Gate**: Changed from "NON-NEGOTIABLE" to "IMPORTANT", allows validation during/after implementation
- **Performance Gate**: Changed from requiring detailed analysis upfront to awareness of potential issues
- **Performance Standards**: Changed from "NON-NEGOTIABLE" exact millisecond targets to "ASPIRATIONAL TARGETS"
- **Testing Gate**: Reduced from detailed upfront test planning to general testing approach
- **Accessibility Gate**: Changed from requiring detailed upfront planning to basic awareness
- **Accessibility Principle**: Changed from "NON-NEGOTIABLE" WCAG compliance to "IMPORTANT" goal with pragmatic approach
- **Code Quality Gate**: Relaxed from strict pylint/type hints/docstrings for all functions to reasonable standards
- **Runtime Performance Validation**: Changed from precise measurements to subjective testing ("feels reasonable")
- **Accessibility Validation**: Reduced from comprehensive testing to basic keyboard navigation checks

**Rationale**: Many constitutional gates were creating excessive overhead for AI agents, requiring multiple iterations to satisfy pedantic requirements that didn't provide proportional value. The overly strict gates forced AI agents to spend significant token budgets on:
- Detailed upfront design documents for every gate
- Precise measurements and analysis before implementation
- Comprehensive test plans before writing any code
- Perfect accessibility and performance before merge

This amendment shifts focus from bureaucratic gatekeeping to pragmatic development:
- **Upfront gates** are now awareness checks, not detailed plans
- **Implementation gates** focus on working code, not perfect code
- **Validation** happens during/after implementation when it makes sense
- **Quality targets** are aspirational goals, not blocking requirements

**Impact**: 
- Significantly reduces AI agent request overhead (estimated 30-50% reduction in planning phase requests)
- Allows faster iteration and implementation without sacrificing meaningful quality
- Maintains important principles (testing, accessibility, performance) while removing bureaucracy
- Shifts from "perfect before merge" to "good enough, improve iteratively"
- Enables developers to focus on delivering value rather than satisfying checkboxes

**Migration**: Immediately applicable to all new features. Existing features with strict compliance remain valid but not required.

### Version 1.1.0 (2025-10-21) - MINOR

**Change**: Relaxed integration testing requirements to improve development velocity

**Details**:
- Modified Principle III (Test-First Development) from "NON-NEGOTIABLE" strict TDD to "FLEXIBLE APPROACH"
- Integration tests (Playwright) now optional during implementation, required before merge
- Unit tests still required during implementation for business logic
- Updated Testing Gate (Phase -1) to clarify integration tests can be executed at end
- Updated Test Coverage Gate to allow integration tests as final validation step
- Added guidance that Playwright setup complexity should not block development

**Rationale**: Strict TDD with Playwright integration tests during implementation causes excessive friction and slows development. Playwright tests are valuable for final validation but their setup complexity (server management, browser automation, timing issues) creates bottlenecks during active development. Unit tests provide sufficient guidance during implementation, while integration tests verify end-to-end behavior before merge.

**Impact**: 
- Allows developers to complete implementation without being blocked by Playwright test setup
- Integration tests remain mandatory but can be written after implementation
- All tests must still pass before code review approval
- No reduction in test coverage - only timing flexibility

**Migration**: No code changes required - existing projects can continue current testing practices or adopt more flexible approach for new features.

### Version 1.0.1 (2025-10-15) - PATCH

**Change**: Added test isolation requirements to quality gates

**Details**:
- Added test isolation checkpoint to Testing Gate (Phase -1)
- Added test isolation verification to Test Coverage Gate (Implementation)
- Documented mandatory use of `tempfile` for test file operations
- Added requirement that tests must run in any order without failures

**Rationale**: Prevent test pollution of project workspace and ensure tests can run independently. Tests creating files in project root directory cause false failures when run in parallel or in different orders.

**Impact**: No code changes required - existing tests already follow these patterns using `tempfile.TemporaryDirectory()` and `tempfile.NamedTemporaryFile()` fixtures.
