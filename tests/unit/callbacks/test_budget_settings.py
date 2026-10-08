from unittest.mock import MagicMock, patch

import pytest

from callbacks.budget_settings._save import save_budget_settings


@pytest.fixture
def mock_db_connection():
    with patch("callbacks.budget_settings._save.get_db_connection") as mock:
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        mock.return_value.__enter__.return_value = conn
        yield mock, conn, cursor


def test_save_requires_time_allocated(mock_db_connection):
    mock_conn_func, mock_conn, mock_cursor = mock_db_connection

    result_notification, result_store = save_budget_settings(
        n_clicks=1,
        profile_id="test_profile",
        query_id="test_query",
        time_allocated=None,
        currency_symbol="€",
        team_cost=2500,
        revision_reason="Initial budget",
        current_settings=None,
        effective_date=None,
    )

    assert result_notification is not None
    toast_message = result_notification.children
    assert "time allocated" in toast_message.lower()


def test_save_requires_team_cost(mock_db_connection):
    mock_conn_func, mock_conn, mock_cursor = mock_db_connection

    result_notification, result_store = save_budget_settings(
        n_clicks=1,
        profile_id="test_profile",
        query_id="test_query",
        time_allocated=20,
        currency_symbol="€",
        team_cost=None,
        revision_reason="Initial budget",
        current_settings=None,
        effective_date=None,
    )

    assert result_notification is not None
    toast_message = result_notification.children
    assert "team cost" in toast_message.lower()


def test_budget_calculates_from_time_and_cost(mock_db_connection):
    mock_conn_func, mock_conn, mock_cursor = mock_db_connection

    result_notification, result_store = save_budget_settings(
        n_clicks=1,
        profile_id="test_profile",
        query_id="test_query",
        time_allocated=10,
        currency_symbol="€",
        team_cost=3000,
        revision_reason="Initial budget",
        current_settings=None,
        effective_date=None,
    )

    assert result_notification is not None
    toast_message = result_notification.children
    assert "successfully" in toast_message.lower()

    insert_call = mock_cursor.execute.call_args_list[0]
    insert_values = insert_call[0][1]
    assert insert_values[4] == 30000


def test_budget_update_with_optional_fields(mock_db_connection):
    mock_conn_func, mock_conn, mock_cursor = mock_db_connection

    result_notification, result_store = save_budget_settings(
        n_clicks=1,
        profile_id="test_profile",
        query_id="test_query",
        time_allocated=20,
        currency_symbol="$",
        team_cost=3500,
        revision_reason="Q2 budget allocation",
        current_settings=None,
        effective_date="2026-01-01",
    )

    assert result_notification is not None
    toast_message = result_notification.children
    assert "successfully" in toast_message.lower()

    insert_call = mock_cursor.execute.call_args_list[0]
    insert_values = insert_call[0][1]
    assert insert_values[4] == 70000
