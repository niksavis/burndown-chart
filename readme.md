# Burndown Chart Generator

[![python](https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

This project generates a burndown chart for project management using Python and Matplotlib.

## Installation

1. Install Python 3.13+ from the [official website](https://www.python.org).

2. Clone the repository:

    ```sh
    git clone https://github.com/niksavis/burndown-chart.git
    cd burndown-chart
    ```

3. Create a virtual environment and activate it:

    ```sh
    python -m venv .venv
    .venv\Scripts\activate  # On macOS and Linux use `source .venv/bin/activate`
    ```

4. Install the required dependencies:

    ```sh
    python -m pip install -r requirements.txt
    ```

## Usage

You can display detailed help by running:

```sh
python burndown.py --help
```

### Single Burndown

To generate a single burndown chart, use the `single` subcommand followed by five arguments:

```sh
python burndown.py single <items_val> <story_points_val> <throughput_val> <velocity_val> <deadline_str_val>
```

- `<items>`: Total number of items to be completed.
- `<story_points>`: Total number of story points to be completed.
- `<throughput>`: Weekly throughput (number of items completed per week).
- `<velocity>`: Weekly velocity (number of story points completed per week).
- `<deadline_str_val>`: Project deadline in `YYYY-MM-DD` format.

Example:

```sh
python burndown.py single 73 348 8 22 2025-05-29
```

The generated burndown chart will be saved as [`burndown_chart.svg`](burndown_chart.svg).

### Multiple Burndown

To generate multiple burndown charts at once, use the `multi` subcommand followed by repeated groups of six arguments:

```sh
python burndown.py multi <dataset_name> <items> <story_points> <throughput> <velocity> <deadline_str> ...
```

Each group corresponds to one dataset:

- `<dataset_name>`: A label/name for the dataset.
- `<items>`: Total number of items for this dataset.
- `<story_points>`: Total number of story points for this dataset.
- `<throughput>`: Weekly throughput (number of items completed per week) for this dataset.
- `<velocity>`: Weekly velocity (number of story points completed per week) for this dataset.
- `<deadline_str_val>`: Project deadline in `YYYY-MM-DD` format for this dataset.

Example:

```sh
python burndown.py multi "Team A" 70 344 10 26 2025-05-29 "Team B" 122 488 15 46 2025-05-29
```

The generated multiple burndown chart will be saved as [`multiple_burndown_chart.svg`](multiple_burndown_chart.svg).

## Example

Here is an example of the generated burndown chart:

![Burndown Chart](burndown_chart.svg)

Here is an example of the generated multiple burndown chart:

![Multiple Burndown Chart](multiple_burndown_chart.svg)

## License

This repository is licensed under the [MIT License](LICENSE)

**[⬆ Back to Top](#burndown-chart-generator)**
