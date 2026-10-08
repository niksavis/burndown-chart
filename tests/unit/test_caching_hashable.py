from unittest.mock import patch

import pandas as pd
import pytest

from utils.caching import _make_hashable


@pytest.fixture
def simple_dataframe():
    return pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})


@pytest.fixture
def complex_dataframe():
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
    return {"a": 1, "b": "string", "c": {"nested": "value", "list": [1, 2, 3]}}


def test_make_hashable_with_primitives():
    assert _make_hashable(5) == 5
    assert _make_hashable("string") == "string"
    assert _make_hashable(3.14) == 3.14
    assert _make_hashable(True) is True
    assert _make_hashable(None) is None
    assert _make_hashable((1, 2, 3)) == (1, 2, 3)


def test_make_hashable_with_dataframe(simple_dataframe):
    result = _make_hashable(simple_dataframe)

    assert isinstance(result, str)
    assert result.startswith("DataFrame:")

    assert _make_hashable(simple_dataframe) == result

    different_df = pd.DataFrame({"a": [4, 5, 6], "b": ["p", "q", "r"]})
    assert _make_hashable(different_df) != result


def test_make_hashable_with_complex_dataframe(complex_dataframe):
    result = _make_hashable(complex_dataframe)

    assert isinstance(result, str)
    assert result.startswith("DataFrame:")


def test_make_hashable_with_lists_and_dicts(nested_dict):
    list_result = _make_hashable([1, 2, 3])
    assert isinstance(list_result, str)
    assert list_result.startswith("list:")

    dict_result = _make_hashable({"a": 1, "b": 2})
    assert isinstance(dict_result, str)
    assert dict_result.startswith("dict:")

    nested_result = _make_hashable(nested_dict)
    assert isinstance(nested_result, str)
    assert nested_result.startswith("dict:")

    assert _make_hashable(nested_dict) == nested_result

    reordered_dict = {
        "b": "string",
        "a": 1,
        "c": {"list": [1, 2, 3], "nested": "value"},
    }
    assert _make_hashable(reordered_dict) == nested_result


def test_make_hashable_fallback_mechanisms():
    df = pd.DataFrame({"a": [1, 2, 3]})

    with patch("pandas.DataFrame.to_json", side_effect=Exception("to_json failed")):
        result = _make_hashable(df)
        assert isinstance(result, str)
        assert result.startswith("DataFrame:")

    with (
        patch("pandas.DataFrame.to_json", side_effect=Exception("to_json failed")),
        patch("pandas.DataFrame.values", side_effect=Exception("values failed")),
    ):
        result = _make_hashable(df)
        assert isinstance(result, str)
        assert result.startswith("DataFrame:")


def test_make_hashable_with_non_serializable():

    class NonSerializable:
        def __init__(self):
            self.value = "test"

    obj = NonSerializable()

    non_serializable_dict = {"a": obj}
    result = _make_hashable(non_serializable_dict)

    assert isinstance(result, str)

    non_serializable_list = [1, obj, 3]
    result = _make_hashable(non_serializable_list)

    assert isinstance(result, str)
