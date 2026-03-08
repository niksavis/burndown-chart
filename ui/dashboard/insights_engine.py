"""Insights Engine - re-export shim.

Public API is preserved here; implementations have been split into:
- insights_engine_scoring.py: scoring logic and insight generation
- insights_engine_rendering.py: Dash component rendering for insight cards
"""

from __future__ import annotations

from ui.dashboard.insights_engine_rendering import create_insights_section  # noqa: F401

__all__ = ["create_insights_section"]
