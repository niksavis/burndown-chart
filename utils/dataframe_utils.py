"""
DataFrame Utilities Module

This module provides common utilities for handling pandas DataFrames
across the application.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import hashlib
import logging
from typing import Any, Dict, List, Union, Literal, Hashable, Callable

# Third-party library imports
import pandas as pd

#######################################################################
# LOGGING
#######################################################################
logger = logging.getLogger("burndown_chart")

#######################################################################
# DATAFRAME CONVERSION UTILITIES
#######################################################################


def df_to_dict(
    df: pd.DataFrame,
    orient: Literal[
        "dict", "list", "series", "split", "records", "index", "tight"
    ] = "records",
) -> Union[Dict[Hashable, Any], List[Dict[Hashable, Any]]]:
    """
    Convert a DataFrame to a dictionary with proper error handling.

    Args:
        df: The DataFrame to convert
        orient: Orientation for the resulting dictionary (default: "records")
            See pandas.DataFrame.to_dict documentation for options

    Returns:
        Dictionary representation of the DataFrame, type depends on the orient parameter
    """
    if not isinstance(df, pd.DataFrame):
        logger.warning(f"Input is not a DataFrame: {type(df)}. Returning as is.")
        return df

    try:
        return df.to_dict(orient=orient)
    except Exception as e:
        logger.error(f"Error converting DataFrame to dict: {str(e)}")
        # Fallback to simpler conversion
        try:
            return df.to_dict()
        except Exception:
            logger.error("Failed to convert DataFrame to dict. Returning empty list.")
            return []


def df_to_hashable(df: pd.DataFrame) -> str:
    """
    Convert a DataFrame to a hashable string representation.

    This is useful for caching functions that take DataFrames as arguments.

    Args:
        df: The DataFrame to convert to a hashable representation

    Returns:
        A hashable string representation of the DataFrame
    """
    if not isinstance(df, pd.DataFrame):
        logger.warning(f"Input is not a DataFrame: {type(df)}. Returning as string.")
        return str(df)

    try:
        # Use to_json for a stable string representation
        return f"DataFrame:{hashlib.md5(df.to_json().encode()).hexdigest()}"
    except Exception as e:
        logger.debug(f"Failed to hash DataFrame with to_json: {str(e)}")
        try:
            # Alternative approach using values
            return f"DataFrame:{hashlib.md5(str(df.values).encode()).hexdigest()}"
        except Exception:
            # Last fallback if all else fails
            return f"DataFrame:{id(df)}"


def ensure_dataframe(
    data: Union[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any]],
) -> pd.DataFrame:
    """
    Ensure data is a DataFrame, converting from list or dict if necessary.

    Args:
        data: Data to convert to DataFrame

    Returns:
        Data as a pandas DataFrame
    """
    if isinstance(data, pd.DataFrame):
        return data

    try:
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Failed to convert data to DataFrame: {str(e)}")
        # Return empty DataFrame as fallback
        return pd.DataFrame()


def safe_dataframe_operation(
    df: pd.DataFrame, operation: Callable, fallback: Any = None, *args, **kwargs
) -> Any:
    """
    Safely perform an operation on a DataFrame with proper error handling.

    Args:
        df: DataFrame to operate on
        operation: Function to call on the DataFrame
        fallback: Value to return if operation fails
        *args, **kwargs: Additional arguments to pass to the operation

    Returns:
        Result of the operation or fallback value if failed
    """
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
