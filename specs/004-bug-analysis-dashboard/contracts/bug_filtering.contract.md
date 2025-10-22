# Contract: Bug Filtering

**Feature**: Bug Analysis Dashboard  
**Module**: `data/bug_processing.py`  
**Phase**: 1 - Design & Architecture

## Function Signature

```python
def filter_bug_issues(
    issues: List[Dict],
    bug_type_mappings: Dict[str, str]
) -> List[BugIssue]:
    """
    Filter JIRA issues to only include bugs based on issue type mapping.
    
    Args:
        issues: Raw JIRA issues from API
        bug_type_mappings: Mapping of JIRA type names to "bug" category
                          Example: {"Bug": "bug", "Defect": "bug"}
    
    Returns:
        List of bug issues with mapped types
        
    Raises:
        ValueError: If issues list is empty or None
        KeyError: If issue missing required fields
    """
```

## Contract Specification

### Preconditions

- `issues` must be a non-empty list
- Each issue must have `fields` dictionary
- Each issue must have `fields.issuetype.name`
- `bug_type_mappings` must be a non-empty dictionary

### Postconditions

- Returns list of only bug-typed issues
- Each returned issue has `type` field set to mapped value
- Each returned issue has `original_type` field with JIRA type name
- Order preserved from input
- No issues with non-bug types included

### Input Validation

```python
# Validate issues structure
assert isinstance(issues, list), "issues must be a list"
assert len(issues) > 0, "issues cannot be empty"

for issue in issues:
    assert "fields" in issue, f"Issue {issue.get('key')} missing 'fields'"
    assert "issuetype" in issue["fields"], f"Issue {issue.get('key')} missing 'issuetype'"
    assert "name" in issue["fields"]["issuetype"], f"Issue {issue.get('key')} missing issuetype.name"

# Validate mappings
assert isinstance(bug_type_mappings, dict), "bug_type_mappings must be a dict"
assert len(bug_type_mappings) > 0, "bug_type_mappings cannot be empty"
```

### Output Guarantees

```python
# Verify output structure
assert isinstance(result, list), "Result must be a list"
assert all(isinstance(item, dict) for item in result), "All items must be dicts"

for bug in result:
    assert "key" in bug, "Bug missing 'key'"
    assert "type" in bug, "Bug missing 'type'"
    assert "original_type" in bug, "Bug missing 'original_type'"
    assert bug["type"] == "bug", f"Bug {bug['key']} has invalid type: {bug['type']}"
    assert bug["original_type"] in bug_type_mappings, f"Original type {bug['original_type']} not in mappings"
```

### Example Usage

```python
# Setup
jira_issues = [
    {
        "key": "PROJ-1",
        "fields": {
            "issuetype": {"name": "Bug"},
            "created": "2025-01-01T10:00:00Z",
            "status": {"name": "Open"}
        }
    },
    {
        "key": "PROJ-2",
        "fields": {
            "issuetype": {"name": "Story"},
            "created": "2025-01-02T10:00:00Z",
            "status": {"name": "Done"}
        }
    },
    {
        "key": "PROJ-3",
        "fields": {
            "issuetype": {"name": "Defect"},
            "created": "2025-01-03T10:00:00Z",
            "status": {"name": "In Progress"}
        }
    }
]

mappings = {
    "Bug": "bug",
    "Defect": "bug",
    "Incident": "bug"
}

# Execute
bug_issues = filter_bug_issues(jira_issues, mappings)

# Expected result: 2 bugs (PROJ-1 and PROJ-3)
assert len(bug_issues) == 2
assert bug_issues[0]["key"] == "PROJ-1"
assert bug_issues[0]["type"] == "bug"
assert bug_issues[0]["original_type"] == "Bug"
assert bug_issues[1]["key"] == "PROJ-3"
assert bug_issues[1]["type"] == "bug"
assert bug_issues[1]["original_type"] == "Defect"
```

### Edge Cases

| Case           | Input                       | Expected Output      | Handling                   |
| -------------- | --------------------------- | -------------------- | -------------------------- |
| No bugs        | All issues are type "Story" | Empty list           | Return `[]`                |
| All bugs       | All issues match mappings   | All issues returned  | Return full filtered list  |
| Unknown type   | Issue type not in mappings  | Excluded from result | Skip silently              |
| Missing type   | Issue missing `issuetype`   | Raise KeyError       | Fail fast with clear error |
| Case sensitive | "bug" vs "Bug" in JIRA      | Exact match required | No case normalization      |
| Empty mappings | `{}` passed                 | Raise ValueError     | Fail fast                  |

### Performance Requirements

- **Time Complexity**: O(n) where n = number of issues
- **Space Complexity**: O(m) where m = number of bug issues
- **Benchmark**: Process 1000 issues in < 50ms

### Error Messages

```python
# Error message templates
ERROR_EMPTY_ISSUES = "Cannot filter bugs from empty issue list"
ERROR_MISSING_FIELDS = "Issue {key} missing required 'fields' dictionary"
ERROR_MISSING_ISSUETYPE = "Issue {key} missing 'fields.issuetype.name'"
ERROR_EMPTY_MAPPINGS = "Bug type mappings cannot be empty"
```

### Testing Requirements

- ✅ Unit test with mixed issue types
- ✅ Unit test with all bugs
- ✅ Unit test with no bugs
- ✅ Unit test with empty input (should raise)
- ✅ Unit test with missing issuetype (should raise)
- ✅ Unit test with custom type mappings
- ✅ Integration test with real JIRA data structure

---

## Contract Verification

This contract will be verified by:

1. **Type Checking**: MyPy static analysis
2. **Unit Tests**: pytest with 100% coverage of edge cases
3. **Property Testing**: Hypothesis for random input validation
4. **Integration Tests**: End-to-end workflow with mock JIRA data

**Contract Status**: ✅ **APPROVED** - Ready for implementation
