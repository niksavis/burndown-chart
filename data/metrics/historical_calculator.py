import logging

from data.iso_week_bucketing import get_last_n_weeks
from data.metrics.weekly_calculator import calculate_and_save_weekly_metrics
from data.metrics_snapshots import batch_write_mode
from data.task_progress import TaskProgress

logger = logging.getLogger(__name__)


def calculate_metrics_for_last_n_weeks(
    n_weeks: int = 12, progress_callback=None, custom_weeks=None
) -> tuple[bool, str]:

    try:
        if custom_weeks:
            weeks = custom_weeks
            n_weeks = len(weeks)
            logger.info(
                f"Calculating metrics for {n_weeks} custom weeks "
                "(based on actual data range)"
            )
        else:
            weeks = get_last_n_weeks(n_weeks)
            logger.info(f"Calculating metrics for last {n_weeks} weeks from today")

        successful_weeks = []
        failed_weeks = []
        skipped_weeks = []

        progress_update_interval = min(5, max(1, n_weeks // 50))
        logger.info(
            f"Progress will update every {progress_update_interval} week(s) "
            f"(~{100 * progress_update_interval / max(n_weeks, 1):.1f}% increments)"
        )

        with batch_write_mode():
            week_number = 0
            for week_label, monday, sunday in weeks:
                logger.info(f"Processing week {week_label} ({monday} to {sunday})")

                week_number += 1
                try:
                    is_cancelled = TaskProgress.is_task_cancelled()
                    logger.debug(
                        f"[Metrics] Cancellation check: is_cancelled={is_cancelled}"
                    )
                    if is_cancelled:
                        logger.info(
                            "[Metrics] Calculation cancelled by user at week "
                            f"{week_number}/{n_weeks}"
                        )
                        TaskProgress.fail_task(
                            "update_data", "Operation cancelled by user"
                        )
                        return (
                            False,
                            "Cancelled after calculating "
                            f"{week_number - 1}/{n_weeks} weeks",
                        )
                except Exception as e:
                    logger.warning(
                        "[Progress] Failed to check cancellation for week "
                        f"{week_label}: {e}"
                    )

                if progress_callback:
                    progress_callback(
                        f"[Date] Calculating metrics for week {week_label} "
                        f"({monday} to {sunday})..."
                    )

                success, message = calculate_and_save_weekly_metrics(
                    week_label=week_label,
                    progress_callback=progress_callback,
                )

                should_update_progress = (
                    week_number % progress_update_interval == 0
                    or week_number == n_weeks
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
                            "[Progress] Calculation progress: "
                            f"{week_number}/{n_weeks} weeks "
                            f"({week_number / n_weeks * 100:.0f}%)"
                        )
                    except Exception as e:
                        logger.warning(
                            "[Progress] Failed to update progress for week "
                            f"{week_label}: {e}"
                        )

                import time  # noqa: PLC0415

                time.sleep(0.001)

                if success:
                    if "not affected" in message:
                        skipped_weeks.append(week_label)
                    else:
                        successful_weeks.append(week_label)
                else:
                    failed_weeks.append((week_label, message))

        if skipped_weeks:
            summary = (
                f"[Delta] Calculated {len(successful_weeks)} weeks, "
                f"skipped {len(skipped_weeks)} unaffected weeks"
            )
            if failed_weeks:
                summary += f", {len(failed_weeks)} failures"
            logger.info(summary)
        elif failed_weeks:
            summary = (
                f"[!] Calculated metrics for {len(successful_weeks)}/"
                f"{n_weeks} weeks. Failures:\n"
            )
            for week, msg in failed_weeks[:3]:
                summary += f"  {week}: {msg[:100]}...\n"
            logger.info(summary)
        else:
            if successful_weeks:
                summary = (
                    "[OK] Successfully calculated metrics for all "
                    f"{n_weeks} weeks ({successful_weeks[0]} "
                    f"to {successful_weeks[-1]})"
                )
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
