/**
 * Client-side callback to sync JQL editor textarea to dcc.Store
 *
 * This bridges the gap between the JavaScript-managed textarea
 * and Dash's callback system that reads from dcc.Store.
 */

window.dash_clientside = Object.assign({}, window.dash_clientside, {
  jql_editor: {
    /**
     * Sync textarea value changes to dcc.Store
     * This allows Dash callbacks to read the current editor value
     */
    sync_to_store: function (textarea_value) {
      // Simply return the textarea value to update the Store
      return textarea_value || "";
    },
  },
});
