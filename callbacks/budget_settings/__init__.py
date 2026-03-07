"""
Budget settings callbacks package.

Imports all sub-modules to register Dash callbacks at startup.
Split by feature:
  _load.py    -- load, display, and populate callbacks
  _save.py    -- save/update budget callback
  _history.py -- revision history and pagination callbacks
  _delete.py  -- danger-zone toggles and delete callbacks
"""

from callbacks.budget_settings import (  # noqa: F401
    _delete,
    _history,
    _load,
    _save,
)
