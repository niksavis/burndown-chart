"""
Configuration Module

This module contains configuration settings for the burndown chart application.
"""

# Application version - used in the UI and for tracking
# Follow semantic versioning (MAJOR.MINOR.PATCH)
__version__ = "1.0.0"

from configuration.settings import (
    # Constants
    DEFAULT_PERT_FACTOR,
    DEFAULT_TOTAL_ITEMS,
    DEFAULT_TOTAL_POINTS,
    DEFAULT_DEADLINE,
    DEFAULT_ESTIMATED_ITEMS,
    DEFAULT_ESTIMATED_POINTS,
    DEFAULT_DATA_POINTS_COUNT,
    # File paths
    SETTINGS_FILE,
    STATISTICS_FILE,
    # Data structures
    SAMPLE_DATA,
    COLOR_PALETTE,
    HELP_TEXTS,
    # Logging
    logger,
)

from configuration.server import (
    get_server_config,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_SERVER_MODE,
)

# Define public API
__all__ = [
    "DEFAULT_PERT_FACTOR",
    "DEFAULT_TOTAL_ITEMS",
    "DEFAULT_TOTAL_POINTS",
    "DEFAULT_DEADLINE",
    "DEFAULT_ESTIMATED_ITEMS",
    "DEFAULT_ESTIMATED_POINTS",
    "DEFAULT_DATA_POINTS_COUNT",
    "SETTINGS_FILE",
    "STATISTICS_FILE",
    "SAMPLE_DATA",
    "COLOR_PALETTE",
    "HELP_TEXTS",
    "logger",
    "__version__",
    # Server configuration
    "get_server_config",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "DEFAULT_SERVER_MODE",
]
