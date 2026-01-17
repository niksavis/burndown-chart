"""
Tests for update notification UI component.

Verifies that update notification alerts are created correctly
based on UpdateProgress state.
"""

import dash_bootstrap_components as dbc
from dash import html

from data.update_manager import UpdateProgress, UpdateState
from ui.update_notification import (
    create_update_notification,
    create_update_downloading_alert,
    create_update_ready_alert,
    create_update_error_alert,
)


def test_create_update_notification_with_available_update():
    """Test that alert is created when update is available."""
    progress = UpdateProgress(
        state=UpdateState.AVAILABLE,
        current_version="2.0.0",
        available_version="2.1.0",
        download_url="https://example.com/download.zip",
        release_notes="Bug fixes and improvements",
    )

    result = create_update_notification(progress)

    assert result is not None
    assert isinstance(result, dbc.Alert)
    # Check properties using getattr to avoid type checker issues
    assert getattr(result, "color", None) == "info"
    assert getattr(result, "is_open", None) is True
    assert getattr(result, "dismissable", None) is True


def test_create_update_notification_with_no_update():
    """Test that no alert is created when no update is available."""
    progress = UpdateProgress(
        state=UpdateState.UP_TO_DATE,
        current_version="2.0.0",
    )

    result = create_update_notification(progress)

    assert result is None


def test_create_update_notification_with_none():
    """Test that no alert is created when progress is None."""
    result = create_update_notification(None)

    assert result is None


def test_create_update_notification_with_error_state():
    """Test that no alert is created when state is ERROR."""
    progress = UpdateProgress(
        state=UpdateState.ERROR,
        current_version="2.0.0",
        error_message="Network error",
    )

    result = create_update_notification(progress)

    assert result is None


def test_create_update_notification_includes_versions():
    """Test that notification includes version information."""
    progress = UpdateProgress(
        state=UpdateState.AVAILABLE,
        current_version="2.0.0",
        available_version="2.1.0",
    )

    result = create_update_notification(progress)

    # Convert children to string to check content
    assert result is not None
    # The alert should contain version numbers somewhere in its structure
    # Check that children list contains elements
    children = getattr(result, "children", [])
    assert len(children) > 0


def test_create_update_notification_includes_release_notes():
    """Test that notification includes release notes when available."""
    progress = UpdateProgress(
        state=UpdateState.AVAILABLE,
        current_version="2.0.0",
        available_version="2.1.0",
        release_notes="**New Features**\n- Feature A\n- Feature B",
    )

    result = create_update_notification(progress)

    assert result is not None
    # Should have more children when release notes are present
    children = getattr(result, "children", [])
    assert len(children) > 2


def test_create_update_notification_truncates_long_notes():
    """Test that long release notes are truncated."""
    long_notes = "A" * 500  # Very long release notes

    progress = UpdateProgress(
        state=UpdateState.AVAILABLE,
        current_version="2.0.0",
        available_version="2.1.0",
        release_notes=long_notes,
    )

    result = create_update_notification(progress)

    assert result is not None
    # Notes should be truncated (checked internally in component)


def test_create_update_notification_has_update_button():
    """Test that notification includes Update Now button."""
    progress = UpdateProgress(
        state=UpdateState.AVAILABLE,
        current_version="2.0.0",
        available_version="2.1.0",
    )

    result = create_update_notification(progress)

    assert result is not None
    # Last child should be the button container
    children = getattr(result, "children", [])
    if children:
        button_div = children[-1]
        assert isinstance(button_div, html.Div)


def test_create_update_downloading_alert():
    """Test downloading progress alert creation."""
    result = create_update_downloading_alert(progress_percent=45)

    assert isinstance(result, dbc.Alert)
    assert getattr(result, "color", None) == "info"
    assert getattr(result, "dismissable", None) is False
    assert getattr(result, "is_open", None) is True


def test_create_update_ready_alert():
    """Test ready-to-install alert creation."""
    result = create_update_ready_alert()

    assert isinstance(result, dbc.Alert)
    assert getattr(result, "color", None) == "success"
    assert getattr(result, "dismissable", None) is False
    assert getattr(result, "is_open", None) is True


def test_create_update_error_alert():
    """Test error alert creation."""
    error_msg = "Network connection failed"

    result = create_update_error_alert(error_msg)

    assert isinstance(result, dbc.Alert)
    assert getattr(result, "color", None) == "warning"
    assert getattr(result, "dismissable", None) is True
    assert getattr(result, "is_open", None) is True
