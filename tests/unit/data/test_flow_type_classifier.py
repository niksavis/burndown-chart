"""
Unit tests for data/flow_type_classifier.py

All functions are pure logic operating on dict or simple-namespace issue objects.
No database, no network, no I/O needed.
"""

from types import SimpleNamespace

import pytest

from data.flow_type_classifier import (
    FLOW_TYPE_DEFECT,
    FLOW_TYPE_FEATURE,
    FLOW_TYPE_RISK,
    FLOW_TYPE_TECHNICAL_DEBT,
    classify_issues_by_flow_type,
    count_by_flow_type,
    get_flow_distribution,
    get_flow_type,
)

EFFORT_FIELD = "customfield_10099"

###############################################################################
# Helpers
###############################################################################


def _dict_issue(
    issue_type: str, effort_category: object = None, key: str = "T-1"
) -> dict:
    """Build a JIRA issue in the nested dict (JSON) format."""
    fields: dict = {"issuetype": {"name": issue_type}}
    if effort_category is not None:
        fields[EFFORT_FIELD] = effort_category
    return {"key": key, "fields": fields}


def _obj_issue(issue_type: str, effort_category: object = None, key: str = "T-1"):
    """Build a JIRA issue in the object (JIRA library) format."""
    issuetype = SimpleNamespace(name=issue_type)
    fields_kw: dict = {"issuetype": issuetype}
    if effort_category is not None:
        fields_kw[EFFORT_FIELD] = effort_category
    fields = SimpleNamespace(**fields_kw)
    return SimpleNamespace(key=key, fields=fields)


###############################################################################
# get_flow_type — dict format
###############################################################################


class TestGetFlowTypeDictFormat:
    def test_bug_is_always_defect(self) -> None:
        issue = _dict_issue("Bug")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_DEFECT

    def test_bug_ignores_effort_category(self) -> None:
        issue = _dict_issue("Bug", effort_category="Technical debt")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_DEFECT

    def test_task_with_technical_debt(self) -> None:
        issue = _dict_issue("Task", effort_category="Technical debt")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_TECHNICAL_DEBT

    def test_story_with_technical_debt(self) -> None:
        issue = _dict_issue("Story", effort_category="Technical debt")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_TECHNICAL_DEBT

    def test_task_with_security_is_risk(self) -> None:
        issue = _dict_issue("Task", effort_category="Security")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_RISK

    def test_task_with_gdpr_is_risk(self) -> None:
        issue = _dict_issue("Task", effort_category="GDPR Compliance")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_RISK

    def test_task_with_regulatory_is_risk(self) -> None:
        issue = _dict_issue("Task", effort_category="Regulatory")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_RISK

    def test_task_with_maintenance_is_risk(self) -> None:
        issue = _dict_issue("Task", effort_category="Maintenance")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_RISK

    def test_task_with_upgrades_is_risk(self) -> None:
        issue = _dict_issue("Task", effort_category="Upgrades")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_RISK

    def test_task_with_spikes_is_risk(self) -> None:
        issue = _dict_issue("Task", effort_category="Spikes (Analysis)")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_RISK

    def test_task_with_new_feature_is_feature(self) -> None:
        issue = _dict_issue("Task", effort_category="New feature")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_FEATURE

    def test_task_with_improvement_is_feature(self) -> None:
        issue = _dict_issue("Task", effort_category="Improvement")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_FEATURE

    def test_task_with_none_effort_is_feature(self) -> None:
        issue = _dict_issue("Task", effort_category="None")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_FEATURE

    def test_task_with_missing_effort_defaults_to_feature(self) -> None:
        issue = _dict_issue("Task")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_FEATURE

    def test_task_with_empty_effort_defaults_to_feature(self) -> None:
        issue = _dict_issue("Task", effort_category="")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_FEATURE

    def test_story_with_new_feature_is_feature(self) -> None:
        issue = _dict_issue("Story", effort_category="New feature")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_FEATURE

    def test_unknown_issue_type_defaults_to_feature(self) -> None:
        issue = _dict_issue("Epic")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_FEATURE

    def test_missing_issue_type_defaults_to_feature(self) -> None:
        issue = {"key": "T-1", "fields": {}}
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_FEATURE

    def test_effort_category_as_dict_with_value_key(self) -> None:
        # JIRA select field format: {"value": "Technical debt"}
        issue = _dict_issue("Task", effort_category={"value": "Technical debt"})
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_TECHNICAL_DEBT

    def test_unknown_effort_category_defaults_to_feature(self) -> None:
        issue = _dict_issue("Task", effort_category="Some Other Category")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_FEATURE


###############################################################################
# get_flow_type — object format
###############################################################################


class TestGetFlowTypeObjectFormat:
    def test_bug_is_defect(self) -> None:
        issue = _obj_issue("Bug")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_DEFECT

    def test_task_with_technical_debt(self) -> None:
        issue = _obj_issue("Task", effort_category="Technical debt")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_TECHNICAL_DEBT

    def test_task_with_security_is_risk(self) -> None:
        issue = _obj_issue("Task", effort_category="Security")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_RISK

    def test_task_with_new_feature(self) -> None:
        issue = _obj_issue("Task", effort_category="New feature")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_FEATURE

    def test_story_with_missing_effort_defaults_to_feature(self) -> None:
        issue = _obj_issue("Story")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_FEATURE

    def test_no_fields_attribute_defaults_to_feature(self) -> None:
        issue = SimpleNamespace(key="T-1")
        assert get_flow_type(issue, EFFORT_FIELD) == FLOW_TYPE_FEATURE


###############################################################################
# classify_issues_by_flow_type
###############################################################################


class TestClassifyIssuesByFlowType:
    def test_classifies_single_bug(self) -> None:
        issues = [_dict_issue("Bug")]
        result = classify_issues_by_flow_type(issues, EFFORT_FIELD)
        assert len(result[FLOW_TYPE_DEFECT]) == 1
        assert len(result[FLOW_TYPE_FEATURE]) == 0

    def test_classifies_mixed_issues(self) -> None:
        issues = [
            _dict_issue("Bug", key="B-1"),
            _dict_issue("Task", effort_category="New feature", key="T-1"),
            _dict_issue("Task", effort_category="Technical debt", key="T-2"),
            _dict_issue("Task", effort_category="Security", key="T-3"),
        ]
        result = classify_issues_by_flow_type(issues, EFFORT_FIELD)
        assert len(result[FLOW_TYPE_DEFECT]) == 1
        assert len(result[FLOW_TYPE_FEATURE]) == 1
        assert len(result[FLOW_TYPE_TECHNICAL_DEBT]) == 1
        assert len(result[FLOW_TYPE_RISK]) == 1

    def test_empty_issues_returns_empty_buckets(self) -> None:
        result = classify_issues_by_flow_type([], EFFORT_FIELD)
        assert all(len(v) == 0 for v in result.values())

    def test_result_has_all_four_flow_types(self) -> None:
        result = classify_issues_by_flow_type([], EFFORT_FIELD)
        assert set(result.keys()) == {
            FLOW_TYPE_FEATURE,
            FLOW_TYPE_DEFECT,
            FLOW_TYPE_TECHNICAL_DEBT,
            FLOW_TYPE_RISK,
        }


###############################################################################
# count_by_flow_type
###############################################################################


class TestCountByFlowType:
    def test_counts_match_classification(self) -> None:
        issues = [
            _dict_issue("Bug", key="B-1"),
            _dict_issue("Bug", key="B-2"),
            _dict_issue("Task", effort_category="New feature", key="T-1"),
        ]
        result = count_by_flow_type(issues, EFFORT_FIELD)
        assert result[FLOW_TYPE_DEFECT] == 2
        assert result[FLOW_TYPE_FEATURE] == 1
        assert result[FLOW_TYPE_TECHNICAL_DEBT] == 0
        assert result[FLOW_TYPE_RISK] == 0

    def test_empty_issues_all_zeros(self) -> None:
        result = count_by_flow_type([], EFFORT_FIELD)
        assert all(v == 0 for v in result.values())

    def test_returns_int_values(self) -> None:
        result = count_by_flow_type([_dict_issue("Bug")], EFFORT_FIELD)
        assert all(isinstance(v, int) for v in result.values())


###############################################################################
# get_flow_distribution
###############################################################################


class TestGetFlowDistribution:
    def test_single_type_is_100_percent(self) -> None:
        issues = [_dict_issue("Bug", key="B-1"), _dict_issue("Bug", key="B-2")]
        result = get_flow_distribution(issues, EFFORT_FIELD)
        assert result[FLOW_TYPE_DEFECT] == pytest.approx(100.0)
        assert result[FLOW_TYPE_FEATURE] == pytest.approx(0.0)

    def test_fifty_fifty_split(self) -> None:
        issues = [
            _dict_issue("Bug", key="B-1"),
            _dict_issue("Task", effort_category="New feature", key="T-1"),
        ]
        result = get_flow_distribution(issues, EFFORT_FIELD)
        assert result[FLOW_TYPE_DEFECT] == pytest.approx(50.0)
        assert result[FLOW_TYPE_FEATURE] == pytest.approx(50.0)

    def test_percentages_sum_to_100(self) -> None:
        issues = [
            _dict_issue("Bug", key="B-1"),
            _dict_issue("Task", effort_category="New feature", key="T-1"),
            _dict_issue("Task", effort_category="Technical debt", key="T-2"),
            _dict_issue("Task", effort_category="Security", key="T-3"),
        ]
        result = get_flow_distribution(issues, EFFORT_FIELD)
        assert sum(result.values()) == pytest.approx(100.0)

    def test_empty_issues_returns_all_zeros(self) -> None:
        result = get_flow_distribution([], EFFORT_FIELD)
        assert all(v == pytest.approx(0.0) for v in result.values())
        assert set(result.keys()) == {
            FLOW_TYPE_FEATURE,
            FLOW_TYPE_DEFECT,
            FLOW_TYPE_TECHNICAL_DEBT,
            FLOW_TYPE_RISK,
        }
