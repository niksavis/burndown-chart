(function () {
  "use strict";

  const FADE_MS = 300;

  function removeToastElement(toastElement) {
    if (!toastElement) return;

    toastElement.classList.remove("show");
    setTimeout(() => {
      if (toastElement.parentElement) {
        toastElement.remove();
      }
    }, FADE_MS);
  }

  function attachToastDismiss(toastElement, autoDismissId) {
    if (!toastElement) return;

    const closeButton = toastElement.querySelector(".btn-close");
    if (!closeButton) return;

    closeButton.addEventListener(
      "click",
      (event) => {
        event.preventDefault();
        if (autoDismissId) {
          clearTimeout(autoDismissId);
        }
        removeToastElement(toastElement);
      },
      { once: true },
    );
  }

  window.update_reconnect_helpers = window.update_reconnect_helpers || {};
  window.update_reconnect_helpers.attach_toast_dismiss = attachToastDismiss;
  window.update_reconnect_helpers.remove_toast_element = removeToastElement;
})();
