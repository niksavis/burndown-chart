/**
 * Clientside callbacks for import conflict resolution UI
 */

window.dash_clientside = Object.assign({}, window.dash_clientside, {
  clientside: {
    /**
     * Toggle visibility of rename input section based on selected strategy
     * @param {string} strategy - Selected conflict resolution strategy ('merge', 'overwrite', or 'rename')
     * @returns {object} Style object to show/hide the rename section
     */
    toggleRenameInput: function (strategy) {
      if (strategy === "rename") {
        return { display: "block" };
      }
      return { display: "none" };
    },
  },
});
