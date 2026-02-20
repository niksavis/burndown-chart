"""
JIRA Data Transformation Module

Transforms JIRA API responses into CSV statistics format for burndown chart visualization.
"""

from datetime import datetime, timedelta

from configuration import logger
from data.jira.field_utils import extract_story_points_value


def jira_to_csv_format(issues: list[dict], config: dict) -> list[dict]:
    """Transform JIRA issues to CSV statistics format.

    Converts JIRA API issue format to weekly burndown statistics with:
    - Week labels (ISO week format: YYYY-Wxx)
    - Remaining items/points at end of each week
    - Completed items/points during each week
    - Created items/points during each week

    Args:
        issues: List of JIRA issue dictionaries (nested or flat format)
        config: Configuration with story_points_field and other settings

    Returns:
        List of weekly data dictionaries with burndown statistics
    """
    from data.iso_week_bucketing import get_week_label

    try:
        if not issues:
            return []

        # Determine date range from actual issues data
        all_dates = []
        for issue in issues:
            if issue.get("fields", {}).get("created"):
                created_date = datetime.strptime(
                    issue["fields"]["created"][:10], "%Y-%m-%d"
                )
                all_dates.append(created_date)
            if issue.get("fields", {}).get("resolutiondate"):
                resolution_date = datetime.strptime(
                    issue["fields"]["resolutiondate"][:10], "%Y-%m-%d"
                )
                all_dates.append(resolution_date)

        if not all_dates:
            logger.warning("[JIRA] No valid dates found in issues")
            return []

        # Use actual data range, extending to full weeks
        date_from = min(all_dates)
        date_to = max(all_dates)

        # Extend range to at least today to include weeks with zero activity
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if date_to < today:
            date_to = today

        # Extend range to ensure we capture all activity (extend to full weeks)
        date_from = date_from - timedelta(days=date_from.weekday())  # Start of week
        date_to = date_to + timedelta(days=6 - date_to.weekday())  # End of week

        weekly_data = []
        current_date = date_from

        while current_date <= date_to:
            week_end = current_date + timedelta(days=6)
            week_end = min(week_end, date_to)

            # Count completed and created items for this week
            completed_items = 0
            completed_points = 0
            created_items = 0
            created_points = 0

            for issue in issues:
                # Handle both nested (JIRA API) and flat (database) formats
                if "fields" in issue and isinstance(issue.get("fields"), dict):
                    # Nested format
                    resolution_date_str = issue.get("fields", {}).get("resolutiondate")
                    created_date_str = issue.get("fields", {}).get("created")
                    story_points_field_value = issue.get("fields", {}).get(
                        config.get("story_points_field", "")
                    )
                else:
                    # Flat format
                    resolution_date_str = issue.get("resolved")
                    created_date_str = issue.get("created")
                    story_points_field_value = issue.get(
                        config.get("story_points_field", "")
                    )

                # Check if item was completed this week
                if resolution_date_str:
                    resolution_date = datetime.strptime(
                        resolution_date_str[:10], "%Y-%m-%d"
                    )
                    if current_date <= resolution_date <= week_end:
                        completed_items += 1
                        # Add story points if available and field is specified
                        story_points = 0
                        if (
                            config.get("story_points_field")
                            and config["story_points_field"].strip()
                        ):
                            story_points = extract_story_points_value(
                                story_points_field_value, config["story_points_field"]
                            )
                        completed_points += story_points

                # Check if item was created this week
                if created_date_str:
                    created_date = datetime.strptime(created_date_str[:10], "%Y-%m-%d")
                    if current_date <= created_date <= week_end:
                        created_items += 1
                        # Add story points if available and field is specified
                        story_points = 0
                        if (
                            config.get("story_points_field")
                            and config["story_points_field"].strip()
                        ):
                            story_points = extract_story_points_value(
                                story_points_field_value, config["story_points_field"]
                            )
                        created_points += story_points

            # Calculate week_label for this date (YYYY-Wxx format)
            week_label = get_week_label(current_date)

            # Calculate remaining items/points as of this week's end date
            # An issue is "remaining" if: created <= week_end AND (not resolved OR resolved > week_end)
            remaining_items_count = 0
            remaining_points_sum = 0

            for issue in issues:
                # Handle both nested (JIRA API) and flat (database) formats
                if "fields" in issue and isinstance(issue.get("fields"), dict):
                    # Nested format
                    created_date_str = issue.get("fields", {}).get("created")
                    resolution_date_str = issue.get("fields", {}).get("resolutiondate")
                    story_points_field_value = issue.get("fields", {}).get(
                        config.get("story_points_field", "")
                    )
                else:
                    # Flat format
                    created_date_str = issue.get("created")
                    resolution_date_str = issue.get("resolved")
                    story_points_field_value = issue.get(
                        config.get("story_points_field", "")
                    )

                if not created_date_str:
                    continue

                created_date = datetime.strptime(created_date_str[:10], "%Y-%m-%d")
                if created_date > week_end:
                    continue  # Issue didn't exist yet

                # Check if issue was resolved by this week's end
                if resolution_date_str:
                    resolution_date = datetime.strptime(
                        resolution_date_str[:10], "%Y-%m-%d"
                    )
                    if resolution_date <= week_end:
                        continue  # Issue was already completed

                # Issue is remaining
                remaining_items_count += 1

                # Add story points if available
                story_points = 0
                if (
                    config.get("story_points_field")
                    and config["story_points_field"].strip()
                ):
                    story_points = extract_story_points_value(
                        story_points_field_value, config["story_points_field"]
                    )
                remaining_points_sum += story_points

            weekly_data.append(
                {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "week_label": week_label,
                    "remaining_items": remaining_items_count,
                    "remaining_total_points": float(remaining_points_sum),
                    "completed_items": completed_items,
                    "completed_points": completed_points,
                    "created_items": created_items,
                    "created_points": created_points,
                }
            )

            current_date = week_end + timedelta(days=1)

        logger.info(f"[JIRA] Generated {len(weekly_data)} weekly data points")
        return weekly_data

    except Exception as e:
        logger.error(f"[JIRA] Transform failed: {e}")
        return []
