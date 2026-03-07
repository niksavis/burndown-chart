"""
Unit tests for data/fixversion_matcher.py

These tests cover pure logic paths only — no I/O, no database, no network.
"""

from datetime import date

from data.fixversion_matcher import (
    extract_fixversion_ids,
    extract_fixversion_names,
    find_matching_operational_tasks,
    get_earliest_release_date,
    get_fallback_release_date,
    get_fixversions,
)

###############################################################################
# Helpers
###############################################################################


def _nested_issue(fixversions: list[dict], key: str = "DEV-1") -> dict:
    """Build a JIRA API-format issue (fields/fixVersions nested)."""
    return {"key": key, "fields": {"fixVersions": fixversions}}


def _flat_issue(fixversions: list[dict], key: str = "OP-1") -> dict:
    """Build a flat/DB-format issue (fixVersions at root level)."""
    return {"key": key, "fixVersions": fixversions}


_FV_A = {"id": "10001", "name": "Release 2025-01", "releaseDate": "2025-01-15"}
_FV_B = {"id": "10002", "name": "Release-2025-02", "releaseDate": "2025-02-20"}
_FV_C = {"id": "10003", "name": "Release Future", "releaseDate": "2099-12-31"}
_FV_NO_DATE = {"id": "10004", "name": "No Date"}

###############################################################################
# get_fixversions
###############################################################################


class TestGetFixversions:
    def test_nested_jira_format(self) -> None:
        issue = _nested_issue([_FV_A, _FV_B])
        result = get_fixversions(issue)
        assert result == [_FV_A, _FV_B]

    def test_flat_format(self) -> None:
        issue = _flat_issue([_FV_A])
        result = get_fixversions(issue)
        assert result == [_FV_A]

    def test_empty_fixversions_nested(self) -> None:
        issue = _nested_issue([])
        assert get_fixversions(issue) == []

    def test_empty_fixversions_flat(self) -> None:
        issue = _flat_issue([])
        assert get_fixversions(issue) == []

    def test_missing_fixversions_key_nested(self) -> None:
        issue = {"key": "DEV-1", "fields": {}}
        assert get_fixversions(issue) == []

    def test_missing_fixversions_key_flat(self) -> None:
        issue = {"key": "DEV-1"}
        assert get_fixversions(issue) == []

    def test_graceful_on_none_fields(self) -> None:
        # fields present but None — should not crash
        issue = {"key": "DEV-1", "fields": None}
        # When fields is None, isinstance check fails → falls through to flat path
        result = get_fixversions(issue)
        assert isinstance(result, list)


###############################################################################
# extract_fixversion_ids
###############################################################################


class TestExtractFixversionIds:
    def test_extracts_ids_from_nested(self) -> None:
        issue = _nested_issue([_FV_A, _FV_B])
        assert extract_fixversion_ids(issue) == {"10001", "10002"}

    def test_extracts_ids_from_flat(self) -> None:
        issue = _flat_issue([_FV_A])
        assert extract_fixversion_ids(issue) == {"10001"}

    def test_skips_entries_without_id(self) -> None:
        fv_no_id = {"name": "No ID version"}
        issue = _nested_issue([_FV_A, fv_no_id])
        assert extract_fixversion_ids(issue) == {"10001"}

    def test_empty_issue_returns_empty_set(self) -> None:
        assert extract_fixversion_ids(_nested_issue([])) == set()

    def test_returns_set_type(self) -> None:
        issue = _nested_issue([_FV_A])
        result = extract_fixversion_ids(issue)
        assert isinstance(result, set)


###############################################################################
# extract_fixversion_names
###############################################################################


class TestExtractFixversionNames:
    def test_normalizes_lowercase(self) -> None:
        fv = {"id": "1", "name": "Release UPPER"}
        issue = _nested_issue([fv])
        assert extract_fixversion_names(issue) == {"release_upper"}

    def test_normalizes_spaces_to_underscores(self) -> None:
        fv = {"id": "1", "name": "My Release 2025"}
        issue = _nested_issue([fv])
        assert extract_fixversion_names(issue) == {"my_release_2025"}

    def test_normalizes_hyphens_to_underscores(self) -> None:
        issue = _nested_issue([_FV_B])  # "Release-2025-02"
        assert extract_fixversion_names(issue) == {"release_2025_02"}

    def test_multiple_fixversions(self) -> None:
        issue = _nested_issue([_FV_A, _FV_B])
        names = extract_fixversion_names(issue)
        assert "release_2025_01" in names
        assert "release_2025_02" in names

    def test_skips_entries_without_name(self) -> None:
        fv_no_name = {"id": "99"}
        issue = _nested_issue([_FV_A, fv_no_name])
        names = extract_fixversion_names(issue)
        assert len(names) == 1
        assert "release_2025_01" in names

    def test_empty_returns_empty_set(self) -> None:
        assert extract_fixversion_names(_nested_issue([])) == set()


###############################################################################
# get_earliest_release_date
###############################################################################


class TestGetEarliestReleaseDate:
    _today = date(2025, 6, 1)

    def test_returns_earliest_past_date(self) -> None:
        fixversions = [_FV_A, _FV_B]  # 2025-01-15 and 2025-02-20
        result = get_earliest_release_date(fixversions, today=self._today)
        assert result == date(2025, 1, 15)

    def test_filters_out_future_dates(self) -> None:
        fixversions = [_FV_C]  # 2099-12-31
        result = get_earliest_release_date(fixversions, today=self._today)
        assert result is None

    def test_includes_today_exactly(self) -> None:
        fv_today = {"id": "99", "releaseDate": "2025-06-01"}
        result = get_earliest_release_date([fv_today], today=self._today)
        assert result == self._today

    def test_mixed_past_and_future(self) -> None:
        fixversions = [_FV_A, _FV_C]  # 2025-01-15 (past) + 2099-12-31 (future)
        result = get_earliest_release_date(fixversions, today=self._today)
        assert result == date(2025, 1, 15)

    def test_skips_entries_without_release_date(self) -> None:
        result = get_earliest_release_date([_FV_NO_DATE], today=self._today)
        assert result is None

    def test_empty_list_returns_none(self) -> None:
        assert get_earliest_release_date([], today=self._today) is None

    def test_invalid_date_format_skipped(self) -> None:
        fv_bad = {"id": "x", "releaseDate": "not-a-date"}
        fv_good = {"id": "y", "releaseDate": "2025-01-15"}
        result = get_earliest_release_date([fv_bad, fv_good], today=self._today)
        assert result == date(2025, 1, 15)

    def test_defaults_to_today_when_none_passed(self) -> None:
        # Just check it does not crash and returns a date when there is a past date
        past_fv = {"id": "1", "releaseDate": "2020-01-01"}
        result = get_earliest_release_date([past_fv])
        assert result == date(2020, 1, 1)


###############################################################################
# get_fallback_release_date
###############################################################################


class TestGetFallbackReleaseDate:
    def test_parses_iso8601_with_offset(self) -> None:
        issue = {
            "key": "OP-1",
            "fields": {"resolutiondate": "2025-10-31T18:00:00.000+02:00"},
        }
        result = get_fallback_release_date(issue)
        assert result == date(2025, 10, 31)

    def test_parses_iso8601_with_z(self) -> None:
        issue = {
            "key": "OP-1",
            "fields": {"resolutiondate": "2025-10-31T18:00:00.000Z"},
        }
        result = get_fallback_release_date(issue)
        assert result == date(2025, 10, 31)

    def test_returns_none_when_no_resolutiondate(self) -> None:
        issue = {"key": "OP-1", "fields": {}}
        assert get_fallback_release_date(issue) is None

    def test_returns_none_when_no_fields(self) -> None:
        issue = {"key": "OP-1"}
        assert get_fallback_release_date(issue) is None

    def test_returns_none_when_resolutiondate_is_none(self) -> None:
        issue = {"key": "OP-1", "fields": {"resolutiondate": None}}
        assert get_fallback_release_date(issue) is None


###############################################################################
# find_matching_operational_tasks
###############################################################################


class TestFindMatchingOperationalTasks:
    def _make_dev(self, fvs: list[dict]) -> dict:
        return _nested_issue(fvs, key="DEV-1")

    def _make_op(self, fvs: list[dict], key: str = "OP-1") -> dict:
        return _nested_issue(fvs, key=key)

    def test_id_match_returns_id_label(self) -> None:
        dev = self._make_dev([_FV_A])
        op = self._make_op([_FV_A])
        results = find_matching_operational_tasks(dev, [op], match_by="auto")
        assert len(results) == 1
        task, method = results[0]
        assert task is op
        assert method == "id"

    def test_name_match_fallback(self) -> None:
        # Same name different ID
        fv_dev = {"id": "AAA", "name": "release 2025-01"}
        fv_op = {"id": "BBB", "name": "release 2025-01"}
        dev = self._make_dev([fv_dev])
        op = self._make_op([fv_op])
        results = find_matching_operational_tasks(dev, [op], match_by="auto")
        assert len(results) == 1
        _, method = results[0]
        assert method == "name"

    def test_no_match_returns_empty(self) -> None:
        dev = self._make_dev([_FV_A])
        op = self._make_op([_FV_B])
        results = find_matching_operational_tasks(dev, [op], match_by="auto")
        assert results == []

    def test_match_by_id_only_skips_name(self) -> None:
        fv_dev = {"id": "AAA", "name": "release 2025-01"}
        fv_op = {"id": "BBB", "name": "release 2025-01"}
        dev = self._make_dev([fv_dev])
        op = self._make_op([fv_op])
        # match_by="id" must not fall back to name
        results = find_matching_operational_tasks(dev, [op], match_by="id")
        assert results == []

    def test_match_by_name_only(self) -> None:
        fv_dev = {"id": "AAA", "name": "release 2025-01"}
        fv_op = {"id": "AAA", "name": "release 2025-01"}
        dev = self._make_dev([fv_dev])
        op = self._make_op([fv_op])
        results = find_matching_operational_tasks(dev, [op], match_by="name")
        assert len(results) == 1
        _, method = results[0]
        assert method == "name"

    def test_dev_with_no_fixversions_returns_empty(self) -> None:
        dev = self._make_dev([])
        op = self._make_op([_FV_A])
        results = find_matching_operational_tasks(dev, [op])
        assert results == []

    def test_multiple_ops_partial_match(self) -> None:
        dev = self._make_dev([_FV_A])
        op_match = self._make_op([_FV_A], key="OP-1")
        op_no_match = self._make_op([_FV_B], key="OP-2")
        results = find_matching_operational_tasks(dev, [op_match, op_no_match])
        assert len(results) == 1
        task, _ = results[0]
        assert task is op_match

    def test_id_match_takes_priority_over_name(self) -> None:
        # Both share ID — should be an ID match, not name
        dev = self._make_dev([_FV_A])
        op = self._make_op([_FV_A])
        results = find_matching_operational_tasks(dev, [op], match_by="auto")
        _, method = results[0]
        assert method == "id"
