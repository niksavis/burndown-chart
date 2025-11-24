"""DORA & Flow Metrics Configuration Loader.

This module provides the master configuration loader for all DORA and Flow metrics settings.
It loads customer-specific configuration from profiles/{profile_id}/profile.json including:
- Field mappings (JIRA custom fields → internal metric fields)
- Workflow status mappings (WIP, active, completion, flow_start statuses)
- Project classifications (development vs operational)
- Flow type mappings (Feature, Defect, Technical Debt, Risk)

Reference: docs/metrics/IMPLEMENTATION_GUIDE.md
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class MetricsConfig:
    """Configuration manager for DORA & Flow metrics.

    Loads and validates customer-specific configuration from profile.json.
    Provides methods for accessing field mappings, status configurations, and
    project classifications.

    Example:
        >>> config = MetricsConfig(profile_id="p_7987a9f5e52e")
        >>> wip_statuses = config.get_wip_statuses()
        >>> ['In Progress', 'Patch Available', 'Reopened']
    """

    def __init__(self, profile_id: Optional[str] = None):
        """Initialize configuration loader.

        Args:
            profile_id: Profile ID to load. If None, loads active profile from profiles.json
        """
        self.profile_id = profile_id or self._get_active_profile_id()
        self.profile_config = self._load_profile_config()

    def _get_active_profile_id(self) -> str:
        """Get active profile ID from profiles/profiles.json.

        Returns:
            Active profile ID

        Raises:
            FileNotFoundError: If profiles.json doesn't exist
        """
        profiles_path = Path("profiles/profiles.json")

        if not profiles_path.exists():
            logger.error(
                "profiles/profiles.json not found. Cannot load profile configuration."
            )
            raise FileNotFoundError(
                "profiles/profiles.json not found. "
                "Create a profile via UI before calculating metrics."
            )

        try:
            with open(profiles_path, "r", encoding="utf-8") as f:
                profiles_data = json.load(f)
                active_profile_id = profiles_data.get("active_profile_id")

                if not active_profile_id:
                    logger.error("No active_profile_id in profiles.json")
                    raise ValueError("No active profile configured in profiles.json")

                logger.info(f"Loaded active profile ID: {active_profile_id}")
                return active_profile_id
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in profiles/profiles.json: {e}")
            raise

    def _load_profile_config(self) -> Dict[str, Any]:
        """Load configuration from profiles/{profile_id}/profile.json.

        Returns:
            Profile configuration dictionary

        Raises:
            FileNotFoundError: If profile doesn't exist
            json.JSONDecodeError: If profile is invalid JSON
        """
        profile_path = Path(f"profiles/{self.profile_id}/profile.json")

        if not profile_path.exists():
            logger.warning(
                f"Profile {self.profile_id} not found at {profile_path}. "
                "Using default empty configuration."
            )
            return self._get_default_profile_config()

        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                logger.info(f"Loaded profile configuration from {profile_path}")
                return config
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {profile_path}: {e}")
            raise

    def _get_default_profile_config(self) -> Dict[str, Any]:
        """Get default empty profile configuration when profile doesn't exist.

        Returns:
            Dictionary with empty profile structure
        """
        return {
            "id": self.profile_id,
            "name": "Default",
            "project_classification": {
                "completion_statuses": [],
                "active_statuses": [],
                "flow_start_statuses": [],
                "wip_statuses": [],
                "devops_projects": [],
                "development_projects": [],
            },
            "field_mappings": {},
            "flow_type_mappings": {},
        }

    # ========================================================================
    # Field Mappings
    # ========================================================================

    def get_dora_field_mappings(self) -> Dict[str, str]:
        """Get DORA metric field mappings from profile.

        Returns:
            Dictionary mapping internal field names to JIRA field IDs
            Example: {"deployment_date": "customfield_10100", ...}
        """
        return self.profile_config.get("field_mappings", {}).get("dora", {})

    def get_flow_field_mappings(self) -> Dict[str, str]:
        """Get Flow metric field mappings from profile.

        Returns:
            Dictionary mapping internal field names to JIRA field IDs
            Example: {"flow_item_type": "customfield_10200", ...}
        """
        return self.profile_config.get("field_mappings", {}).get("flow", {})

    def get_all_field_mappings(self) -> Dict[str, Dict[str, str]]:
        """Get all field mappings (DORA + Flow) from profile.

        Returns:
            Dictionary with 'dora' and 'flow' field mappings
        """
        return self.profile_config.get("field_mappings", {})

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
    # Workflow Status Mappings (from Profile project_classification)
    # ========================================================================

    def get_wip_statuses(self) -> List[str]:
        """Get list of statuses that indicate work-in-progress (WIP) from profile.

        Returns:
            List of WIP status names configured in profile
            Example: ["In Progress", "Patch Available", "Reopened"]
        """
        return self.profile_config.get("project_classification", {}).get(
            "wip_statuses", []
        )

    def get_active_statuses(self) -> List[str]:
        """Get list of statuses where work is actively being done from profile.

        Used for Flow Efficiency calculation (active time vs waiting time).

        Returns:
            List of active status names configured in profile
            Example: ["In Progress", "In Review", "Testing"]
        """
        return self.profile_config.get("project_classification", {}).get(
            "active_statuses", []
        )

    def get_completion_statuses(self) -> List[str]:
        """Get list of statuses that indicate work is completed from profile.

        Returns:
            List of completion status names configured in profile
            Example: ["Done", "Resolved", "Closed"]
        """
        return self.profile_config.get("project_classification", {}).get(
            "completion_statuses", []
        )

    def get_flow_start_statuses(self) -> List[str]:
        """Get list of statuses that indicate work has started from profile.

        Returns:
            List of flow start status names configured in profile
            Example: ["In Progress", "Open"]
        """
        return self.profile_config.get("project_classification", {}).get(
            "flow_start_statuses", []
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

    def get_devops_projects(self) -> List[str]:
        """Get list of DevOps/operational project keys from profile.

        DevOps projects contain deployment tracking (Operational Tasks).

        Returns:
            List of DevOps project keys
            Example: ["KAFKA-OPS", "DEVOPS"]
        """
        return self.profile_config.get("project_classification", {}).get(
            "devops_projects", []
        )

    def get_development_projects(self) -> List[str]:
        """Get list of development project keys from profile.

        Returns:
            List of development project keys
            Example: ["KAFKA", "HBASE"]
        """
        return self.profile_config.get("project_classification", {}).get(
            "development_projects", []
        )

    def is_devops_project(self, project_key: str) -> bool:
        """Check if a project is a DevOps/operational project.

        Args:
            project_key: JIRA project key (e.g., "KAFKA-OPS")

        Returns:
            True if project is DevOps, False otherwise
        """
        return project_key in self.get_devops_projects()

    # ========================================================================
    # Flow Type Mappings
    # ========================================================================

    def get_flow_type_mappings(self) -> Dict[str, Any]:
        """Get flow type mappings from profile.

        Returns:
            Dictionary mapping flow types to issue types and effort categories
            Example: {"Feature": {"issue_types": ["Story"], "effort_categories": []}}
        """
        return self.profile_config.get("flow_type_mappings", {})

    def get_flow_type_for_issue(
        self, issue_type: str, effort_category: Optional[str] = None
    ) -> Optional[str]:
        """Determine flow type (Feature/Defect/Technical_Debt/Risk) for an issue.

        Args:
            issue_type: JIRA issue type name (e.g., "Story", "Bug")
            effort_category: Optional effort category value

        Returns:
            Flow type name or None if not mapped
        """
        flow_mappings = self.get_flow_type_mappings()

        for flow_type, mapping in flow_mappings.items():
            issue_types = mapping.get("issue_types", [])
            effort_categories = mapping.get("effort_categories", [])

            if issue_type in issue_types:
                return flow_type

            if effort_category and effort_category in effort_categories:
                return flow_type

        return None

    # ========================================================================
    # Validation
    # ========================================================================

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate profile configuration completeness and return status.

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

        # Check for completion statuses
        completion_statuses = self.get_completion_statuses()
        if not completion_statuses:
            warnings.append(
                "No completion statuses configured. "
                "Configure via 'Configure JIRA Mappings' → Status tab → Completion Statuses"
            )

        # Check for active statuses (required for Flow Efficiency)
        active_statuses = self.get_active_statuses()
        if not active_statuses:
            warnings.append(
                "No active statuses configured. "
                "Flow Efficiency metric will not calculate. "
                "Configure via 'Configure JIRA Mappings' → Status tab → Active Statuses"
            )

        # Check for WIP statuses (required for Flow Load)
        wip_statuses = self.get_wip_statuses()
        if not wip_statuses:
            warnings.append(
                "No WIP statuses configured. "
                "Flow Load metric will not calculate. "
                "Configure via 'Configure JIRA Mappings' → Status tab → WIP Statuses"
            )

        # Check for field mappings
        dora_mappings = self.get_dora_field_mappings()
        flow_mappings = self.get_flow_field_mappings()

        if not dora_mappings and not flow_mappings:
            warnings.append(
                "No field mappings configured. "
                "Use 'Configure JIRA Mappings' modal → Fields tab to configure JIRA custom fields."
            )

        # Check for development projects (for DORA metrics)
        dev_projects = self.get_development_projects()
        if not dev_projects:
            warnings.append(
                "No development projects configured. "
                "DORA metrics may not calculate correctly. "
                "Configure via 'Configure JIRA Mappings' → Projects tab"
            )

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def get_configuration_summary(self) -> str:
        """Get human-readable profile configuration summary.

        Returns:
            Multi-line string with configuration overview
        """
        validation = self.validate_configuration()

        validation = self.validate_configuration()

        summary_lines = [
            "DORA & Flow Metrics Configuration Summary",
            "=" * 50,
            f"Profile ID: {self.profile_id}",
            f"Status: {'Valid' if validation['is_valid'] else 'Invalid'}",
            "",
            f"DORA field mappings: {len(self.get_dora_field_mappings())} configured",
            f"Flow field mappings: {len(self.get_flow_field_mappings())} configured",
            f"Completion statuses: {len(self.get_completion_statuses())} configured",
            f"Active statuses: {len(self.get_active_statuses())} configured",
            f"WIP statuses: {len(self.get_wip_statuses())} configured",
            f"Flow start statuses: {len(self.get_flow_start_statuses())} configured",
            f"Development projects: {len(self.get_development_projects())} configured",
            f"DevOps projects: {len(self.get_devops_projects())} configured",
        ]

        if validation["errors"]:
            summary_lines.append("")
            summary_lines.append("Errors:")
            for error in validation["errors"]:
                summary_lines.append(f"  - {error}")

        if validation["warnings"]:
            summary_lines.append("")
            summary_lines.append("Warnings:")
            for warning in validation["warnings"]:
                summary_lines.append(f"  - {warning}")

        return "\n".join(summary_lines)


# Singleton instance for convenient access
_config_instance: Optional[MetricsConfig] = None


def get_metrics_config(profile_id: Optional[str] = None) -> MetricsConfig:
    """Get singleton instance of MetricsConfig.

    Args:
        profile_id: Optional profile ID. If None, uses active profile.

    Returns:
        Shared MetricsConfig instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = MetricsConfig(profile_id=profile_id)
    return _config_instance


def reload_metrics_config(profile_id: Optional[str] = None) -> MetricsConfig:
    """Reload configuration from disk (e.g., after user updates settings).

    Args:
        profile_id: Optional profile ID. If None, uses active profile.

    Returns:
        Reloaded MetricsConfig instance
    """
    global _config_instance
    _config_instance = MetricsConfig(profile_id=profile_id)
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
