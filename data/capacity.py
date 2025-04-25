"""
Capacity Module

This module handles team capacity data and calculations for visualizing
and forecasting team workload against capacity.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
from datetime import datetime, timedelta

# Third-party library imports
import pandas as pd

#######################################################################
# CLASSES
#######################################################################


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
            stats_df: DataFrame containing historical statistics with 'date', 'completed_items', 'completed_points'

        Returns:
            Dictionary with calculated capacity metrics
        """
        if stats_df.empty:
            return {
                "avg_hours_per_point": 0,
                "avg_hours_per_item": 0,
                "weekly_points_capacity": 0,
                "weekly_items_capacity": 0,
                "utilization_percentage": 0,
                "recent_trend_percentage": 0,
            }

        # Group by week
        stats_df["week"] = pd.to_datetime(stats_df["date"]).dt.isocalendar().week
        stats_df["year"] = pd.to_datetime(stats_df["date"]).dt.isocalendar().year
        weekly_stats = (
            stats_df.groupby(["year", "week"])
            .agg({"completed_items": "sum", "completed_points": "sum"})
            .reset_index()
        )

        # Calculate averages if we have capacity hours set and team members
        if self.capacity_hours_per_week > 0 and self.team_members > 0:
            avg_weekly_items = weekly_stats["completed_items"].mean()
            avg_weekly_points = weekly_stats["completed_points"].mean()

            # Calculate hours per item based on individual productivity
            # Instead of using total team capacity, calculate per-member productivity
            hours_per_member = self.capacity_hours_per_week / self.team_members

            if avg_weekly_items > 0:
                # Calculate individual productivity (hours per item per person)
                self.hours_per_item = hours_per_member / (
                    avg_weekly_items / self.team_members
                )

            if avg_weekly_points > 0:
                # Calculate individual productivity (hours per point per person)
                self.hours_per_point = hours_per_member / (
                    avg_weekly_points / self.team_members
                )

        weekly_points_capacity = 0
        weekly_items_capacity = 0

        if self.hours_per_point and self.hours_per_point > 0:
            weekly_points_capacity = self.capacity_hours_per_week / self.hours_per_point

        if self.hours_per_item and self.hours_per_item > 0:
            weekly_items_capacity = self.capacity_hours_per_week / self.hours_per_item

        # Calculate capacity utilization based on recent weeks (last 4 weeks)
        utilization_percentage = 0
        recent_trend_percentage = 0

        if len(weekly_stats) > 0 and self.capacity_hours_per_week > 0:
            # Sort by year and week to ensure proper ordering
            weekly_stats = weekly_stats.sort_values(["year", "week"])

            # Calculate estimated hours per week based on items and points
            if self.hours_per_item > 0:
                weekly_stats["estimated_hours_items"] = (
                    weekly_stats["completed_items"] * self.hours_per_item
                )
            else:
                weekly_stats["estimated_hours_items"] = 0

            if self.hours_per_point > 0:
                weekly_stats["estimated_hours_points"] = (
                    weekly_stats["completed_points"] * self.hours_per_point
                )
            else:
                weekly_stats["estimated_hours_points"] = 0

            # Use the max of the two as the estimated hours (more conservative approach)
            weekly_stats["estimated_hours"] = weekly_stats[
                ["estimated_hours_items", "estimated_hours_points"]
            ].max(axis=1)

            # Calculate utilization percentage based on the most recent 4 weeks or all available data
            recent_weeks = min(4, len(weekly_stats))
            recent_data = weekly_stats.tail(recent_weeks)

            avg_recent_hours = recent_data["estimated_hours"].mean()
            utilization_percentage = (
                avg_recent_hours / self.capacity_hours_per_week
            ) * 100

            # Calculate trend (comparing last 2 weeks with previous 2 weeks)
            if len(weekly_stats) >= 4:
                last_2_weeks = weekly_stats.tail(2)["estimated_hours"].mean()
                prev_2_weeks = weekly_stats.iloc[-4:-2]["estimated_hours"].mean()

                if prev_2_weeks > 0:
                    recent_trend_percentage = (
                        (last_2_weeks - prev_2_weeks) / prev_2_weeks
                    ) * 100
                else:
                    recent_trend_percentage = 0

        return {
            "avg_hours_per_point": self.hours_per_point,
            "avg_hours_per_item": self.hours_per_item,
            "weekly_points_capacity": weekly_points_capacity,
            "weekly_items_capacity": weekly_items_capacity,
            "utilization_percentage": utilization_percentage,
            "recent_trend_percentage": recent_trend_percentage,
        }

    def generate_capacity_forecast(
        self,
        start_date,
        end_date,
        remaining_items,
        remaining_points,
        burndown_forecast=None,
    ):
        """
        Generate capacity forecast data for visualization

        Args:
            start_date: Start date for forecast
            end_date: End date for forecast
            remaining_items: Number of items remaining to be completed
            remaining_points: Number of points remaining to be completed
            burndown_forecast: Optional dictionary with burndown forecast data to align forecasts

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
                "year": date_range.isocalendar().year,
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

        if self.hours_per_item and self.hours_per_item > 0 and remaining_items > 0:
            total_hours_items = remaining_items * self.hours_per_item
            items_days = total_hours_items / (self.capacity_hours_per_week / 5)
            items_completion_date = start_date + timedelta(days=items_days)

        if self.hours_per_point and self.hours_per_point > 0 and remaining_points > 0:
            total_hours_points = remaining_points * self.hours_per_point
            points_days = total_hours_points / (self.capacity_hours_per_week / 5)
            points_completion_date = start_date + timedelta(days=points_days)

        # Add forecasted capacity requirements for upcoming weeks
        # Group by week
        weekly_capacity = (
            capacity_data.groupby(["year", "week_number"])
            .agg(
                {
                    "date": "first",  # First day of the week
                    "capacity_hours": "sum",
                    "items_capacity": "sum",
                    "points_capacity": "sum",
                }
            )
            .reset_index()
        )

        # Calculate remaining work each week
        weekly_capacity["remaining_items"] = (
            remaining_items - weekly_capacity["items_capacity"].cumsum()
        )
        weekly_capacity["remaining_items"] = weekly_capacity["remaining_items"].clip(
            lower=0
        )

        weekly_capacity["remaining_points"] = (
            remaining_points - weekly_capacity["points_capacity"].cumsum()
        )
        weekly_capacity["remaining_points"] = weekly_capacity["remaining_points"].clip(
            lower=0
        )

        # If we have burndown forecast data, align the forecasts for consistent visualization
        if burndown_forecast is not None and isinstance(burndown_forecast, dict):
            # Use burndown completion dates if available
            if "items_completion_date" in burndown_forecast:
                items_completion_date = burndown_forecast["items_completion_date"]
            if "points_completion_date" in burndown_forecast:
                points_completion_date = burndown_forecast["points_completion_date"]

        # Calculate required hours based on actual completion forecast
        # This ensures the capacity forecast aligns with the burndown chart
        if items_completion_date:
            days_to_completion = (items_completion_date - start_date).days
            if days_to_completion > 0:
                weeks_to_completion = days_to_completion / 7
                for i, row in weekly_capacity.iterrows():
                    week_number = i + 1
                    if week_number <= len(weekly_capacity):
                        # Calculate progressive decrease in required hours as we approach completion
                        remaining_work_ratio = max(
                            0, 1 - (week_number / weeks_to_completion)
                        )
                        weekly_capacity.loc[i, "required_hours_items"] = (
                            (
                                (
                                    remaining_items
                                    * self.hours_per_item
                                    * remaining_work_ratio
                                )
                                / (weeks_to_completion - week_number + 1)
                            )
                            if week_number <= weeks_to_completion
                            else 0
                        )
        else:
            # Fallback to simple linear distribution if no completion date
            weeks_until_deadline = len(weekly_capacity)
            if weeks_until_deadline > 0:
                weekly_capacity["required_hours_items"] = (
                    weekly_capacity["remaining_items"].shift(1) * self.hours_per_item
                ) / weeks_until_deadline
                # Fill first week
                weekly_capacity.loc[0, "required_hours_items"] = (
                    remaining_items * self.hours_per_item
                ) / weeks_until_deadline

        # Same for points
        if points_completion_date:
            days_to_completion = (points_completion_date - start_date).days
            if days_to_completion > 0:
                weeks_to_completion = days_to_completion / 7
                for i, row in weekly_capacity.iterrows():
                    week_number = i + 1
                    if week_number <= len(weekly_capacity):
                        remaining_work_ratio = max(
                            0, 1 - (week_number / weeks_to_completion)
                        )
                        weekly_capacity.loc[i, "required_hours_points"] = (
                            (
                                (
                                    remaining_points
                                    * self.hours_per_point
                                    * remaining_work_ratio
                                )
                                / (weeks_to_completion - week_number + 1)
                            )
                            if week_number <= weeks_to_completion
                            else 0
                        )
        else:
            weeks_until_deadline = len(weekly_capacity)
            if weeks_until_deadline > 0:
                weekly_capacity["required_hours_points"] = (
                    weekly_capacity["remaining_points"].shift(1) * self.hours_per_point
                ) / weeks_until_deadline
                # Fill first week
                weekly_capacity.loc[0, "required_hours_points"] = (
                    remaining_points * self.hours_per_point
                ) / weeks_until_deadline

        # Handle NaN values
        weekly_capacity["required_hours_items"] = weekly_capacity[
            "required_hours_items"
        ].fillna(0)
        weekly_capacity["required_hours_points"] = weekly_capacity[
            "required_hours_points"
        ].fillna(0)

        # Use the max of the two as the required hours (more conservative approach)
        weekly_capacity["required_hours"] = weekly_capacity[
            ["required_hours_items", "required_hours_points"]
        ].max(axis=1)

        # Calculate capacity utilization percentage
        weekly_capacity["capacity_utilization"] = (
            weekly_capacity["required_hours"] / self.capacity_hours_per_week
        ) * 100

        self.capacity_data = capacity_data

        return {
            "capacity_data": capacity_data,
            "items_completion_date": items_completion_date,
            "points_completion_date": points_completion_date,
            "weekly_forecast": weekly_capacity,
        }

    def calculate_required_velocity(self, total_items, total_points, deadline):
        """
        Calculate required velocity to meet the deadline

        Args:
            total_items: Total items remaining
            total_points: Total points remaining
            deadline: Deadline date

        Returns:
            Dictionary with required velocity metrics
        """
        today = datetime.now()
        days_to_deadline = (deadline - today).days

        if days_to_deadline <= 0:
            return {
                "required_items_per_week": float("inf"),
                "required_points_per_week": float("inf"),
                "required_hours_per_week": float("inf"),
                "capacity_sufficient": False,
                "capacity_percentage_needed": 0,
            }

        weeks_to_deadline = days_to_deadline / 7

        required_items_per_week = total_items / weeks_to_deadline
        required_points_per_week = total_points / weeks_to_deadline

        # Calculate hours needed for items and points
        if self.hours_per_item and self.hours_per_item > 0:
            hours_for_items = total_items * self.hours_per_item
            required_hours_items = hours_for_items / weeks_to_deadline
        else:
            required_hours_items = 0

        if self.hours_per_point and self.hours_per_point > 0:
            hours_for_points = total_points * self.hours_per_point
            required_hours_points = hours_for_points / weeks_to_deadline
        else:
            required_hours_points = 0

        # Use the max of the two as the required hours
        required_hours_per_week = max(required_hours_items, required_hours_points)

        # Check if capacity is sufficient
        capacity_sufficient = self.capacity_hours_per_week >= required_hours_per_week

        # Calculate capacity percentage needed
        if self.capacity_hours_per_week > 0:
            capacity_percentage_needed = (
                required_hours_per_week / self.capacity_hours_per_week
            ) * 100
        else:
            capacity_percentage_needed = 0

        return {
            "required_items_per_week": required_items_per_week,
            "required_points_per_week": required_points_per_week,
            "required_hours_per_week": required_hours_per_week,
            "capacity_sufficient": capacity_sufficient,
            "capacity_percentage_needed": capacity_percentage_needed,
        }
