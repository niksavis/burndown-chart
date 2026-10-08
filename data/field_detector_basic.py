import logging

logger = logging.getLogger(__name__)


def _detect_code_commit_date_field(
    issues: list[dict], field_defs: dict[str, dict]
) -> str | None:

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

            if field_type == "datetime":
                score += 40
            elif field_type == "date":
                score += 30

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

            if field_type == "datetime":
                score += 40
            elif field_type == "date":
                score += 30

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

    candidates = {}

    custom_fields_seen = set()

    for issue in issues:
        fields_data = issue.get("fields", {})
        for field_id, field_value in fields_data.items():
            if not field_id.startswith("customfield_"):
                continue

            custom_fields_seen.add(field_id)

            if field_id in candidates and candidates[field_id]["score"] == 0:
                continue

            field_def = field_defs.get(field_id, {})
            field_name = field_def.get("name", "").lower()
            field_type = field_def.get("schema", {}).get("type", "")

            if field_id not in candidates:
                candidates[field_id] = {
                    "score": 0,
                    "name": field_def.get("name", field_id),
                    "type": field_type,
                    "values": [],
                }

            score = 0

            if any(
                keyword in field_name
                for keyword in ["story point", "storypoint", "points", "estimate"]
            ):
                score += 50

            if field_type in ["number", "float"]:
                score += 30
            else:
                score -= 20

            if field_value is not None:
                candidates[field_id]["values"].append(field_value)

                if isinstance(field_value, (int, float)):
                    if 0 < field_value <= 100:
                        score += 15
                    elif field_value > 1000:
                        score -= 30
                else:
                    score -= 50

            candidates[field_id]["score"] += score

    logger.info(
        f"[FieldDetector] DEBUG: Found {len(custom_fields_seen)} "
        f"unique custom fields in {len(issues)} issues"
    )
    if custom_fields_seen:
        sample_fields = list(custom_fields_seen)[:10]
        logger.info(f"[FieldDetector] DEBUG: Sample custom fields: {sample_fields}")

    if not candidates:
        logger.warning(
            "[FieldDetector] No story points candidates found. "
            f"Total custom fields scanned: {len(custom_fields_seen)}"
        )
        return None

    candidates = {k: v for k, v in candidates.items() if v["score"] > 0}

    if not candidates:
        return None

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

    if best_candidate[1]["score"] >= 30:
        return best_candidate[0]

    return None


def _detect_sprint_field(issues: list[dict], field_defs: dict[str, dict]) -> str | None:

    candidates = {}

    for issue in issues:
        fields_data = issue.get("fields", {})
        for field_id, field_value in fields_data.items():
            if not field_id.startswith("customfield_"):
                continue

            field_def = field_defs.get(field_id, {})
            field_name = field_def.get("name", "").lower()

            if "sprint" in field_name:
                if field_id not in candidates:
                    candidates[field_id] = {
                        "score": 0,
                        "name": field_def.get("name", field_id),
                        "populated_count": 0,
                        "total_count": 0,
                    }

                candidates[field_id]["total_count"] += 1
                if field_value:
                    candidates[field_id]["score"] += 10
                    candidates[field_id]["populated_count"] += 1

    if candidates:
        for field_id, stats in candidates.items():
            if stats["total_count"] > 0:
                population_rate = stats["populated_count"] / stats["total_count"]
                if population_rate < 0.10:
                    logger.info(
                        f"[FieldDetector] Rejecting sprint field {field_id} - "
                        f"only {population_rate:.1%} populated"
                    )
                    candidates[field_id]["score"] = 0

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

    candidates = {}

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

    if has_standard_parent and parent_total_count > 0:
        population_rate = parent_populated_count / parent_total_count
        if population_rate >= 0.05:
            logger.info(
                f"[FieldDetector] [OK] Standard parent field detected "
                f"({parent_populated_count}/{parent_total_count} "
                "issues have parent data)"
            )
            return "parent"

    for issue in issues:
        fields_data = issue.get("fields", {})
        for field_id, field_value in fields_data.items():
            if not field_id.startswith("customfield_"):
                continue

            field_def = field_defs.get(field_id, {})
            field_name = field_def.get("name", "").lower()

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

                candidates[field_id]["total_count"] += 1
                if field_value:
                    candidates[field_id]["score"] += 10
                    candidates[field_id]["populated_count"] += 1

            if field_id in ["customfield_10006", "customfield_10014"]:
                if field_id not in candidates:
                    candidates[field_id] = {
                        "score": 0,
                        "name": field_def.get("name", field_id),
                        "populated_count": 0,
                        "total_count": 0,
                    }
                candidates[field_id]["score"] += 5

    if candidates:
        for field_id, stats in candidates.items():
            if stats["total_count"] > 0:
                population_rate = stats["populated_count"] / stats["total_count"]
                if population_rate < 0.05:
                    logger.info(
                        f"[FieldDetector] Rejecting parent field {field_id} - "
                        f"only {population_rate:.1%} populated"
                    )
                    candidates[field_id]["score"] = 0

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
