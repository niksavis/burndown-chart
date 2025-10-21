/**
 * Clientside callbacks for JQL Editor synchronization.
 *
 * These run in the browser and handle real-time syncing between:
 * - CodeMirror editor (user types)
 * - Hidden dcc.Input (bridge component)
 * - dcc.Store (Dash state)
 */

if (!window.dash_clientside) {
  window.dash_clientside = {};
}

window.dash_clientside.jqlEditor = {
  /**
   * Sync hidden Input value to dcc.Store.
   *
   * This callback is triggered when the hidden sync Input changes
   * (which happens when CodeMirror updates it via JavaScript).
   *
   * @param {string} inputValue - Current value of hidden sync Input
   * @returns {string} Value to store in dcc.Store
   */
  syncInputToStore: function (inputValue) {
    // PERFORMANCE FIX: Removed verbose logging that was slowing down input
    return inputValue || "";
  },

  /**
   * Sync dcc.Store value to hidden Input.
   *
   * This callback is triggered when the Store is updated externally
   * (e.g., loading a saved query, resetting the editor).
   *
   * @param {string} storeValue - Current value in dcc.Store
   * @returns {string} Value to set in hidden sync Input
   */
  syncStoreToInput: function (storeValue) {
    // PERFORMANCE FIX: Removed verbose logging that was slowing down input
    return storeValue || "";
  },
};
