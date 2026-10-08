(function () {
  'use strict';

  console.log('[Modal Fix] Script loaded');

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initModalKeyboardFix);
  } else {
    initModalKeyboardFix();
  }

  function initModalKeyboardFix() {
    console.log('[Modal Fix] Initializing modal keyboard handling');

    document.addEventListener(
      'keydown',
      function (e) {
        const staticModals = document.querySelectorAll('.modal.show[data-bs-backdrop="static"]');

        if (staticModals.length === 0) return;

        if (e.key === 'Escape' || e.key === 'Esc') {
          console.log('[Modal Fix] Preventing ESC key from closing static backdrop modal');
          e.preventDefault();
          e.stopPropagation();
          e.stopImmediatePropagation();
          return false;
        }

        if (e.key === ' ' || e.code === 'Space') {
          const activeElement = document.activeElement;
          const isInput =
            activeElement &&
            (activeElement.tagName === 'INPUT' ||
              activeElement.tagName === 'TEXTAREA' ||
              activeElement.tagName === 'SELECT' ||
              activeElement.isContentEditable);

          if (!isInput && activeElement && activeElement.tagName === 'BUTTON') {
            console.log('[Modal Fix] Preventing SPACE key from clicking button');
            e.preventDefault();
            e.stopPropagation();
            return false;
          }
        }
      },
      true
    );

    const observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
          const modal = mutation.target;
          if (modal.classList.contains('modal') && modal.classList.contains('show')) {
            setTimeout(function () {
              const firstInput = modal.querySelector('input:not([type="hidden"]), textarea');
              if (firstInput) {
                firstInput.focus();
                console.log('[Modal Fix] Auto-focused first input in modal');
              }
            }, 100);
          }
        }
      });
    });

    document.querySelectorAll('.modal').forEach(function (modal) {
      observer.observe(modal, { attributes: true, attributeFilter: ['class'] });
    });

    const bodyObserver = new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        mutation.addedNodes.forEach(function (node) {
          if (node.nodeType === 1 && node.classList && node.classList.contains('modal')) {
            observer.observe(node, {
              attributes: true,
              attributeFilter: ['class'],
            });
          }
        });
      });
    });
    bodyObserver.observe(document.body, { childList: true, subtree: true });

    console.log('[Modal Fix] Keyboard handling initialized');
  }
})();
