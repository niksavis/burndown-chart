"""
Unit tests specifically for the hashable conversion functions in the caching module.
"""

import pytest
import pandas as pd
from unittest.mock import patch

from caching import _make_hashable


@pytest.fixture
def simple_dataframe():
    """Create a simple DataFrame for testing hashable conversion."""
    return pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})


@pytest.fixture
def complex_dataframe():
    """Create a more complex DataFrame for testing hashable conversion."""
    return pd.DataFrame(
        {
            "a": [1, 2, 3],
            "b": ["x", "y", "z"],
            "c": [
                pd.Timestamp("2025-01-01"),
                pd.Timestamp("2025-01-02"),
                pd.Timestamp("2025-01-03"),
            ],
            "d": [1.1, 2.2, 3.3],
            "e": [True, False, True],
        }
    )


@pytest.fixture
def nested_dict():
    """Create a nested dictionary for testing hashable conversion."""
    return {"a": 1, "b": "string", "c": {"nested": "value", "list": [1, 2, 3]}}


def test_make_hashable_with_primitives():
    """Test that _make_hashable correctly handles primitive types."""
    # These are already hashable, so they should be returned as is
    assert _make_hashable(5) == 5
    assert _make_hashable("string") == "string"
    assert _make_hashable(3.14) == 3.14
    assert _make_hashable(True) is True
    assert _make_hashable(None) is None
    assert _make_hashable((1, 2, 3)) == (1, 2, 3)


def test_make_hashable_with_dataframe(simple_dataframe):
    """Test that _make_hashable correctly converts a DataFrame to a hashable representation."""
    result = _make_hashable(simple_dataframe)

    # The result should be a string starting with 'DataFrame:'
    assert isinstance(result, str)
    assert result.startswith("DataFrame:")

    # Converting the same DataFrame again should give the same result
    assert _make_hashable(simple_dataframe) == result

    # Different DataFrames should give different results
    different_df = pd.DataFrame({"a": [4, 5, 6], "b": ["p", "q", "r"]})
    assert _make_hashable(different_df) != result


def test_make_hashable_with_complex_dataframe(complex_dataframe):
    """Test that _make_hashable correctly handles a complex DataFrame."""
    result = _make_hashable(complex_dataframe)

    # The result should be a string starting with 'DataFrame:'
    assert isinstance(result, str)
    assert result.startswith("DataFrame:")


def test_make_hashable_with_lists_and_dicts(nested_dict):
    """Test that _make_hashable correctly converts lists and dictionaries."""
    # Test with a list
    list_result = _make_hashable([1, 2, 3])
    assert isinstance(list_result, str)
    assert list_result.startswith("list:")

    # Test with a dictionary
    dict_result = _make_hashable({"a": 1, "b": 2})
    assert isinstance(dict_result, str)
    assert dict_result.startswith("dict:")

    # Test with a nested dictionary
    nested_result = _make_hashable(nested_dict)
    assert isinstance(nested_result, str)
    assert nested_result.startswith("dict:")

    # Same dictionaries should produce the same hash
    assert _make_hashable(nested_dict) == nested_result

    # Different order of keys should produce the same hash
    reordered_dict = {
        "b": "string",
        "a": 1,
        "c": {"list": [1, 2, 3], "nested": "value"},
    }
    assert _make_hashable(reordered_dict) == nested_result


def test_make_hashable_fallback_mechanisms():
    """Test the fallback mechanisms in _make_hashable for DataFrames."""
    df = pd.DataFrame({"a": [1, 2, 3]})

    # Test the to_json fallback
    with patch("pandas.DataFrame.to_json", side_effect=Exception("to_json failed")):
        result = _make_hashable(df)
        assert isinstance(result, str)
        assert result.startswith("DataFrame:")

    # Test both fallbacks failing
    with (
        patch("pandas.DataFrame.to_json", side_effect=Exception("to_json failed")),
        patch("pandas.DataFrame.values", side_effect=Exception("values failed")),
    ):
        result = _make_hashable(df)
        assert isinstance(result, str)
        assert result.startswith("DataFrame:")


def test_make_hashable_with_non_serializable():
    """Test _make_hashable with non-JSON-serializable objects."""

    # Create an object that cannot be JSON serialized
    class NonSerializable:
        def __init__(self):
            self.value = "test"

    obj = NonSerializable()

    # Test with a dictionary containing a non-serializable object
    non_serializable_dict = {"a": obj}
    result = _make_hashable(non_serializable_dict)

    # Should fall back to string representation
    assert isinstance(result, str)

    # Test with a list containing a non-serializable object
    non_serializable_list = [1, obj, 3]
    result = _make_hashable(non_serializable_list)

    # Should fall back to string representation
    assert isinstance(result, str)
