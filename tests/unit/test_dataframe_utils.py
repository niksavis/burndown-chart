from unittest.mock import patch

import pandas as pd
import pytest

from utils.dataframe_utils import (
    df_to_dict,
    df_to_hashable,
    ensure_dataframe,
    safe_dataframe_operation,
)


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})


def test_df_to_dict(sample_dataframe):
    records = df_to_dict(sample_dataframe)
    assert isinstance(records, list)
    assert len(records) == 3
    assert records[0] == {"a": 1, "b": "x"}

    dict_result = df_to_dict(sample_dataframe, orient="dict")
    assert isinstance(dict_result, dict)
    assert "a" in dict_result
    assert "b" in dict_result

    assert df_to_dict("not a dataframe") == "not a dataframe"  # type: ignore[arg-type]

    with patch("pandas.DataFrame.to_dict", side_effect=Exception("Conversion error")):
        result = df_to_dict(sample_dataframe)
        assert isinstance(result, list) or isinstance(result, dict)


def test_df_to_hashable(sample_dataframe):
    result = df_to_hashable(sample_dataframe)
    assert isinstance(result, str)
    assert result.startswith("DataFrame:")

    assert df_to_hashable(sample_dataframe) == result

    different_df = pd.DataFrame({"a": [4, 5, 6], "b": ["p", "q", "r"]})
    assert df_to_hashable(different_df) != result

    assert isinstance(df_to_hashable("not a dataframe"), str)  # type: ignore[arg-type]

    with patch("pandas.DataFrame.to_json", side_effect=Exception("to_json failed")):
        result = df_to_hashable(sample_dataframe)
        assert isinstance(result, str)
        assert result.startswith("DataFrame:")

    with (
        patch("pandas.DataFrame.to_json", side_effect=Exception("to_json failed")),
        patch("pandas.DataFrame.values", side_effect=Exception("values failed")),
    ):
        result = df_to_hashable(sample_dataframe)
        assert isinstance(result, str)
        assert result.startswith("DataFrame:")


def test_ensure_dataframe():
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    result = ensure_dataframe(df)
    assert isinstance(result, pd.DataFrame)
    assert result.equals(df)

    list_data = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
    result = ensure_dataframe(list_data)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert set(result.columns) == {"a", "b"}

    dict_data = {"a": [1, 2], "b": ["x", "y"]}
    result = ensure_dataframe(dict_data)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert set(result.columns) == {"a", "b"}

    result = ensure_dataframe("not convertible")  # type: ignore[arg-type]
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_safe_dataframe_operation(sample_dataframe):

    def sum_column_a(df):
        return df["a"].sum()

    result = safe_dataframe_operation(sample_dataframe, sum_column_a)
    assert result == 6

    result = safe_dataframe_operation(None, sum_column_a, fallback="fallback")  # type: ignore[arg-type]
    assert result == "fallback"

    empty_df = pd.DataFrame()
    result = safe_dataframe_operation(empty_df, sum_column_a, fallback=0)
    assert result == 0

    def failing_operation(df):
        raise ValueError("Operation failed")

    result = safe_dataframe_operation(
        sample_dataframe, failing_operation, fallback="error handled"
    )
    assert result == "error handled"

    def multiply_column(df, column, factor=1):
        return df[column].sum() * factor

    result = safe_dataframe_operation(
        sample_dataframe, multiply_column, 0, "a", factor=2
    )
    assert result == 12
