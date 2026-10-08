from collections import OrderedDict

from dash import html


class TestCreateCompletedItemsSection:
    def test_creates_section_with_multiple_weeks(self):
        from ui.active_work_completed_components import create_completed_items_section

        completed_by_week = OrderedDict(
            [
                (
                    "2026-W06",
                    {
                        "display_label": "Current Week (Feb 3-9)",
                        "issues": [
                            {
                                "issue_key": "PROJ-1",
                                "summary": "Test",
                                "status": "Done",
                                "points": 3.0,
                            }
                        ],
                        "is_current": True,
                        "total_issues": 1,
                        "total_epics_closed": 1,
                        "total_epics_linked": 1,
                        "total_points": 3.0,
                        "epic_groups": [],
                    },
                ),
                (
                    "2026-W05",
                    {
                        "display_label": "Last Week (Jan 27 - Feb 2)",
                        "issues": [],
                        "is_current": False,
                        "total_issues": 0,
                        "total_epics_closed": 0,
                        "total_epics_linked": 0,
                        "total_points": 0.0,
                        "epic_groups": [],
                    },
                ),
            ]
        )

        result = create_completed_items_section(completed_by_week, show_points=True)  # type: ignore[arg-type]

        assert isinstance(result, html.Div)
        assert result.className == "completed-items-section mb-3"  # type: ignore[attr-defined]
        assert result.id == "completed-items-section"  # type: ignore[attr-defined]

        assert len(result.children) == 2  # type: ignore[arg-type]

    def test_empty_dict_returns_empty_div(self):
        from ui.active_work_completed_components import create_completed_items_section

        result = create_completed_items_section({}, show_points=True)

        assert isinstance(result, html.Div)
        assert not result.children or result.children == []  # type: ignore[attr-defined]

    def test_passes_show_points_to_week_containers(self):
        from ui.active_work_completed_components import create_completed_items_section

        completed_by_week = OrderedDict(
            [
                (
                    "2026-W06",
                    {
                        "display_label": "Current Week (Feb 3-9)",
                        "issues": [
                            {
                                "issue_key": "PROJ-1",
                                "summary": "Test",
                                "status": "Done",
                                "points": 5.0,
                            }
                        ],
                        "is_current": True,
                        "total_issues": 1,
                        "total_epics_closed": 1,
                        "total_epics_linked": 1,
                        "total_points": 5.0,
                        "epic_groups": [],
                    },
                )
            ]
        )

        result = create_completed_items_section(completed_by_week, show_points=True)  # type: ignore[arg-type]

        assert isinstance(result, html.Div)
        assert len(result.children) == 1  # type: ignore[arg-defined]


class TestCreateWeekContainer:
    def test_creates_details_element(self):
        from ui.active_work_completed_components import create_week_container

        result = create_week_container(
            week_label="2026-W06",
            display_label="Current Week (Feb 3-9)",
            issues=[],
            total_issues=0,
            total_epics_closed=0,
            total_epics_linked=0,
            total_points=0.0,
            is_current=True,
            epic_groups=[],
            show_points=True,
        )

        assert isinstance(result, html.Details)
        assert result.open is False  # type: ignore[attr-defined]  # Collapsed by default

    def test_container_has_correct_classes(self):
        from ui.active_work_completed_components import create_week_container

        result = create_week_container(
            week_label="2026-W06",
            display_label="Current Week (Feb 3-9)",
            issues=[],
            total_issues=0,
            total_epics_closed=0,
            total_epics_linked=0,
            total_points=0.0,
            is_current=True,
            epic_groups=[],
            show_points=True,
        )

        assert "card" in result.className  # type: ignore[attr-defined]
        assert "active-work-epic-card" in result.className  # type: ignore[attr-defined]
        assert "week-container" in result.className  # type: ignore[attr-defined]
        assert "week-current" in result.className  # type: ignore[attr-defined]

    def test_last_week_has_correct_class(self):
        from ui.active_work_completed_components import create_week_container

        result = create_week_container(
            week_label="2026-W05",
            display_label="Last Week (Jan 27 - Feb 2)",
            issues=[],
            total_issues=0,
            total_epics_closed=0,
            total_epics_linked=0,
            total_points=0.0,
            is_current=False,
            epic_groups=[],
            show_points=True,
        )

        assert "week-last" in result.className  # type: ignore[attr-defined]

    def test_displays_correct_label(self):
        from ui.active_work_completed_components import create_week_container

        display_label = "Current Week (Feb 3-9)"

        result = create_week_container(
            week_label="2026-W06",
            display_label=display_label,
            issues=[],
            total_issues=0,
            total_epics_closed=0,
            total_epics_linked=0,
            total_points=0.0,
            is_current=True,
            epic_groups=[],
            show_points=True,
        )

        assert len(result.children) == 2  # type: ignore[attr-defined]  # Summary and content

    def test_empty_issues_shows_placeholder(self):
        from ui.active_work_completed_components import create_week_container

        result = create_week_container(
            week_label="2026-W06",
            display_label="Current Week (Feb 3-9)",
            issues=[],
            total_issues=0,
            total_epics_closed=0,
            total_epics_linked=0,
            total_points=0.0,
            is_current=True,
            epic_groups=[],
            show_points=True,
        )

        assert isinstance(result, html.Details)
        assert len(result.children) == 2  # type: ignore[attr-defined]

    def test_with_issues_creates_issue_rows(self):
        from ui.active_work_completed_components import create_week_container

        issues = [
            {
                "issue_key": "PROJ-1",
                "summary": "Test 1",
                "status": "Done",
                "issue_type": "Story",
                "points": 3.0,
            },
            {
                "issue_key": "PROJ-2",
                "summary": "Test 2",
                "status": "Done",
                "issue_type": "Bug",
                "points": 5.0,
            },
        ]

        result = create_week_container(
            week_label="2026-W06",
            display_label="Current Week (Feb 3-9)",
            issues=issues,
            total_issues=2,
            total_epics_closed=1,
            total_epics_linked=1,
            total_points=8.0,
            is_current=True,
            epic_groups=[],
            show_points=True,
        )

        assert isinstance(result, html.Details)
        assert len(result.children) == 2  # type: ignore[attr-defined]

    def test_id_attribute_set(self):
        from ui.active_work_completed_components import create_week_container

        result = create_week_container(
            week_label="2026-W06",
            display_label="Current Week (Feb 3-9)",
            issues=[],
            total_issues=0,
            total_epics_closed=0,
            total_epics_linked=0,
            total_points=0.0,
            is_current=True,
            epic_groups=[],
            show_points=True,
        )

        assert result.id == "week-2026-W06"  # type: ignore[attr-defined]

    def test_shows_completed_icon(self):
        from ui.active_work_completed_components import create_week_container

        result = create_week_container(
            week_label="2026-W06",
            display_label="Current Week (Feb 3-9)",
            issues=[],
            total_issues=5,
            total_epics_closed=1,
            total_epics_linked=1,
            total_points=12.0,
            is_current=True,
            epic_groups=[],
            show_points=True,
        )

        assert isinstance(result, html.Details)
        assert len(result.children) == 2  # type: ignore[attr-defined]

    def test_respects_show_points_flag(self):
        from ui.active_work_completed_components import create_week_container

        result = create_week_container(
            week_label="2026-W06",
            display_label="Current Week (Feb 3-9)",
            issues=[],
            total_issues=5,
            total_epics_closed=1,
            total_epics_linked=1,
            total_points=12.0,
            is_current=True,
            epic_groups=[],
            show_points=False,
        )

        assert isinstance(result, html.Details)
