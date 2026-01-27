"""Reusable toast notification components.

Provides a consistent toast notification system for the application.
Use toasts for non-blocking feedback messages that auto-dismiss.

Usage:
    from ui.toast_notifications import create_toast

    # Success toast
    toast = create_toast("Settings saved!", "success")

    # Warning with custom header
    toast = create_toast("Cache cleared", "warning", header="Cache Status")

    # Error with longer duration
    toast = create_toast("Failed to connect", "danger", duration=5000)
"""

from dash import html
import dash_bootstrap_components as dbc
from typing import Optional, Union, List


def create_toast(
    message: Union[str, List],
    toast_type: str = "info",
    header: Optional[str] = None,
    duration: int = 3000,
    dismissable: bool = True,
    icon: Optional[str] = None,
) -> dbc.Toast:
    """Create a standardized toast notification.

    Args:
        message: Toast message (string or list of Dash components)
        toast_type: Type of toast - "success", "warning", "danger", "info"
        header: Optional header text (auto-generated if None)
        duration: Auto-dismiss duration in milliseconds (0 for no auto-dismiss)
        dismissable: Whether user can manually dismiss the toast
        icon: Optional FontAwesome icon name override

    Returns:
        dbc.Toast component ready to render
    """
    import logging
    import traceback

    logger = logging.getLogger(__name__)

    # Log every toast creation with caller info for debugging
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
        f"[TOAST CREATED] type={toast_type}, header={header or 'auto'}, message={message_preview}",
        extra={
            "operation": "create_toast",
            "toast_type": toast_type,
            "header": header,
            "caller_file": caller_file,
            "caller_function": caller_function,
            "caller_line": caller_line,
        },
    )

    # Default headers based on type
    default_headers = {
        "success": "Success",
        "warning": "Warning",
        "danger": "Error",
        "info": "Info",
    }

    # Default icons based on type
    default_icons = {
        "success": "check-circle",
        "warning": "exclamation-triangle",
        "danger": "times-circle",
        "info": "info-circle",
    }

    # Icon color classes
    icon_colors = {
        "success": "text-success",
        "warning": "text-warning",
        "danger": "text-danger",
        "info": "text-info",
    }

    # Build toast content
    icon_name = icon or default_icons.get(toast_type, "info-circle")
    icon_color = icon_colors.get(toast_type, "text-info")

    if isinstance(message, str):
        content = html.Div(
            [
                html.I(className=f"fas fa-{icon_name} me-2 {icon_color}"),
                message,
            ]
        )
    elif isinstance(message, list):
        # If message is already a list of components, prepend icon
        content = html.Div(
            [html.I(className=f"fas fa-{icon_name} me-2 {icon_color}")] + message
        )
    else:
        # Single component
        content = html.Div(
            [
                html.I(className=f"fas fa-{icon_name} me-2 {icon_color}"),
                message,
            ]
        )

    return dbc.Toast(
        content,
        header=header or default_headers.get(toast_type, "Notification"),
        icon=toast_type,
        is_open=True,
        dismissable=dismissable,
        duration=duration if duration > 0 else None,
        style={"minWidth": "300px"},
    )


def create_success_toast(
    message: str,
    header: Optional[str] = None,
    duration: int = 3000,
    icon: Optional[str] = None,
) -> dbc.Toast:
    """Create a success toast notification.

    Args:
        message: Success message to display
        header: Optional header (defaults to "Success")
        duration: Auto-dismiss duration in ms
        icon: Optional FontAwesome icon name override

    Returns:
        dbc.Toast with success styling
    """
    return create_toast(message, "success", header, duration, icon=icon)


def create_error_toast(
    message: str,
    header: Optional[str] = None,
    duration: int = 5000,
    icon: Optional[str] = None,
) -> dbc.Toast:
    """Create an error toast notification.

    Args:
        message: Error message to display
        header: Optional header (defaults to "Error")
        duration: Auto-dismiss duration in ms (longer for errors)
        icon: Optional FontAwesome icon name override

    Returns:
        dbc.Toast with danger styling
    """
    return create_toast(message, "danger", header, duration, icon=icon)


def create_warning_toast(
    message: str,
    header: Optional[str] = None,
    duration: int = 4000,
    icon: Optional[str] = None,
) -> dbc.Toast:
    """Create a warning toast notification.

    Args:
        message: Warning message to display
        header: Optional header (defaults to "Warning")
        duration: Auto-dismiss duration in ms
        icon: Optional FontAwesome icon name override

    Returns:
        dbc.Toast with warning styling
    """
    return create_toast(message, "warning", header, duration, icon=icon)


def create_info_toast(
    message: str,
    header: Optional[str] = None,
    duration: int = 3000,
    icon: Optional[str] = None,
) -> dbc.Toast:
    """Create an info toast notification.

    Args:
        message: Info message to display
        header: Optional header (defaults to "Info")
        duration: Auto-dismiss duration in ms
        icon: Optional FontAwesome icon name override

    Returns:
        dbc.Toast with info styling
    """
    return create_toast(message, "info", header, duration, icon=icon)
