/**
 * Client-side callback to toggle 'active' class on panel toggle buttons.
 *
 * This provides immediate visual feedback when panels open/close by:
 * - Adding 'active' class to button when its panel is open
 * - Removing 'active' class when panel is closed
 * - Changing button tooltip dynamically
 * - Showing/hiding backdrop overlay for visual separation
 *
 * The active class triggers CSS styling for solid background and rotated chevron.
 */

window.dash_clientside = Object.assign({}, window.dash_clientside, {
  panelState: {
    /**
     * Update backdrop visibility directly based on panel states.
     * This callback is triggered immediately when any panel opens/closes.
     */
    updateBackdropState: function (parameterOpen, settingsOpen, dataOpen) {
      // Return class based on whether any panel is open
      return parameterOpen || settingsOpen || dataOpen
        ? "panel-backdrop active"
        : "panel-backdrop";
    },

    /**
     * Toggle active class on parameter panel button.
     */
    toggleParameterButton: function (is_open, currentClassName) {
      const button = document.getElementById("btn-expand-parameters");
      if (button) {
        if (is_open) {
          button.title = "Close Parameters";
        } else {
          button.title = "Expand Parameters";
        }
      }

      // Update className by adding/removing 'active'
      if (!currentClassName) currentClassName = "";
      const classes = currentClassName
        .split(" ")
        .filter((c) => c && c !== "active");
      if (is_open) {
        classes.push("active");
      }
      return classes.join(" ");
    },

    /**
     * Toggle active class on settings panel button.
     */
    toggleSettingsButton: function (is_open, currentClassName) {
      const button = document.getElementById("settings-button");
      if (button) {
        if (is_open) {
          button.title = "Close Settings";
        } else {
          button.title = "Expand Settings";
        }
      }

      // Update className by adding/removing 'active'
      if (!currentClassName) currentClassName = "";
      const classes = currentClassName
        .split(" ")
        .filter((c) => c && c !== "active");
      if (is_open) {
        classes.push("active");
      }
      return classes.join(" ");
    },

    /**
     * Toggle active class on data panel button.
     */
    toggleDataButton: function (is_open, currentClassName) {
      const button = document.getElementById("toggle-import-export-panel");
      if (button) {
        if (is_open) {
          button.title = "Close Data";
        } else {
          button.title = "Expand Data";
        }
      }

      // Update className by adding/removing 'active'
      if (!currentClassName) currentClassName = "";
      const classes = currentClassName
        .split(" ")
        .filter((c) => c && c !== "active");
      if (is_open) {
        classes.push("active");
      }
      return classes.join(" ");
    },
  },
});
