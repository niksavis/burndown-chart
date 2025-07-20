"""
Unit tests for the caching module with focus on handling pandas DataFrames.
"""

import pytest
import pandas as pd
from unittest.mock import patch
import time

from caching import memoize, clear_cache


# Test data fixtures
@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame(
        {"date": pd.date_range(start="2025-01-01", periods=3), "value": [1, 2, 3]}
    )


@pytest.fixture
def another_dataframe():
    """Create a different DataFrame for testing."""
    return pd.DataFrame(
        {"date": pd.date_range(start="2025-01-01", periods=3), "value": [4, 5, 6]}
    )


# Regular function for caching tests - renamed to avoid pytest confusion
def dataframe_function(df, multiplier=1):
    """Function that takes a DataFrame and returns the sum of values multiplied."""
    if isinstance(df, pd.DataFrame) and "value" in df.columns:
        return df["value"].sum() * multiplier
    return 0


# Apply the decorator separately to avoid pytest confusion
cached_test_function = memoize(max_age_seconds=10)(dataframe_function)


def test_memoize_with_dataframe(sample_dataframe):
    """Test that the memoize decorator works with DataFrames."""
    # Clear cache first to ensure clean test
    clear_cache()

    # First call should calculate and cache
    result1 = cached_test_function(sample_dataframe)
    assert result1 == 6  # sum of [1, 2, 3]

    # Create a new DataFrame with identical data
    identical_df = pd.DataFrame(
        {"date": pd.date_range(start="2025-01-01", periods=3), "value": [1, 2, 3]}
    )

    # Second call with identical data should use cache
    with patch(
        "pandas.core.series.Series.sum", return_value=100
    ):  # This won't be called if cache works
        result2 = cached_test_function(identical_df)
        assert result2 == 6  # Should return cached result without calling sum

    # Test with different dataframe
    different_df = pd.DataFrame(
        {"date": pd.date_range(start="2025-01-01", periods=3), "value": [4, 5, 6]}
    )

    # Call with different data should calculate new result
    result3 = cached_test_function(different_df)
    assert result3 == 15  # sum of [4, 5, 6]
    assert result3 != result1  # Different from first result


def test_memoize_with_dataframe_kwargs(sample_dataframe):
    """Test that the memoize decorator works with DataFrames and keyword arguments."""
    # Clear cache first to ensure clean test
    clear_cache()

    # Call with multiplier=2
    result1 = cached_test_function(sample_dataframe, multiplier=2)
    assert result1 == 12  # (1+2+3)*2

    # Call with same DataFrame but different multiplier
    result2 = cached_test_function(sample_dataframe, multiplier=3)
    assert result2 == 18  # (1+2+3)*3
    assert result2 != result1  # Different result due to different multiplier


def test_memoize_cache_expiration(sample_dataframe):
    """Test that cache entries expire after max_age_seconds."""
    # Clear cache first to ensure clean test
    clear_cache()

    # First call should calculate and cache
    result1 = cached_test_function(sample_dataframe)
    assert result1 == 6

    # Mock time.time to simulate passage of time
    with patch(
        "time.time", return_value=time.time() + 11
    ):  # 11 seconds later (> max_age of 10)
        # Call should recalculate since cache expired
        with patch(
            "pandas.core.series.Series.sum", return_value=10
        ):  # Mock sum for test
            result2 = cached_test_function(sample_dataframe)
            assert result2 == 10  # Using mocked sum result
            assert result2 != result1  # Different from cached result


def test_memoize_with_different_dataframe_same_values(
    sample_dataframe, another_dataframe
):
    """Test memoize with different DataFrames having different values."""
    # Clear cache first to ensure clean test
    clear_cache()

    # First call with sample_dataframe
    result1 = cached_test_function(sample_dataframe)
    assert result1 == 6

    # Second call with another_dataframe
    result2 = cached_test_function(another_dataframe)
    assert result2 == 15
    assert result2 != result1  # Different results
