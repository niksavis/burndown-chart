(function () {
  function detectViewportSize() {
    const width = window.innerWidth;

    if (width < 768) {
      return 'mobile';
    } else if (width < 1024) {
      return 'tablet';
    } else {
      return 'desktop';
    }
  }

  function updateViewportSize() {
    const viewportSize = detectViewportSize();

    try {
      if (window.dash_clientside && window.dash_clientside.set_props) {
        const viewportElement = document.getElementById('viewport-size');
        if (viewportElement) {
          window.dash_clientside.set_props('viewport-size', { data: viewportSize });
        }
      }
    } catch (error) {
      console.warn('Could not update viewport size:', error);
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    updateViewportSize();

    let resizeTimeout;
    window.addEventListener('resize', function () {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(updateViewportSize, 150);
    });
  });

  if (window.dash_clientside) {
    window.dash_clientside.viewport_detection = {
      detect_viewport: function () {
        return detectViewportSize();
      },
    };
  }
})();
