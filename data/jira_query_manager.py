"""
JIRA Query Profile Manager Module

This module handles saving, loading, and managing JQL query profiles.
Users can save multiple JIRA queries with names and descriptions for easy reuse.
"""

#######################################################################
# IMPORTS
#######################################################################
import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# Application imports
from configuration import logger
from data.schema import validate_query_profile

#######################################################################
# CONSTANTS
#######################################################################
QUERY_PROFILES_FILE = "jira_query_profiles.json"

#######################################################################
# QUERY PROFILE MANAGEMENT FUNCTIONS
#######################################################################


def _load_profiles_from_disk() -> List[Dict[str, Any]]:
    """
    Load query profiles from disk.

    Returns:
        List of query profile dictionaries
    """
    if not os.path.exists(QUERY_PROFILES_FILE):
        return []

    try:
        with open(QUERY_PROFILES_FILE, "r", encoding="utf-8") as f:
            profiles = json.load(f)
            return profiles if isinstance(profiles, list) else []
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading query profiles: {e}")
        return []


def _save_profiles_to_disk(profiles: List[Dict[str, Any]]) -> bool:
    """
    Save query profiles to disk.

    Args:
        profiles: List of query profile dictionaries

    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        with open(QUERY_PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        logger.error(f"Error saving query profiles: {e}")
        return False


def load_query_profiles() -> List[Dict[str, Any]]:
    """
    Load all query profiles from disk.

    Returns:
        List of query profile dictionaries from jira_query_profiles.json
    """
    # Load user-created profiles from disk
    return _load_profiles_from_disk()


def get_query_profile_by_id(profile_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific query profile by ID.

    Args:
        profile_id: UUID or default profile ID

    Returns:
        Query profile dictionary or None if not found
    """
    all_profiles = load_query_profiles()

    for profile in all_profiles:
        if profile.get("id") == profile_id:
            return profile

    return None


def save_query_profile(
    name: str, jql: str, description: str = "", profile_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Save a new query profile or update existing one.

    Args:
        name: User-friendly name for the query
        jql: JQL query string
        description: Optional description
        profile_id: Optional ID for update, None for new profile

    Returns:
        Saved profile dictionary or None if validation failed
    """
    # Validate inputs
    if not name or not name.strip():
        logger.error("Query profile name cannot be empty")
        return None

    if not isinstance(jql, str):
        logger.error("JQL query must be a string")
        return None

    # Load existing user profiles
    user_profiles = _load_profiles_from_disk()

    # Check for duplicate names (only for new profiles or rename)
    for profile in user_profiles:
        if profile.get("name") == name.strip():
            if profile_id is None or profile.get("id") != profile_id:
                logger.error(f"Query profile with name '{name}' already exists")
                return None

    now = datetime.now().isoformat()

    if profile_id:
        # Update existing profile
        for i, profile in enumerate(user_profiles):
            if profile.get("id") == profile_id:
                user_profiles[i].update(
                    {
                        "name": name.strip(),
                        "jql": jql.strip(),
                        "description": description.strip(),
                        "last_used": now,
                    }
                )
                updated_profile = user_profiles[i]
                break
        else:
            logger.error(f"Profile with ID '{profile_id}' not found")
            return None
    else:
        # Create new profile
        updated_profile = {
            "id": str(uuid.uuid4()),
            "name": name.strip(),
            "jql": jql.strip(),
            "description": description.strip(),
            "created_at": now,
            "last_used": now,
            "is_default": False,
        }
        user_profiles.append(updated_profile)

    # Validate profile
    if not validate_query_profile(updated_profile):
        logger.error("Invalid query profile structure")
        return None

    # Save to disk
    if _save_profiles_to_disk(user_profiles):
        logger.info(f"Saved query profile: {name}")
        return updated_profile
    else:
        return None


def delete_query_profile(profile_id: str) -> bool:
    """
    Delete a query profile.

    Args:
        profile_id: UUID of the profile to delete

    Returns:
        bool: True if deleted successfully, False otherwise
    """
    # Cannot delete default profiles
    if profile_id.startswith("default-"):
        logger.error("Cannot delete default query profiles")
        return False

    # Load user profiles
    user_profiles = _load_profiles_from_disk()

    # Find and remove profile
    updated_profiles = [p for p in user_profiles if p.get("id") != profile_id]

    if len(updated_profiles) == len(user_profiles):
        logger.error(f"Profile with ID '{profile_id}' not found")
        return False

    # Save updated list
    if _save_profiles_to_disk(updated_profiles):
        logger.info(f"Deleted query profile: {profile_id}")
        return True
    else:
        return False


def update_query_profile(
    profile_id: str, name: str, jql: str, description: str = ""
) -> Optional[Dict[str, Any]]:
    """
    Update an existing query profile.

    Args:
        profile_id: UUID of the profile to update
        name: Updated name
        jql: Updated JQL query
        description: Updated description

    Returns:
        Updated profile dictionary or None if update failed
    """
    return save_query_profile(name, jql, description, profile_id)


def update_profile_last_used(profile_id: str) -> bool:
    """
    Update the last_used timestamp for a profile.

    Args:
        profile_id: UUID of the profile

    Returns:
        bool: True if updated successfully, False otherwise
    """
    # Skip updating default profiles timestamps
    if profile_id.startswith("default-"):
        return True

    user_profiles = _load_profiles_from_disk()

    for profile in user_profiles:
        if profile.get("id") == profile_id:
            profile["last_used"] = datetime.now().isoformat()
            return _save_profiles_to_disk(user_profiles)

    return False


def get_profile_names() -> List[str]:
    """
    Get a list of all query profile names.

    Returns:
        List of profile names
    """
    profiles = load_query_profiles()
    return [p.get("name", "") for p in profiles if p.get("name")]


def validate_profile_name_unique(name: str, exclude_id: Optional[str] = None) -> bool:
    """
    Check if a profile name is unique.

    Args:
        name: Name to check
        exclude_id: Optional profile ID to exclude from check (for updates)

    Returns:
        bool: True if name is unique, False otherwise
    """
    profiles = load_query_profiles()

    for profile in profiles:
        if profile.get("name") == name.strip():
            if exclude_id is None or profile.get("id") != exclude_id:
                return False

    return True


def set_default_query(profile_id: str) -> bool:
    """
    Set a query profile as the default query.
    Only one query can be default at a time.

    Args:
        profile_id: ID of the profile to set as default

    Returns:
        bool: True if set successfully, False otherwise
    """
    profiles = _load_profiles_from_disk()

    # Remove default flag from all profiles first
    for profile in profiles:
        profile["is_default"] = False

    # Set the specified profile as default
    for profile in profiles:
        if profile.get("id") == profile_id:
            profile["is_default"] = True
            profile["last_used"] = datetime.now().isoformat()

            success = _save_profiles_to_disk(profiles)
            if success:
                logger.info(f"Set query profile '{profile['name']}' as default")
            return success

    logger.error(f"Query profile with ID '{profile_id}' not found")
    return False


def get_default_query() -> Optional[Dict[str, Any]]:
    """
    Get the current default query profile.

    Returns:
        Default query profile dictionary or None if no default is set
    """
    profiles = _load_profiles_from_disk()

    for profile in profiles:
        if profile.get("is_default", False):
            return profile

    return None


def remove_default_query() -> bool:
    """
    Remove the default flag from all query profiles.

    Returns:
        bool: True if updated successfully, False otherwise
    """
    profiles = _load_profiles_from_disk()

    # Remove default flag from all profiles
    changed = False
    for profile in profiles:
        if profile.get("is_default", False):
            profile["is_default"] = False
            changed = True

    if changed:
        success = _save_profiles_to_disk(profiles)
        if success:
            logger.info("Removed default query setting")
        return success

    return True  # No change needed
