import json
import logging
import time
from datetime import datetime, timedelta

from dash import (
    ClientsideFunction,
    Input,
    Output,
    State,
    callback,
    clientside_callback,
    ctx,
    html,
    no_update,
)

from data.import_export import export_profile_with_mode, resolve_profile_conflict
from data.import_export_changelog import normalize_imported_changelog_entries
from data.persistence.factory import get_backend
from data.query_manager import get_active_profile_id, get_active_query_id
from ui.toast_notifications import create_toast

logger = logging.getLogger(__name__)


@callback(
    Output("export-profile-download", "data"),
    Output("app-notifications", "children", allow_duplicate=True),
    Input("export-profile-button", "n_clicks"),
    State("export-mode-radio", "value"),
    State("include-token-checkbox", "value"),
    State("include-budget-checkbox", "value"),
    State("include-changelog-checkbox", "value"),
    prevent_initial_call=True,
)
def export_full_profile(
    n_clicks, export_mode, include_token, include_budget, include_changelog
):

    if not n_clicks:
        return no_update, no_update

    try:
        profile_id = get_active_profile_id()
        query_id = get_active_query_id()

        if not profile_id or not query_id:
            logger.error("[Export] Missing active profile/query")
            return no_update, create_toast(
                "No active profile or query selected", "danger", header="Export Failed"
            )

        export_package = export_profile_with_mode(
            profile_id=profile_id,
            query_id=query_id,
            export_mode=export_mode or "CONFIG_ONLY",
            include_token=bool(include_token),
            include_budget=bool(include_budget),
            include_changelog=bool(include_changelog),
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        profile_name = profile_id.replace(" ", "_").replace("/", "_")
        query_name = query_id.replace(" ", "_").replace("/", "_")

        mode_suffix = "config_only" if export_mode == "CONFIG_ONLY" else "full_data"

        token_suffix = "_with_token" if bool(include_token) else ""

        filename = (
            f"{timestamp}_{profile_name}_{query_name}_export_"
            f"{mode_suffix}{token_suffix}.json"
        )

        json_content = json.dumps(export_package, indent=2, ensure_ascii=False)
        file_size_kb = len(json_content) / 1024

        mode_display = (
            "Configuration only" if export_mode == "CONFIG_ONLY" else "Full data"
        )

        logger.info(
            "Exported profile/query data: "
            f"{file_size_kb:.1f} KB, mode={export_mode}, "
            f"token={include_token}"
        )

        return (
            {"content": json_content, "filename": filename},
            create_toast(
                "Profile exported successfully "
                f"({file_size_kb:.1f} KB). Mode: {mode_display}",
                toast_type="success",
                header="Export Successful",
                duration=4000,
            ),
        )

    except Exception as e:
        logger.error(f"Profile export failed: {e}", exc_info=True)
        return no_update, create_toast(
            f"Could not export profile: {str(e)}", "danger", header="Export Failed"
        )


@callback(
    Output("conflict-resolution-modal", "is_open"),
    Output("conflict-profile-name", "children"),
    Output("import-data-store", "data"),
    Output("conflict-rename-input", "placeholder"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    prevent_initial_call=True,
)
def detect_import_conflict(contents, filename):
    if not contents:
        return no_update, no_update, no_update, no_update

    try:
        import base64  # noqa: PLC0415

        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        import_data = json.loads(decoded.decode("utf-8"))

        profile_data = import_data.get("profile_data", {})
        profile_id = profile_data.get("id") or import_data.get("profile_id")
        profile_name = profile_data.get("name", profile_id)

        if not profile_id:
            return False, "", None, no_update

        backend = get_backend()
        existing_profile = backend.get_profile(profile_id)

        if existing_profile:
            logger.info(
                f"Import conflict detected: Profile '{profile_id}' already exists"
            )
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            friendly_base = profile_name or profile_id
            suggested_name = f"{friendly_base} (imported {timestamp})"
            return True, profile_name, import_data, suggested_name
        else:
            logger.info(
                f"No conflict detected for profile '{profile_id}' - "
                "proceeding with import"
            )
            return False, "", import_data, no_update

    except Exception as e:
        logger.error(f"Conflict detection failed: {e}", exc_info=True)
        return False, "", None, no_update


@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Output("metrics-refresh-trigger", "data", allow_duplicate=True),
    Output("profile-switch-trigger", "data", allow_duplicate=True),
    Output("upload-data", "contents", allow_duplicate=True),
    Input("import-data-store", "data"),
    State("conflict-resolution-modal", "is_open"),
    prevent_initial_call=True,
)
def import_without_conflict(import_data, modal_is_open):
    if not import_data or modal_is_open:
        return no_update, no_update, no_update, no_update
    toast, refresh, profile_switch = perform_import(import_data)
    return toast, refresh, profile_switch, None


@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Output("conflict-resolution-modal", "is_open", allow_duplicate=True),
    Output("metrics-refresh-trigger", "data", allow_duplicate=True),
    Output("profile-switch-trigger", "data", allow_duplicate=True),
    Output("upload-data", "contents", allow_duplicate=True),
    Input("conflict-proceed", "n_clicks"),
    Input("conflict-cancel", "n_clicks"),
    State("conflict-resolution-strategy", "value"),
    State("conflict-rename-input", "value"),
    State("conflict-rename-input", "placeholder"),
    State("import-data-store", "data"),
    prevent_initial_call=True,
)
def handle_conflict_resolution(
    proceed_clicks,
    cancel_clicks,
    strategy,
    custom_name,
    rename_placeholder,
    import_data,
):

    if not ctx.triggered or not import_data:
        return no_update, no_update, no_update, no_update, no_update

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "conflict-cancel":
        return (
            create_toast(
                "Import cancelled by user",
                toast_type="info",
                header="Import Cancelled",
                duration=3000,
            ),
            False,
            no_update,
            no_update,
            None,
        )

    resolved_name = custom_name
    if (
        strategy == "rename"
        and (not custom_name or not custom_name.strip())
        and rename_placeholder
    ):
        resolved_name = rename_placeholder

    toast, refresh_trigger, profile_switch = perform_import(
        import_data, strategy, resolved_name
    )
    return toast, False, refresh_trigger, profile_switch, None


def perform_import(import_data, conflict_strategy=None, custom_name=None):

    try:
        backend = get_backend()

        profile_data = import_data.get("profile_data", {})
        profile_id = profile_data.get("id") or import_data.get("profile_id")

        manifest = import_data.get("manifest", {})
        export_mode = manifest.get("export_mode", "FULL_DATA")
        is_config_only = export_mode == "CONFIG_ONLY"

        if conflict_strategy:
            existing_profile = backend.get_profile(profile_id)
            if existing_profile:
                if (
                    conflict_strategy == "rename"
                    and custom_name
                    and custom_name.strip()
                ):
                    import copy  # noqa: PLC0415

                    final_profile_id = custom_name.strip()

                    all_profiles = backend.list_profiles()
                    for profile in all_profiles:
                        if profile["name"].lower() == final_profile_id.lower():
                            return (
                                create_toast(
                                    [
                                        html.Div(
                                            "Import failed: Profile with name "
                                            f"'{final_profile_id}' already exists."
                                        ),
                                        html.Div(
                                            "Please choose a different name "
                                            "or use the Overwrite option.",
                                            className="mt-2 text-muted",
                                        ),
                                    ],
                                    toast_type="warning",
                                    header="Duplicate Profile Name",
                                    duration=8000,
                                ),
                                no_update,
                                no_update,
                            )

                    resolved_data = copy.deepcopy(profile_data)
                    resolved_data["id"] = final_profile_id
                    resolved_data["name"] = final_profile_id
                else:
                    final_profile_id, resolved_data = resolve_profile_conflict(
                        profile_id, conflict_strategy, profile_data, existing_profile
                    )

                profile_id = final_profile_id
                profile_data = resolved_data

        if "created_at" not in profile_data:
            profile_data["created_at"] = datetime.now().isoformat()
        if "last_used" not in profile_data:
            profile_data["last_used"] = datetime.now().isoformat()

        logger.info(
            "[Import] Saving profile with "
            f"show_points={profile_data.get('show_points')} "
            f"(type: {type(profile_data.get('show_points'))})"
        )

        backend.save_profile(profile_data)
        logger.info(f"Imported profile '{profile_id}' to database")

        query_data_dict = import_data.get("query_data", {})
        imported_query_count = 0
        first_imported_query_id = None
        budget_imported = False

        if query_data_dict:
            for exported_query_id, query_data in query_data_dict.items():
                query_metadata = query_data.get("query_metadata", {})
                query_name = query_metadata.get(
                    "name", f"Imported Query {exported_query_id}"
                )
                query_jql = query_metadata.get("jql", "")

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                created_query_id = f"q_{timestamp}"

                query_record = {
                    "id": created_query_id,
                    "name": query_name,
                    "jql": query_jql,
                    "created_at": query_metadata.get(
                        "created_at", datetime.now().isoformat()
                    ),
                    "last_used": query_metadata.get(
                        "last_used", datetime.now().isoformat()
                    ),
                }
                backend.save_query(profile_id, query_record)

                if first_imported_query_id is None:
                    first_imported_query_id = created_query_id

                if export_mode == "FULL_DATA":
                    if "jira_cache" in query_data:
                        issues = query_data["jira_cache"].get("issues", [])
                        if issues:
                            valid_issues = []
                            invalid_count = 0
                            for issue in issues:
                                issue_key = issue.get("key") or issue.get("issue_key")
                                if not issue_key:
                                    invalid_count += 1
                                    logger.warning(
                                        "Skipping issue without 'key' or "
                                        f"'issue_key' in query '{query_name}'"
                                    )
                                    continue

                                if "key" not in issue and "issue_key" in issue:
                                    issue["key"] = issue["issue_key"]

                                if "fields" not in issue:
                                    issue["fields"] = {
                                        "summary": issue.get("summary", ""),
                                        "status": {"name": issue.get("status", "")},
                                        "assignee": {
                                            "displayName": issue.get("assignee")
                                        }
                                        if issue.get("assignee")
                                        else {},
                                        "issuetype": {
                                            "name": issue.get("issue_type", "")
                                        },
                                        "priority": {"name": issue.get("priority")}
                                        if issue.get("priority")
                                        else {},
                                        "resolution": {"name": issue.get("resolution")}
                                        if issue.get("resolution")
                                        else {},
                                        "created": issue.get("created"),
                                        "updated": issue.get("updated"),
                                        "resolutiondate": issue.get("resolved"),
                                        "project": {
                                            "key": issue.get("project_key", ""),
                                            "name": issue.get("project_name", ""),
                                        },
                                        "fixVersions": issue.get("fixVersions", [])
                                        if isinstance(issue.get("fixVersions"), list)
                                        else json.loads(
                                            issue.get("fix_versions") or "[]"
                                        ),
                                        "labels": issue.get("labels", [])
                                        if isinstance(issue.get("labels"), list)
                                        else json.loads(issue.get("labels") or "[]"),
                                        "components": issue.get("components", [])
                                        if isinstance(issue.get("components"), list)
                                        else json.loads(
                                            issue.get("components") or "[]"
                                        ),
                                    }

                                    if "custom_fields" in issue:
                                        custom_fields = issue.get("custom_fields")
                                        if isinstance(custom_fields, str):
                                            custom_fields = json.loads(custom_fields)
                                        if isinstance(custom_fields, dict):
                                            issue["fields"].update(custom_fields)

                                    if (
                                        "points" in issue
                                        and issue["points"] is not None
                                    ):
                                        pass

                                if "fetched_at" not in issue:
                                    issue["fetched_at"] = datetime.now().isoformat()
                                if "version" not in issue:
                                    issue["version"] = 1
                                valid_issues.append(issue)

                            if valid_issues:
                                cache_key = f"import_{created_query_id}"
                                expires_at = datetime.now() + timedelta(days=1)
                                backend.save_issues_batch(
                                    profile_id,
                                    created_query_id,
                                    cache_key,
                                    valid_issues,
                                    expires_at,
                                )
                                logger.info(
                                    "Imported "
                                    f"{len(valid_issues)} valid issues "
                                    f"for query '{query_name}'"
                                    + (
                                        f" ({invalid_count} invalid issues skipped)"
                                        if invalid_count > 0
                                        else ""
                                    )
                                )

                    if "statistics" in query_data:
                        statistics = query_data["statistics"]
                        if statistics:
                            backend.save_statistics_batch(
                                profile_id, created_query_id, statistics
                            )
                            logger.info(
                                f"Imported {len(statistics)} statistics "
                                f"for query '{query_name}'"
                            )

                    if "project_scope" in query_data:
                        project_scope = query_data["project_scope"]
                        if project_scope:
                            backend.save_scope(
                                profile_id, created_query_id, project_scope
                            )
                            logger.info(
                                f"Imported project scope for query '{query_name}': "
                                f"total_items={project_scope.get('total_items')}, "
                                "estimated_items="
                                f"{project_scope.get('estimated_items')}, "
                                "total_points="
                                f"{project_scope.get('remaining_total_points')}, "
                                f"estimated_points={project_scope.get('estimated_points')}"
                            )

                    if "metrics" in query_data:
                        metrics = query_data["metrics"]
                        if metrics:
                            backend.save_metrics_batch(
                                profile_id, created_query_id, metrics
                            )
                            logger.info(
                                "Imported "
                                f"{len(metrics)} metrics data points "
                                f"for query '{query_name}'"
                            )

                    if "changelog_entries" in query_data:
                        changelog_entries = query_data["changelog_entries"]
                        if changelog_entries:
                            normalized_entries = normalize_imported_changelog_entries(
                                changelog_entries
                            )
                            if normalized_entries:
                                expires_at = datetime.now() + timedelta(days=365)
                                backend.save_changelog_batch(
                                    profile_id,
                                    created_query_id,
                                    normalized_entries,
                                    expires_at,
                                )
                                logger.info(
                                    "Imported "
                                    f"{len(normalized_entries)} changelog entries "
                                    f"for query '{query_name}'"
                                )

                if "budget_settings" in query_data:
                    budget_settings = query_data["budget_settings"]
                    budget_settings["created_at"] = datetime.now().isoformat()
                    budget_settings["updated_at"] = datetime.now().isoformat()
                    backend.save_budget_settings(
                        profile_id, created_query_id, budget_settings
                    )
                    budget_imported = True
                    logger.info(f"Imported budget settings for query '{query_name}'")

                if "budget_revisions" in query_data:
                    budget_revisions = query_data["budget_revisions"]
                    if budget_revisions:
                        backend.save_budget_revisions(
                            profile_id, created_query_id, budget_revisions
                        )
                        logger.info(
                            "Imported "
                            f"{len(budget_revisions)} budget revisions "
                            f"for query '{query_name}'"
                        )

                imported_query_count += 1
                logger.info(f"Imported query '{query_name}' as {created_query_id}")

            logger.info(
                f"Successfully imported {imported_query_count} queries "
                f"for profile '{profile_id}'"
            )

        active_query_id = (
            first_imported_query_id or query_data_dict.keys()[0]
            if query_data_dict
            else None
        )

        if active_query_id:
            backend.set_app_state("active_profile_id", profile_id)
            backend.set_app_state("active_query_id", active_query_id)

        strategy_msg = f" ({conflict_strategy} strategy)" if conflict_strategy else ""
        logger.info(
            f"Imported profile {profile_id} with {imported_query_count} queries, "
            f"active={active_query_id}, mode={export_mode}{strategy_msg}"
        )

        has_token = bool(profile_data.get("jira_config", {}).get("token", "").strip())

        if is_config_only:
            query_count_msg = (
                f"{imported_query_count} queries"
                if imported_query_count > 1
                else "1 query"
            )
            warning_parts = [
                html.Div(
                    f"Successfully imported profile '{profile_id}' "
                    f"with {query_count_msg}"
                ),
                html.Div(
                    "Warning: This is a configuration-only import. "
                    "Connect to JIRA and click 'Update Data' to fetch issue data.",
                    className="mt-2 text-warning",
                ),
            ]

            if not has_token:
                warning_parts.append(
                    html.Div(
                        "JIRA token not included in import. "
                        "Go to Settings → Configure JIRA Connection to add your token. "
                        "Field mappings will be empty until token is configured.",
                        className="mt-2 text-info fw-bold",
                    )
                )

            if budget_imported:
                warning_parts.append(
                    html.Div(
                        "Budget data included in import and has been configured.",
                        className="mt-2 text-success",
                    )
                )
            else:
                warning_parts.append(
                    html.Div(
                        "Budget data not included. Configure in Budget tab if needed.",
                        className="mt-2 text-muted",
                    )
                )

            return (
                create_toast(
                    warning_parts,
                    toast_type="info",
                    header="Config Import Complete",
                    duration=20000,
                ),
                time.time(),
                time.time(),
            )
        else:
            query_count_msg = (
                f"{imported_query_count} queries"
                if imported_query_count > 1
                else "1 query"
            )
            success_parts = [
                html.Div(
                    f"Successfully imported profile '{profile_id}' "
                    f"with {query_count_msg}"
                ),
                html.Div(
                    "Data loaded successfully. Select a query from the dropdown.",
                    className="mt-2",
                ),
            ]

            if not has_token:
                success_parts.append(
                    html.Div(
                        "JIRA token not included. Field mappings will be empty "
                        "until you add your token "
                        "in Settings → Configure JIRA Connection.",
                        className="mt-2 text-warning fw-bold",
                    )
                )

            if budget_imported:
                success_parts.append(
                    html.Div(
                        "Budget data included in import and has been configured.",
                        className="mt-2 text-success",
                    )
                )
            else:
                success_parts.append(
                    html.Div(
                        "Budget data not included. Configure in Budget tab if needed.",
                        className="mt-2 text-muted",
                    )
                )

            return (
                create_toast(
                    success_parts,
                    toast_type="success",
                    header="Import Complete",
                    duration=15000 if not has_token else 10000,
                ),
                int(time.time() * 1000),
                time.time(),
            )

    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        return (
            create_toast(
                [html.Div(f"Import failed: {str(e)}")],
                toast_type="danger",
                header="Import Failed",
                duration=10000,
            ),
            no_update,
            no_update,
        )


@callback(
    Output("token-warning-modal", "is_open"),
    Input("include-token-checkbox", "value"),
    Input("token-warning-proceed", "n_clicks"),
    Input("token-warning-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def show_token_warning_callback(include_token, proceed_clicks, cancel_clicks):

    if not ctx.triggered:
        return no_update

    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if triggered_id == "include-token-checkbox" and include_token:
        return True

    if triggered_id in ["token-warning-proceed", "token-warning-cancel"]:
        return False

    return no_update


@callback(
    Output("include-token-checkbox", "value", allow_duplicate=True),
    Input("token-warning-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_token_warning_callback(cancel_clicks):

    if not ctx.triggered:
        return no_update

    return False


clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="toggleRenameInput"),
    Output("conflict-rename-section", "style"),
    Input("conflict-resolution-strategy", "value"),
)
