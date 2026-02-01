"""Historical metrics calculation for multiple weeks."""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def calculate_metrics_for_last_n_weeks(
    n_weeks: int = 12, progress_callback=None, custom_weeks=None
) -> Tuple[bool, str]:
    """
    Calculate metrics for the last N weeks (including current week).

    This is useful for populating historical data and ensuring sparklines/trends
    have enough data points.

    Args:
        n_weeks: Number of weeks to calculate (default: 12) - ignored if custom_weeks provided
        progress_callback: Optional callback function(message: str) for progress updates
        custom_weeks: Optional list of (week_label, monday, sunday) tuples based on actual data range

    Returns:
        Tuple of (success: bool, summary_message: str)
    """
    from data.iso_week_bucketing import get_last_n_weeks
    from data.metrics_snapshots import batch_write_mode
    from data.metrics.weekly_calculator import calculate_and_save_weekly_metrics

    try:
        # Use custom weeks if provided, otherwise generate last N weeks from today
        if custom_weeks:
            weeks = custom_weeks
            n_weeks = len(weeks)
            logger.info(
                f"Calculating metrics for {n_weeks} custom weeks (based on actual data range)"
            )
        else:
            # Get week labels for last N weeks from today
            weeks = get_last_n_weeks(n_weeks)
            logger.info(f"Calculating metrics for last {n_weeks} weeks from today")

        successful_weeks = []
        failed_weeks = []
        skipped_weeks = []

        # Note: Legacy delta optimization removed - database timestamps provide sufficient tracking

        # Use batch write mode to accumulate all changes and write once
        # Import TaskProgress once before loop for progress updates
        from data.task_progress import TaskProgress

        # Calculate progress update interval: every 5 weeks or every 2%, whichever is more frequent
        # This balances UI smoothness with reduced database writes (80% reduction for large datasets)
        progress_update_interval = min(
            5, max(1, n_weeks // 50)
        )  # Update every 2% or every 5 weeks
        logger.info(
            f"Progress will update every {progress_update_interval} week(s) (~{100 * progress_update_interval / max(n_weeks, 1):.1f}% increments)"
        )

        with batch_write_mode():
            week_number = 0
            for week_label, monday, sunday in weeks:
                # Use ISO week format (YYYY-Wxx) consistently - DO NOT normalize/strip the 'W'
                # This ensures saved data keys match what loaders expect

                logger.info(f"Processing week {week_label} ({monday} to {sunday})")

                # Check for cancellation request BEFORE processing
                week_number += 1
                try:
                    # Check if task was cancelled
                    is_cancelled = TaskProgress.is_task_cancelled()
                    logger.debug(
                        f"[Metrics] Cancellation check: is_cancelled={is_cancelled}"
                    )
                    if is_cancelled:
                        logger.info(
                            f"[Metrics] Calculation cancelled by user at week {week_number}/{n_weeks}"
                        )
                        TaskProgress.fail_task(
                            "update_data", "Operation cancelled by user"
                        )
                        return (
                            False,
                            f"Cancelled after calculating {week_number - 1}/{n_weeks} weeks",
                        )
                except Exception as e:
                    logger.warning(
                        f"[Progress] Failed to check cancellation for week {week_label}: {e}"
                    )

                if progress_callback:
                    progress_callback(
                        f"[Date] Calculating metrics for week {week_label} ({monday} to {sunday})..."
                    )

                success, message = calculate_and_save_weekly_metrics(
                    week_label=week_label,
                    progress_callback=progress_callback,
                )

                # Report calculation progress AFTER week is calculated (not before)
                # This ensures 100% means "all work done", not "starting last week"
                # Only update at intervals to reduce database writes (Phase 1 optimization)
                should_update_progress = (
                    week_number % progress_update_interval == 0
                    or week_number == n_weeks  # Always update on completion
                )

                if should_update_progress:
                    try:
                        TaskProgress.update_progress(
                            "update_data",
                            "calculate",
                            current=week_number,
                            total=n_weeks,
                            message=f"Week {week_label}",
                        )
                        logger.info(
                            f"[Progress] Calculation progress: {week_number}/{n_weeks} weeks ({week_number / n_weeks * 100:.0f}%)"
                        )
                    except Exception as e:
                        logger.warning(
                            f"[Progress] Failed to update progress for week {week_label}: {e}"
                        )

                # Yield control to allow other Dash callbacks (like progress bar polling) to execute
                # This prevents the long-running calculation from blocking the UI
                import time

                time.sleep(0.001)  # 1ms sleep to yield to event loop

                if success:
                    # Check if it was actually calculated or skipped
                    if "not affected" in message:
                        skipped_weeks.append(week_label)
                    else:
                        successful_weeks.append(week_label)
                else:
                    failed_weeks.append((week_label, message))

        # Summary
        if skipped_weeks:
            summary = f"[Delta] Calculated {len(successful_weeks)} weeks, skipped {len(skipped_weeks)} unaffected weeks"
            if failed_weeks:
                summary += f", {len(failed_weeks)} failures"
            logger.info(summary)
        elif failed_weeks:
            summary = f"[!] Calculated metrics for {len(successful_weeks)}/{n_weeks} weeks. Failures:\n"
            for week, msg in failed_weeks[:3]:  # Show first 3 failures
                summary += f"  {week}: {msg[:100]}...\n"
            logger.info(summary)
        else:
            if successful_weeks:
                summary = f"[OK] Successfully calculated metrics for all {n_weeks} weeks ({successful_weeks[0]} to {successful_weeks[-1]})"
            else:
                summary = (
                    f"[OK] All {n_weeks} weeks up-to-date (no recalculation needed)"
                )
            logger.info(summary)

        return len(failed_weeks) == 0, summary

    except Exception as e:
        error_msg = f"Error calculating multi-week metrics: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg
