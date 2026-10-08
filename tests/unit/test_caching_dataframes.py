import time
from unittest.mock import patch

import pandas as pd
import pytest

from utils.caching import clear_cache, memoize


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame(
        {"date": pd.date_range(start="2025-01-01", periods=3), "value": [1, 2, 3]}
    )


@pytest.fixture
def another_dataframe():
    return pd.DataFrame(
        {"date": pd.date_range(start="2025-01-01", periods=3), "value": [4, 5, 6]}
    )


def dataframe_function(df, multiplier=1):
    if isinstance(df, pd.DataFrame) and "value" in df.columns:
        return df["value"].sum() * multiplier
    return 0


cached_test_function = memoize(max_age_seconds=10)(dataframe_function)


def test_memoize_with_dataframe(sample_dataframe):
    clear_cache()

    result1 = cached_test_function(sample_dataframe)
    assert result1 == 6

    identical_df = pd.DataFrame(
        {"date": pd.date_range(start="2025-01-01", periods=3), "value": [1, 2, 3]}
    )

    with patch("pandas.core.series.Series.sum", return_value=100):
        result2 = cached_test_function(identical_df)
        assert result2 == 6

    different_df = pd.DataFrame(
        {"date": pd.date_range(start="2025-01-01", periods=3), "value": [4, 5, 6]}
    )

    result3 = cached_test_function(different_df)
    assert result3 == 15
    assert result3 != result1


def test_memoize_with_dataframe_kwargs(sample_dataframe):
    clear_cache()

    result1 = cached_test_function(sample_dataframe, multiplier=2)
    assert result1 == 12

    result2 = cached_test_function(sample_dataframe, multiplier=3)
    assert result2 == 18
    assert result2 != result1


def test_memoize_cache_expiration(sample_dataframe):
    clear_cache()

    result1 = cached_test_function(sample_dataframe)
    assert result1 == 6

    with patch("time.time", return_value=time.time() + 11):
        with patch("pandas.core.series.Series.sum", return_value=10):
            result2 = cached_test_function(sample_dataframe)
            assert result2 == 10
            assert result2 != result1


def test_memoize_with_different_dataframe_same_values(
    sample_dataframe, another_dataframe
):
    clear_cache()

    result1 = cached_test_function(sample_dataframe)
    assert result1 == 6

    result2 = cached_test_function(another_dataframe)
    assert result2 == 15
    assert result2 != result1
