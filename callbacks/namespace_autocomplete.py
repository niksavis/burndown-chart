import logging

from dash import ClientsideFunction, Input, Output, clientside_callback

logger = logging.getLogger(__name__)


clientside_callback(
    ClientsideFunction(
        namespace="namespace_autocomplete", function_name="buildAutocompleteData"
    ),
    Output("namespace-autocomplete-data", "data"),
    Input("jira-metadata-store", "data"),
    prevent_initial_call=True,
)


clientside_callback(
    ClientsideFunction(
        namespace="namespace_autocomplete", function_name="collectNamespaceValues"
    ),
    Output("namespace-collected-values", "data"),
    [
        Input("field-mapping-save-button", "n_clicks"),
        Input("validate-mappings-button", "n_clicks"),
        Input("mappings-tabs", "active_tab"),
    ],
    prevent_initial_call=True,
)
