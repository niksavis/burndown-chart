"""DORA & Flow Metrics Configuration Loader.

This module provides the master configuration loader for all DORA and Flow metrics settings.
It loads customer-specific configuration from app_settings.json including:
- Field mappings (JIRA custom fields → internal metric fields)
- Workflow status mappings (WIP, active, completion statuses)
- Project classifications (development vs operational)
- Effort category to flow type mappings

Reference: docs/metrics/IMPLEMENTATION_GUIDE.md
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class MetricsConfig:
    """Configuration manager for DORA & Flow metrics.

    Loads and validates customer-specific configuration from app_settings.json.
    Provides methods for accessing field mappings, status configurations, and
    project classifications.

    Example:
        >>> config = MetricsConfig()
        >>> wip_statuses = config.get_wip_included_statuses()
        >>> ['In Progress', 'In Review', 'Testing', 'In Deployment']
    """

    def __init__(self, config_file: str = "app_settings.json"):
        """Initialize configuration loader.

        Args:
            config_file: Path to app_settings.json configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from app_settings.json.

        Returns:
            Configuration dictionary with all settings

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        config_path = Path(self.config_file)

        if not config_path.exists():
            logger.warning(
                f"Configuration file {self.config_file} not found. "
                "Using default configuration. Create app_settings.json for "
                "customer-specific DORA/Flow metrics configuration."
            )
            return self._get_default_config()

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                logger.info(f"Loaded metrics configuration from {self.config_file}")
                return config
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {self.config_file}: {e}")
            raise

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration when app_settings.json doesn't exist.

        Returns:
            Dictionary with minimal default configuration
        """
        return {
            "dora_flow_config": {"field_mappings": {"dora": {}, "flow": {}}},
            "workflow_config": {
                "wip_statuses": ["In Progress"],
                "active_statuses": ["In Progress"],
                "completion_statuses": ["Done"],
            },
            "project_config": {"operational_projects": []},
            "flow_type_mappings": {
                "Feature": {"issue_types": ["Story", "Epic"], "effort_categories": []},
                "Defect": {"issue_types": ["Bug"], "effort_categories": []},
                "Technical_Debt": {"issue_types": ["Task"], "effort_categories": []},
                "Risk": {"issue_types": ["Spike"], "effort_categories": []},
            },
            "effort_category_mappings": {},  # Deprecated
        }

    # ========================================================================
    # Field Mappings
    # ========================================================================

    def get_dora_field_mappings(self) -> Dict[str, str]:
        """Get DORA metric field mappings.

        Returns:
            Dictionary mapping internal field names to JIRA field IDs
            Example: {"deployment_date": "customfield_10100", ...}
        """
        return (
            self.config.get("dora_flow_config", {})
            .get("field_mappings", {})
            .get("dora", {})
        )

    def get_flow_field_mappings(self) -> Dict[str, str]:
        """Get Flow metric field mappings.

        Returns:
            Dictionary mapping internal field names to JIRA field IDs
            Example: {"flow_item_type": "customfield_10200", ...}
        """
        return (
            self.config.get("dora_flow_config", {})
            .get("field_mappings", {})
            .get("flow", {})
        )

    def get_all_field_mappings(self) -> Dict[str, Dict[str, str]]:
        """Get all field mappings (DORA + Flow).

        Returns:
            Dictionary with 'dora' and 'flow' field mappings
        """
        return self.config.get("dora_flow_config", {}).get("field_mappings", {})

    def get_custom_field_id(
        self, field_name: str, metric_type: str = "dora"
    ) -> Optional[str]:
        """Get custom field ID for a specific field.

        Args:
            field_name: Internal field name (e.g., "deployment_date")
            metric_type: Either "dora" or "flow"

        Returns:
            JIRA field ID (e.g., "customfield_10100") or None if not configured
        """
        mappings = (
            self.get_dora_field_mappings()
            if metric_type == "dora"
            else self.get_flow_field_mappings()
        )
        return mappings.get(field_name)

    # ========================================================================
    # Workflow Status Mappings (Positive Inclusion)
    # ========================================================================

    def get_wip_included_statuses(self) -> List[str]:
        """Get list of statuses that indicate work-in-progress (WIP).

        CRITICAL: Uses positive inclusion strategy (not exclusion).
        Only issues in these statuses are considered WIP.

        Returns:
            List of WIP status names (case-sensitive)
            Example: ["In Progress", "In Review", "Testing", "In Deployment"]
        """
        return self.config.get("workflow_config", {}).get(
            "wip_statuses", ["In Progress", "In Review", "Testing"]
        )

    def get_active_statuses(self) -> List[str]:
        """Get list of statuses where work is actively being done.

        Used for Flow Efficiency calculation (active time vs waiting time).
        CRITICAL: Uses positive inclusion strategy.

        Returns:
            List of active status names (case-sensitive)
            Example: ["In Progress", "In Review", "Testing"]
        """
        return self.config.get("workflow_config", {}).get(
            "active_statuses", ["In Progress", "In Review", "Testing"]
        )

    def get_completion_statuses(self) -> List[str]:
        """Get list of statuses that indicate work is completed.

        Returns:
            List of completion status names (case-sensitive)
            Example: ["Done", "Resolved", "Closed"]
        """
        return self.config.get("workflow_config", {}).get(
            "completion_statuses", ["Done", "Resolved", "Closed"]
        )

    def is_status_in_list(
        self, status_name: str, status_list: List[str], case_sensitive: bool = False
    ) -> bool:
        """Check if status is in a given list with optional case-insensitive matching.

        Args:
            status_name: Status name to check
            status_list: List of status names to check against
            case_sensitive: Whether to use case-sensitive matching (default: False)

        Returns:
            True if status is in the list
        """
        if case_sensitive:
            return status_name in status_list
        else:
            status_lower = status_name.lower()
            return status_lower in [s.lower() for s in status_list]

    # ========================================================================
    # Project Configuration
    # ========================================================================

    def get_operational_projects(self) -> List[str]:
        """Get list of operational/DevOps project keys.

        Operational projects contain deployment tracking (Operational Tasks).
        All other projects are considered development projects.

        Returns:
            List of operational project keys
            Example: ["RI", "OPS", "DEVOPS"]
        """
        return self.config.get("project_config", {}).get("operational_projects", [])

    def get_development_projects(self) -> List[str]:
        """Get list of development project keys (if explicitly configured).

        Note: Development projects are typically inferred from JQL query,
        not explicitly configured. This is optional.

        Returns:
            List of development project keys or empty list if not configured
        """
        return self.config.get("project_config", {}).get("development_projects", [])

    def is_operational_project(self, project_key: str) -> bool:
        """Check if a project is an operational/DevOps project.

        Args:
            project_key: JIRA project key (e.g., "RI")

        Returns:
            True if project is operational, False otherwise
        """
        return project_key in self.get_operational_projects()

    # ========================================================================
    # Effort Category to Flow Type Mappings
    # ========================================================================

    def get_effort_category_mappings(self) -> Dict[str, str]:
        """Get effort category to flow type mappings.

        Maps JIRA effort category values to Flow Framework types.
        Used for two-tier flow type classification.

        Returns:
            Dictionary mapping effort categories to flow types
            Example: {"Technical debt": "Technical Debt", "Security": "Risk", ...}
        """
        return self.config.get(
            "effort_category_mappings",
            {
                "Technical debt": "Technical Debt",
                "Security": "Risk",
                "GDPR Compliance": "Risk",
                "Regulatory": "Risk",
                "Spikes (Analysis)": "Risk",
                # All others default to Feature
            },
        )

    def map_effort_category_to_flow_type(self, effort_category: Optional[str]) -> str:
        """Map effort category value to flow type.

        Args:
            effort_category: Effort category from JIRA (e.g., "Technical debt")

        Returns:
            Flow type: "Feature", "Defect", "Risk", or "Technical Debt"
        """
        if not effort_category or effort_category == "None":
            return "Feature"  # Default

        mappings = self.get_effort_category_mappings()
        return mappings.get(effort_category, "Feature")

    # ========================================================================
    # Issue Type Configuration
    # ========================================================================

    def get_wip_included_issue_types(self) -> List[str]:
        """Get list of issue types included in WIP calculation.

        Returns:
            List of issue type names
            Example: ["Task", "Story", "Bug"]
        """
        return self.config.get("workflow_config", {}).get(
            "wip_issue_types", ["Task", "Story", "Bug"]
        )

    # ========================================================================
    # Flow Type Mappings (AND-filter classification)
    # ========================================================================

    def get_flow_type_mappings(self) -> Dict[str, Dict[str, List[str]]]:
        """Get Flow type classification mappings (AND-filter system).

        Returns:
            Dictionary with Flow types as keys, each containing:
            - issue_types: List of JIRA issue types
            - effort_categories: List of effort category values (empty = no filter)

        Example:
            {
                "Feature": {
                    "issue_types": ["Story", "Epic"],
                    "effort_categories": ["New feature", "Improvement"]
                },
                "Defect": {
                    "issue_types": ["Bug"],
                    "effort_categories": []  # Empty = all Bugs are Defects
                }
            }
        """
        # Check for new flow_type_mappings structure
        if "flow_type_mappings" in self.config:
            return self.config["flow_type_mappings"]

        # Fallback to default mappings if not configured
        return {
            "Feature": {"issue_types": ["Story", "Epic"], "effort_categories": []},
            "Defect": {"issue_types": ["Bug"], "effort_categories": []},
            "Technical_Debt": {"issue_types": ["Task"], "effort_categories": []},
            "Risk": {"issue_types": ["Spike"], "effort_categories": []},
        }

    def classify_issue_to_flow_type(
        self, issue_type: str, effort_category: Optional[str] = None
    ) -> Optional[str]:
        """Classify an issue to a Flow type using AND-filter logic.

        Args:
            issue_type: JIRA issue type name (e.g., "Story", "Bug")
            effort_category: Effort category value (optional)

        Returns:
            Flow type ("Feature", "Defect", "Technical_Debt", "Risk") or None

        Logic:
            For each Flow type configuration:
            1. Check if issue_type is in configured issue_types
            2. If effort_categories is empty → match (no filter)
            3. If effort_categories is not empty → check if effort_category matches

        Example:
            >>> config.classify_issue_to_flow_type("Story", "New feature")
            "Feature"
            >>> config.classify_issue_to_flow_type("Story", "Bug Fix")
            None  # If "Bug Fix" not in Feature's effort_categories
            >>> config.classify_issue_to_flow_type("Bug", "Security")
            "Defect"  # If Defect has empty effort_categories
        """
        mappings = self.get_flow_type_mappings()

        for flow_type, config in mappings.items():
            issue_types = config.get("issue_types", [])
            effort_categories = config.get("effort_categories", [])

            # Check if issue type matches
            if issue_type not in issue_types:
                continue

            # If no effort category filter, issue qualifies
            if not effort_categories:
                return flow_type

            # If effort category filter exists, must match
            if effort_category and effort_category in effort_categories:
                return flow_type

        return None  # No match found

    # ========================================================================
    # Validation
    # ========================================================================

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate configuration completeness and return status.

        Returns:
            Dictionary with validation results:
            {
                "is_valid": bool,
                "errors": List[str],
                "warnings": List[str]
            }
        """
        errors = []
        warnings = []

        # Check for required sections
        if "dora_flow_config" not in self.config:
            errors.append("Missing 'dora_flow_config' section in app_settings.json")

        if "workflow_config" not in self.config:
            warnings.append("Missing 'workflow_config' section - using defaults")

        if "project_config" not in self.config:
            warnings.append(
                "Missing 'project_config' section - all projects treated as development"
            )

        # Check for field mappings
        dora_mappings = self.get_dora_field_mappings()
        flow_mappings = self.get_flow_field_mappings()

        if not dora_mappings and not flow_mappings:
            warnings.append(
                "No field mappings configured. Use Field Mapping modal to configure "
                "JIRA custom fields for DORA and Flow metrics."
            )

        # Check for operational projects
        operational_projects = self.get_operational_projects()
        if not operational_projects:
            warnings.append(
                "No operational projects configured. DORA metrics (Deployment Frequency, "
                "Lead Time) require operational project configuration."
            )

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def get_configuration_summary(self) -> str:
        """Get human-readable configuration summary.

        Returns:
            Multi-line string with configuration overview
        """
        validation = self.validate_configuration()

        summary_lines = [
            "DORA & Flow Metrics Configuration Summary",
            "=" * 50,
            f"Configuration file: {self.config_file}",
            f"Status: {'✅ Valid' if validation['is_valid'] else '❌ Invalid'}",
            "",
            f"DORA field mappings: {len(self.get_dora_field_mappings())} configured",
            f"Flow field mappings: {len(self.get_flow_field_mappings())} configured",
            f"WIP statuses: {len(self.get_wip_included_statuses())} configured",
            f"Active statuses: {len(self.get_active_statuses())} configured",
            f"Operational projects: {len(self.get_operational_projects())} configured",
        ]

        if validation["errors"]:
            summary_lines.append("")
            summary_lines.append("❌ Errors:")
            for error in validation["errors"]:
                summary_lines.append(f"  - {error}")

        if validation["warnings"]:
            summary_lines.append("")
            summary_lines.append("⚠️ Warnings:")
            for warning in validation["warnings"]:
                summary_lines.append(f"  - {warning}")

        return "\n".join(summary_lines)


# Singleton instance for convenient access
_config_instance: Optional[MetricsConfig] = None


def get_metrics_config() -> MetricsConfig:
    """Get singleton instance of MetricsConfig.

    Returns:
        Shared MetricsConfig instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = MetricsConfig()
    return _config_instance


def reload_metrics_config() -> MetricsConfig:
    """Reload configuration from disk (e.g., after user updates settings).

    Returns:
        Reloaded MetricsConfig instance
    """
    global _config_instance
    _config_instance = MetricsConfig()
    return _config_instance


# ============================================================================
# FORECAST CONFIGURATION CONSTANTS (Feature 009)
# ============================================================================

# Forecast calculation weights (oldest to newest week)
FORECAST_WEIGHTS_4_WEEK = [0.1, 0.2, 0.3, 0.4]  # 4-week weighted average

# Minimum weeks required for forecast
FORECAST_MIN_WEEKS = 2  # At least 2 weeks needed for baseline

# Decimal precision for forecast values
FORECAST_DECIMAL_PRECISION = 1  # Round to 1 decimal place

# Trend threshold for "on track" vs "above/below" status
FORECAST_TREND_THRESHOLD = 0.10  # ±10% neutral zone

# Flow Load range percentage for WIP bounds
FLOW_LOAD_RANGE_PERCENT = 0.20  # ±20% range

# Metrics classification by direction (for trend interpretation)
HIGHER_BETTER_METRICS = [
    "flow_velocity",
    "flow_efficiency",
    "dora_deployment_frequency",
]

LOWER_BETTER_METRICS = [
    "flow_time",
    "dora_lead_time",
    "dora_change_failure_rate",
    "dora_mttr",
]

# Flow Load is bidirectional (range-based, not point-based)
# Too high OR too low is bad
