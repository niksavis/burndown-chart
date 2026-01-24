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

/**
 * Update backdrop visibility based on whether any panel is open
 */
function updateBackdrop() {
  const parameterOpen = document
    .getElementById("parameter-collapse")
    ?.classList.contains("show");
  const settingsOpen = document
    .getElementById("settings-collapse")
    ?.classList.contains("show");
  const dataOpen = document
    .getElementById("import-export-collapse")
    ?.classList.contains("show");

  const backdrop = document.getElementById("panel-backdrop");
  if (backdrop) {
    if (parameterOpen || settingsOpen || dataOpen) {
      backdrop.classList.add("active");
    } else {
      backdrop.classList.remove("active");
    }
  }
}

window.dash_clientside = Object.assign({}, window.dash_clientside, {
  panelState: {
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

      // Update backdrop
      setTimeout(updateBackdrop, 10);

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

      // Update backdrop
      setTimeout(updateBackdrop, 10);

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

      // Update backdrop
      setTimeout(updateBackdrop, 10);

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
