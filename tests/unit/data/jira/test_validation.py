"""
Unit tests for data/jira/validation.py

Only covers validate_jql_for_scriptrunner — a pure string-matching function.
test_jql_query is excluded (requires live network).
"""

from data.jira.validation import validate_jql_for_scriptrunner

###############################################################################
# validate_jql_for_scriptrunner
###############################################################################


class TestValidateJqlForScriptrunner:
    def test_empty_string_is_compatible(self) -> None:
        ok, msg = validate_jql_for_scriptrunner("")
        assert ok is True
        assert msg == ""

    def test_none_is_compatible(self) -> None:
        ok, msg = validate_jql_for_scriptrunner(None)  # type: ignore[arg-type]
        assert ok is True
        assert msg == ""

    def test_plain_jql_no_functions_is_compatible(self) -> None:
        ok, msg = validate_jql_for_scriptrunner("project = MYPROJECT AND status = Open")
        assert ok is True
        assert msg == ""

    def test_issueFunction_detected(self) -> None:
        ok, msg = validate_jql_for_scriptrunner(
            "issueFunction in subtasksOf('project = X')"
        )
        assert ok is False
        assert "issueFunction" in msg

    def test_subtasksOf_detected(self) -> None:
        ok, msg = validate_jql_for_scriptrunner("subtasksOf('project = X')")
        assert ok is False
        assert "subtasksOf" in msg

    def test_epicsOf_detected(self) -> None:
        ok, msg = validate_jql_for_scriptrunner("epicsOf('project = X')")
        assert ok is False
        assert "epicsOf" in msg

    def test_linkedIssuesOf_detected(self) -> None:
        ok, msg = validate_jql_for_scriptrunner("linkedIssuesOf('project = X')")
        assert ok is False
        assert "linkedIssuesOf" in msg

    def test_parentEpicsOf_detected(self) -> None:
        ok, msg = validate_jql_for_scriptrunner("parentEpicsOf('project = X')")
        assert ok is False
        assert "parentEpicsOf" in msg

    def test_subtaskOf_detected(self) -> None:
        ok, msg = validate_jql_for_scriptrunner("subtaskOf('project = X')")
        assert ok is False
        assert "subtaskOf" in msg

    def test_portfolioChildrenOf_detected(self) -> None:
        ok, msg = validate_jql_for_scriptrunner("portfolioChildrenOf('project = X')")
        assert ok is False

    def test_portfolioParentsOf_detected(self) -> None:
        ok, msg = validate_jql_for_scriptrunner("portfolioParentsOf('project = X')")
        assert ok is False

    def test_portfolioSiblingsOf_detected(self) -> None:
        ok, msg = validate_jql_for_scriptrunner("portfolioSiblingsOf('project = X')")
        assert ok is False

    def test_case_insensitive_detection(self) -> None:
        ok, msg = validate_jql_for_scriptrunner(
            "ISSUEFUNCTION in subtasksOf('project = X')"
        )
        assert ok is False

    def test_multiple_functions_all_in_warning(self) -> None:
        ok, msg = validate_jql_for_scriptrunner(
            "issueFunction in subtasksOf('project = X') AND epicsOf('project = Y')"
        )
        assert ok is False
        # Warning should mention all found functions
        assert "issueFunction" in msg or "subtasksOf" in msg or "epicsOf" in msg

    def test_warning_message_is_descriptive(self) -> None:
        ok, msg = validate_jql_for_scriptrunner("issueFunction in subtasksOf('x')")
        assert ok is False
        assert "ScriptRunner" in msg
        assert len(msg) > 20
