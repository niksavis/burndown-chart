"""
Unit tests for data/error_handling.py

All logic is pure (string matching, dataclass construction, aggregation).
No network, no database, no I/O needed.
"""

from data.error_handling import (
    ContextualError,
    ErrorCategory,
    ErrorSeverity,
    analyze_error_with_context,
    format_error_for_ui,
    get_error_recovery_workflow,
    get_error_summary_for_dashboard,
    should_show_error_in_setup_step,
)

###############################################################################
# Helpers
###############################################################################


def _status(jira_connected: bool = False, fields_mapped: bool = False) -> dict:
    return {
        "jira_connected": jira_connected,
        "fields_mapped": fields_mapped,
        "current_step": "jira_connection",
    }


def _err(msg: str = "test error") -> Exception:
    return RuntimeError(msg)


###############################################################################
# ContextualError
###############################################################################


class TestContextualError:
    def test_minimal_construction(self) -> None:
        err = ContextualError(
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            title="Test",
            description="Desc",
        )
        assert err.category == ErrorCategory.NETWORK
        assert err.severity == ErrorSeverity.HIGH
        assert err.title == "Test"
        assert err.description == "Desc"
        assert err.remediation == []
        assert err.related_docs == []
        assert err.setup_step is None
        assert err.technical_details is None

    def test_full_construction(self) -> None:
        err = ContextualError(
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.MEDIUM,
            title="Config Error",
            description="Bad config",
            setup_step="jira_connection",
            remediation=["Fix this", "Fix that"],
            technical_details="raw error",
            related_docs=[{"title": "Guide", "url": "#guide"}],
        )
        assert err.setup_step == "jira_connection"
        assert len(err.remediation) == 2
        assert err.technical_details == "raw error"
        assert len(err.related_docs) == 1

    def test_to_dict_contains_all_keys(self) -> None:
        err = ContextualError(
            category=ErrorCategory.DATA,
            severity=ErrorSeverity.LOW,
            title="T",
            description="D",
        )
        d = err.to_dict()
        assert "category" in d
        assert "severity" in d
        assert "title" in d
        assert "description" in d
        assert "setup_step" in d
        assert "remediation" in d
        assert "technical_details" in d
        assert "related_docs" in d

    def test_to_dict_serializes_enum_values(self) -> None:
        err = ContextualError(
            category=ErrorCategory.PERMISSIONS,
            severity=ErrorSeverity.CRITICAL,
            title="T",
            description="D",
        )
        d = err.to_dict()
        assert d["category"] == "permissions"
        assert d["severity"] == "critical"

    def test_to_dict_remediation_is_list(self) -> None:
        err = ContextualError(
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            title="T",
            description="D",
            remediation=["Step 1", "Step 2"],
        )
        d = err.to_dict()
        assert d["remediation"] == ["Step 1", "Step 2"]


###############################################################################
# ErrorCategory / ErrorSeverity enums
###############################################################################


class TestErrorEnums:
    def test_error_category_values(self) -> None:
        assert ErrorCategory.CONFIGURATION.value == "configuration"
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.DATA.value == "data"
        assert ErrorCategory.PERMISSIONS.value == "permissions"
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.DEPENDENCY.value == "dependency"

    def test_error_severity_values(self) -> None:
        assert ErrorSeverity.CRITICAL.value == "critical"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.LOW.value == "low"


###############################################################################
# analyze_error_with_context
###############################################################################


class TestAnalyzeErrorWithContext:
    def test_network_error_when_not_connected(self) -> None:
        err = _err("connection timeout")
        result = analyze_error_with_context(err, _status(jira_connected=False), "fetch")
        assert result.category == ErrorCategory.NETWORK
        assert result.severity == ErrorSeverity.HIGH

    def test_network_error_when_connected(self) -> None:
        err = _err("connection timeout")
        result = analyze_error_with_context(err, _status(jira_connected=True), "fetch")
        assert result.category == ErrorCategory.NETWORK
        assert result.severity == ErrorSeverity.MEDIUM

    def test_auth_error_401(self) -> None:
        err = _err("unauthorized 401")
        result = analyze_error_with_context(err, _status(), "fetch")
        assert result.category == ErrorCategory.PERMISSIONS

    def test_auth_error_forbidden(self) -> None:
        err = _err("403 forbidden")
        result = analyze_error_with_context(err, _status(), "fetch")
        assert result.category == ErrorCategory.PERMISSIONS

    def test_auth_error_token(self) -> None:
        err = _err("invalid token")
        result = analyze_error_with_context(err, _status(), "fetch")
        assert result.category == ErrorCategory.PERMISSIONS

    def test_jira_config_error_field(self) -> None:
        err = _err("customfield_10001 not found")
        result = analyze_error_with_context(err, _status(), "fetch")
        allowed = (ErrorCategory.CONFIGURATION, ErrorCategory.VALIDATION)
        assert result.category in allowed
        err = _err("jql parse error")
        result = analyze_error_with_context(err, _status(), "fetch")
        allowed = (ErrorCategory.CONFIGURATION, ErrorCategory.VALIDATION)
        assert result.category in allowed

    def test_validation_error(self) -> None:
        # Error must NOT contain jira/field/customfield/jql to avoid JIRA config path
        err = _err("required parameter is invalid or missing")
        result = analyze_error_with_context(err, _status(), "save")
        assert result.category == ErrorCategory.VALIDATION

    def test_dependency_error(self) -> None:
        err = _err("dependencies not met for this step")
        result = analyze_error_with_context(err, _status(), "setup")
        assert result.category == ErrorCategory.DEPENDENCY

    def test_generic_error_fallback(self) -> None:
        err = _err("some completely unknown error abcxyz12345")
        result = analyze_error_with_context(err, _status(), "unknown_op")
        assert isinstance(result, ContextualError)
        assert result.category == ErrorCategory.DATA

    def test_result_has_technical_details(self) -> None:
        err = _err("connection timeout")
        result = analyze_error_with_context(err, _status(), "fetch")
        assert result.technical_details == str(err)

    def test_result_has_non_empty_remediation(self) -> None:
        err = _err("connection timeout")
        result = analyze_error_with_context(err, _status(), "fetch")
        assert len(result.remediation) > 0


###############################################################################
# get_error_recovery_workflow
###############################################################################


class TestGetErrorRecoveryWorkflow:
    def test_network_connection_setup_step(self) -> None:
        err = ContextualError(
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            title="T",
            description="D",
            setup_step="jira_connection",
        )
        steps = get_error_recovery_workflow(err)
        assert len(steps) >= 1
        assert all("step" in s and "title" in s and "action" in s for s in steps)

    def test_permissions_error_workflow(self) -> None:
        err = ContextualError(
            category=ErrorCategory.PERMISSIONS,
            severity=ErrorSeverity.HIGH,
            title="T",
            description="D",
        )
        steps = get_error_recovery_workflow(err)
        assert len(steps) >= 1

    def test_generic_error_fallback_workflow(self) -> None:
        err = ContextualError(
            category=ErrorCategory.DATA,
            severity=ErrorSeverity.MEDIUM,
            title="T",
            description="D",
        )
        steps = get_error_recovery_workflow(err)
        assert len(steps) >= 1

    def test_each_step_has_success_indicator(self) -> None:
        err = ContextualError(
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            title="T",
            description="D",
            setup_step="jira_connection",
        )
        steps = get_error_recovery_workflow(err)
        assert all("success_indicator" in s for s in steps)


###############################################################################
# format_error_for_ui
###############################################################################


class TestFormatErrorForUi:
    def _make_err(
        self, severity: ErrorSeverity = ErrorSeverity.HIGH
    ) -> ContextualError:
        return ContextualError(
            category=ErrorCategory.NETWORK,
            severity=severity,
            title="Network error",
            description="Cannot connect",
            remediation=["Check URL"],
            technical_details="raw traceback",
        )

    def test_contains_required_keys(self) -> None:
        result = format_error_for_ui(self._make_err())
        for key in ("alert_type", "icon", "title", "description", "remediation"):
            assert key in result

    def test_technical_excluded_by_default(self) -> None:
        result = format_error_for_ui(self._make_err())
        assert "technical_details" not in result

    def test_technical_included_when_flag_set(self) -> None:
        result = format_error_for_ui(self._make_err(), include_technical=True)
        assert "technical_details" in result
        assert result["technical_details"] == "raw traceback"

    def test_critical_maps_to_danger(self) -> None:
        result = format_error_for_ui(self._make_err(ErrorSeverity.CRITICAL))
        assert result["alert_type"] == "danger"

    def test_high_maps_to_warning(self) -> None:
        result = format_error_for_ui(self._make_err(ErrorSeverity.HIGH))
        assert result["alert_type"] == "warning"

    def test_medium_maps_to_info(self) -> None:
        result = format_error_for_ui(self._make_err(ErrorSeverity.MEDIUM))
        assert result["alert_type"] == "info"

    def test_severity_value_is_string(self) -> None:
        result = format_error_for_ui(self._make_err())
        assert isinstance(result["severity"], str)


###############################################################################
# should_show_error_in_setup_step
###############################################################################


class TestShouldShowErrorInSetupStep:
    def _err_for_step(
        self,
        step: str | None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    ) -> ContextualError:
        return ContextualError(
            category=ErrorCategory.NETWORK,
            severity=severity,
            title="T",
            description="D",
            setup_step=step,
        )

    def test_critical_always_shown(self) -> None:
        err = self._err_for_step("other_step", ErrorSeverity.CRITICAL)
        assert should_show_error_in_setup_step(err, "jira_connection") is True

    def test_matching_step_shown(self) -> None:
        err = self._err_for_step("jira_connection")
        assert should_show_error_in_setup_step(err, "jira_connection") is True

    def test_high_severity_shown_even_if_different_step(self) -> None:
        err = self._err_for_step("other_step", ErrorSeverity.HIGH)
        assert should_show_error_in_setup_step(err, "jira_connection") is True

    def test_low_priority_different_step_not_shown(self) -> None:
        err = self._err_for_step("some_other_step", ErrorSeverity.LOW)
        assert should_show_error_in_setup_step(err, "jira_connection") is False

    def test_medium_different_step_not_shown(self) -> None:
        err = self._err_for_step("some_other_step", ErrorSeverity.MEDIUM)
        assert should_show_error_in_setup_step(err, "jira_connection") is False


###############################################################################
# get_error_summary_for_dashboard
###############################################################################


class TestGetErrorSummaryForDashboard:
    def _make(self, severity: ErrorSeverity) -> ContextualError:
        return ContextualError(
            category=ErrorCategory.DATA,
            severity=severity,
            title="T",
            description="D",
        )

    def test_empty_list_is_healthy(self) -> None:
        result = get_error_summary_for_dashboard([])
        assert result["status"] == "healthy"
        assert result["total"] == 0

    def test_critical_error_status(self) -> None:
        result = get_error_summary_for_dashboard([self._make(ErrorSeverity.CRITICAL)])
        assert result["status"] == "critical"

    def test_high_error_status_without_critical(self) -> None:
        result = get_error_summary_for_dashboard([self._make(ErrorSeverity.HIGH)])
        assert result["status"] == "warning"

    def test_medium_only_is_info(self) -> None:
        result = get_error_summary_for_dashboard([self._make(ErrorSeverity.MEDIUM)])
        assert result["status"] == "info"

    def test_total_count_correct(self) -> None:
        errors = [
            self._make(ErrorSeverity.HIGH),
            self._make(ErrorSeverity.MEDIUM),
            self._make(ErrorSeverity.LOW),
        ]
        result = get_error_summary_for_dashboard(errors)
        assert result["total"] == 3

    def test_critical_takes_precedence_over_high(self) -> None:
        errors = [
            self._make(ErrorSeverity.HIGH),
            self._make(ErrorSeverity.CRITICAL),
        ]
        result = get_error_summary_for_dashboard(errors)
        assert result["status"] == "critical"
