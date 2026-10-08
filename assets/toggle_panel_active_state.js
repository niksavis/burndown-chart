window.dash_clientside = Object.assign({}, window.dash_clientside, {
  panelState: {
    updateBackdropState: function (parameterOpen, settingsOpen, dataOpen) {
      return parameterOpen || settingsOpen || dataOpen ? 'panel-backdrop active' : 'panel-backdrop';
    },

    toggleParameterButton: function (is_open, currentClassName) {
      const button = document.getElementById('btn-expand-parameters');
      if (button) {
        if (is_open) {
          button.title = 'Close Parameters';
        } else {
          button.title = 'Expand Parameters';
        }
      }

      if (!currentClassName) currentClassName = '';
      const classes = currentClassName.split(' ').filter((c) => c && c !== 'active');
      if (is_open) {
        classes.push('active');
      }
      return classes.join(' ');
    },

    toggleSettingsButton: function (is_open, currentClassName) {
      const button = document.getElementById('settings-button');
      if (button) {
        if (is_open) {
          button.title = 'Close Settings';
        } else {
          button.title = 'Expand Settings';
        }
      }

      if (!currentClassName) currentClassName = '';
      const classes = currentClassName.split(' ').filter((c) => c && c !== 'active');
      if (is_open) {
        classes.push('active');
      }
      return classes.join(' ');
    },

    toggleDataButton: function (is_open, currentClassName) {
      const button = document.getElementById('toggle-import-export-panel');
      if (button) {
        if (is_open) {
          button.title = 'Close Data';
        } else {
          button.title = 'Expand Data';
        }
      }

      if (!currentClassName) currentClassName = '';
      const classes = currentClassName.split(' ').filter((c) => c && c !== 'active');
      if (is_open) {
        classes.push('active');
      }
      return classes.join(' ');
    },
  },
});
