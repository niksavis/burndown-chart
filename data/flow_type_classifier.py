"""
Flow Type Classifier

Classifies JIRA issues into Flow types using two-tier logic:
1. Primary: Issue type → Flow type
2. Secondary: Effort Category → Flow type (overrides primary for Task/Story only)

Flow Types:
- Feature: New features, improvements
- Defect: Bugs (all bugs regardless of effort category)
- Technical Debt: Technical debt work
- Risk: Security, compliance, regulatory, maintenance, upgrades, spikes

Created: October 31, 2025
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


# Flow type constants
FLOW_TYPE_FEATURE = "Feature"
FLOW_TYPE_DEFECT = "Defect"
FLOW_TYPE_TECHNICAL_DEBT = "Technical Debt"
FLOW_TYPE_RISK = "Risk"


# Effort category constants for flow metrics classification
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
    """
    Classify issue into Flow type using two-tier logic.

    Two-Tier Classification:
    1. Primary (Issue Type):
       - Bug → Defect (ALWAYS, regardless of effort category)
       - Task → Feature (default, can be overridden by effort category)
       - Story → Feature (default, can be overridden by effort category)

    2. Secondary (Effort Category - overrides primary for Task/Story ONLY):
       - "Technical debt" → Technical Debt
       - "Security" → Risk
       - "GDPR Compliance" → Risk
       - "Regulatory" → Risk
       - "Maintenance" → Risk
       - "Upgrades" → Risk
       - "Spikes (Analysis)" → Risk
       - All others → use primary (Feature)

    Args:
        issue: JIRA issue object with fields attribute
        effort_category_field: Custom field ID for effort category (e.g., "customfield_XXXXX")

    Returns:
        Flow type string: "Feature", "Defect", "Technical Debt", or "Risk"

    Examples:
        >>> issue.fields.issuetype.name = "Bug"
        >>> issue.fields.customfield_XXXXX = "New feature"
        >>> get_flow_type(issue)
        "Defect"  # Bug ALWAYS = Defect, ignores effort category

        >>> issue.fields.issuetype.name = "Task"
        >>> issue.fields.customfield_XXXXX = "Technical debt"
        >>> get_flow_type(issue)
        "Technical Debt"  # Effort category overrides primary

        >>> issue.fields.issuetype.name = "Story"
        >>> issue.fields.customfield_XXXXX = "Security"
        >>> get_flow_type(issue)
        "Risk"  # Security effort = Risk

        >>> issue.fields.issuetype.name = "Task"
        >>> issue.fields.customfield_XXXXX = "None"
        >>> get_flow_type(issue)
        "Feature"  # Default for Task with "None" effort category
    """
    # Get issue type - handle both dict and object formats
    fields = (
        issue.get("fields", {})
        if isinstance(issue, dict)
        else getattr(issue, "fields", {})
    )

    if isinstance(fields, dict):
        # Dict format (from JSON)
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
        # Object format (from JIRA library)
        issue_type = (
            getattr(fields.issuetype, "name", None)
            if hasattr(fields, "issuetype")
            else None
        )
        issue_key = getattr(issue, "key", "UNKNOWN")

    if not issue_type:
        logger.warning(f"Issue {issue_key} has no issue type, defaulting to Feature")
        return FLOW_TYPE_FEATURE

    # PRIMARY CLASSIFICATION: Bug ALWAYS = Defect
    if issue_type == "Bug":
        logger.debug(f"Issue {issue_key}: Bug → Defect (ignoring effort category)")
        return FLOW_TYPE_DEFECT

    # For Task and Story: Check effort category (secondary classification)
    # NOTE: Operational Tasks should NEVER reach this function - they're filtered out in metrics_calculator
    if issue_type in ("Task", "Story"):
        # Get effort category - handle both dict and object formats
        if isinstance(fields, dict):
            effort_category = fields.get(effort_category_field)
        else:
            effort_category = getattr(fields, effort_category_field, None)

        # Handle JIRA select field format (dict with 'value' key)
        if isinstance(effort_category, dict):
            effort_category = effort_category.get("value")

        # Handle missing effort category
        if not effort_category or effort_category == "":
            logger.debug(
                f"Issue {issue_key}: Missing effort category, defaulting to Feature"
            )
            return FLOW_TYPE_FEATURE

        # SECONDARY CLASSIFICATION: Effort category overrides
        flow_type = _map_effort_category_to_flow_type(effort_category)

        logger.debug(
            f"Issue {issue_key}: {issue_type} + '{effort_category}' → {flow_type}"
        )
        return flow_type

    # Unknown issue types default to Feature
    logger.debug(f"Issue {issue_key}: Unknown type '{issue_type}' → Feature")
    return FLOW_TYPE_FEATURE


def _map_effort_category_to_flow_type(effort_category: str) -> str:
    """
    Map effort category to Flow type.

    Mapping:
    - "Technical debt" → Technical Debt
    - "Security" → Risk
    - "GDPR Compliance" → Risk
    - "Regulatory" → Risk
    - "Maintenance" → Risk
    - "Upgrades" → Risk
    - "Spikes (Analysis)" → Risk
    - All others → Feature (New feature, Improvement, None)

    Args:
        effort_category: Effort category value from configured custom field

    Returns:
        Flow type string
    """
    # Technical Debt mapping
    if effort_category == EFFORT_TECHNICAL_DEBT:
        return FLOW_TYPE_TECHNICAL_DEBT

    # Risk mappings
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

    # Feature mappings (default for Task/Story)
    feature_categories = {
        EFFORT_NEW_FEATURE,
        EFFORT_IMPROVEMENT,
        EFFORT_NONE,
    }

    if effort_category in feature_categories:
        return FLOW_TYPE_FEATURE

    # Unknown effort category - log warning and default to Feature
    logger.warning(
        f"Unknown effort category: '{effort_category}', defaulting to Feature"
    )
    return FLOW_TYPE_FEATURE


def classify_issues_by_flow_type(
    issues: list, effort_category_field: str
) -> Dict[str, list]:
    """
    Classify a list of issues by Flow type.

    Args:
        issues: List of JIRA issue objects
        effort_category_field: Custom field ID for effort category

    Returns:
        Dictionary mapping Flow type to list of issues:
        {
            "Feature": [issue1, issue2, ...],
            "Defect": [issue3, ...],
            "Technical Debt": [issue4, ...],
            "Risk": [issue5, ...]
        }

    Example:
        >>> issues = fetch_all_issues()
        >>> classified = classify_issues_by_flow_type(issues)
        >>> print(f"Features: {len(classified['Feature'])}")
        Features: 45
        >>> print(f"Defects: {len(classified['Defect'])}")
        Defects: 12
    """
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


def count_by_flow_type(issues: list, effort_category_field: str) -> Dict[str, int]:
    """
    Count issues by Flow type.

    Args:
        issues: List of JIRA issue objects
        effort_category_field: Custom field ID for effort category

    Returns:
        Dictionary mapping Flow type to count:
        {
            "Feature": 45,
            "Defect": 12,
            "Technical Debt": 8,
            "Risk": 5
        }

    Example:
        >>> issues = fetch_completed_issues()
        >>> counts = count_by_flow_type(issues)
        >>> print(f"Total: {sum(counts.values())}")
        Total: 70
    """
    classified = classify_issues_by_flow_type(issues, effort_category_field)

    return {
        flow_type: len(issues_list) for flow_type, issues_list in classified.items()
    }


def get_flow_distribution(issues: list, effort_category_field: str) -> Dict[str, float]:
    """
    Calculate Flow distribution as percentages.

    Args:
        issues: List of JIRA issue objects
        effort_category_field: Custom field ID for effort category

    Returns:
        Dictionary mapping Flow type to percentage:
        {
            "Feature": 64.3,
            "Defect": 17.1,
            "Technical Debt": 11.4,
            "Risk": 7.1
        }

    Example:
        >>> issues = fetch_completed_issues()
        >>> distribution = get_flow_distribution(issues)
        >>> print(f"Feature work: {distribution['Feature']:.1f}%")
        Feature work: 64.3%
    """
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
