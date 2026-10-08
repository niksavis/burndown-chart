import dash_bootstrap_components as dbc
from dash import html


def create_toast(
    message: str | list,
    toast_type: str = "info",
    header: str | None = None,
    duration: int = 3000,
    dismissable: bool = True,
    icon: str | None = None,
) -> dbc.Toast:

    import logging  # noqa: PLC0415
    import traceback  # noqa: PLC0415

    logger = logging.getLogger(__name__)

    caller_info = traceback.extract_stack()[-2]
    caller_file = caller_info.filename.split("\\")[-1]
    caller_function = caller_info.name
    caller_line = caller_info.lineno

    message_preview = (
        str(message)[:100]
        if isinstance(message, str)
        else f"[{len(message)} components]"
    )

    logger.info(
        f"[TOAST CREATED] type={toast_type}, "
        f"header={header or 'auto'}, message={message_preview}",
        extra={
            "operation": "create_toast",
            "toast_type": toast_type,
            "header": header,
            "caller_file": caller_file,
            "caller_function": caller_function,
            "caller_line": caller_line,
        },
    )

    default_headers = {
        "success": "Success",
        "warning": "Warning",
        "danger": "Error",
        "info": "Info",
    }

    default_icons = {
        "success": "check-circle",
        "warning": "exclamation-triangle",
        "danger": "times-circle",
        "info": "info-circle",
    }

    icon_colors = {
        "success": "text-success",
        "warning": "text-warning",
        "danger": "text-danger",
        "info": "text-info",
    }

    icon_name = icon or default_icons.get(toast_type, "info-circle")
    icon_color = icon_colors.get(toast_type, "text-info")

    header_text = header or default_headers.get(toast_type, "Notification")
    custom_header = html.Div(
        [
            html.I(className=f"fas fa-{icon_name} me-2 {icon_color}"),
            html.Strong(header_text),
        ],
        className="d-flex align-items-center",
    )

    if isinstance(message, str):
        content = message
    elif isinstance(message, list):
        content = html.Div(message)
    else:
        content = message

    return dbc.Toast(
        content,
        header=custom_header,
        is_open=True,
        dismissable=dismissable,
        duration=duration if duration > 0 else None,
        className="app-toast",
    )


def create_success_toast(
    message: str,
    header: str | None = None,
    duration: int = 3000,
    icon: str | None = None,
) -> dbc.Toast:

    return create_toast(message, "success", header, duration, icon=icon)


def create_error_toast(
    message: str,
    header: str | None = None,
    duration: int = 5000,
    icon: str | None = None,
) -> dbc.Toast:

    return create_toast(message, "danger", header, duration, icon=icon)


def create_warning_toast(
    message: str,
    header: str | None = None,
    duration: int = 4000,
    icon: str | None = None,
) -> dbc.Toast:

    return create_toast(message, "warning", header, duration, icon=icon)


def create_info_toast(
    message: str,
    header: str | None = None,
    duration: int = 3000,
    icon: str | None = None,
) -> dbc.Toast:

    return create_toast(message, "info", header, duration, icon=icon)
