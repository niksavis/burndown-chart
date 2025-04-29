# Burndown Chart Generator

[![python](https://img.shields.io/badge/Python-3.13-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

An interactive web app that helps you track project progress and forecast completion dates using burndown and burnup charts.

## Quick Start

1. **Install Python 3.13+** from [python.org](https://www.python.org)

2. **Get the code:**

   ```sh
   git clone https://github.com/niksavis/burndown-chart.git
   cd burndown-chart
   ```

3. **Set up environment:**

   ```sh
   python -m venv .venv
   .venv\Scripts\activate  # On macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Run the app:**

   ```sh
   python app.py
   ```

5. **Open in browser:** [http://127.0.0.1:8050/](http://127.0.0.1:8050/)

## What Can You Do With This App?

- **Track Project Progress**: See completion trends with interactive charts
- **Switch Views**: Toggle between burndown (work remaining) and burnup (work completed) charts
- **Get Forecasts**: View optimistic, most likely, and pessimistic completion dates
- **Monitor Scope Changes**: Track when requirements grow and get alerts for significant scope changes
- **Customize Parameters**: Set deadlines, initial scope, and analysis settings
- **Export Data**: Save charts as images or download raw data for reports

## Using Your Own Data

Upload a CSV file with your project data. Format should be:

```csv
date;completed_items;completed_points;created_items;created_points
2025-03-01;5;50;0;0
2025-03-02;7;70;2;15
```

- `date`: When work was completed (YYYY-MM-DD)
- `completed_items`: Number of tasks finished that day
- `completed_points`: Story points/effort completed that day
- `created_items`: New tasks added that day
- `created_points`: Story points/effort added that day

**Tip**: Use the included sample file `statistics.csv` to test the app's features.

## Troubleshooting

- **Missing packages?** Run `pip install -r requirements.txt` again
- **Port in use?** Change the port in app.py: `app.run_server(debug=True, port=8060)`
- **Data issues?** Delete `forecast_settings.json` and `forecast_statistics.csv` to reset

## License

[MIT License](LICENSE)

**[⬆ Back to Top](#burndown-chart-generator)**
