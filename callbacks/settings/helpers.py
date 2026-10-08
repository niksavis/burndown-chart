from configuration import logger
from data.persistence import load_unified_project_data


def normalize_show_points(value):

    if isinstance(value, list):
        return "show" in value
    elif isinstance(value, int):
        return value != 0
    elif isinstance(value, bool):
        return value
    else:
        return False


def get_data_points_info(value: int, min_val: int, max_val: int) -> str:

    if min_val == max_val:
        return "Using all available data points"

    percent = (
        ((value - min_val) / (max_val - min_val) * 100) if max_val > min_val else 100
    )

    if value == min_val:
        return f"Using minimum data points ({value} points, most recent data only)"
    elif value == max_val:
        return f"Using all available data points ({value} points)"
    else:
        return (
            f"Using {value} most recent data points ({percent:.0f}% of available data)"
        )


def calculate_remaining_work_for_data_window(data_points_count, statistics):

    if not data_points_count:
        return None

    try:
        unified_data = load_unified_project_data()
        project_scope = unified_data.get("project_scope", {})

        estimated_items = project_scope.get("estimated_items", 0)
        remaining_items = project_scope.get("remaining_items", 0)
        estimated_points = project_scope.get("estimated_points", 0)
        remaining_points = project_scope.get("remaining_total_points", 0)

        avg_points_per_item = 0
        if remaining_items > 0:
            avg_points_per_item = remaining_points / remaining_items

        logger.info("[PARAM PANEL] Current remaining work (independent of slider):")
        logger.info(
            f"  Estimated items: {estimated_items}, Remaining items: {remaining_items}"
        )
        logger.info(
            "  Estimated points: "
            f"{estimated_points:.1f}, Remaining points: {remaining_points:.1f}"
        )
        logger.info(f"  Avg: {avg_points_per_item:.2f} points/item")

        calc_results = {
            "total_points": remaining_points,
            "avg_points_per_item": avg_points_per_item,
        }

        return (
            estimated_items,
            int(remaining_items),
            estimated_points,
            f"{remaining_points:.0f}",
            calc_results,
        )

    except Exception as e:
        logger.error(f"Error calculating remaining work for data window: {e}")
        return None
