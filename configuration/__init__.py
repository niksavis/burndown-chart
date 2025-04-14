"""
Configuration package.

This package contains all configuration related modules.
"""

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
]
