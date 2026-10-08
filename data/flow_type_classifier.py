import logging
from typing import Any

logger = logging.getLogger(__name__)


FLOW_TYPE_FEATURE = "Feature"
FLOW_TYPE_DEFECT = "Defect"
FLOW_TYPE_TECHNICAL_DEBT = "Technical Debt"
FLOW_TYPE_RISK = "Risk"


EFFORT_NEW_FEATURE = "New feature"
EFFORT_TECHNICAL_DEBT = "Technical debt"
EFFORT_IMPROVEMENT = "Improvement"
EFFORT_MAINTENANCE = "Maintenance"
EFFORT_UPGRADES = "Upgrades"
EFFORT_SPIKES = "Spikes (Analysis)"
EFFORT_SECURITY = "Security"
EFFORT_GDPR = "GDPR Compliance"
EFFORT_REGULATORY = "Regulatory"
EFFORT_NONE = "None"


def get_flow_type(issue: Any, effort_category_field: str) -> str:

    fields = (
        issue.get("fields", {})
        if isinstance(issue, dict)
        else getattr(issue, "fields", {})
    )

    if isinstance(fields, dict):
        issuetype_obj = fields.get("issuetype", {})
        issue_type = (
            issuetype_obj.get("name") if isinstance(issuetype_obj, dict) else None
        )
        issue_key = (
            issue.get("key", "UNKNOWN")
            if isinstance(issue, dict)
            else getattr(issue, "key", "UNKNOWN")
        )
    else:
        issue_type = (
            getattr(fields.issuetype, "name", None)
            if hasattr(fields, "issuetype")
            else None
        )
        issue_key = getattr(issue, "key", "UNKNOWN")

    if not issue_type:
        logger.warning(f"Issue {issue_key} has no issue type, defaulting to Feature")
        return FLOW_TYPE_FEATURE

    if issue_type == "Bug":
        logger.debug(f"Issue {issue_key}: Bug → Defect (ignoring effort category)")
        return FLOW_TYPE_DEFECT

    if issue_type in ("Task", "Story"):
        if isinstance(fields, dict):
            effort_category = fields.get(effort_category_field)
        else:
            effort_category = getattr(fields, effort_category_field, None)

        if isinstance(effort_category, dict):
            effort_category = effort_category.get("value")

        if not effort_category or effort_category == "":
            logger.debug(
                f"Issue {issue_key}: Missing effort category, defaulting to Feature"
            )
            return FLOW_TYPE_FEATURE

        flow_type = _map_effort_category_to_flow_type(effort_category)

        logger.debug(
            f"Issue {issue_key}: {issue_type} + '{effort_category}' → {flow_type}"
        )
        return flow_type

    logger.debug(f"Issue {issue_key}: Unknown type '{issue_type}' → Feature")
    return FLOW_TYPE_FEATURE


def _map_effort_category_to_flow_type(effort_category: str) -> str:

    if effort_category == EFFORT_TECHNICAL_DEBT:
        return FLOW_TYPE_TECHNICAL_DEBT

    risk_categories = {
        EFFORT_SECURITY,
        EFFORT_GDPR,
        EFFORT_REGULATORY,
        EFFORT_MAINTENANCE,
        EFFORT_UPGRADES,
        EFFORT_SPIKES,
    }

    if effort_category in risk_categories:
        return FLOW_TYPE_RISK

    feature_categories = {
        EFFORT_NEW_FEATURE,
        EFFORT_IMPROVEMENT,
        EFFORT_NONE,
    }

    if effort_category in feature_categories:
        return FLOW_TYPE_FEATURE

    logger.warning(
        f"Unknown effort category: '{effort_category}', defaulting to Feature"
    )
    return FLOW_TYPE_FEATURE


def classify_issues_by_flow_type(
    issues: list, effort_category_field: str
) -> dict[str, list]:

    classified = {
        FLOW_TYPE_FEATURE: [],
        FLOW_TYPE_DEFECT: [],
        FLOW_TYPE_TECHNICAL_DEBT: [],
        FLOW_TYPE_RISK: [],
    }

    for issue in issues:
        flow_type = get_flow_type(issue, effort_category_field)
        classified[flow_type].append(issue)

    logger.info(
        f"Classified {len(issues)} issues by Flow type: "
        f"Feature={len(classified[FLOW_TYPE_FEATURE])}, "
        f"Defect={len(classified[FLOW_TYPE_DEFECT])}, "
        f"Technical Debt={len(classified[FLOW_TYPE_TECHNICAL_DEBT])}, "
        f"Risk={len(classified[FLOW_TYPE_RISK])}"
    )

    return classified


def count_by_flow_type(issues: list, effort_category_field: str) -> dict[str, int]:

    classified = classify_issues_by_flow_type(issues, effort_category_field)

    return {
        flow_type: len(issues_list) for flow_type, issues_list in classified.items()
    }


def get_flow_distribution(issues: list, effort_category_field: str) -> dict[str, float]:

    counts = count_by_flow_type(issues, effort_category_field)
    total = sum(counts.values())

    if total == 0:
        logger.warning("No issues to calculate Flow distribution")
        return {
            FLOW_TYPE_FEATURE: 0.0,
            FLOW_TYPE_DEFECT: 0.0,
            FLOW_TYPE_TECHNICAL_DEBT: 0.0,
            FLOW_TYPE_RISK: 0.0,
        }

    distribution = {
        flow_type: (count / total) * 100 for flow_type, count in counts.items()
    }

    logger.info(
        f"Flow distribution: Feature={distribution[FLOW_TYPE_FEATURE]:.1f}%, "
        f"Defect={distribution[FLOW_TYPE_DEFECT]:.1f}%, "
        f"Technical Debt={distribution[FLOW_TYPE_TECHNICAL_DEBT]:.1f}%, "
        f"Risk={distribution[FLOW_TYPE_RISK]:.1f}%"
    )

    return distribution
