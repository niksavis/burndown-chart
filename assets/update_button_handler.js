(function () {
  'use strict';

  console.log('[update_button_handler] Initializing direct click handler');

  function attachUpdateButtonHandler() {
    const observer = new MutationObserver(() => {
      const updateButton = document.getElementById('install-update-button');

      if (updateButton && !updateButton.dataset.handlerAttached) {
        console.log('[update_button_handler] Found Update button - attaching handler');

        updateButton.dataset.handlerAttached = 'true';

        updateButton.addEventListener(
          'click',
          function (_event) {
            console.log('[update_button_handler] CLICK CAPTURED - triggering overlay');

            const overlayEvent = new CustomEvent('trigger-update-overlay');
            window.dispatchEvent(overlayEvent);

            console.log(
              '[update_button_handler] Overlay event dispatched, Dash callback will follow'
            );
          },
          true
        );

        console.log('[update_button_handler] Click handler attached in capture phase');
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });

    console.log('[update_button_handler] MutationObserver started');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', attachUpdateButtonHandler);
  } else {
    attachUpdateButtonHandler();
  }
})();
