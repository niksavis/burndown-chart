import logging
from typing import Any

logger = logging.getLogger(__name__)


def get_backend():  # noqa: PLC0415
    from data.persistence.factory import (  # noqa: PLC0415
        get_backend as _get_backend,
    )

    return _get_backend()


class MetricsConfig:
    def __init__(self, profile_id: str | None = None):

        self.profile_id = profile_id or self._get_active_profile_id()
        self.profile_config = self._load_profile_config()

    def _get_active_profile_id(self) -> str:

        try:
            backend = get_backend()
            active_profile_id = backend.get_app_state("active_profile_id")

            if not active_profile_id:
                logger.error("No active_profile_id in database")
                raise RuntimeError(
                    "No active profile configured. "
                    "Create a profile via UI before calculating metrics."
                )

            logger.info(f"Loaded active profile ID from database: {active_profile_id}")
            return active_profile_id
        except Exception as e:
            logger.error(f"Failed to load active profile ID: {e}")
            raise RuntimeError(f"Cannot load profile configuration: {e}") from e

    def _load_profile_config(self) -> dict[str, Any]:

        try:
            backend = get_backend()
            profile_data = backend.get_profile(self.profile_id)

            if not profile_data:
                logger.warning(
                    f"Profile {self.profile_id} not found in database. "
                    "Using default empty configuration."
                )
                return self._get_default_profile_config()

            logger.info(
                f"Loaded profile configuration for {self.profile_id} from database"
            )
            return profile_data
        except Exception as e:
            logger.error(f"Failed to load profile configuration: {e}")
            return self._get_default_profile_config()

    def _get_default_profile_config(self) -> dict[str, Any]:

        return {
            "id": self.profile_id,
            "name": "Default",
            "project_classification": {
                "flow_end_statuses": [],
                "active_statuses": [],
                "flow_start_statuses": [],
                "wip_statuses": [],
                "devops_projects": [],
                "development_projects": [],
            },
            "field_mappings": {},
            "flow_type_mappings": {},
        }

    def get_dora_field_mappings(self) -> dict[str, str]:

        return self.profile_config.get("field_mappings", {}).get("dora", {})

    def get_flow_field_mappings(self) -> dict[str, str]:

        return self.profile_config.get("field_mappings", {}).get("flow", {})

    def get_all_field_mappings(self) -> dict[str, dict[str, str]]:

        return self.profile_config.get("field_mappings", {})

    def get_custom_field_id(
        self, field_name: str, metric_type: str = "dora"
    ) -> str | None:

        mappings = (
            self.get_dora_field_mappings()
            if metric_type == "dora"
            else self.get_flow_field_mappings()
        )
        return mappings.get(field_name)

    def get_wip_statuses(self) -> list[str]:

        return self.profile_config.get("project_classification", {}).get(
            "wip_statuses", []
        )

    def get_active_statuses(self) -> list[str]:

        return self.profile_config.get("project_classification", {}).get(
            "active_statuses", []
        )

    def get_flow_end_statuses(self) -> list[str]:

        return self.profile_config.get("project_classification", {}).get(
            "flow_end_statuses", []
        )

    def get_flow_start_statuses(self) -> list[str]:

        return self.profile_config.get("project_classification", {}).get(
            "flow_start_statuses", []
        )

    def is_status_in_list(
        self, status_name: str, status_list: list[str], case_sensitive: bool = False
    ) -> bool:

        if case_sensitive:
            return status_name in status_list
        else:
            status_lower = status_name.lower()
            return status_lower in [s.lower() for s in status_list]

    def get_devops_projects(self) -> list[str]:

        return self.profile_config.get("project_classification", {}).get(
            "devops_projects", []
        )

    def get_development_projects(self) -> list[str]:

        return self.profile_config.get("project_classification", {}).get(
            "development_projects", []
        )

    def is_devops_project(self, project_key: str) -> bool:

        return project_key in self.get_devops_projects()

    def get_flow_type_mappings(self) -> dict[str, Any]:

        return self.profile_config.get("flow_type_mappings", {})

    def get_flow_type_for_issue(
        self, issue_type: str, effort_category: str | None = None
    ) -> str | None:

        flow_mappings = self.get_flow_type_mappings()

        logger.debug(
            f"[FLOW TYPE CLASSIFICATION] Classifying issue_type='{issue_type}', "
            f"effort_category='{effort_category}'"
        )
        logger.debug(f"[FLOW TYPE CLASSIFICATION] Available mappings: {flow_mappings}")

        matching_flow_types = []
        catch_all_flow_type = None

        for flow_type, mapping in flow_mappings.items():
            issue_types = mapping.get("issue_types", [])
            if issue_type in issue_types:
                effort_categories = mapping.get("effort_categories", [])
                logger.debug(
                    f"[FLOW TYPE CLASSIFICATION] Found match: flow_type='{flow_type}', "
                    f"effort_categories={effort_categories}"
                )
                if not effort_categories:
                    if catch_all_flow_type is None:
                        catch_all_flow_type = flow_type
                        logger.debug(
                            "[FLOW TYPE CLASSIFICATION] Set catch-all: "
                            f"'{catch_all_flow_type}'"
                        )
                else:
                    matching_flow_types.append((flow_type, effort_categories))

        if effort_category:
            logger.debug(
                "[FLOW TYPE CLASSIFICATION] "
                f"Searching for exact effort match in: {matching_flow_types}"
            )
            for flow_type, effort_categories in matching_flow_types:
                if effort_category in effort_categories:
                    logger.debug(
                        f"[FLOW TYPE CLASSIFICATION] Found exact match: '{flow_type}' "
                        f"(effort '{effort_category}' in {effort_categories})"
                    )
                    return flow_type

        if catch_all_flow_type:
            logger.debug(
                f"[FLOW TYPE CLASSIFICATION] Using catch-all: '{catch_all_flow_type}'"
            )
            return catch_all_flow_type

        if matching_flow_types and not effort_category:
            result = matching_flow_types[0][0]
            logger.debug(
                f"[FLOW TYPE CLASSIFICATION] Using first match (no effort): '{result}'"
            )
            return result

        logger.warning(
            "[FLOW TYPE CLASSIFICATION] No mapping found for "
            f"issue_type='{issue_type}', "
            f"effort_category='{effort_category}'"
        )
        return None

    def validate_configuration(self) -> dict[str, Any]:

        errors = []
        warnings = []

        flow_end_statuses = self.get_flow_end_statuses()
        if not flow_end_statuses:
            warnings.append(
                "No completion statuses configured. "
                "Configure via 'Configure JIRA Mappings' "
                "→ Status tab → Completion Statuses"
            )

        active_statuses = self.get_active_statuses()
        if not active_statuses:
            warnings.append(
                "No active statuses configured. "
                "Flow Efficiency metric will not calculate. "
                "Configure via 'Configure JIRA Mappings' → Status tab → Active Statuses"
            )

        wip_statuses = self.get_wip_statuses()
        if not wip_statuses:
            warnings.append(
                "No WIP statuses configured. "
                "Flow Load metric will not calculate. "
                "Configure via 'Configure JIRA Mappings' → Status tab → WIP Statuses"
            )

        dora_mappings = self.get_dora_field_mappings()
        flow_mappings = self.get_flow_field_mappings()

        if not dora_mappings and not flow_mappings:
            warnings.append(
                "No field mappings configured. "
                "Use 'Configure JIRA Mappings' modal → Fields tab "
                "to configure JIRA custom fields."
            )

        dev_projects = self.get_development_projects()
        if not dev_projects:
            warnings.append(
                "No development projects configured. "
                "DORA metrics may not calculate correctly. "
                "Configure via 'Configure JIRA Mappings' → Projects tab"
            )

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def get_configuration_summary(self) -> str:

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
            f"Flow End statuses: {len(self.get_flow_end_statuses())} configured",
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


_config_instance: MetricsConfig | None = None


def get_metrics_config(profile_id: str | None = None) -> MetricsConfig:

    global _config_instance
    if _config_instance is None:
        _config_instance = MetricsConfig(profile_id=profile_id)
    return _config_instance


def reload_metrics_config(profile_id: str | None = None) -> MetricsConfig:

    global _config_instance
    _config_instance = MetricsConfig(profile_id=profile_id)
    return _config_instance


FORECAST_WEIGHTS_4_WEEK = [0.1, 0.2, 0.3, 0.4]

FORECAST_MIN_WEEKS = 2

FORECAST_DECIMAL_PRECISION = 1

FORECAST_TREND_THRESHOLD = 0.10

FLOW_LOAD_RANGE_PERCENT = 0.20

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
