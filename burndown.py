import sys
import datetime
import matplotlib.pyplot as plt
import math


def generate_burndown_chart(
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

    ideal_items = [
        max(total_items - (total_items / days_to_deadline) * d, 0)
        if days_to_deadline > 0
        else 0
        for d in range(days_to_deadline + 1)
    ]
    ideal_points = [
        max(total_story_points - (total_story_points / days_to_deadline) * d, 0)
        if days_to_deadline > 0
        else 0
        for d in range(days_to_deadline + 1)
    ]

    actual_items = [
        max(total_items - (weekly_throughput / 7) * d, 0)
        for d in range(days_to_plot + 1)
    ]
    actual_points = [
        max(total_story_points - (weekly_velocity / 7) * d, 0)
        for d in range(days_to_plot + 1)
    ]

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

    ideal_items_x, ideal_items_y = truncate_at_zero(dates, ideal_items)
    actual_items_x, actual_items_y = truncate_at_zero(dates, actual_items)
    ideal_points_x, ideal_points_y = truncate_at_zero(dates, ideal_points)
    actual_points_x, actual_points_y = truncate_at_zero(dates, actual_points)

    plt.figure(figsize=(10, 6))

    plt.plot(
        ideal_items_x,
        ideal_items_y,
        linestyle=":",
        label="Ideal Throughput",
        color="blue",
    )
    plt.plot(
        actual_items_x,
        actual_items_y,
        linestyle="-",
        label="Actual Throughput",
        color="darkblue",
    )

    plt.plot(
        ideal_points_x,
        ideal_points_y,
        linestyle=":",
        label="Ideal Velocity",
        color="red",
    )
    plt.plot(
        actual_points_x,
        actual_points_y,
        linestyle="-",
        label="Actual Velocity",
        color="darkred",
    )

    execution_date = today.strftime("%Y-%m-%d")
    plt.title(f"Project Burndown For {execution_date}")

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
        color="red",
    )
    plt.text(
        0.95,
        y_base - 3 * line_spacing,
        f"Weekly Velocity: {weekly_velocity}",
        transform=plt.gca().transAxes,
        ha="right",
        va="top",
        color="darkred",
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
        ideal_items_x[-1], actual_items_x[-1], ideal_points_x[-1], actual_points_x[-1]
    )

    all_dates = [
        today + datetime.timedelta(days=d) for d in range((last_date - today).days + 1)
    ]
    plt.xticks(
        all_dates[::7],
        [date.strftime("%Y-%m-%d") for date in all_dates[::7]],
        rotation=45,
    )

    plt.axvline(
        x=deadline, color="magenta", linestyle="--", linewidth=2, label="Deadline"
    )

    plt.grid(True)
    plt.gcf().autofmt_xdate()
    plt.tight_layout()

    plt.savefig("burndown_chart.svg")
    plt.close()


if __name__ == "__main__":
    if len(sys.argv) != 6:
        print(
            "Usage: python burndown.py <items> <story_points> <throughput> <velocity> <deadline YYYY-MM-DD>"
        )
        sys.exit(1)

    items = int(sys.argv[1])
    story_points = int(sys.argv[2])
    throughput = int(sys.argv[3])
    velocity = int(sys.argv[4])
    deadline_input = sys.argv[5]

    generate_burndown_chart(items, story_points, throughput, velocity, deadline_input)
    print("Burndown chart saved as burndown_chart.svg")
