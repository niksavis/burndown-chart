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
    pip install -r requirements.txt
    ```

## Usage

To generate a burndown chart, run the [burndown.py](http://_vscodecontentref_/1) script with the following arguments:

```sh
python burndown.py <items> <story_points> <throughput> <velocity> <deadline YYYY-MM-DD>
