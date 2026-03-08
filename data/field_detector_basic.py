"""Basic field detection helpers for JIRA custom fields.

Contains heuristic detectors for commit dates, completed dates,
story points, sprint, and parent/epic-link fields.
"""

import logging

logger = logging.getLogger(__name__)


def _detect_code_commit_date_field(
    issues: list[dict], field_defs: dict[str, dict]
) -> str | None:
    """Detect code commit date field for DORA Lead Time.

    Heuristics:
    - Field name contains: "commit", "code", "merge", "push", "git"
    - Field type: datetime
    - Has date values in the past
    """
    candidates = {}

    for issue in issues:
        fields_data = issue.get("fields", {})
        for field_id, field_value in fields_data.items():
            if not field_id.startswith("customfield_"):
                continue

            field_def = field_defs.get(field_id, {})
            field_name = field_def.get("name", "").lower()
            field_type = field_def.get("schema", {}).get("type", "")

            score = 0

            # Name matching
            if any(
                kw in field_name
                for kw in [
                    "commit",
                    "code commit",
                    "git",
                    "merge",
                    "push",
                    "source control",
                    "scm",
                ]
            ):
                score += 60

            # Type must be datetime
            if field_type == "datetime":
                score += 40
            elif field_type == "date":
                score += 30

            # Has timestamp value
            if field_value:
                score += 20

            if score > 0:
                if field_id not in candidates:
                    candidates[field_id] = {
                        "score": score,
                        "name": field_def.get("name", field_id),
                    }
                else:
                    candidates[field_id]["score"] += score

    if candidates:
        best = max(candidates.items(), key=lambda x: x[1]["score"])
        if best[1]["score"] >= 60:
            return best[0]

    return None


def _detect_completed_date_field(
    issues: list[dict], field_defs: dict[str, dict]
) -> str | None:
    """Detect completed date field for Flow metrics (alternative to resolutiondate).

    Heuristics:
    - Field name contains: "completed", "resolved", "resolution"
    - Field type: datetime
    - Has date values in the past
    - Different from work_completed_date (broader matching)
    """
    candidates = {}

    for issue in issues:
        fields_data = issue.get("fields", {})
        for field_id, field_value in fields_data.items():
            if not field_id.startswith("customfield_"):
                continue

            field_def = field_defs.get(field_id, {})
            field_name = field_def.get("name", "").lower()
            field_type = field_def.get("schema", {}).get("type", "")

            score = 0

            # Name matching (broader than work_completed_date)
            if any(
                kw in field_name
                for kw in [
                    "completed",
                    "resolved",
                    "resolution",
                    "finish",
                    "done date",
                    "closed date",
                ]
            ):
                score += 60

            # Type must be datetime
            if field_type == "datetime":
                score += 40
            elif field_type == "date":
                score += 30

            # Has timestamp value
            if field_value:
                score += 20

            if score > 0:
                if field_id not in candidates:
                    candidates[field_id] = {
                        "score": score,
                        "name": field_def.get("name", field_id),
                    }
                else:
                    candidates[field_id]["score"] += score

    if candidates:
        best = max(candidates.items(), key=lambda x: x[1]["score"])
        if best[1]["score"] >= 60:
            return best[0]

    return None


def _detect_points_field(issues: list[dict], field_defs: dict[str, dict]) -> str | None:
    """Detect story points field using fuzzy matching and data analysis.

    Heuristics:
    - Field name contains: "story point", "estimate", "effort", "size"
    - Field type: number
    - Values: Small positive numbers (typically 1-100)
    - Usage: Present in Story/Task issues, often missing in Bugs
    """
    candidates = {}

    # DEBUG: Track custom fields found
    custom_fields_seen = set()

    # Scan all custom fields in issues
    for issue in issues:
        fields_data = issue.get("fields", {})
        for field_id, field_value in fields_data.items():
            # Only check custom fields
            if not field_id.startswith("customfield_"):
                continue

            custom_fields_seen.add(field_id)

            # Skip if already ruled out
            if field_id in candidates and candidates[field_id]["score"] == 0:
                continue

            # Get field definition
            field_def = field_defs.get(field_id, {})
            field_name = field_def.get("name", "").lower()
            field_type = field_def.get("schema", {}).get("type", "")

            # Initialize candidate tracking
            if field_id not in candidates:
                candidates[field_id] = {
                    "score": 0,
                    "name": field_def.get("name", field_id),
                    "type": field_type,
                    "values": [],
                }

            # Scoring rules
            score = 0

            # Rule 1: Field name matching (strongest signal)
            if any(
                keyword in field_name
                for keyword in ["story point", "storypoint", "points", "estimate"]
            ):
                score += 50

            # Rule 2: Field type is number (CRITICAL for story points)
            if field_type in ["number", "float"]:
                score += 30  # Increased from 20 - numeric type is essential
            else:
                score -= 20  # Penalize non-numeric fields

            # Rule 3: Check actual value
            if field_value is not None:
                candidates[field_id]["values"].append(field_value)

                # Numeric values between 0-100 (typical story point range)
                if isinstance(field_value, (int, float)):
                    if 0 < field_value <= 100:
                        score += 15
                    elif field_value > 1000:  # Too large to be story points
                        score -= 30
                else:
                    # Non-numeric disqualifies as story points
                    score -= 50

            candidates[field_id]["score"] += score

    # DEBUG: Log what custom fields were found
    logger.info(
        f"[FieldDetector] DEBUG: Found {len(custom_fields_seen)} "
        f"unique custom fields in {len(issues)} issues"
    )
    if custom_fields_seen:
        sample_fields = list(custom_fields_seen)[:10]
        logger.info(f"[FieldDetector] DEBUG: Sample custom fields: {sample_fields}")

    # Find best candidate
    if not candidates:
        logger.warning(
            "[FieldDetector] No story points candidates found. "
            f"Total custom fields scanned: {len(custom_fields_seen)}"
        )
        return None

    # Filter out negative scores
    candidates = {k: v for k, v in candidates.items() if v["score"] > 0}

    if not candidates:
        return None

    # Sort by score
    best_candidate = max(candidates.items(), key=lambda x: x[1]["score"])

    logger.info(
        f"[FieldDetector] Points field candidates: {
            [
                (k, v['score'], v['name'])
                for k, v in sorted(
                    candidates.items(), key=lambda x: x[1]['score'], reverse=True
                )[:3]
            ]
        }"
    )

    # Return if score is confident enough
    if best_candidate[1]["score"] >= 30:  # Minimum confidence threshold
        return best_candidate[0]

    return None


def _detect_sprint_field(issues: list[dict], field_defs: dict[str, dict]) -> str | None:
    """Detect sprint field.

    Heuristics:
    - Field name contains: "sprint"
    - Field type: array, string, or custom sprint type
    - Values: Sprint names/objects with sprint data
    - CRITICAL: Must have actual sprint data in at least 10% of sampled issues
    """
    candidates = {}

    for issue in issues:
        fields_data = issue.get("fields", {})
        for field_id, field_value in fields_data.items():
            if not field_id.startswith("customfield_"):
                continue

            field_def = field_defs.get(field_id, {})
            field_name = field_def.get("name", "").lower()

            # Strong signal: "sprint" in name
            if "sprint" in field_name:
                if field_id not in candidates:
                    candidates[field_id] = {
                        "score": 0,
                        "name": field_def.get("name", field_id),
                        "populated_count": 0,
                        "total_count": 0,
                    }

                # Check if field has actual sprint data (not null/empty)
                candidates[field_id]["total_count"] += 1
                if field_value:  # Has sprint data
                    candidates[field_id]["score"] += 10
                    candidates[field_id]["populated_count"] += 1

    # Return sprint field even with low population.
    # Many JIRA instances (especially test/demo instances) have sprint field
    # but few sprints.
    if candidates:
        for field_id, stats in candidates.items():
            if stats["total_count"] > 0:
                population_rate = stats["populated_count"] / stats["total_count"]
                if population_rate < 0.10:  # Less than 10% populated
                    logger.info(
                        f"[FieldDetector] Rejecting sprint field {field_id} - "
                        f"only {population_rate:.1%} populated"
                    )
                    candidates[field_id]["score"] = 0  # Reject

        # Get best candidate with score > 0
        valid_candidates = {k: v for k, v in candidates.items() if v["score"] > 0}
        if valid_candidates:
            best = max(valid_candidates.items(), key=lambda x: x[1]["score"])
            logger.info(
                f"[FieldDetector] [OK] Sprint field detected: {best[0]} "
                f"({best[1]['populated_count']}/{best[1]['total_count']} "
                "issues have sprint data)"
            )
            return best[0]

    logger.info(
        "[FieldDetector] No sprint field found with sufficient data. "
        "Scope calculations will use all issues without sprint filtering."
    )
    return None


def _detect_parent_field(issues: list[dict], field_defs: dict[str, dict]) -> str | None:
    """Detect parent/Epic Link field for epic hierarchy.

    Heuristics:
    - Field name contains: "epic link", "parent", "epic"
    - Field type: object, string, or custom epic type
    - Common Epic Link IDs: customfield_10006, customfield_10014
    - Fallback: Check for standard "parent" field
    - Must have actual parent data in at least 5% of sampled issues
    """
    candidates = {}

    # Check for standard parent field first
    has_standard_parent = False
    parent_populated_count = 0
    parent_total_count = 0

    for issue in issues:
        fields_data = issue.get("fields", {})
        if "parent" in fields_data:
            parent_total_count += 1
            if fields_data.get("parent"):
                has_standard_parent = True
                parent_populated_count += 1

    # If standard parent field has data, use it
    if has_standard_parent and parent_total_count > 0:
        population_rate = parent_populated_count / parent_total_count
        if population_rate >= 0.05:  # At least 5% populated
            logger.info(
                f"[FieldDetector] [OK] Standard parent field detected "
                f"({parent_populated_count}/{parent_total_count} "
                "issues have parent data)"
            )
            return "parent"

    # Check custom fields for Epic Link
    for issue in issues:
        fields_data = issue.get("fields", {})
        for field_id, field_value in fields_data.items():
            if not field_id.startswith("customfield_"):
                continue

            field_def = field_defs.get(field_id, {})
            field_name = field_def.get("name", "").lower()

            # Strong signals: "epic link", "parent", "epic" in name
            if any(
                keyword in field_name for keyword in ["epic link", "parent", "epic"]
            ):
                if field_id not in candidates:
                    candidates[field_id] = {
                        "score": 0,
                        "name": field_def.get("name", field_id),
                        "populated_count": 0,
                        "total_count": 0,
                    }

                # Check if field has actual parent data (not null/empty)
                candidates[field_id]["total_count"] += 1
                if field_value:  # Has parent data
                    candidates[field_id]["score"] += 10
                    candidates[field_id]["populated_count"] += 1

            # Boost score for common Epic Link field IDs
            if field_id in ["customfield_10006", "customfield_10014"]:
                if field_id not in candidates:
                    candidates[field_id] = {
                        "score": 0,
                        "name": field_def.get("name", field_id),
                        "populated_count": 0,
                        "total_count": 0,
                    }
                candidates[field_id]["score"] += 5  # Bonus for common IDs

    # Return parent field with at least 5% population
    if candidates:
        for field_id, stats in candidates.items():
            if stats["total_count"] > 0:
                population_rate = stats["populated_count"] / stats["total_count"]
                if population_rate < 0.05:  # Less than 5% populated
                    logger.info(
                        f"[FieldDetector] Rejecting parent field {field_id} - "
                        f"only {population_rate:.1%} populated"
                    )
                    candidates[field_id]["score"] = 0  # Reject

        # Get best candidate with score > 0
        valid_candidates = {k: v for k, v in candidates.items() if v["score"] > 0}
        if valid_candidates:
            best = max(valid_candidates.items(), key=lambda x: x[1]["score"])
            logger.info(
                f"[FieldDetector] [OK] Parent/Epic Link field detected: {best[0]} "
                f"({best[1]['populated_count']}/{best[1]['total_count']} "
                "issues have parent data)"
            )
            return best[0]

    logger.info(
        "[FieldDetector] No parent/Epic Link field found. "
        "Active Work Timeline will not show epic hierarchy."
    )
    return None
