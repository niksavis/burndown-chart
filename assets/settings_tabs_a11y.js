(function () {
  const DESCRIPTION_ID = 'tab-profile-required-description';
  let isApplyingA11yState = false;

  function ensureDescriptionNode() {
    if (document.getElementById(DESCRIPTION_ID)) {
      return;
    }

    const node = document.createElement('span');
    node.id = DESCRIPTION_ID;
    node.className = 'visually-hidden';
    node.textContent = 'Create or import a profile first.';
    document.body.appendChild(node);
  }

  function updateTabA11yState() {
    if (isApplyingA11yState) {
      return;
    }

    isApplyingA11yState = true;
    ensureDescriptionNode();

    const links = document.querySelectorAll('#settings-tabs .nav-link');
    links.forEach((link) => {
      const label = (link.textContent || '').trim().toLowerCase();
      const managedTab = label === 'connect' || label === 'queries';

      if (!managedTab) {
        return;
      }

      const isDisabled = link.classList.contains('disabled');
      const ariaDisabled = isDisabled ? 'true' : 'false';

      if (link.getAttribute('aria-disabled') !== ariaDisabled) {
        link.setAttribute('aria-disabled', ariaDisabled);
      }

      if (isDisabled) {
        if (link.getAttribute('aria-describedby') !== DESCRIPTION_ID) {
          link.setAttribute('aria-describedby', DESCRIPTION_ID);
        }
      } else if (link.hasAttribute('aria-describedby')) {
        link.removeAttribute('aria-describedby');
      }
    });

    isApplyingA11yState = false;
  }

  function initA11yObserver() {
    updateTabA11yState();

    const observer = new MutationObserver(() => {
      updateTabA11yState();
    });

    observer.observe(document.body, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ['class'],
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initA11yObserver);
  } else {
    initA11yObserver();
  }
})();
