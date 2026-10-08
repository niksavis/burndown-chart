from datetime import datetime, timedelta

import pandas as pd


def generate_realistic_sample_data():

    end_date = datetime.now()
    start_date = end_date - timedelta(days=12 * 7)

    dates = []
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5:
            dates.append(current_date)
        current_date += timedelta(days=1)

    n_dates = len(dates)

    base_items = 3
    base_points = 30

    base_created_items = 2
    base_created_points = 20

    completed_items = []
    completed_points = []
    created_items = []
    created_points = []

    for i in range(n_dates):
        progress_factor = 1.0 + (i / n_dates) * 0.5

        day_of_week = dates[i].weekday()
        day_factor = 0.8 + (1.4 - abs(day_of_week - 2) * 0.15)

        random_factor = 0.5 + (1.0 * (i % 3)) if i % 10 < 8 else 0

        day_items = max(
            0, round(base_items * progress_factor * day_factor * random_factor)
        )

        points_per_item = base_points / base_items * (0.8 + random_factor * 0.4)
        day_points = max(0, round(day_items * points_per_item))

        completed_items.append(day_items)
        completed_points.append(day_points)

        project_phase = i / n_dates
        scope_creep_factor = 1.2 if project_phase < 0.7 else 0.6

        scope_spike = 3 if i % 14 == 0 else 1

        day_created_items = max(
            0,
            round(
                base_created_items * scope_creep_factor * scope_spike * random_factor
            ),
        )

        created_points_per_item = (
            base_created_points / base_created_items * (0.9 + random_factor * 0.3)
        )
        day_created_points = max(0, round(day_created_items * created_points_per_item))

        created_items.append(day_created_items)
        created_points.append(day_created_points)

    sample_df = pd.DataFrame(
        {
            "date": [d.strftime("%Y-%m-%d") for d in dates],
            "completed_items": completed_items,
            "completed_points": completed_points,
            "created_items": created_items,
            "created_points": created_points,
        }
    )

    return sample_df


def read_and_clean_data(df):

    required_columns = ["date", "completed_items", "completed_points"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in data")

    if "created_items" not in df.columns:
        df["created_items"] = 0
    if "created_points" not in df.columns:
        df["created_points"] = 0

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    df = df.dropna(subset=["date"])

    numeric_columns = [
        "completed_items",
        "completed_points",
        "created_items",
        "created_points",
    ]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df = df.sort_values("date", ascending=True)

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    valid_columns = required_columns + ["created_items", "created_points"]

    existing_columns = [col for col in valid_columns if col in df.columns]
    df = df[existing_columns]

    return df
