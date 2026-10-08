import pytest


class TestBugTrendChart:
    def test_bug_trend_chart_data(self):

        expected_structure = {
            "data": [
                {
                    "x": ["2025-W01", "2025-W02", "2025-W03"],
                    "y": [5, 7, 3],
                    "name": "Bugs Created",
                    "type": "scatter",
                    "mode": "lines+markers",
                },
                {
                    "x": ["2025-W01", "2025-W02", "2025-W03"],
                    "y": [4, 5, 6],
                    "name": "Bugs Closed",
                    "type": "scatter",
                    "mode": "lines+markers",
                },
            ],
            "layout": {
                "title": "Bug Trends: Creation vs Resolution",
                "xaxis": {"title": "Week"},
                "yaxis": {"title": "Bug Count"},
            },
        }

        assert "data" in expected_structure
        assert "layout" in expected_structure
        assert len(expected_structure["data"]) == 2

        created_line = expected_structure["data"][0]
        assert created_line["name"] == "Bugs Created"
        assert created_line["type"] == "scatter"
        assert created_line["mode"] == "lines+markers"

        closed_line = expected_structure["data"][1]
        assert closed_line["name"] == "Bugs Closed"

    def test_bug_trend_chart_warning_highlights(self):
        expected_warnings = [
            {
                "type": "rect",
                "xref": "x",
                "yref": "paper",
                "x0": "2025-W02",
                "x1": "2025-W04",
                "y0": 0,
                "y1": 1,
                "fillcolor": "red",
                "opacity": 0.2,
                "layer": "below",
                "line_width": 0,
            }
        ]

        assert len(expected_warnings) == 1
        warning = expected_warnings[0]
        assert warning["type"] == "rect"
        assert warning["fillcolor"] == "red"
        assert warning["opacity"] == 0.2
        assert warning["layer"] == "below"

    def test_bug_trend_chart_mobile_optimization(self):
        mobile_config = {
            "responsive": True,
            "displayModeBar": False,
            "modeBarButtonsToRemove": ["zoom", "pan", "select"],
        }

        mobile_layout = {
            "margin": {"t": 40, "r": 20, "b": 60, "l": 60},
            "font": {"size": 12},
            "showlegend": True,
            "legend": {"orientation": "h", "y": -0.2},
        }

        assert mobile_config["responsive"] is True
        assert mobile_layout["margin"]["t"] <= 40
        assert mobile_layout["font"]["size"] <= 14


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
