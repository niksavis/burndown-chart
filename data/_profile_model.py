"""Profile data model and ID generation.

Extracted from profile_manager.py to respect file-size limits.
Constants (PROFILES_DIR, DEFAULT_PROFILE_ID, etc.) remain in
data.profile_manager so test fixtures can patch them in one place.
"""

import logging
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


class Profile:
    """Profile workspace metadata and settings.

    Attributes:
        id: Unique identifier (slugified name)
        name: Human-readable profile name
        description: Optional description
        created_at: ISO 8601 timestamp of creation
        last_used: ISO 8601 timestamp of last access
        jira_config: JIRA connection settings (base_url, token, points_field, etc.)
        field_mappings: DORA/Flow field mappings
        forecast_settings: PERT factor, deadline, data_points_count
        project_classification: DevOps/development project classification
        flow_type_mappings: Flow Framework type mappings
        queries: List of query IDs in this profile
        show_milestone: Toggle milestone display on charts
        show_points: Toggle between points/items display
    """

    def __init__(
        self,
        id: str,
        name: str,
        description: str = "",
        created_at: str = "",
        last_used: str = "",
        jira_config: dict | None = None,
        field_mappings: dict | None = None,
        forecast_settings: dict | None = None,
        project_classification: dict | None = None,
        flow_type_mappings: dict | None = None,
        queries: list | None = None,
        show_milestone: bool = False,
        show_points: bool = False,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.created_at = created_at or datetime.now(UTC).isoformat()
        self.last_used = last_used or datetime.now(UTC).isoformat()
        self.jira_config = jira_config or {}
        self.field_mappings = field_mappings or {}
        self.forecast_settings = forecast_settings or {
            "pert_factor": 1.2,
            "deadline": None,
            "data_points_count": 12,
        }
        self.project_classification = project_classification or {}
        self.flow_type_mappings = flow_type_mappings or {}
        self.queries = queries or []
        self.show_milestone = show_milestone
        self.show_points = show_points

    def to_dict(self) -> dict:
        """Convert profile to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "jira_config": self.jira_config,
            "field_mappings": self.field_mappings,
            "forecast_settings": self.forecast_settings,
            "project_classification": self.project_classification,
            "flow_type_mappings": self.flow_type_mappings,
            "queries": self.queries,
            "show_milestone": self.show_milestone,
            "show_points": self.show_points,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        """Create profile from dictionary loaded from JSON."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            created_at=data.get("created_at", ""),
            last_used=data.get("last_used", ""),
            jira_config=data.get("jira_config", {}),
            field_mappings=data.get("field_mappings", {}),
            forecast_settings=data.get("forecast_settings", {}),
            project_classification=data.get("project_classification", {}),
            flow_type_mappings=data.get("flow_type_mappings", {}),
            queries=data.get("queries", []),
            show_milestone=data.get("show_milestone", False),
            show_points=data.get("show_points", False),
        )


def _generate_unique_profile_id() -> str:
    """Generate unique profile ID using UUID.

    Format: p_{12-char-hex} (e.g., p_a1b2c3d4e5f6)

    Returns:
        str: Unique profile ID guaranteed to not collide

    Examples:
        >>> _generate_unique_profile_id()
        'p_a1b2c3d4e5f6'
    """
    import uuid

    return f"p_{uuid.uuid4().hex[:12]}"
