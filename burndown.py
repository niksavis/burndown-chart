#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import sys
import argparse
import datetime
import math
import os
import contextlib
from typing import List, Dict, Any, Tuple

# Third-party library imports
import matplotlib.pyplot as plt
from adjustText import adjust_text


def truncate_at_zero(
    x_vals: List[datetime.date], y_vals: List[float]
) -> Tuple[List[datetime.date], List[float]]:
    """
    Truncates the y-values at zero, preserving x-values up to that same index.
    """
    truncated_x, truncated_y = [], []
    for x, y in zip(x_vals, y_vals):
        if y <= 0:
            truncated_x.append(x)
            truncated_y.append(0)
            break
        truncated_x.append(x)
        truncated_y.append(y)
    return truncated_x, truncated_y


def generate_burndown_data(
    total_items: int,
    total_story_points: int,
    weekly_throughput: int,
    weekly_velocity: int,
    deadline_str: str,
    today: datetime.date,
) -> Dict[str, Any]:
    """
    Generates values needed for plotting both ideal and actual burndown lines.
    """
    deadline = datetime.datetime.strptime(deadline_str, "%Y-%m-%d").date()
    days_to_deadline = (deadline - today).days

    days_to_zero_items = (
        math.ceil(total_items / (weekly_throughput / 7)) if weekly_throughput > 0 else 0
    )
    days_to_zero_points = (
        math.ceil(total_story_points / (weekly_velocity / 7))
        if weekly_velocity > 0
        else 0
    )
    days_to_finish = max(days_to_zero_items, days_to_zero_points)
    days_to_plot = max(days_to_deadline, days_to_finish)

    dates = [today + datetime.timedelta(days=d) for d in range(days_to_plot + 1)]

    def ideal_curve(total: int, deadline_days: int) -> List[float]:
        return [
            max(total - (total / deadline_days) * d, 0) if deadline_days > 0 else 0
            for d in range(deadline_days + 1)
        ]

    ideal_items = ideal_curve(total_items, days_to_deadline)
    ideal_points = ideal_curve(total_story_points, days_to_deadline)

    actual_items = [
        max(total_items - (weekly_throughput / 7) * d, 0)
        for d in range(days_to_plot + 1)
    ]
    actual_points = [
        max(total_story_points - (weekly_velocity / 7) * d, 0)
        for d in range(days_to_plot + 1)
    ]

    ideal_items_x, ideal_items_y = truncate_at_zero(dates, ideal_items)
    actual_items_x, actual_items_y = truncate_at_zero(dates, actual_items)
    ideal_points_x, ideal_points_y = truncate_at_zero(dates, ideal_points)
    actual_points_x, actual_points_y = truncate_at_zero(dates, actual_points)

    return {
        "today": today,
        "deadline": deadline,
        "ideal_items_x": ideal_items_x,
        "ideal_items_y": ideal_items_y,
        "actual_items_x": actual_items_x,
        "actual_items_y": actual_items_y,
        "ideal_points_x": ideal_points_x,
        "ideal_points_y": ideal_points_y,
        "actual_points_x": actual_points_x,
        "actual_points_y": actual_points_y,
    }


def plot_lines(data_dict: Dict[str, Any], label_suffix: str = "") -> List[Any]:
    """
    Plots four lines (ideal/actual items, ideal/actual points) with optional suffix for their labels.
    """
    texts = []
    config = [
        ("ideal_items_x", "ideal_items_y", ":", "Ideal Throughput", "blue", 0.5),
        ("actual_items_x", "actual_items_y", "-", "Actual Throughput", "darkblue", 1.0),
        ("ideal_points_x", "ideal_points_y", ":", "Ideal Velocity", "lightcoral", 0.5),
        ("actual_points_x", "actual_points_y", "-", "Actual Velocity", "red", 1.0),
    ]
    for x_key, y_key, style, label_text, color, alpha_val in config:
        plt.plot(
            data_dict[x_key],
            data_dict[y_key],
            linestyle=style,
            label=f"{label_text}{label_suffix}",
            color=color,
            alpha=alpha_val,
        )
        if data_dict[x_key]:
            txt = plt.text(
                data_dict[x_key][-1],
                data_dict[y_key][-1],
                f"{label_suffix.strip()}",
                color=color,
                fontsize=9,
                ha="left",
                va="center",
            )
            texts.append(txt)
    return texts


def finalize_figure(texts: List[Any], prefix: str, date_obj: datetime.date) -> None:
    """
    Saves the figure as both SVG and PNG, then closes it.
    """
    with open(os.devnull, "w") as fnull, contextlib.redirect_stdout(fnull):
        adjust_text(texts, arrowprops=dict(arrowstyle="->", color="gray"), ax=plt.gca())

    date_str = date_obj.strftime("%Y%m%d")
    plt.savefig(f"{prefix}.svg")
    plt.savefig(f"{prefix}_{date_str}.png")
    plt.close()


def generate_burndown_chart(
    total_items: int,
    total_story_points: int,
    weekly_throughput: int,
    weekly_velocity: int,
    deadline_str: str,
    today: datetime.date,
) -> None:
    """
    Generates a single burndown chart as both SVG and PNG.
    """
    data = generate_burndown_data(
        total_items,
        total_story_points,
        weekly_throughput,
        weekly_velocity,
        deadline_str,
        today,
    )
    deadline = data["deadline"]

    plt.figure(figsize=(10, 8))  # Increased height from 6 to 8
    texts = plot_lines(data)

    plt.title(f"Project Burndown For {today.strftime('%Y-%m-%d')}")
    plt.legend(loc="upper right")

    y_base = 0.65
    line_spacing = 0.05
    plt.text(
        0.95,
        y_base,
        f"Total Items: {total_items}",
        transform=plt.gca().transAxes,
        ha="right",
        va="top",
        color="blue",
    )
    plt.text(
        0.95,
        y_base - line_spacing,
        f"Weekly Throughput: {weekly_throughput}",
        transform=plt.gca().transAxes,
        ha="right",
        va="top",
        color="darkblue",
    )
    plt.text(
        0.95,
        y_base - 2 * line_spacing,
        f"Total Story Points: {total_story_points}",
        transform=plt.gca().transAxes,
        ha="right",
        va="top",
        color="lightcoral",
    )
    plt.text(
        0.95,
        y_base - 3 * line_spacing,
        f"Weekly Velocity: {weekly_velocity}",
        transform=plt.gca().transAxes,
        ha="right",
        va="top",
        color="red",
    )
    plt.text(
        0.95,
        y_base - 4 * line_spacing,
        f"Deadline: {deadline_str}",
        transform=plt.gca().transAxes,
        ha="right",
        va="top",
        color="magenta",
    )

    last_date = max(
        data["ideal_items_x"][-1],
        data["actual_items_x"][-1],
        data["ideal_points_x"][-1],
        data["actual_points_x"][-1],
    )
    all_dates = [
        today + datetime.timedelta(days=d) for d in range((last_date - today).days + 1)
    ]
    plt.xticks(
        all_dates[::7], [d.strftime("%Y-%m-%d") for d in all_dates[::7]], rotation=45
    )

    plt.axvline(
        x=deadline, color="magenta", linestyle="--", linewidth=2, label="Deadline"
    )
    plt.grid(True)
    plt.gcf().autofmt_xdate()
    plt.tight_layout()

    finalize_figure(texts, "burndown_chart", today)


def generate_multiple_burndown_charts(
    datasets: List[Dict[str, Any]], today: datetime.date
) -> None:
    """
    Generates multiple burndown charts on a single figure.
    """
    plt.figure(figsize=(10, 8))  # Increased height from 6 to 8
    execution_date = today.strftime("%Y-%m-%d")
    plt.title(f"Project Burndowns For {execution_date}")

    all_dates = []
    deadlines = []
    all_texts = []

    for params in datasets:
        data = generate_burndown_data(
            params["items"],
            params["story_points"],
            params["throughput"],
            params["velocity"],
            params["deadline_str"],
            today,
        )
        text_objs = plot_lines(data, label_suffix=f" ({params['name']})")
        all_texts.extend(text_objs)
        deadlines.append(data["deadline"])
        if data["actual_items_x"]:
            all_dates.append(data["actual_items_x"][-1])
        if data["actual_points_x"]:
            all_dates.append(data["actual_points_x"][-1])

    plt.legend(loc="upper right")
    for d in deadlines:
        plt.axvline(x=d, color="magenta", linestyle="--", linewidth=1)

    if all_dates:
        max_date = max(all_dates)
        range_in_days = (max_date - today).days
        date_list = [
            today + datetime.timedelta(days=i) for i in range(range_in_days + 1)
        ]
        plt.xticks(
            date_list[::7],
            [dt.strftime("%Y-%m-%d") for dt in date_list[::7]],
            rotation=45,
        )

    plt.grid(True)
    plt.gcf().autofmt_xdate()
    plt.tight_layout()

    finalize_figure(all_texts, "multiple_burndown_chart", today)


def main() -> None:
    """
    Parses command-line options using argparse and runs either single or multiple chart generation.
    """
    parser = argparse.ArgumentParser(description="Generate burndown charts.")
    subparsers = parser.add_subparsers(
        dest="mode", help="Command mode: single or multi"
    )

    single_parser = subparsers.add_parser(
        "single", help="Generate a single burndown chart"
    )
    single_parser.add_argument(
        "items_val", type=int, help="total number of backlog items"
    )
    single_parser.add_argument("story_points_val", type=int, help="total story points")
    single_parser.add_argument(
        "throughput_val", type=int, help="weekly throughput of items"
    )
    single_parser.add_argument(
        "velocity_val", type=int, help="weekly velocity in story points"
    )
    single_parser.add_argument(
        "deadline_str_val", type=str, help="deadline in YYYY-MM-DD format"
    )

    multi_parser = subparsers.add_parser(
        "multi", help="Generate multiple burndown charts"
    )
    multi_parser.add_argument(
        "dataset_params",
        nargs="+",
        help=(
            "List of six arguments repeated for each dataset: "
            "dataset_name items story_points throughput velocity deadline_str"
        ),
    )

    args = parser.parse_args()
    if not args.mode:
        parser.print_help()
        sys.exit(1)

    if args.mode == "multi":
        if len(args.dataset_params) % 6 != 0:
            print("Error: The 'multi' command requires arguments in multiples of six.")
            sys.exit(1)

        dp = args.dataset_params
        datasets_input = []
        for i in range(0, len(dp), 6):
            dataset_name = dp[i]
            items = int(dp[i + 1])
            points = int(dp[i + 2])
            throughput = int(dp[i + 3])
            velocity = int(dp[i + 4])
            deadline_input = dp[i + 5]
            datasets_input.append(
                {
                    "name": dataset_name,
                    "items": items,
                    "story_points": points,
                    "throughput": throughput,
                    "velocity": velocity,
                    "deadline_str": deadline_input,
                }
            )

        today_date = datetime.date.today()
        generate_multiple_burndown_charts(datasets_input, today_date)
        print("Multiple burndown chart saved as multiple_burndown_chart.svg")
    else:
        today_date = datetime.date.today()
        generate_burndown_chart(
            args.items_val,
            args.story_points_val,
            args.throughput_val,
            args.velocity_val,
            args.deadline_str_val,
            today_date,
        )
        print("Burndown chart saved as burndown_chart.svg")


if __name__ == "__main__":
    main()
