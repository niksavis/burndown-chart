/**
 * Active Work Search - clientside metadata helpers
 *
 * Builder-first search executes query construction and filtering server-side.
 * This script only provides metadata extraction for builder value dropdowns.
 */

(function () {
  "use strict";

  if (window.dash_clientside === undefined) {
    window.dash_clientside = {};
  }

  window.dash_clientside.activeWorkSearch = {
    /**
     * Build searchable metadata from timeline data.
     *
     * Input: timeline (epics with child_issues)
     * Output: { fields: string[], values: Record<string, string[]> }
     */
    buildSearchMetadata: function (timeline) {
      if (!Array.isArray(timeline) || timeline.length === 0) {
        return {
          fields: [
            "key",
            "summary",
            "assignee",
            "issuetype",
            "project",
            "fixversion",
            "labels",
            "components",
          ],
          values: {
            key: [],
            assignee: [],
            issuetype: [],
            project: [],
            fixversion: [],
            labels: [],
            components: [],
          },
        };
      }

      const values = {
        key: new Set(),
        assignee: new Set(),
        issuetype: new Set(),
        project: new Set(),
        fixversion: new Set(),
        labels: new Set(),
        components: new Set(),
      };

      for (const epic of timeline) {
        const issues = Array.isArray(epic?.child_issues)
          ? epic.child_issues
          : [];
        for (const issue of issues) {
          addIfPresent(values.key, issue?.issue_key);
          addIfPresent(values.assignee, issue?.assignee);
          addIfPresent(values.issuetype, issue?.issue_type);
          addIfPresent(values.project, issue?.project_key);

          addMany(values.labels, toValueList(issue?.labels));
          addMany(values.components, toValueList(issue?.components));

          const fixVersionsRaw =
            issue?.fix_versions !== undefined
              ? issue.fix_versions
              : issue?.fixVersions;
          addMany(values.fixversion, toValueList(fixVersionsRaw));
        }
      }

      return {
        fields: [
          "key",
          "summary",
          "assignee",
          "issuetype",
          "project",
          "fixversion",
          "labels",
          "components",
        ],
        values: {
          key: toSortedArray(values.key),
          assignee: toSortedArray(values.assignee),
          issuetype: toSortedArray(values.issuetype),
          project: toSortedArray(values.project),
          fixversion: toSortedArray(values.fixversion),
          labels: toSortedArray(values.labels),
          components: toSortedArray(values.components),
        },
      };
    },
  };

  function addMany(target, items) {
    if (!(target instanceof Set) || !Array.isArray(items)) {
      return;
    }
    for (const item of items) {
      addIfPresent(target, item);
    }
  }

  function addIfPresent(target, value) {
    if (!(target instanceof Set)) {
      return;
    }

    const normalized = normalizeDisplayValue(value);
    if (normalized) {
      target.add(normalized);
    }
  }

  function toSortedArray(setValue) {
    if (!(setValue instanceof Set)) {
      return [];
    }
    return Array.from(setValue).sort((a, b) => a.localeCompare(b));
  }

  function toValueList(rawValue) {
    if (rawValue === null || rawValue === undefined) {
      return [];
    }

    if (Array.isArray(rawValue)) {
      return rawValue
        .map((entry) => normalizeDisplayValue(entry))
        .filter((entry) => !!entry);
    }

    if (typeof rawValue === "string") {
      const trimmed = rawValue.trim();
      if (!trimmed) {
        return [];
      }

      if (trimmed.startsWith("[") || trimmed.startsWith("{")) {
        try {
          return toValueList(JSON.parse(trimmed));
        } catch (_error) {
          return [trimmed];
        }
      }

      if (trimmed.includes(",") || trimmed.includes(";")) {
        return trimmed
          .split(/[;,]/)
          .map((item) => item.trim())
          .filter((item) => !!item);
      }

      return [trimmed];
    }

    const normalized = normalizeDisplayValue(rawValue);
    return normalized ? [normalized] : [];
  }

  function normalizeDisplayValue(value) {
    if (value === null || value === undefined) {
      return "";
    }

    if (typeof value === "string") {
      return value.trim();
    }

    if (typeof value === "number" || typeof value === "boolean") {
      return String(value);
    }

    if (typeof value === "object") {
      const candidate =
        value.displayName || value.name || value.value || value.key || "";
      return typeof candidate === "string"
        ? candidate.trim()
        : String(candidate);
    }

    return String(value).trim();
  }
})();
