"""
Test fixtures for dashboard metrics testing.

This module provides reusable test data for dashboard calculation and rendering tests.
All fixtures follow test isolation principles - they return fresh data on each call.
"""

import pytest
from datetime import datetime, timedelta


@pytest.fixture
def sample_statistics_data():
    """Standard statistics data for dashboard testing (10 weeks of realistic project data).

    Returns:
        list: 10 weeks of StatisticsDataPoint dictionaries with completed items/points
    """
    base_date = datetime(2025, 1, 1)
    return [
        {
            "date": (base_date + timedelta(weeks=i)).strftime("%Y-%m-%d"),
            "completed_items": 5 + (i % 3),  # Varies 5-7
            "completed_points": 25.0 + (i % 3) * 5.0,  # Varies 25-35
            "created_items": 2,
            "created_points": 10.0,
        }
        for i in range(10)
    ]


@pytest.fixture
def sample_settings():
    """Standard settings for dashboard testing.

    Returns:
        dict: DashboardSettings with standard PERT/deadline configuration
    """
    return {
        "pert_factor": 1.5,
        "deadline": "2025-12-31",
        "estimated_total_items": 100,
        "estimated_total_points": 500.0,
        "data_points_count": 10,
        "forecast_max_days": 730,
        "pessimistic_multiplier_cap": 5,
    }


@pytest.fixture
def empty_statistics_data():
    """Empty statistics data for new project edge case testing.

    Returns:
        list: Empty list representing no historical data
    """
    return []


@pytest.fixture
def minimal_statistics_data():
    """Single data point for edge case testing.

    Returns:
        list: Single StatisticsDataPoint for minimal data scenario
    """
    return [
        {
            "date": "2025-01-01",
            "completed_items": 1,
            "completed_points": 5.0,
            "created_items": 0,
            "created_points": 0.0,
        }
    ]


@pytest.fixture
def extreme_velocity_data():
    """Very low velocity data causing >10 year forecast scenarios.

    Returns:
        list: Statistics with extremely low completion rates
    """
    return [
        {
            "date": "2025-01-01",
            "completed_items": 0.1,  # Very slow progress
            "completed_points": 0.5,
            "created_items": 0,
            "created_points": 0.0,
        }
    ]


@pytest.fixture
def zero_velocity_data():
    """Zero velocity data for no-progress edge case testing.

    Returns:
        list: Statistics with zero completed items
    """
    return [
        {
            "date": "2025-01-01",
            "completed_items": 0,
            "completed_points": 0.0,
            "created_items": 2,
            "created_points": 10.0,
        },
        {
            "date": "2025-01-08",
            "completed_items": 0,
            "completed_points": 0.0,
            "created_items": 3,
            "created_points": 15.0,
        },
    ]


@pytest.fixture
def increasing_velocity_data():
    """Statistics showing increasing velocity trend.

    Returns:
        list: Data with accelerating completion rates
    """
    return [
        {"date": "2025-01-01", "completed_items": 3, "completed_points": 15.0},
        {"date": "2025-01-08", "completed_items": 4, "completed_points": 20.0},
        {"date": "2025-01-15", "completed_items": 5, "completed_points": 25.0},
        {"date": "2025-01-22", "completed_items": 6, "completed_points": 30.0},
        {"date": "2025-01-29", "completed_items": 7, "completed_points": 35.0},
        {"date": "2025-02-05", "completed_items": 8, "completed_points": 40.0},
        {"date": "2025-02-12", "completed_items": 9, "completed_points": 45.0},
        {"date": "2025-02-19", "completed_items": 10, "completed_points": 50.0},
        {"date": "2025-02-26", "completed_items": 11, "completed_points": 55.0},
        {"date": "2025-03-05", "completed_items": 12, "completed_points": 60.0},
    ]


@pytest.fixture
def decreasing_velocity_data():
    """Statistics showing decreasing velocity trend.

    Returns:
        list: Data with declining completion rates
    """
    return [
        {"date": "2025-01-01", "completed_items": 12, "completed_points": 60.0},
        {"date": "2025-01-08", "completed_items": 11, "completed_points": 55.0},
        {"date": "2025-01-15", "completed_items": 10, "completed_points": 50.0},
        {"date": "2025-01-22", "completed_items": 9, "completed_points": 45.0},
        {"date": "2025-01-29", "completed_items": 8, "completed_points": 40.0},
        {"date": "2025-02-05", "completed_items": 7, "completed_points": 35.0},
        {"date": "2025-02-12", "completed_items": 6, "completed_points": 30.0},
        {"date": "2025-02-19", "completed_items": 5, "completed_points": 25.0},
        {"date": "2025-02-26", "completed_items": 4, "completed_points": 20.0},
        {"date": "2025-03-05", "completed_items": 3, "completed_points": 15.0},
    ]


@pytest.fixture
def stable_velocity_data():
    """Statistics showing stable velocity trend.

    Returns:
        list: Data with consistent completion rates (±10% variation)
    """
    return [
        {"date": "2025-01-01", "completed_items": 6, "completed_points": 30.0},
        {"date": "2025-01-08", "completed_items": 6, "completed_points": 30.0},
        {"date": "2025-01-15", "completed_items": 7, "completed_points": 35.0},
        {"date": "2025-01-22", "completed_items": 6, "completed_points": 30.0},
        {"date": "2025-01-29", "completed_items": 6, "completed_points": 30.0},
        {"date": "2025-02-05", "completed_items": 7, "completed_points": 35.0},
        {"date": "2025-02-12", "completed_items": 6, "completed_points": 30.0},
        {"date": "2025-02-19", "completed_items": 6, "completed_points": 30.0},
        {"date": "2025-02-26", "completed_items": 7, "completed_points": 35.0},
        {"date": "2025-03-05", "completed_items": 6, "completed_points": 30.0},
    ]


@pytest.fixture
def past_deadline_settings():
    """Settings with deadline in the past for edge case testing.

    Returns:
        dict: Settings with past deadline date
    """
    return {
        "pert_factor": 1.5,
        "deadline": "2024-01-01",  # Past deadline
        "estimated_total_items": 100,
        "estimated_total_points": 500.0,
        "data_points_count": 10,
        "forecast_max_days": 730,
        "pessimistic_multiplier_cap": 5,
    }


@pytest.fixture
def no_deadline_settings():
    """Settings without deadline for edge case testing.

    Returns:
        dict: Settings with None deadline
    """
    return {
        "pert_factor": 1.5,
        "deadline": None,
        "estimated_total_items": 100,
        "estimated_total_points": 500.0,
        "data_points_count": 10,
        "forecast_max_days": 730,
        "pessimistic_multiplier_cap": 5,
    }


@pytest.fixture
def extreme_pert_factor_settings():
    """Settings with very large PERT factor for edge case testing.

    Returns:
        dict: Settings with PERT factor of 10.0
    """
    return {
        "pert_factor": 10.0,  # Very wide confidence window
        "deadline": "2025-12-31",
        "estimated_total_items": 100,
        "estimated_total_points": 500.0,
        "data_points_count": 10,
        "forecast_max_days": 730,
        "pessimistic_multiplier_cap": 5,
    }


@pytest.fixture
def completion_exceeds_100_data():
    """Statistics and settings where completion exceeds 100% (scope decreased).

    Returns:
        tuple: (statistics, settings) where 110 items completed out of 100 total
    """
    statistics = [
        {"date": "2025-01-01", "completed_items": 110, "completed_points": 550.0},
    ]
    settings = {
        "pert_factor": 1.5,
        "deadline": "2025-12-31",
        "estimated_total_items": 100,
        "estimated_total_points": 500.0,
        "data_points_count": 10,
        "forecast_max_days": 730,
        "pessimistic_multiplier_cap": 5,
    }
    return statistics, settings
