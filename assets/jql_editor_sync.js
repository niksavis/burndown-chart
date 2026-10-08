window.dash_clientside = Object.assign({}, window.dash_clientside, {
  jql_editor: {
    sync_to_store: function (textarea_value) {
      return textarea_value || '';
    },
  },
});
