"""
Unit tests for JQL Syntax Highlighter component.

Tests cover:
- T009: Component structure and properties
- T010: Token rendering (keywords, strings, operators, functions, errors)
- T011: Edge cases
- T012: Accessibility requirements
"""

from dash import html

from ui.components import parse_jql_syntax, render_syntax_tokens
from ui.jql_syntax_highlighter import (
    SCRIPTRUNNER_FUNCTIONS,
    create_jql_syntax_highlighter,
    detect_syntax_errors,
    is_scriptrunner_function,
)

#######################################################################
# TEST: T009 - Component Structure
#######################################################################


class TestComponentStructure:
    """Test JQL syntax highlighter component structure (Task T009)."""

    def test_create_basic_component(self):
        """Test basic component creation with default parameters."""
        component = create_jql_syntax_highlighter(
            component_id="test-jql", value="project = TEST"
        )

        # Should return a wrapper div
        assert isinstance(component, html.Div)
        props = component.to_plotly_json()["props"]
        assert props["id"] == "test-jql-wrapper"
        assert "jql-syntax-wrapper" in props["className"]

    def test_component_contains_two_children(self):
        """Test component has highlight div and textarea."""
        component = create_jql_syntax_highlighter(
            component_id="test-jql", value="project = TEST"
        )

        # Access children directly from component object
        children = component.children
        assert children is not None, "Component should have children"
        assert len(children) == 2

        # First child is highlight div
        highlight_div = children[0]
        highlight_json = highlight_div.to_plotly_json()
        assert highlight_json["type"] == "Div"
        assert highlight_json["props"]["id"] == "test-jql-highlight"

        # Second child is textarea
        textarea = children[1]
        textarea_json = textarea.to_plotly_json()
        assert textarea_json["type"] == "Textarea"
        assert textarea_json["props"]["id"] == "test-jql"
        assert textarea_json["props"]["children"] == "project = TEST"

    def test_component_with_custom_properties(self):
        """Test component accepts custom properties."""
        component = create_jql_syntax_highlighter(
            component_id="custom-jql",
            value="status = Done",
            placeholder="Enter query",
            rows=10,
            disabled=True,
            aria_label="Custom Input",
        )

        assert component.children is not None
        textarea = component.children[1]
        textarea_props = textarea.to_plotly_json()["props"]

        assert textarea_props["placeholder"] == "Enter query"
        assert textarea_props["rows"] == 10
        assert textarea_props["disabled"] is True
        assert textarea_props["title"] == "Custom Input"

    def test_component_clamps_rows(self):
        """Test rows parameter is clamped to 1-20 range."""
        # Minimum
        component_min = create_jql_syntax_highlighter("test1", rows=0)
        assert component_min.children is not None
        textarea_min = component_min.children[1]
        assert textarea_min.to_plotly_json()["props"]["rows"] == 1

        # Maximum
        component_max = create_jql_syntax_highlighter("test2", rows=50)
        assert component_max.children is not None
        textarea_max = component_max.children[1]
        assert textarea_max.to_plotly_json()["props"]["rows"] == 20

    def test_component_truncates_long_queries(self):
        """Test queries exceeding 5000 chars are truncated."""
        long_query = "x" * 6000
        component = create_jql_syntax_highlighter("test", value=long_query)

        assert component.children is not None
        textarea = component.children[1]
        textarea_children = textarea.to_plotly_json()["props"]["children"]
        assert len(textarea_children) == 5000


#######################################################################
# TEST: T010 - Token Rendering
#######################################################################


class TestTokenRendering:
    """Test JQL token parsing and rendering."""

    def test_parse_jql_keywords(self):
        """Test JQL keywords are detected."""
        tokens = parse_jql_syntax("project = TEST AND status IN (Done)")
        keyword_tokens = [t for t in tokens if t["type"] == "keyword"]
        keyword_texts = [t["text"] for t in keyword_tokens]

        assert "AND" in keyword_texts
        assert "IN" in keyword_texts

    def test_parse_jql_strings(self):
        """Test quoted strings are detected."""
        tokens = parse_jql_syntax('status = "In Progress"')
        string_tokens = [t for t in tokens if t["type"] == "string"]
        assert len(string_tokens) == 1
        assert '"In Progress"' in [t["text"] for t in string_tokens]

    def test_parse_jql_operators(self):
        """Test operators are detected."""
        tokens = parse_jql_syntax("priority != High")
        operator_tokens = [t for t in tokens if t["type"] == "operator"]
        assert "!=" in [t["text"] for t in operator_tokens]

    def test_parse_scriptrunner_functions(self):
        """Test ScriptRunner functions are detected."""
        tokens = parse_jql_syntax("issue IN linkedIssuesOf('TEST-1')")
        function_tokens = [t for t in tokens if t["type"] == "function"]
        assert "linkedIssuesOf" in [t["text"] for t in function_tokens]

    def test_render_tokens_to_html(self):
        """Test tokens are rendered to HTML with CSS classes."""
        tokens = [
            {"text": "AND", "type": "keyword", "start": 0, "end": 3},
            {"text": "=", "type": "operator", "start": 4, "end": 5},
        ]

        rendered = render_syntax_tokens(tokens)
        assert len(rendered) == 2

        # Check keyword has CSS class
        keyword_json = rendered[0].to_plotly_json()
        assert keyword_json["type"] == "Mark"
        assert "jql-keyword" in keyword_json["props"]["className"]

    def test_render_function_tokens(self):
        """Test ScriptRunner function tokens render with purple styling."""
        tokens = [{"text": "linkedIssuesOf", "type": "function", "start": 0, "end": 14}]
        rendered = render_syntax_tokens(tokens)

        function_json = rendered[0].to_plotly_json()
        assert "jql-function" in function_json["props"]["className"]

    def test_render_error_tokens(self):
        """Test error tokens render with error styling."""
        tokens = [
            {
                "text": '"unclosed',
                "type": "error",
                "error_type": "unclosed_string",
                "start": 0,
                "end": 9,
            }
        ]

        rendered = render_syntax_tokens(tokens)
        error_json = rendered[0].to_plotly_json()
        assert "jql-error-unclosed" in error_json["props"]["className"]


#######################################################################
# TEST: T011 - Edge Cases
#######################################################################


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_query(self):
        """Test empty query returns empty token list."""
        assert parse_jql_syntax("") == []
        assert parse_jql_syntax(None) == []

    def test_whitespace_only_query(self):
        """Test whitespace-only query."""
        tokens = parse_jql_syntax("   \n\t   ")
        assert len(tokens) > 0

    def test_unclosed_string_detection(self):
        """Test detect_syntax_errors() finds unclosed strings."""
        tokens = [{"text": '"unclosed', "type": "string", "start": 0, "end": 9}]
        errors = detect_syntax_errors(tokens)

        assert len(errors) == 1
        assert errors[0]["error_type"] == "unclosed_string"

    def test_no_errors_in_valid_query(self):
        """Test detect_syntax_errors() returns empty list for valid query."""
        tokens = [{"text": '"Done"', "type": "string", "start": 0, "end": 6}]
        errors = detect_syntax_errors(tokens)
        assert len(errors) == 0

    def test_very_long_query_performance(self):
        """Test performance with 5000 char query."""
        long_query = "project = TEST AND " * 250

        import time

        start_time = time.time()
        tokens = parse_jql_syntax(long_query[:5000])
        elapsed_ms = (time.time() - start_time) * 1000

        # Should complete in < 50ms per FR-010
        assert elapsed_ms < 50
        assert len(tokens) > 0


#######################################################################
# TEST: T012 - Accessibility
#######################################################################


class TestAccessibility:
    """Test accessibility requirements."""

    def test_component_has_aria_label(self):
        """Test textarea has accessibility label."""
        component = create_jql_syntax_highlighter(
            component_id="test-jql", aria_label="JQL Query Input"
        )

        assert component.children is not None
        textarea = component.children[1]
        textarea_props = textarea.to_plotly_json()["props"]
        assert textarea_props["title"] == "JQL Query Input"

    def test_highlight_div_not_editable(self):
        """Test highlight div is contentEditable=false."""
        component = create_jql_syntax_highlighter("test")

        assert component.children is not None
        highlight_div = component.children[0]
        highlight_props = highlight_div.to_plotly_json()["props"]
        assert highlight_props["contentEditable"] == "false"

    def test_component_supports_disabled_state(self):
        """Test component respects disabled state."""
        component = create_jql_syntax_highlighter("test", disabled=True)

        assert component.children is not None
        textarea = component.children[1]
        textarea_props = textarea.to_plotly_json()["props"]
        assert textarea_props["disabled"] is True


#######################################################################
# TEST: ScriptRunner Helper Functions
#######################################################################


class TestScriptRunnerHelpers:
    """Test ScriptRunner helper functions."""

    def test_scriptrunner_functions_constant(self):
        """Test SCRIPTRUNNER_FUNCTIONS contains 15 core functions."""
        assert len(SCRIPTRUNNER_FUNCTIONS) == 15
        assert "linkedIssuesOf" in SCRIPTRUNNER_FUNCTIONS
        assert "issuesInEpics" in SCRIPTRUNNER_FUNCTIONS

    def test_is_scriptrunner_function_valid(self):
        """Test is_scriptrunner_function() returns True for valid functions."""
        assert is_scriptrunner_function("linkedIssuesOf") is True
        assert is_scriptrunner_function("hasAttachments") is True

    def test_is_scriptrunner_function_invalid(self):
        """Test is_scriptrunner_function() returns False for invalid input."""
        assert is_scriptrunner_function("invalidFunction") is False
        assert is_scriptrunner_function("") is False

    def test_is_scriptrunner_function_case_sensitive(self):
        """Test is_scriptrunner_function() is case-sensitive."""
        assert is_scriptrunner_function("linkedIssuesOf") is True
        assert is_scriptrunner_function("LINKEDISSUESOF") is False
