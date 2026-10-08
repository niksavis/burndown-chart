from datetime import datetime, timedelta

import pytest


@pytest.fixture
def sample_statistics_data():

    base_date = datetime(2025, 1, 1)
    return [
        {
            "date": (base_date + timedelta(weeks=i)).strftime("%Y-%m-%d"),
            "completed_items": 5 + (i % 3),
            "completed_points": 25.0 + (i % 3) * 5.0,
            "created_items": 2,
            "created_points": 10.0,
        }
        for i in range(10)
    ]


@pytest.fixture
def sample_settings():

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

    return []


@pytest.fixture
def minimal_statistics_data():

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

    return [
        {
            "date": "2025-01-01",
            "completed_items": 0.1,
            "completed_points": 0.5,
            "created_items": 0,
            "created_points": 0.0,
        }
    ]


@pytest.fixture
def zero_velocity_data():

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

    return {
        "pert_factor": 1.5,
        "deadline": "2024-01-01",
        "estimated_total_items": 100,
        "estimated_total_points": 500.0,
        "data_points_count": 10,
        "forecast_max_days": 730,
        "pessimistic_multiplier_cap": 5,
    }


@pytest.fixture
def no_deadline_settings():

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

    return {
        "pert_factor": 10.0,
        "deadline": "2025-12-31",
        "estimated_total_items": 100,
        "estimated_total_points": 500.0,
        "data_points_count": 10,
        "forecast_max_days": 730,
        "pessimistic_multiplier_cap": 5,
    }


@pytest.fixture
def completion_exceeds_100_data():

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
