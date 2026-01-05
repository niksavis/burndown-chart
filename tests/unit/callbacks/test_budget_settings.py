"""Tests for budget settings callback validation."""

import pytest
from unittest.mock import patch, MagicMock

from callbacks.budget_settings import save_budget_settings


@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    with patch("callbacks.budget_settings.get_db_connection") as mock:
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        mock.return_value.__enter__.return_value = conn
        yield mock, conn, cursor


def test_manual_override_does_not_require_time_and_cost(mock_db_connection):
    """Test that manual override mode only requires manual budget total."""
    mock_conn_func, mock_conn, mock_cursor = mock_db_connection

    # Manual mode with only manual budget total (no time/cost)
    result_notification, result_store = save_budget_settings(
        n_clicks=1,
        profile_id="test_profile",
        budget_mode="manual",
        time_allocated=None,  # Not required in manual mode
        budget_total_manual=50000,
        currency_symbol="€",
        team_cost=None,  # Not required in manual mode
        revision_reason="Initial budget",
        current_settings=None,
        effective_date=None,
    )

    # Should succeed without errors
    assert result_notification is not None
    # Toast structure: children is a Div containing [Icon, message_text]
    toast_content = result_notification.children.children[
        1
    ]  # Index 1 is the message text
    assert "successfully" in toast_content.lower()

    # Verify database was called
    assert mock_cursor.execute.called


def test_manual_override_requires_manual_budget_value(mock_db_connection):
    """Test that manual override mode requires manual budget total value."""
    mock_conn_func, mock_conn, mock_cursor = mock_db_connection

    # Manual mode without manual budget total
    result_notification, result_store = save_budget_settings(
        n_clicks=1,
        profile_id="test_profile",
        budget_mode="manual",
        time_allocated=None,
        budget_total_manual=None,  # Missing required field
        currency_symbol="€",
        team_cost=None,
        revision_reason="Initial budget",
        current_settings=None,
        effective_date=None,
    )

    # Should fail with validation error
    assert result_notification is not None
    toast_content = result_notification.children.children[
        1
    ]  # Index 1 is the message text
    assert "manual budget total" in toast_content.lower()
    assert "greater than 0" in toast_content.lower()


def test_auto_mode_requires_time_and_cost(mock_db_connection):
    """Test that auto mode requires time and cost fields."""
    mock_conn_func, mock_conn, mock_cursor = mock_db_connection

    # Auto mode without time allocated
    result_notification, result_store = save_budget_settings(
        n_clicks=1,
        profile_id="test_profile",
        budget_mode="auto",
        time_allocated=None,  # Missing required field for auto mode
        budget_total_manual=None,
        currency_symbol="€",
        team_cost=2500,
        revision_reason="Initial budget",
        current_settings=None,
        effective_date=None,
    )

    # Should fail with validation error
    assert result_notification is not None
    toast_content = result_notification.children.children[
        1
    ]  # Index 1 is the message text
    assert "time allocated" in toast_content.lower()


def test_auto_mode_calculates_budget_from_time_and_cost(mock_db_connection):
    """Test that auto mode calculates budget from time × cost."""
    mock_conn_func, mock_conn, mock_cursor = mock_db_connection

    # Auto mode with time and cost
    result_notification, result_store = save_budget_settings(
        n_clicks=1,
        profile_id="test_profile",
        budget_mode="auto",
        time_allocated=10,
        budget_total_manual=None,  # Should be ignored in auto mode
        currency_symbol="€",
        team_cost=3000,
        revision_reason="Initial budget",
        current_settings=None,
        effective_date=None,
    )

    # Should succeed
    assert result_notification is not None
    toast_content = result_notification.children.children[
        1
    ]  # Index 1 is the message text
    assert "successfully" in toast_content.lower()

    # Verify budget was calculated as time × cost = 10 × 3000 = 30000
    insert_call = mock_cursor.execute.call_args_list[0]
    insert_values = insert_call[0][1]
    # Values are: profile_id, time, cost, total, currency, created, updated
    assert insert_values[3] == 30000  # budget_total_eur


def test_manual_override_with_optional_time_and_cost(mock_db_connection):
    """Test that manual override can optionally include time/cost for tracking."""
    mock_conn_func, mock_conn, mock_cursor = mock_db_connection

    # Manual mode with optional time and cost provided
    result_notification, result_store = save_budget_settings(
        n_clicks=1,
        profile_id="test_profile",
        budget_mode="manual",
        time_allocated=20,  # Optional in manual mode
        budget_total_manual=75000,
        currency_symbol="$",
        team_cost=3500,  # Optional in manual mode
        revision_reason="Fixed budget with team info",
        current_settings=None,
        effective_date=None,
    )

    # Should succeed
    assert result_notification is not None
    toast_content = result_notification.children.children[
        1
    ]  # Index 1 is the message text
    assert "successfully" in toast_content.lower()

    # Verify manual budget total was used (not calculated)
    insert_call = mock_cursor.execute.call_args_list[0]
    insert_values = insert_call[0][1]
    assert insert_values[3] == 75000  # budget_total_eur (not 20 × 3500 = 70000)
