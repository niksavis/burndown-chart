if (!window.dash_clientside) {
  window.dash_clientside = {};
}

window.dash_clientside.jqlEditor = {
  syncInputToStore: function (inputValue) {
    return inputValue || '';
  },

  syncStoreToInput: function (storeValue) {
    return storeValue || '';
  },
};
