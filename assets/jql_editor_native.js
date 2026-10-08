(function () {
  'use strict';

  function ensureJqlModeRegistered() {
    if (typeof CodeMirror === 'undefined' || !CodeMirror.defineMode) {
      return;
    }

    if (CodeMirror.modes && CodeMirror.modes.jql) {
      return;
    }

    if (typeof window !== 'undefined' && window.jqlLanguageMode) {
      CodeMirror.defineMode('jql', function () {
        return window.jqlLanguageMode;
      });
    }
  }

  function isJqlModeAvailable() {
    if (typeof CodeMirror === 'undefined') {
      return false;
    }

    ensureJqlModeRegistered();

    try {
      const testMode = CodeMirror.getMode({}, 'jql');
      return testMode && testMode.name === 'jql';
    } catch {
      return false;
    }
  }

  function initializeNativeEditors() {
    const codeMirrorAvailable =
      typeof CodeMirror !== 'undefined' && typeof CodeMirror === 'function';

    if (!codeMirrorAvailable) {
      console.error('[Native JQL] CodeMirror not loaded');
      return;
    }

    const jqlModeAvailable = isJqlModeAvailable();

    if (!jqlModeAvailable) {
      console.warn('[Native JQL] JQL mode not loaded - using plain text');
    }

    const containers = document.querySelectorAll('.jql-codemirror-container');

    if (containers.length === 0) {
      return;
    }

    console.log(`[Native JQL] Initializing ${containers.length} editor(s)`);

    containers.forEach((container) => {
      if (container._cmEditor) {
        return;
      }

      const editorId = container.getAttribute('data-editor-id');
      const initialValue = container.getAttribute('data-initial-value') || '';
      const placeholder = container.getAttribute('data-placeholder') || 'Enter JQL query...';

      const hiddenInput = document.getElementById(editorId);
      if (!hiddenInput) {
        console.error(`[Native JQL] Hidden input not found: ${editorId}`);
        return;
      }

      const actualInitialValue = hiddenInput.value || initialValue;

      console.log(
        `[Native JQL] Creating editor for ${editorId} with value: "${actualInitialValue.substring(
          0,
          50
        )}..."`
      );

      const editor = CodeMirror(container, {
        value: actualInitialValue,
        mode: jqlModeAvailable ? 'jql' : 'text/plain',
        lineNumbers: false,
        lineWrapping: true,
        theme: 'default',
        placeholder: placeholder,
        indentWithTabs: false,
        indentUnit: 2,
        tabSize: 2,
        autofocus: false,
        viewportMargin: Infinity,
        extraKeys: {
          Tab: false,
        },
      });

      container._cmEditor = editor;

      const isVisible = container.offsetParent !== null;
      if (!isVisible) {
        console.log(`[Native JQL] ${editorId} initialized in hidden tab, will refresh on tab show`);
        container.setAttribute('data-needs-refresh', 'true');
      }

      setTimeout(function () {
        editor.refresh();
      }, 1);

      editor.on('change', function () {
        const value = editor.getValue();
        if (hiddenInput.value !== value) {
          hiddenInput.value = value;
          const event = new Event('input', { bubbles: true });
          hiddenInput.dispatchEvent(event);
        }
      });

      const elementPrototype =
        hiddenInput.tagName === 'TEXTAREA'
          ? HTMLTextAreaElement.prototype
          : HTMLInputElement.prototype;

      const originalDescriptor = Object.getOwnPropertyDescriptor(elementPrototype, 'value');

      Object.defineProperty(hiddenInput, 'value', {
        get: function () {
          return originalDescriptor.get.call(this);
        },
        set: function (val) {
          originalDescriptor.set.call(this, val);
          if (editor && editor.getValue() !== val) {
            editor.setValue(val || '');
          }
        },
      });

      console.log(
        `[Native JQL] Initialized ${editorId} with ${
          actualInitialValue.length
        } chars: "${actualInitialValue.substring(0, 50)}..."`
      );
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeNativeEditors);
  } else {
    initializeNativeEditors();
  }

  let retryCount = 0;
  const maxRetries = 10;
  const retryInterval = setInterval(function () {
    const uninitializedContainers = Array.from(
      document.querySelectorAll('.jql-codemirror-container')
    ).filter((c) => !c._cmEditor);

    if (uninitializedContainers.length > 0) {
      console.log(
        `[Native JQL] Retry ${retryCount + 1}: Found ${
          uninitializedContainers.length
        } uninitialized container(s)`
      );
      initializeNativeEditors();
    }

    retryCount++;
    if (retryCount >= maxRetries) {
      clearInterval(retryInterval);
      console.log('[Native JQL] Stopped retry polling');
    }
  }, 500);

  const observer = new MutationObserver(function (mutations) {
    let shouldReinit = false;
    mutations.forEach(function (mutation) {
      mutation.addedNodes.forEach(function (node) {
        if (node.nodeType === 1) {
          if (node.classList && node.classList.contains('jql-codemirror-container')) {
            shouldReinit = true;
          } else if (node.querySelectorAll) {
            const containers = node.querySelectorAll('.jql-codemirror-container');
            if (containers.length > 0) {
              shouldReinit = true;
            }
          }
        }
      });
    });

    if (shouldReinit) {
      console.log('[Native JQL] New containers detected, reinitializing...');
      setTimeout(initializeNativeEditors, 50);
    }
  });

  if (document.body) {
    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  } else {
    document.addEventListener('DOMContentLoaded', function () {
      observer.observe(document.body, {
        childList: true,
        subtree: true,
      });
    });
  }

  document.addEventListener('shown.bs.tab', function (_event) {
    console.log('[Native JQL] Bootstrap tab shown event');
    refreshAllEditors();
  });

  document.addEventListener('click', function (event) {
    const target = event.target;
    if (
      target &&
      (target.textContent?.includes('Queries') ||
        target.closest('[tab_id="queries-tab"]') ||
        (target.classList && target.classList.contains('nav-link')))
    ) {
      console.log('[Native JQL] Queries tab clicked, will refresh editors');
      setTimeout(refreshAllEditors, 150);
    }
  });

  function refreshAllEditors() {
    console.log('[Native JQL] Refreshing all editors...');

    initializeNativeEditors();

    setTimeout(function () {
      const containers = document.querySelectorAll('.jql-codemirror-container');
      containers.forEach(function (container) {
        if (container._cmEditor) {
          const needsRefresh = container.getAttribute('data-needs-refresh') === 'true';

          if (needsRefresh) {
            console.log(
              `[Native JQL] Refreshing ${container.getAttribute(
                'data-editor-id'
              )} (was hidden on init)`
            );
            container.removeAttribute('data-needs-refresh');
          }

          container._cmEditor.refresh();

          setTimeout(function () {
            container._cmEditor.refresh();
          }, 100);
        }
      });
    }, 50);
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (window.dash_clientside) {
      window.dash_clientside = window.dash_clientside || {};
      window.dash_clientside.reinit_jql = function () {
        setTimeout(initializeNativeEditors, 100);
        return window.dash_clientside.no_update;
      };
    }
  });

  window.reinitJQLEditors = initializeNativeEditors;
})();
