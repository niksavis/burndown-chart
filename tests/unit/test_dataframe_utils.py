"""
Unit tests for DataFrame utilities module.
"""

import pytest
import pandas as pd
from unittest.mock import patch

from utils.dataframe_utils import (
    df_to_dict,
    df_to_hashable,
    ensure_dataframe,
    safe_dataframe_operation,
)


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})


def test_df_to_dict(sample_dataframe):
    """Test converting DataFrame to dictionary."""
    # Test with records orient (default)
    records = df_to_dict(sample_dataframe)
    assert isinstance(records, list)
    assert len(records) == 3
    assert records[0] == {"a": 1, "b": "x"}

    # Test with different orient
    dict_result = df_to_dict(sample_dataframe, orient="dict")
    assert isinstance(dict_result, dict)
    assert "a" in dict_result
    assert "b" in dict_result

    # Test with non-DataFrame input
    assert df_to_dict("not a dataframe") == "not a dataframe"

    # Test error handling
    with patch("pandas.DataFrame.to_dict", side_effect=Exception("Conversion error")):
        # Should use fallback mechanism
        result = df_to_dict(sample_dataframe)
        assert isinstance(result, list) or isinstance(result, dict)


def test_df_to_hashable(sample_dataframe):
    """Test converting DataFrame to hashable representation."""
    # Basic functionality
    result = df_to_hashable(sample_dataframe)
    assert isinstance(result, str)
    assert result.startswith("DataFrame:")

    # Same DataFrame should produce same hash
    assert df_to_hashable(sample_dataframe) == result

    # Different DataFrame should produce different hash
    different_df = pd.DataFrame({"a": [4, 5, 6], "b": ["p", "q", "r"]})
    assert df_to_hashable(different_df) != result

    # Test with non-DataFrame input
    assert isinstance(df_to_hashable("not a dataframe"), str)

    # Test fallback mechanisms
    with patch("pandas.DataFrame.to_json", side_effect=Exception("to_json failed")):
        # Should use values fallback
        result = df_to_hashable(sample_dataframe)
        assert isinstance(result, str)
        assert result.startswith("DataFrame:")

    # Test all fallbacks failing
    with (
        patch("pandas.DataFrame.to_json", side_effect=Exception("to_json failed")),
        patch("pandas.DataFrame.values", side_effect=Exception("values failed")),
    ):
        # Should use id fallback
        result = df_to_hashable(sample_dataframe)
        assert isinstance(result, str)
        assert result.startswith("DataFrame:")


def test_ensure_dataframe():
    """Test ensuring data is in DataFrame format."""
    # Test with existing DataFrame
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    result = ensure_dataframe(df)
    assert isinstance(result, pd.DataFrame)
    assert result.equals(df)

    # Test with list of dicts
    list_data = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
    result = ensure_dataframe(list_data)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert set(result.columns) == {"a", "b"}

    # Test with single dict
    dict_data = {"a": [1, 2], "b": ["x", "y"]}
    result = ensure_dataframe(dict_data)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert set(result.columns) == {"a", "b"}

    # Test with invalid input
    result = ensure_dataframe("not convertible")
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_safe_dataframe_operation(sample_dataframe):
    """Test safely performing operations on DataFrames."""

    # Test with successful operation
    def sum_column_a(df):
        return df["a"].sum()

    result = safe_dataframe_operation(sample_dataframe, sum_column_a)
    assert result == 6  # 1 + 2 + 3

    # Test with fallback value
    result = safe_dataframe_operation(None, sum_column_a, fallback="fallback")
    assert result == "fallback"

    # Test with empty DataFrame
    empty_df = pd.DataFrame()
    result = safe_dataframe_operation(empty_df, sum_column_a, fallback=0)
    assert result == 0

    # Test with operation that fails
    def failing_operation(df):
        raise ValueError("Operation failed")

    result = safe_dataframe_operation(
        sample_dataframe, failing_operation, fallback="error handled"
    )
    assert result == "error handled"

    # Test with args and kwargs
    def multiply_column(df, column, factor=1):
        return df[column].sum() * factor

    result = safe_dataframe_operation(
        sample_dataframe, multiply_column, 0, "a", factor=2
    )
    assert result == 12  # (1 + 2 + 3) * 2
