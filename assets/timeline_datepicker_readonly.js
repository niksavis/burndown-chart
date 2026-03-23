(function () {
  'use strict';

  function enforceCalendarOnlyDatepickers() {
    const ids = ['deadline-picker', 'milestone-picker'];

    for (const id of ids) {
      const input = document.getElementById(id);
      if (!(input instanceof HTMLInputElement)) {
        continue;
      }

      input.readOnly = true;
      input.setAttribute('readonly', 'readonly');
      input.setAttribute('inputmode', 'none');
      input.setAttribute('autocomplete', 'off');
      input.style.cursor = 'pointer';
    }
  }

  function init() {
    enforceCalendarOnlyDatepickers();

    const observer = new MutationObserver(() => {
      enforceCalendarOnlyDatepickers();
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: false,
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
