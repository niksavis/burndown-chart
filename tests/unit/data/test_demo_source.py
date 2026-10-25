from datetime import datetime

import pytest

from data.demo.config import AS_OF, SCENARIOS, START, profile_config
from data.demo.issues import scenario_issues


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_synthetic_history_is_consistent_and_inside_eight_weeks(scenario: str) -> None:
    issues = scenario_issues(scenario)
    assert len({issue["key"] for issue in issues}) == len(issues)
    for issue in issues:
        fields = issue["fields"]
        created = datetime.fromisoformat(fields["created"])
        assert START <= created <= AS_OF
        histories = issue["changelog"]["histories"]
        for history in histories:
            assert created <= datetime.fromisoformat(history["created"]) <= AS_OF
            assert datetime.fromisoformat(history["created"]) <= datetime.fromisoformat(
                fields["updated"]
            )
        status_changes = [
            entry for entry in histories if entry["items"][0]["field"] == "status"
        ]
        if status_changes:
            latest = max(status_changes, key=lambda entry: entry["created"])
            assert latest["items"][0]["toString"] == fields["status"]["name"]
        assert (fields["resolutiondate"] is not None) == (
            fields["status"]["name"] == "Done"
        )


def test_complete_project_has_known_source_population_and_points() -> None:
    issues = scenario_issues("complete")
    development = [
        issue
        for issue in issues
        if issue["fields"]["project"]["key"] == "DEMO"
        and issue["fields"]["issuetype"]["name"] != "Epic"
    ]
    assert len(development) == 48
    assert sum(issue["fields"]["customfield_10001"] for issue in development) == 96.0
    assert (
        sum(issue["fields"]["resolutiondate"] is not None for issue in development)
        == 32
    )
    assert (
        sum(
            issue["fields"]["customfield_10001"]
            for issue in development
            if issue["fields"]["resolutiondate"]
        )
        == 64.0
    )
    assert (
        len(
            {
                datetime.fromisoformat(issue["fields"]["created"]).strftime("%G-W%V")
                for issue in development
            }
        )
        == 8
    )
    assert {issue["fields"]["customfield_10003"] for issue in issues} == {
        "PROD",
        "TEST",
    }


def test_scenarios_do_not_share_mutable_issue_or_profile_data() -> None:
    changed = scenario_issues("complete")
    changed[0]["fields"]["summary"] = "changed"
    assert scenario_issues("complete")[0]["fields"]["summary"] != "changed"
    profile = profile_config("complete")
    profile["field_mappings"]["general"]["estimate"] = "changed"
    assert (
        profile_config("complete")["field_mappings"]["general"]["estimate"]
        == "customfield_10001"
    )


@pytest.mark.parametrize("scenario", ["complete", "reopened"])
def test_sprint_history_names_join_the_current_field_metadata(scenario: str) -> None:
    from data.sprint_manager import _parse_sprint_name, _parse_sprint_object

    for issue in scenario_issues(scenario):
        sprints = issue["fields"]["customfield_10002"]
        parsed = _parse_sprint_object(sprints[0]) if sprints else None
        assert parsed is not None or not sprints
        current = parsed["name"] if parsed else None
        changes = [
            history
            for history in issue["changelog"]["histories"]
            if history["items"][0]["field"] == "Sprint"
        ]
        latest = max(changes, key=lambda history: history["created"])
        assert _parse_sprint_name(latest["items"][0]["toString"]) == current


def test_scope_change_changes_a_development_story_and_sprint_changes_match_fields() -> (
    None
):
    issues = scenario_issues("scope-change")
    story = next(issue for issue in issues if issue["key"] == "DEMO-42")
    assert story["fields"]["issuetype"]["name"] == "Story"
    assert story["fields"]["customfield_10001"] == 3.5
    changed = scenario_issues("reopened")
    assert "Demo Sprint 2" in changed[1]["fields"]["customfield_10002"][0]
    assert changed[2]["fields"]["customfield_10002"] == []
    assert changed[2]["changelog"]["histories"][-1]["items"][0]["toString"] == ""


def test_nominal_recorded_deployments_have_consistent_release_flags() -> None:
    deployments = [
        issue
        for issue in scenario_issues("complete")
        if issue["fields"]["project"]["key"] == "OPS"
    ]
    for deployment in deployments:
        version = deployment["fields"]["fixVersions"][0]
        assert version["released"] is True
        assert datetime.fromisoformat(version["releaseDate"]).date() <= AS_OF.date()


def test_unknown_demo_scenario_is_refused_by_name() -> None:
    with pytest.raises(ValueError, match="Unknown demo scenario: misspelled"):
        scenario_issues("misspelled")


def test_unreleased_version_is_an_explicit_eligibility_edge() -> None:
    issue = next(
        issue
        for issue in scenario_issues("unreleased-version")
        if issue["key"] == "OPS-8"
    )
    assert issue["fields"]["status"]["name"] == "Done"
    version = issue["fields"]["fixVersions"][0]
    assert version["released"] is False
    assert version["releaseDate"] == "2026-01-29"
