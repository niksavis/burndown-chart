window.dash_clientside = Object.assign({}, window.dash_clientside, {
  clientside: {
    toggleRenameInput: function (strategy) {
      if (strategy === 'rename') {
        return { display: 'block' };
      }
      return { display: 'none' };
    },
  },
});
