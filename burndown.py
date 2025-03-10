import sys
import datetime
import matplotlib.pyplot as plt
import math
from adjustText import adjust_text
import contextlib
import os


def truncate_at_zero(x_vals, y_vals):
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
    total_items, total_story_points, weekly_throughput, weekly_velocity, deadline_str
):
    deadline = datetime.datetime.strptime(deadline_str, "%Y-%m-%d").date()
    today = datetime.date.today()
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

    def ideal_curve(total, deadline_days):
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


def plot_burndown_data(data_dict, label_suffix=""):
    texts = []

    plt.plot(
        data_dict["ideal_items_x"],
        data_dict["ideal_items_y"],
        linestyle=":",
        label=f"Ideal Throughput{label_suffix}",
        color="blue",
    )
    if data_dict["ideal_items_x"]:
        t = plt.text(
            data_dict["ideal_items_x"][-1],
            data_dict["ideal_items_y"][-1],
            f"{label_suffix.strip()}",
            color="blue",
            fontsize=9,
            ha="left",
            va="center",
        )
        texts.append(t)

    plt.plot(
        data_dict["actual_items_x"],
        data_dict["actual_items_y"],
        linestyle="-",
        label=f"Actual Throughput{label_suffix}",
        color="darkblue",
    )
    if data_dict["actual_items_x"]:
        t = plt.text(
            data_dict["actual_items_x"][-1],
            data_dict["actual_items_y"][-1],
            f"{label_suffix.strip()}",
            color="darkblue",
            fontsize=9,
            ha="left",
            va="center",
        )
        texts.append(t)

    plt.plot(
        data_dict["ideal_points_x"],
        data_dict["ideal_points_y"],
        linestyle=":",
        label=f"Ideal Velocity{label_suffix}",
        color="lightcoral",
    )
    if data_dict["ideal_points_x"]:
        t = plt.text(
            data_dict["ideal_points_x"][-1],
            data_dict["ideal_points_y"][-1],
            f"{label_suffix.strip()}",
            color="lightcoral",
            fontsize=9,
            ha="left",
            va="center",
        )
        texts.append(t)

    plt.plot(
        data_dict["actual_points_x"],
        data_dict["actual_points_y"],
        linestyle="-",
        label=f"Actual Velocity{label_suffix}",
        color="red",
    )
    if data_dict["actual_points_x"]:
        t = plt.text(
            data_dict["actual_points_x"][-1],
            data_dict["actual_points_y"][-1],
            f"{label_suffix.strip()}",
            color="red",
            fontsize=9,
            ha="left",
            va="center",
        )
        texts.append(t)

    return texts


def save_figure(prefix, date_obj):
    date_str = date_obj.strftime("%Y%m%d")
    plt.savefig(f"{prefix}.svg")
    plt.savefig(f"{prefix}_{date_str}.png")


def generate_burndown_chart(
    total_items, total_story_points, weekly_throughput, weekly_velocity, deadline_str
):
    data = generate_burndown_data(
        total_items,
        total_story_points,
        weekly_throughput,
        weekly_velocity,
        deadline_str,
    )
    today = data["today"]
    deadline = data["deadline"]

    plt.figure(figsize=(10, 6))

    texts = plot_burndown_data(data)

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

    with open(os.devnull, "w") as fnull, contextlib.redirect_stdout(fnull):
        adjust_text(texts, arrowprops=dict(arrowstyle="->", color="gray"), ax=plt.gca())

    save_figure("burndown_chart", today)
    plt.close()


def generate_multiple_burndown_charts(datasets):
    plt.figure(figsize=(10, 6))
    today = datetime.date.today()
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
        )
        text_objs = plot_burndown_data(data, label_suffix=f" ({params['name']})")
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
        all_range_in_days = (max_date - today).days
        dates = [
            today + datetime.timedelta(days=i) for i in range(all_range_in_days + 1)
        ]
        plt.xticks(
            dates[::7], [date.strftime("%Y-%m-%d") for date in dates[::7]], rotation=45
        )

    plt.grid(True)
    plt.gcf().autofmt_xdate()
    plt.tight_layout()

    with open(os.devnull, "w") as fnull, contextlib.redirect_stdout(fnull):
        adjust_text(
            all_texts, arrowprops=dict(arrowstyle="->", color="gray"), ax=plt.gca()
        )

    save_figure("multiple_burndown_chart", today)
    plt.close()


def print_help():
    print(
        "Usage for single dataset:\n"
        "  python burndown.py <items> <story_points> <throughput> <velocity> <deadline YYYY-MM-DD>\n"
        "\n"
        "Usage for multiple datasets:\n"
        "  python burndown.py multi "
        "<dataset_name> <items> <points> <throughput> <velocity> <deadline YYYY-MM-DD> "
        "... (repeated for each dataset) ..."
    )


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print_help()
        sys.exit(1)

    if len(sys.argv) >= 2 and sys.argv[1] == "multi":
        if len(sys.argv) == 2:
            print_help()
            sys.exit(1)

        args = sys.argv[2:]
        if len(args) % 6 != 0:
            print_help()
            sys.exit(1)

        datasets = []
        for i in range(0, len(args), 6):
            dataset_name = args[i]
            items = int(args[i + 1])
            points = int(args[i + 2])
            throughput = int(args[i + 3])
            velocity = int(args[i + 4])
            deadline_input = args[i + 5]
            datasets.append(
                {
                    "name": dataset_name,
                    "items": items,
                    "story_points": points,
                    "throughput": throughput,
                    "velocity": velocity,
                    "deadline_str": deadline_input,
                }
            )

        generate_multiple_burndown_charts(datasets)
        print("Multiple burndown chart saved as multiple_burndown_chart.svg")
        sys.exit(0)

    if len(sys.argv) != 6:
        print_help()
        sys.exit(1)

    items = int(sys.argv[1])
    story_points = int(sys.argv[2])
    throughput = int(sys.argv[3])
    velocity = int(sys.argv[4])
    deadline_input = sys.argv[5]

    generate_burndown_chart(items, story_points, throughput, velocity, deadline_input)
    print("Burndown chart saved as burndown_chart.svg")
