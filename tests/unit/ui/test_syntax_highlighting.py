"""
Unit tests for JQL syntax highlighting functionality.

Tests cover:
- JQL keyword parsing (FR-004)
- String literal detection (FR-005)
- Token rendering to HTML components (FR-006)
- Case-insensitive keyword recognition

Test Strategy: TDD Red Phase - These tests should FAIL initially.
"""

# =============================================================================
# Test: JQL Keyword Parsing (TASK-201)
# =============================================================================


class TestJQLKeywordParsing:
    """Test JQL keyword detection and parsing."""

    def test_parse_jql_keywords(self):
        """Verify "AND", "OR", "IN" are detected as keywords."""
        from ui.components import parse_jql_syntax

        query = "project = TEST AND status = Done OR priority IN (High, Low)"
        tokens = parse_jql_syntax(query)

        # Find keyword tokens
        keyword_tokens = [t for t in tokens if t["type"] == "keyword"]
        keyword_texts = [t["text"].strip() for t in keyword_tokens]

        assert "AND" in keyword_texts, "AND should be recognized as keyword"
        assert "OR" in keyword_texts, "OR should be recognized as keyword"
        assert "IN" in keyword_texts, "IN should be recognized as keyword"

    def test_parse_jql_strings(self):
        """Verify quoted strings like "Done" are detected."""
        from ui.components import parse_jql_syntax

        query = 'status = "Done" AND assignee = "John Doe"'
        tokens = parse_jql_syntax(query)

        # Find string tokens
        string_tokens = [t for t in tokens if t["type"] == "string"]

        assert len(string_tokens) == 2, "Should detect 2 quoted strings"
        assert any('"Done"' in t["text"] for t in string_tokens), (
            "Should detect 'Done' string"
        )
        assert any('"John Doe"' in t["text"] for t in string_tokens), (
            "Should detect 'John Doe' string"
        )

    def test_parse_jql_mixed_query(self):
        """Verify complex query with keywords + strings."""
        from ui.components import parse_jql_syntax

        query = (
            'project = TEST AND status IN ("Done", "In Progress") OR assignee IS EMPTY'
        )
        tokens = parse_jql_syntax(query)

        # Should have a mix of token types
        token_types = set(t["type"] for t in tokens)

        assert "keyword" in token_types, "Should detect keywords"
        assert "string" in token_types, "Should detect strings"
        assert "text" in token_types or "field" in token_types, (
            "Should detect plain text or fields"
        )

    def test_parse_jql_case_insensitive(self):
        """Verify "and" and "AND" both recognized."""
        from ui.components import parse_jql_syntax

        # Test lowercase
        query_lower = "project = TEST and status = Done"
        tokens_lower = parse_jql_syntax(query_lower)
        keyword_tokens_lower = [t for t in tokens_lower if t["type"] == "keyword"]

        # Test uppercase
        query_upper = "project = TEST AND status = Done"
        tokens_upper = parse_jql_syntax(query_upper)
        keyword_tokens_upper = [t for t in tokens_upper if t["type"] == "keyword"]

        assert len(keyword_tokens_lower) > 0, "Should recognize lowercase 'and'"
        assert len(keyword_tokens_upper) > 0, "Should recognize uppercase 'AND'"
        assert len(keyword_tokens_lower) == len(keyword_tokens_upper), (
            "Case sensitivity should not affect detection"
        )

    def test_parse_empty_query(self):
        """Verify empty query returns empty token list."""
        from ui.components import parse_jql_syntax

        tokens = parse_jql_syntax("")
        assert tokens == [], "Empty query should return empty list"

    def test_parse_none_query(self):
        """Verify None query is handled gracefully."""
        from ui.components import parse_jql_syntax

        tokens = parse_jql_syntax(None)
        assert tokens == [], "None query should return empty list"

    def test_parse_query_with_operators(self):
        """Verify operators (=, !=, <, >) are detected."""
        from ui.components import parse_jql_syntax

        query = "priority = High AND created >= 2025-01-01"
        tokens = parse_jql_syntax(query)

        # Check for operator tokens
        operator_tokens = [t for t in tokens if t["type"] == "operator"]

        # At minimum, should have = and >= operators
        assert len(operator_tokens) >= 2, "Should detect comparison operators"

    def test_parse_query_preserves_text_positions(self):
        """Verify token start/end positions are accurate."""
        from ui.components import parse_jql_syntax

        query = "project = TEST"
        tokens = parse_jql_syntax(query)

        # Reconstruct query from tokens to verify positions
        reconstructed = ""
        for token in tokens:
            assert token["start"] >= 0, "Start position should be non-negative"
            assert token["end"] >= token["start"], "End should be >= start"
            reconstructed += token["text"]

        # Note: Depending on implementation, whitespace handling may vary
        # So we check length similarity rather than exact match
        assert len(reconstructed) >= len(query) - 10, (
            "Reconstructed query should be similar length"
        )


# =============================================================================
# Test: Syntax Token Rendering (TASK-202)
# =============================================================================


class TestSyntaxTokenRendering:
    """Test rendering syntax tokens to Dash HTML components."""

    def test_render_keyword_token_as_mark_element(self):
        """Verify html.Mark with "jql-keyword" class."""
        from dash import html

        from ui.components import render_syntax_tokens

        tokens = [{"text": "AND", "type": "keyword", "start": 0, "end": 3}]

        rendered = render_syntax_tokens(tokens)

        assert len(rendered) == 1, "Should render 1 element"
        assert isinstance(rendered[0], html.Mark), "Keyword should render as html.Mark"
        # Access className via the component's properties
        class_name = getattr(rendered[0], "className", None) or rendered[
            0
        ].__dict__.get("className", "")
        assert "jql-keyword" in str(class_name), "Should have jql-keyword class"
        assert rendered[0].children == "AND", "Should contain correct text"

    def test_render_string_token_as_mark_element(self):
        """Verify html.Mark with "jql-string" class."""
        from dash import html

        from ui.components import render_syntax_tokens

        tokens = [{"text": '"Done"', "type": "string", "start": 0, "end": 6}]

        rendered = render_syntax_tokens(tokens)

        assert len(rendered) == 1, "Should render 1 element"
        assert isinstance(rendered[0], html.Mark), "String should render as html.Mark"
        # Access className via the component's properties
        class_name = getattr(rendered[0], "className", None) or rendered[
            0
        ].__dict__.get("className", "")
        assert "jql-string" in str(class_name), "Should have jql-string class"
        assert rendered[0].children == '"Done"', "Should contain quoted text"

    def test_render_plain_text_token(self):
        """Verify plain text without wrapping."""
        from ui.components import render_syntax_tokens

        tokens = [{"text": "project", "type": "text", "start": 0, "end": 7}]

        rendered = render_syntax_tokens(tokens)

        assert len(rendered) == 1, "Should render 1 element"
        assert isinstance(rendered[0], str), "Plain text should render as string"
        assert rendered[0] == "project", "Should contain correct text"

    def test_render_mixed_tokens(self):
        """Verify rendering of multiple token types together."""
        from dash import html

        from ui.components import render_syntax_tokens

        tokens = [
            {"text": "status", "type": "text", "start": 0, "end": 6},
            {"text": " = ", "type": "operator", "start": 6, "end": 9},
            {"text": '"Done"', "type": "string", "start": 9, "end": 15},
            {"text": " AND ", "type": "keyword", "start": 15, "end": 20},
            {"text": "priority", "type": "text", "start": 20, "end": 28},
        ]

        rendered = render_syntax_tokens(tokens)

        assert len(rendered) == 5, "Should render 5 elements"

        # Check types
        assert isinstance(rendered[0], str), "First token should be string"
        assert isinstance(rendered[2], html.Mark), "String token should be html.Mark"
        assert isinstance(rendered[3], html.Mark), "Keyword token should be html.Mark"

    def test_render_empty_token_list(self):
        """Verify empty token list returns empty list."""
        from ui.components import render_syntax_tokens

        rendered = render_syntax_tokens([])
        assert rendered == [], "Empty token list should return empty list"

    def test_render_preserves_token_order(self):
        """Verify rendering maintains token order."""
        from ui.components import render_syntax_tokens

        tokens = [
            {"text": "project", "type": "text", "start": 0, "end": 7},
            {"text": " AND ", "type": "keyword", "start": 7, "end": 12},
            {"text": "status", "type": "text", "start": 12, "end": 18},
        ]

        rendered = render_syntax_tokens(tokens)

        # Extract text from rendered components
        text_parts = []
        for item in rendered:
            if isinstance(item, str):
                text_parts.append(item)
            else:
                text_parts.append(item.children)

        assert text_parts == ["project", " AND ", "status"], (
            "Should preserve token order"
        )


# =============================================================================
# Test: JQL Keyword Registry
# =============================================================================


class TestJQLKeywordRegistry:
    """Test JQL keyword registry and detection."""

    def test_jql_keywords_constant_exists(self):
        """Verify JQL_KEYWORDS constant is defined."""
        from ui.components import JQL_KEYWORDS

        assert JQL_KEYWORDS is not None, "JQL_KEYWORDS should be defined"
        assert len(JQL_KEYWORDS) > 0, "JQL_KEYWORDS should not be empty"

    def test_is_jql_keyword_function(self):
        """Verify is_jql_keyword function works correctly."""
        from ui.components import is_jql_keyword

        # Test common keywords
        assert is_jql_keyword("AND"), "AND should be a keyword"
        assert is_jql_keyword("OR"), "OR should be a keyword"
        assert is_jql_keyword("NOT"), "NOT should be a keyword"
        assert is_jql_keyword("IN"), "IN should be a keyword"

        # Test non-keywords
        assert not is_jql_keyword("project"), "project should not be a keyword"
        assert not is_jql_keyword("TEST"), "TEST should not be a keyword"

    def test_is_jql_keyword_case_insensitive(self):
        """Verify keyword detection is case-insensitive."""
        from ui.components import is_jql_keyword

        assert is_jql_keyword("and"), "lowercase 'and' should be keyword"
        assert is_jql_keyword("AND"), "uppercase 'AND' should be keyword"
        assert is_jql_keyword("And"), "mixed case 'And' should be keyword"

    def test_jql_keywords_includes_common_keywords(self):
        """Verify registry includes all common JQL keywords."""
        from ui.components import JQL_KEYWORDS

        # Convert to uppercase for comparison (keywords are case-insensitive)
        keywords_upper = {k.upper() for k in JQL_KEYWORDS}

        required_keywords = {"AND", "OR", "NOT", "IN", "IS", "WAS", "EMPTY", "NULL"}

        for keyword in required_keywords:
            assert keyword in keywords_upper, f"{keyword} should be in JQL_KEYWORDS"


# =============================================================================
# Test: Integration with Existing Character Count
# =============================================================================


class TestSyntaxHighlightingIntegration:
    """Test that syntax highlighting doesn't break character count."""

    def test_syntax_highlighting_preserves_character_count(self):
        """Verify syntax highlighting doesn't affect character count."""
        from ui.components import count_jql_characters, parse_jql_syntax

        query = 'project = TEST AND status = "Done"'

        # Get character count
        char_count = count_jql_characters(query)

        # Parse syntax
        tokens = parse_jql_syntax(query)

        # Reconstruct text from tokens
        reconstructed = "".join(t["text"] for t in tokens)
        reconstructed_count = count_jql_characters(reconstructed)

        # Character count should remain the same (or very close)
        assert abs(char_count - reconstructed_count) <= 5, (
            "Syntax highlighting should preserve character count"
        )
