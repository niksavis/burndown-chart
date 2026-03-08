"""Forecast chart renderer: assembles traces, layout, and metrics.

Entry point for creating the complete interactive forecast plot.
Part of visualization/forecast_chart.py split.
"""

import logging
from datetime import datetime

import pandas as pd
from plotly.subplots import make_subplots

from visualization.elements import create_empty_figure
from visualization.forecast_chart_layout import (
    add_deadline_marker,
    add_metrics_annotations,
    configure_axes,
)
from visualization.forecast_chart_traces import create_plot_traces
from visualization.helpers import (
    get_weekly_metrics,
    handle_forecast_error,
    parse_deadline_milestone,
    safe_numeric_convert,
)


def create_forecast_plot(
    df,
    total_items,
    total_points,
    pert_factor,
    deadline_str,
    milestone_str=None,
    data_points_count=None,
    show_forecast=True,
    forecast_visibility=True,
    hover_mode="x unified",
    show_points=True,
):
    """
    Create the complete forecast plot with all components.

    Args:
        df: DataFrame with historical data
        total_items: Total number of items to complete
        total_points: Total number of points to complete
        pert_factor: PERT factor for calculations
        deadline_str: Deadline date as string (YYYY-MM-DD)
        milestone_str: Milestone date as string (YYYY-MM-DD), optional
        data_points_count: Number of most recent data points to use (defaults to all)
        show_forecast: Whether to show forecast traces
        forecast_visibility: Visibility mode for forecast traces
            ("legendonly", True, False)
        hover_mode: Hover mode for the plot ("x unified", "closest", etc.)
        show_points: Whether points tracking is enabled (default: True)

    Returns:
        Tuple of (figure, pert_data_dict) where pert_data_dict
        contains all PERT forecast information
    """
    # Import helper functions (to avoid circular dependency)
    from visualization.charts import (
        _calculate_forecast_completion_dates,
        _prepare_metrics_data,
    )
    from visualization.data_preparation import prepare_visualization_data

    try:
        if df is None:
            df = pd.DataFrame()
        elif not isinstance(df, pd.DataFrame):
            if isinstance(df, (list, dict)):
                # Convert list of dictionaries or dictionary to DataFrame
                try:
                    df = pd.DataFrame(df)
                except Exception:
                    df = pd.DataFrame()
            else:
                df = pd.DataFrame()

        # Ensure numeric types for calculations with explicit conversion
        total_items = safe_numeric_convert(total_items, default=0.0)
        total_points = safe_numeric_convert(total_points, default=0.0)
        pert_factor = int(safe_numeric_convert(pert_factor, default=3.0))

        # Parse deadline and milestone dates
        deadline, milestone = parse_deadline_milestone(deadline_str, milestone_str)

        # Prepare all data needed for the visualization
        forecast_data = prepare_visualization_data(
            df,
            total_items,
            total_points,
            pert_factor,
            data_points_count,
            is_burnup=False,
            scope_items=None,
            scope_points=None,
            show_points=show_points,
        )

        df_calc = forecast_data.get("df_calc")
        if df_calc is None or df_calc.empty or "date" not in df_calc.columns:
            fig = create_empty_figure("No data available for forecast")
            pert_data = {
                "pert_time_items": 0.0,
                "pert_time_points": 0.0,
                "items_completion_enhanced": "Unknown",
                "points_completion_enhanced": "Unknown",
                "days_to_deadline": 0,
                "avg_weekly_items": 0.0,
                "avg_weekly_points": 0.0,
                "med_weekly_items": 0.0,
                "med_weekly_points": 0.0,
                "forecast_timestamp": datetime.now().isoformat(),
                "velocity_cv": 0.0,
                "schedule_variance_days": 0.0,
            }
            return fig, pert_data

        # Create subplot with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add all traces to the figure
        traces = create_plot_traces(
            forecast_data, show_forecast, forecast_visibility, show_points
        )
        for trace in traces:
            # Only add forecast traces if show_forecast is True
            is_forecast = (
                "Forecast" in trace["data"].name
                if hasattr(trace["data"], "name")
                else False
            )

            if not is_forecast or (is_forecast and show_forecast):
                # Set visibility for all forecast traces
                # based on forecast_visibility parameter
                if is_forecast:
                    trace["data"].visible = forecast_visibility

                fig.add_trace(trace["data"], secondary_y=trace["secondary_y"])

        # Add deadline marker and configure axes
        fig = add_deadline_marker(fig, deadline, milestone)
        fig = configure_axes(fig, forecast_data)

        # Apply layout settings with the specified hover_mode
        # Increased top margin from 80 to 100px
        # to accommodate legend (y=1.06) and toolbar without overlap
        fig.update_layout(
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.06,
                xanchor="center",
                x=0.5,
                itemclick="toggle",
                itemdoubleclick=False,
            ),
            hovermode=hover_mode,
            margin=dict(l=60, r=60, t=100, b=50),
            height=700,
            template="plotly_white",
        )

        # Calculate days to deadline for metrics
        current_date = datetime.now()
        # Handle None or NaT deadline safely
        if deadline is None or pd.isna(deadline):
            days_to_deadline = 0
        else:
            days_to_deadline = max(0, (deadline - pd.Timestamp(current_date)).days)

        # Calculate weekly metrics
        avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
            get_weekly_metrics(df, data_points_count)
        )

        # Calculate enhanced formatted strings for PERT estimates
        pert_time_items = forecast_data.get("pert_time_items", 0.0)
        pert_time_points = forecast_data.get("pert_time_points", 0.0)

        # Ensure valid numbers for PERT times
        pert_time_items = safe_numeric_convert(pert_time_items, default=0.0)
        pert_time_points = safe_numeric_convert(pert_time_points, default=0.0)

        # Get formatted completion date strings
        items_completion_enhanced, points_completion_enhanced = (
            _calculate_forecast_completion_dates(pert_time_items, pert_time_points)
        )

        # Prepare metrics data for display
        try:
            metrics_data = _prepare_metrics_data(
                total_items,
                total_points,
                deadline,
                pert_time_items,
                pert_time_points,
                data_points_count,
                df,
                items_completion_enhanced,
                points_completion_enhanced,
                avg_weekly_items,  # Removed round() to preserve decimal places
                avg_weekly_points,  # Removed round() to preserve decimal places
                med_weekly_items,  # Removed round() to preserve decimal places
                med_weekly_points,  # Removed round() to preserve decimal places
            )

            # Ensure metrics_data is never None
            if metrics_data is None:
                metrics_data = {}  # Default to empty dict if None

            # Add metrics annotations
            fig = add_metrics_annotations(fig, metrics_data, data_points_count)
        except Exception as metrics_error:
            # Log the error but continue without metrics
            logger = logging.getLogger("burndown_chart")
            logger.error(
                f"[Visualization] Error preparing metrics data: {str(metrics_error)}"
            )

            # Create minimal metrics data with default values
            metrics_data = {
                "total_items": total_items,
                "total_points": total_points,
                "deadline": deadline.strftime("%Y-%m-%d")
                if deadline is not None
                and hasattr(deadline, "strftime")
                and not pd.isna(deadline)
                else "Unknown",
                "days_to_deadline": days_to_deadline,
                "avg_weekly_items": float(avg_weekly_items),
                "avg_weekly_points": float(avg_weekly_points),
                "med_weekly_items": float(med_weekly_items),
                "med_weekly_points": float(med_weekly_points),
            }

            # Try to add metrics with the minimal data
            try:
                fig = add_metrics_annotations(fig, metrics_data, data_points_count)
            except Exception:
                # If even this fails, just continue without metrics
                pass

        # Calculate velocity_cv and schedule_variance_days for health score
        velocity_cv = forecast_data.get("velocity_cv", 0)
        schedule_variance_days = (
            abs(pert_time_items - days_to_deadline)
            if pert_time_items > 0 and days_to_deadline > 0
            else 0
        )

        # Create a complete PERT data dictionary with explicit type conversion
        pert_data = {
            "pert_time_items": float(pert_time_items),
            "pert_time_points": float(pert_time_points),
            "items_completion_enhanced": str(items_completion_enhanced),
            "points_completion_enhanced": str(points_completion_enhanced),
            "days_to_deadline": int(days_to_deadline),
            "avg_weekly_items": float(
                avg_weekly_items
            ),  # Ensure this is a float without rounding
            "avg_weekly_points": float(
                avg_weekly_points
            ),  # Ensure this is a float without rounding
            "med_weekly_items": float(med_weekly_items),  # Also keep this as float
            "med_weekly_points": float(med_weekly_points),  # Also keep this as float
            "forecast_timestamp": datetime.now().isoformat(),
            "velocity_cv": float(velocity_cv),
            "schedule_variance_days": float(schedule_variance_days),
        }

        return fig, pert_data

    except Exception as e:
        return handle_forecast_error(e)
