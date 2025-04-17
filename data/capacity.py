"""
Capacity Module

This module handles team capacity data and calculations for visualizing
and forecasting team workload against capacity.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class CapacityManager:
    """Manages team capacity data and calculations"""

    def __init__(self):
        self.capacity_hours_per_week = 0
        self.team_members = 0
        self.hours_per_point = 0
        self.hours_per_item = 0
        self.include_weekends = False
        self.capacity_data = pd.DataFrame()

    def set_capacity_parameters(
        self,
        team_members,
        hours_per_member,
        hours_per_point=None,
        hours_per_item=None,
        include_weekends=False,
    ):
        """
        Set the team capacity parameters

        Args:
            team_members: Number of team members
            hours_per_member: Available hours per team member per week
            hours_per_point: Estimated hours required per story point (optional)
            hours_per_item: Estimated hours required per work item (optional)
            include_weekends: Whether to include weekends in capacity calculations
        """
        self.team_members = team_members
        self.hours_per_point = hours_per_point
        self.hours_per_item = hours_per_item
        self.include_weekends = include_weekends
        self.capacity_hours_per_week = team_members * hours_per_member

    def calculate_capacity_from_stats(self, stats_df):
        """
        Calculate capacity metrics based on historical data

        Args:
            stats_df: DataFrame containing historical statistics with 'date', 'no_items', 'no_points'

        Returns:
            Dictionary with calculated capacity metrics
        """
        if stats_df.empty:
            return {
                "avg_hours_per_point": 0,
                "avg_hours_per_item": 0,
                "weekly_points_capacity": 0,
                "weekly_items_capacity": 0,
            }

        # Group by week
        stats_df["week"] = pd.to_datetime(stats_df["date"]).dt.isocalendar().week
        stats_df["year"] = pd.to_datetime(stats_df["date"]).dt.isocalendar().year
        weekly_stats = (
            stats_df.groupby(["year", "week"])
            .agg({"no_items": "sum", "no_points": "sum"})
            .reset_index()
        )

        # Calculate averages if we have capacity hours set
        if self.capacity_hours_per_week > 0:
            avg_weekly_items = weekly_stats["no_items"].mean()
            avg_weekly_points = weekly_stats["no_points"].mean()

            if avg_weekly_items > 0:
                self.hours_per_item = self.capacity_hours_per_week / avg_weekly_items

            if avg_weekly_points > 0:
                self.hours_per_point = self.capacity_hours_per_week / avg_weekly_points

        weekly_points_capacity = 0
        weekly_items_capacity = 0

        if self.hours_per_point and self.hours_per_point > 0:
            weekly_points_capacity = self.capacity_hours_per_week / self.hours_per_point

        if self.hours_per_item and self.hours_per_item > 0:
            weekly_items_capacity = self.capacity_hours_per_week / self.hours_per_item

        return {
            "avg_hours_per_point": self.hours_per_point,
            "avg_hours_per_item": self.hours_per_item,
            "weekly_points_capacity": weekly_points_capacity,
            "weekly_items_capacity": weekly_items_capacity,
        }

    def generate_capacity_forecast(
        self, start_date, end_date, total_items, total_points
    ):
        """
        Generate capacity forecast data for visualization

        Args:
            start_date: Start date for forecast
            end_date: End date for forecast
            total_items: Total number of items to complete
            total_points: Total number of points to complete

        Returns:
            DataFrame with capacity forecast data
        """
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date)

        if not self.include_weekends:
            # Filter out weekends (0=Monday, 6=Sunday)
            date_range = date_range[~date_range.dayofweek.isin([5, 6])]

        # Initialize capacity data
        capacity_data = pd.DataFrame(
            {
                "date": date_range,
                "day_of_week": date_range.dayofweek,
                "week_number": date_range.isocalendar().week,
                "capacity_hours": self.capacity_hours_per_week
                / 5,  # Daily capacity (5 working days)
            }
        )

        # Adjust for weekends if included
        if self.include_weekends:
            capacity_data["capacity_hours"] = (
                self.capacity_hours_per_week / 7
            )  # Daily capacity (7 days including weekends)

        # Calculate cumulative capacity
        capacity_data["cumulative_capacity_hours"] = capacity_data[
            "capacity_hours"
        ].cumsum()

        # Calculate items and points capacity if hours per item/point is set
        if self.hours_per_item and self.hours_per_item > 0:
            capacity_data["items_capacity"] = (
                capacity_data["capacity_hours"] / self.hours_per_item
            )
            capacity_data["cumulative_items_capacity"] = capacity_data[
                "items_capacity"
            ].cumsum()
        else:
            capacity_data["items_capacity"] = 0
            capacity_data["cumulative_items_capacity"] = 0

        if self.hours_per_point and self.hours_per_point > 0:
            capacity_data["points_capacity"] = (
                capacity_data["capacity_hours"] / self.hours_per_point
            )
            capacity_data["cumulative_points_capacity"] = capacity_data[
                "points_capacity"
            ].cumsum()
        else:
            capacity_data["points_capacity"] = 0
            capacity_data["cumulative_points_capacity"] = 0

        # Calculate projected completion date based on capacity
        items_completion_date = None
        points_completion_date = None

        if self.hours_per_item and self.hours_per_item > 0:
            total_hours_items = total_items * self.hours_per_item
            items_days = total_hours_items / (self.capacity_hours_per_week / 5)
            items_completion_date = start_date + timedelta(days=items_days)

        if self.hours_per_point and self.hours_per_point > 0:
            total_hours_points = total_points * self.hours_per_point
            points_days = total_hours_points / (self.capacity_hours_per_week / 5)
            points_completion_date = start_date + timedelta(days=points_days)

        self.capacity_data = capacity_data

        return {
            "capacity_data": capacity_data,
            "items_completion_date": items_completion_date,
            "points_completion_date": points_completion_date,
        }
