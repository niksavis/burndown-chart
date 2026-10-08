import logging
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    CONFIGURATION = "configuration"
    NETWORK = "network"
    DATA = "data"
    PERMISSIONS = "permissions"
    VALIDATION = "validation"
    DEPENDENCY = "dependency"


class ErrorSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ContextualError:
    def __init__(
        self,
        category: ErrorCategory,
        severity: ErrorSeverity,
        title: str,
        description: str,
        setup_step: str | None = None,
        remediation: list[str] | None = None,
        technical_details: str | None = None,
        related_docs: list[dict[str, str]] | None = None,
    ):
        self.category = category
        self.severity = severity
        self.title = title
        self.description = description
        self.setup_step = setup_step
        self.remediation = remediation or []
        self.technical_details = technical_details
        self.related_docs = related_docs or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "setup_step": self.setup_step,
            "remediation": self.remediation,
            "technical_details": self.technical_details,
            "related_docs": self.related_docs,
        }


def analyze_error_with_context(
    error: Exception, setup_status: dict[str, Any], current_operation: str
) -> ContextualError:

    error_str = str(error).lower()

    if any(
        keyword in error_str
        for keyword in ["connection", "timeout", "unreachable", "dns"]
    ):
        return _handle_network_error(error, setup_status, current_operation)

    if any(
        keyword in error_str
        for keyword in ["unauthorized", "401", "403", "forbidden", "token"]
    ):
        return _handle_auth_error(error, setup_status, current_operation)

    if any(keyword in error_str for keyword in ["jira", "field", "customfield", "jql"]):
        return _handle_jira_config_error(error, setup_status, current_operation)

    if any(
        keyword in error_str
        for keyword in ["validation", "required", "missing", "invalid"]
    ):
        return _handle_validation_error(error, setup_status, current_operation)

    if "dependencies not met" in error_str:
        return _handle_dependency_error(error, setup_status, current_operation)

    return _handle_generic_error(error, setup_status, current_operation)


def _handle_network_error(
    error: Exception, setup_status: dict[str, Any], current_operation: str
) -> ContextualError:
    if not setup_status.get("jira_connected", False):
        return ContextualError(
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            title="Cannot Connect to JIRA",
            description="Network connection to your JIRA instance failed.",
            setup_step="jira_connection",
            remediation=[
                "Check that your JIRA URL is correct and accessible",
                "Verify your network connection",
                "Try accessing the JIRA URL in your browser",
                "Check if your organization uses VPN or proxy settings",
                "Ensure the JIRA instance is running and accessible",
            ],
            technical_details=str(error),
            related_docs=[
                {"title": "JIRA Connection Guide", "url": "#jira-setup"},
                {"title": "Network Troubleshooting", "url": "#network-help"},
            ],
        )
    else:
        return ContextualError(
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            title="Network Connection Lost",
            description="Connection to JIRA was lost during operation.",
            setup_step=None,
            remediation=[
                "Check your internet connection",
                "Retry the operation",
                "If issues persist, verify JIRA instance availability",
            ],
            technical_details=str(error),
        )


def _handle_auth_error(
    error: Exception, setup_status: dict[str, Any], current_operation: str
) -> ContextualError:
    if not setup_status.get("jira_connected", False):
        return ContextualError(
            category=ErrorCategory.PERMISSIONS,
            severity=ErrorSeverity.HIGH,
            title="JIRA Authentication Failed",
            description="Your JIRA credentials are invalid or expired.",
            setup_step="jira_connection",
            remediation=[
                "Verify your JIRA email address is correct",
                "Generate a new API token in Atlassian Account Settings",
                "Ensure the API token hasn't expired",
                "Check that your account has access to the JIRA instance",
                "For JIRA Server, verify username/password combination",
            ],
            technical_details=str(error),
            related_docs=[
                {
                    "title": "Generate API Token",
                    "url": "https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/",
                },
                {"title": "JIRA Authentication Guide", "url": "#auth-help"},
            ],
        )
    else:
        return ContextualError(
            category=ErrorCategory.PERMISSIONS,
            severity=ErrorSeverity.MEDIUM,
            title="JIRA Access Denied",
            description="Your credentials don't have permission for this operation.",
            remediation=[
                "Check that your JIRA account has appropriate permissions",
                "Verify project access permissions",
                "Contact JIRA administrator if needed",
            ],
            technical_details=str(error),
        )


def _handle_jira_config_error(
    error: Exception, setup_status: dict[str, Any], current_operation: str
) -> ContextualError:
    error_str = str(error).lower()

    if "field" in error_str or "customfield" in error_str:
        return ContextualError(
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.MEDIUM,
            title="JIRA Field Configuration Issue",
            description="There's an issue with JIRA field mapping configuration.",
            setup_step="field_mapping",
            remediation=[
                "Verify custom field IDs are correct (format: customfield_XXXXX)",
                "Check that fields exist in your JIRA instance",
                "Ensure you have permission to access these fields",
                "Try using built-in fields as alternatives where possible",
                "Field mapping is optional - you can skip this step for now",
            ],
            technical_details=str(error),
            related_docs=[
                {"title": "Field Mapping Guide", "url": "#field-mapping-help"},
                {"title": "Finding Custom Field IDs", "url": "#field-id-help"},
            ],
        )
    elif "jql" in error_str:
        return ContextualError(
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            title="JQL Query Error",
            description="There's an issue with your JQL query syntax.",
            setup_step="query_creation",
            remediation=[
                "Check JQL syntax in JIRA's issue search",
                "Verify field names and values exist in your project",
                "Use JIRA's autocomplete to build valid queries",
                "Start with a simple query like 'project = YOUR_PROJECT'",
                "Test the query in JIRA before using it here",
            ],
            technical_details=str(error),
            related_docs=[
                {
                    "title": "JQL Reference",
                    "url": "https://support.atlassian.com/jira-service-desk-cloud/docs/use-advanced-search-with-jira-query-language-jql/",
                },
                {"title": "Query Creation Guide", "url": "#query-help"},
            ],
        )

    return ContextualError(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.MEDIUM,
        title="JIRA Configuration Issue",
        description="There's a configuration issue with your JIRA setup.",
        remediation=[
            "Review your JIRA configuration settings",
            "Check the JIRA connection test results",
            "Verify all required fields are configured",
        ],
        technical_details=str(error),
    )


def _handle_validation_error(
    error: Exception, setup_status: dict[str, Any], current_operation: str
) -> ContextualError:
    return ContextualError(
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.MEDIUM,
        title="Input Validation Error",
        description="The provided input doesn't meet the required format.",
        remediation=[
            "Check that all required fields are filled",
            "Verify the input format matches expectations",
            "Remove any invalid characters",
            "Use the suggested formats and examples provided",
        ],
        technical_details=str(error),
    )


def _handle_dependency_error(
    error: Exception, setup_status: dict[str, Any], current_operation: str
) -> ContextualError:
    current_step = setup_status.get("current_step", "unknown")

    remediation = []
    if not setup_status.get("jira_connected", False):
        remediation.append("Configure JIRA connection first")
    if not setup_status.get("fields_mapped", False):
        remediation.append("Map JIRA fields (optional but recommended)")

    return ContextualError(
        category=ErrorCategory.DEPENDENCY,
        severity=ErrorSeverity.HIGH,
        title="Setup Dependencies Not Met",
        description="This operation requires completing previous setup steps.",
        setup_step=current_step,
        remediation=remediation
        + [
            "Follow the setup steps in order",
            "Complete each step before proceeding to the next",
            "Use the action buttons in the setup progress panel",
        ],
        technical_details=str(error),
        related_docs=[
            {"title": "Setup Guide", "url": "#setup-guide"},
        ],
    )


def _handle_generic_error(
    error: Exception, setup_status: dict[str, Any], current_operation: str
) -> ContextualError:
    return ContextualError(
        category=ErrorCategory.DATA,
        severity=ErrorSeverity.MEDIUM,
        title="Operation Failed",
        description=f"An error occurred during {current_operation}.",
        remediation=[
            "Try the operation again",
            "Check your network connection",
            "Verify your configuration settings",
            "Contact support if the issue persists",
        ],
        technical_details=str(error),
    )


def get_error_recovery_workflow(error: ContextualError) -> list[dict[str, str]]:

    if (
        error.category == ErrorCategory.NETWORK
        and error.setup_step == "jira_connection"
    ):
        return [
            {
                "step": "1",
                "title": "Test JIRA URL",
                "action": "Open your JIRA URL in a browser to verify it's accessible",
                "success_indicator": "JIRA login page loads successfully",
            },
            {
                "step": "2",
                "title": "Check Connection",
                "action": "Click 'Test Connection' button in JIRA configuration",
                "success_indicator": "Connection test shows green checkmark",
            },
            {
                "step": "3",
                "title": "Retry Operation",
                "action": "Try the failed operation again",
                "success_indicator": "Operation completes without error",
            },
        ]

    if error.category == ErrorCategory.PERMISSIONS:
        return [
            {
                "step": "1",
                "title": "Verify Credentials",
                "action": "Double-check email and API token in JIRA configuration",
                "success_indicator": "Credentials match your Atlassian account",
            },
            {
                "step": "2",
                "title": "Generate New Token",
                "action": "Create a fresh API token in Atlassian Account Settings",
                "success_indicator": "New token generated and copied",
            },
            {
                "step": "3",
                "title": "Update Configuration",
                "action": "Replace old token with new one in JIRA settings",
                "success_indicator": "Connection test passes with new token",
            },
        ]

    return [
        {
            "step": "1",
            "title": "Review Error Details",
            "action": "Check the technical details for specific error information",
            "success_indicator": "Error cause is understood",
        },
        {
            "step": "2",
            "title": "Follow Remediation",
            "action": "Complete the suggested remediation steps",
            "success_indicator": "All remediation steps completed",
        },
        {
            "step": "3",
            "title": "Retry Operation",
            "action": "Attempt the failed operation again",
            "success_indicator": "Operation succeeds without error",
        },
    ]


def format_error_for_ui(
    error: ContextualError, include_technical: bool = False
) -> dict[str, Any]:

    severity_colors = {
        ErrorSeverity.CRITICAL: "danger",
        ErrorSeverity.HIGH: "warning",
        ErrorSeverity.MEDIUM: "info",
        ErrorSeverity.LOW: "secondary",
    }

    severity_icons = {
        ErrorSeverity.CRITICAL: "fas fa-exclamation-triangle",
        ErrorSeverity.HIGH: "fas fa-exclamation-circle",
        ErrorSeverity.MEDIUM: "fas fa-info-circle",
        ErrorSeverity.LOW: "fas fa-lightbulb",
    }

    formatted = {
        "alert_type": severity_colors.get(error.severity, "info"),
        "icon": severity_icons.get(error.severity, "fas fa-info-circle"),
        "title": error.title,
        "description": error.description,
        "remediation": error.remediation,
        "setup_step": error.setup_step,
        "related_docs": error.related_docs,
        "category": error.category.value,
        "severity": error.severity.value,
    }

    if include_technical and error.technical_details:
        formatted["technical_details"] = error.technical_details

    return formatted


def should_show_error_in_setup_step(
    error: ContextualError, current_setup_step: str
) -> bool:

    if error.severity == ErrorSeverity.CRITICAL:
        return True

    if error.setup_step == current_setup_step:
        return True

    if error.severity == ErrorSeverity.HIGH:
        return True

    return False


def get_error_summary_for_dashboard(errors: list[ContextualError]) -> dict[str, Any]:

    if not errors:
        return {"status": "healthy", "total": 0}

    total = len(errors)
    critical = sum(1 for e in errors if e.severity == ErrorSeverity.CRITICAL)
    high = sum(1 for e in errors if e.severity == ErrorSeverity.HIGH)
    medium = sum(1 for e in errors if e.severity == ErrorSeverity.MEDIUM)
    low = sum(1 for e in errors if e.severity == ErrorSeverity.LOW)

    if critical > 0:
        status = "critical"
        message = f"{critical} critical issue(s) need attention"
    elif high > 0:
        status = "warning"
        message = f"{high} high priority issue(s) found"
    elif medium > 0:
        status = "info"
        message = f"{medium} issue(s) found"
    else:
        status = "healthy"
        message = "No significant issues"

    return {
        "total": total,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "status": status,
        "message": message,
    }
