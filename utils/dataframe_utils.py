import hashlib
import logging
from collections.abc import Callable
from typing import Any, Literal

import pandas as pd

logger = logging.getLogger("burndown_chart")


def df_to_dict(
    df: pd.DataFrame,
    orient: Literal[
        "dict", "list", "series", "split", "records", "index", "tight"
    ] = "records",
) -> Any:

    if not isinstance(df, pd.DataFrame):
        logger.warning(f"Input is not a DataFrame: {type(df)}. Returning as is.")
        return df

    try:
        return df.to_dict(orient=orient)
    except Exception as e:
        logger.error(f"Error converting DataFrame to dict: {str(e)}")
        try:
            return df.to_dict()
        except Exception:
            logger.error("Failed to convert DataFrame to dict. Returning empty list.")
            return []


def df_to_hashable(df: pd.DataFrame) -> str:

    if not isinstance(df, pd.DataFrame):
        logger.warning(f"Input is not a DataFrame: {type(df)}. Returning as string.")
        return str(df)

    try:
        json_str = df.to_json(date_format="iso").encode()
        return f"DataFrame:{hashlib.md5(json_str).hexdigest()}"
    except Exception as e:
        logger.debug(f"Failed to hash DataFrame with to_json: {str(e)}")
        try:
            return f"DataFrame:{hashlib.md5(str(df.values).encode()).hexdigest()}"
        except Exception:
            return f"DataFrame:{id(df)}"


def ensure_dataframe(
    data: pd.DataFrame | list[dict[str, Any]] | dict[str, Any],
) -> pd.DataFrame:

    if isinstance(data, pd.DataFrame):
        return data

    try:
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Failed to convert data to DataFrame: {str(e)}")
        return pd.DataFrame()


def safe_dataframe_operation(
    df: pd.DataFrame, operation: Callable, fallback: Any = None, *args, **kwargs
) -> Any:

    if not isinstance(df, pd.DataFrame):
        logger.warning(f"Input is not a DataFrame: {type(df)}. Returning fallback.")
        return fallback

    if df.empty:
        logger.debug("DataFrame is empty. Returning fallback.")
        return fallback

    try:
        return operation(df, *args, **kwargs)
    except Exception as e:
        logger.error(f"DataFrame operation failed: {str(e)}")
        return fallback
