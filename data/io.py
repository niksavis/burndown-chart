"""
Input/output functions for data handling.
"""

import pandas as pd
import io
import base64
from datetime import datetime


def parse_csv_content(content, filename):
    """Parse CSV content from upload component."""
    _, content_string = content.split(",")
    decoded = base64.b64decode(content_string)

    try:
        # First try with semicolon separator
        df = pd.read_csv(io.StringIO(decoded.decode("utf-8")), sep=";")

        # If we don't have the expected columns, try comma separator
        if not all(
            col in df.columns for col in ["date", "completed_items", "completed_points"]
        ):
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))

        # Add scope tracking columns if they don't exist
        for col in ["created_items", "created_points"]:
            if col not in df.columns:
                df[col] = 0

        # Ensure date format is consistent
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

        # Convert to list of dictionaries for storage
        records = df.to_dict("records")

        return {"data": records, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"error": str(e)}


def dataframe_to_csv(df):
    """Convert DataFrame to CSV string."""
    return df.to_csv(index=False, sep=";")


def prepare_statistics_for_export(statistics_data):
    """Prepare statistics data for export."""
    if (
        not statistics_data
        or "data" not in statistics_data
        or not statistics_data["data"]
    ):
        # Return empty dataframe with all required columns
        return pd.DataFrame(
            columns=[
                "date",
                "completed_items",
                "completed_points",
                "created_items",
                "created_points",
            ]
        )

    # Convert to DataFrame
    df = pd.DataFrame(statistics_data["data"])

    # Ensure all columns exist
    required_cols = [
        "date",
        "completed_items",
        "completed_points",
        "created_items",
        "created_points",
    ]
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0 if col != "date" else ""

    # Sort by date
    df = df.sort_values("date")

    return df[required_cols]  # Return only the required columns in the correct order
