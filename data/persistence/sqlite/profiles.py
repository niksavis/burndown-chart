"""Profile operations mixin for SQLiteBackend."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from data.persistence import ProfileNotFoundError, ValidationError
from data.database import get_db_connection
from data.persistence.sqlite.helpers import retry_on_db_lock

logger = logging.getLogger(__name__)


class ProfilesMixin:
    """Mixin for profile CRUD operations."""

    db_path: Path  # Set by composition class (SQLiteBackend)

    def get_profile(self, profile_id: str) -> Optional[Dict]:
        """Load profile configuration from profiles table."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
                result = cursor.fetchone()

                if not result:
                    return None

                # Convert Row to dict and parse JSON fields
                profile = dict(result)
                profile["jira_config"] = json.loads(profile["jira_config"])
                profile["field_mappings"] = json.loads(profile["field_mappings"])
                profile["forecast_settings"] = json.loads(profile["forecast_settings"])
                profile["project_classification"] = json.loads(
                    profile["project_classification"]
                )
                profile["flow_type_mappings"] = json.loads(
                    profile["flow_type_mappings"]
                )

                return profile

        except Exception as e:
            logger.error(
                f"Failed to get profile '{profile_id}': {e}",
                extra={"error_type": type(e).__name__, "profile_id": profile_id},
            )
            raise

    @retry_on_db_lock(max_retries=3, base_delay=0.1)
    def save_profile(self, profile: Dict) -> None:
        """Save profile configuration (insert or update) to profiles table."""
        required_fields = ["id", "name", "created_at", "last_used"]
        for field in required_fields:
            if field not in profile:
                raise ValidationError(f"Profile missing required field: {field}")

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Serialize JSON fields
                jira_config = json.dumps(profile.get("jira_config", {}))
                field_mappings = json.dumps(profile.get("field_mappings", {}))
                forecast_settings = json.dumps(
                    profile.get(
                        "forecast_settings",
                        {"pert_factor": 1.2, "deadline": None, "data_points_count": 12},
                    )
                )
                project_classification = json.dumps(
                    profile.get("project_classification", {})
                )
                flow_type_mappings = json.dumps(profile.get("flow_type_mappings", {}))

                cursor.execute(
                    """
                    INSERT INTO profiles (
                        id, name, description, created_at, last_used,
                        jira_config, field_mappings, forecast_settings,
                        project_classification, flow_type_mappings,
                        show_milestone, show_points
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        description = excluded.description,
                        last_used = excluded.last_used,
                        jira_config = excluded.jira_config,
                        field_mappings = excluded.field_mappings,
                        forecast_settings = excluded.forecast_settings,
                        project_classification = excluded.project_classification,
                        flow_type_mappings = excluded.flow_type_mappings,
                        show_milestone = excluded.show_milestone,
                        show_points = excluded.show_points
                """,
                    (
                        profile["id"],
                        profile["name"],
                        profile.get("description", ""),
                        profile["created_at"],
                        profile["last_used"],
                        jira_config,
                        field_mappings,
                        forecast_settings,
                        project_classification,
                        flow_type_mappings,
                        profile.get("show_milestone", 0),
                        profile.get("show_points", 0),
                    ),
                )

                conn.commit()
                logger.info(f"Saved profile: {profile['id']}")

        except Exception as e:
            logger.error(
                f"Failed to save profile '{profile.get('id')}': {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def list_profiles(self) -> List[Dict]:
        """List all profiles, ordered by last_used descending."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name, description, created_at, last_used FROM profiles ORDER BY last_used DESC"
                )
                results = cursor.fetchall()
                return [dict(row) for row in results]

        except Exception as e:
            logger.error(
                f"Failed to list profiles: {e}", extra={"error_type": type(e).__name__}
            )
            raise

    @retry_on_db_lock(max_retries=3, base_delay=0.1)
    def delete_profile(self, profile_id: str) -> None:
        """Delete profile and cascade to all queries and data."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if profile exists
                cursor.execute("SELECT id FROM profiles WHERE id = ?", (profile_id,))
                if not cursor.fetchone():
                    raise ProfileNotFoundError(f"Profile '{profile_id}' not found")

                # DELETE CASCADE handles related data automatically
                cursor.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
                conn.commit()

                logger.info(f"Deleted profile: {profile_id}")

        except ProfileNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to delete profile '{profile_id}': {e}",
                extra={"error_type": type(e).__name__, "profile_id": profile_id},
            )
            raise
