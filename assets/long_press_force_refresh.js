window.dash_clientside = window.dash_clientside || {};
window.dash_clientside.clientside = window.dash_clientside.clientside || {};
window.dash_clientside.clientside.setupLongPress = function () {
  let attempts = 0;
  const maxAttempts = 10;

  function tryInitialize() {
    const button = document.getElementById('update-data-unified');
    if (!button) {
      attempts++;
      if (attempts < maxAttempts) {
        setTimeout(tryInitialize, 100 * Math.pow(2, Math.min(attempts - 1, 4)));
      } else {
        console.warn('Update Data button not found after', maxAttempts, 'attempts');
      }
      return;
    }

    let progressInterval = null;
    let textChangeTimer = null;
    let startTime = null;
    let isReadyForForceRefresh = false;
    const originalText = 'Update Data';
    const forceRefreshText = 'Force Refresh';
    const LONG_PRESS_DURATION = 2000;

    function getButtonTextElement() {
      const children = Array.from(button.childNodes);

      for (let child of children) {
        if (child.nodeType === Node.ELEMENT_NODE && child.tagName === 'SPAN') {
          return child;
        }
      }

      for (let child of children) {
        if (child.nodeType === Node.TEXT_NODE) {
          return child;
        }
      }

      return null;
    }

    function startPress(e) {
      e.preventDefault();

      startTime = Date.now();
      isReadyForForceRefresh = false;
      button.classList.add('long-press-active');

      button.style.setProperty('--progress-width', '0%');

      progressInterval = setInterval(function () {
        const elapsed = Date.now() - startTime;
        const progress = Math.min((elapsed / LONG_PRESS_DURATION) * 100, 100);
        button.style.setProperty('--progress-width', progress + '%');
      }, 16);

      textChangeTimer = setTimeout(function () {
        const textElement = getButtonTextElement();
        if (textElement) {
          textElement.textContent = forceRefreshText;
        }
        isReadyForForceRefresh = true;
      }, LONG_PRESS_DURATION);
    }

    function handleRelease(_e) {
      if (isReadyForForceRefresh) {
        console.log('🔄 Force refresh activated!');

        window._forceRefreshPending = true;
        console.log('✅ Set global _forceRefreshPending flag');

        cancelPress();

        return;
      }

      cancelPress();
    }

    function cancelPress() {
      if (textChangeTimer) {
        clearTimeout(textChangeTimer);
        textChangeTimer = null;
      }
      if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
      }

      button.classList.remove('long-press-active');
      isReadyForForceRefresh = false;

      button.style.setProperty('--progress-width', '0%');

      const textElement = getButtonTextElement();
      if (textElement) {
        textElement.textContent = originalText;
      }
    }

    button.addEventListener('mousedown', startPress);
    button.addEventListener('mouseup', handleRelease);
    button.addEventListener('mouseleave', cancelPress);

    button.addEventListener('touchstart', startPress, { passive: false });
    button.addEventListener('touchend', handleRelease);
    button.addEventListener('touchcancel', cancelPress);

    console.log('Long-press force refresh initialized');
  }

  tryInitialize();

  return window.dash_clientside.no_update;
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function () {
    if (window.dash_clientside && window.dash_clientside.clientside) {
      window.dash_clientside.clientside.setupLongPress();
    }
  });
} else {
  if (window.dash_clientside && window.dash_clientside.clientside) {
    window.dash_clientside.clientside.setupLongPress();
  }
}

window.dash_clientside = Object.assign({}, window.dash_clientside, {
  forceRefresh: {
    updateStore: function (_n_clicks) {
      if (window._forceRefreshPending) {
        console.log('✅ Clientside callback: Force refresh detected, returning TRUE');
        window._forceRefreshPending = false;
        return true;
      }
      console.log('✅ Clientside callback: Normal click, returning FALSE');
      return false;
    },
  },
});
