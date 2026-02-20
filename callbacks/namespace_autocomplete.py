"""Namespace autocomplete callbacks using clientside JavaScript.

This module provides clientside callbacks for namespace autocomplete,
eliminating server round-trips that cause focus loss during typing.
The autocomplete data is pre-built from JIRA metadata when the modal opens.

Architecture:
1. buildAutocompleteData: Runs when metadata loads, builds searchable dataset
2. filterSuggestions: Runs on each keystroke via JavaScript (no Dash callback)
3. collectNamespaceValues: Runs on save/validate button click to gather input values
4. DOM event handlers: Initialize keyboard/click handlers on container elements

CRITICAL: We use dcc.Input for namespace inputs but read values via clientside JS
because:
- dcc.Input is a React controlled component that maintains internal state
- We use native DOM operations to update values for autocomplete selection
- collectNamespaceValues reads directly from DOM to collect values on save/validate

The heavy work is done client-side - Dash only provides the data.
"""

import logging

from dash import ClientsideFunction, Input, Output, clientside_callback

logger = logging.getLogger(__name__)


# Build autocomplete dataset from JIRA metadata when it changes
# This uses the clientside JavaScript function in namespace_autocomplete_clientside.js
clientside_callback(
    ClientsideFunction(
        namespace="namespace_autocomplete", function_name="buildAutocompleteData"
    ),
    Output("namespace-autocomplete-data", "data"),
    Input("jira-metadata-store", "data"),
    prevent_initial_call=True,
)


# Collect namespace input values from DOM when save, validate, or tab switch
# Since we use DOM manipulation for autocomplete, this clientside callback
# reads directly from DOM and stores the result for Python to process
# The trigger type ("save", "validate", or "tab_switch") is detected by the JS function
clientside_callback(
    ClientsideFunction(
        namespace="namespace_autocomplete", function_name="collectNamespaceValues"
    ),
    Output("namespace-collected-values", "data"),
    [
        Input("field-mapping-save-button", "n_clicks"),
        Input("validate-mappings-button", "n_clicks"),
        Input("mappings-tabs", "active_tab"),  # Also collect when switching tabs
    ],
    prevent_initial_call=True,
)


# Note: Suggestion filtering is handled entirely in JavaScript via DOM event listeners
# See assets/namespace_autocomplete_clientside.js for the implementation
# This avoids any server round-trips during typing
