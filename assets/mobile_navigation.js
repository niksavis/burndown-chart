(function () {
  if (typeof window.mobileNavState === 'undefined') {
    window.mobileNavState = {
      drawerOpen: false,
      currentTab: 'tab-dashboard',
      swipeEnabled: true,
      touchStartX: 0,
      touchStartY: 0,
      touchEndX: 0,
      touchEndY: 0,
      swipeThreshold: 50,
    };
  }

  if (typeof window.mobileTabsConfig === 'undefined') {
    window.mobileTabsConfig = [
      {
        id: 'tab-dashboard',
        label: 'Project Dashboard',
        short_label: 'Dashboard',
        show_in_bottom_nav: true,
      },
      {
        id: 'tab-burndown',
        label: 'Burndown Chart',
        short_label: 'Chart',
        show_in_bottom_nav: true,
      },
      {
        id: 'tab-scope-tracking',
        label: 'Scope Changes',
        short_label: 'Scope',
        show_in_bottom_nav: true,
      },
      {
        id: 'tab-bug-analysis',
        label: 'Bug Analysis & Quality',
        short_label: 'Bugs',
        show_in_bottom_nav: true,
      },
      {
        id: 'tab-dora-metrics',
        label: 'DORA Metrics',
        short_label: 'DORA',
        show_in_bottom_nav: true,
      },
      {
        id: 'tab-flow-metrics',
        label: 'Flow Metrics',
        short_label: 'Flow',
        show_in_bottom_nav: true,
      },
      {
        id: 'tab-active-work-timeline',
        label: 'Active Work',
        short_label: 'Active',
        show_in_bottom_nav: false,
      },
      {
        id: 'tab-sprint-tracker',
        label: 'Sprint Tracker',
        short_label: 'Sprint',
        show_in_bottom_nav: false,
      },
      {
        id: 'tab-statistics-data',
        label: 'Weekly Data',
        short_label: 'Data',
        show_in_bottom_nav: false,
      },
    ];
  }

  function initializeMobileNavigation() {
    if (window.innerWidth >= 768) return;

    initializeDrawerNavigation();
    initializeBottomNavigation();
    initializeOverflowMenu();
    initializeSwipeGestures();
    initializeTouchOptimizations();
  }

  function initializeDrawerNavigation() {
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const drawer = document.getElementById('mobile-drawer');
    const overlay = document.getElementById('mobile-drawer-overlay');
    const closeBtn = document.getElementById('mobile-drawer-close');

    if (!menuToggle || !drawer || !overlay) return;

    menuToggle.addEventListener('click', () => {
      openMobileDrawer();
    });

    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        closeMobileDrawer();
      });
    }

    overlay.addEventListener('click', () => {
      closeMobileDrawer();
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && mobileNavState.drawerOpen) {
        closeMobileDrawer();
      }
    });

    window.mobileTabsConfig.forEach((tab) => {
      const drawerItem = document.getElementById(`drawer-${tab.id}`);
      if (drawerItem) {
        drawerItem.addEventListener('click', () => {
          switchToTab(tab.id);
          closeMobileDrawer();
        });
      }
    });
  }

  function initializeBottomNavigation() {
    window.mobileTabsConfig.forEach((tab) => {
      const bottomNavItem = document.getElementById(`bottom-nav-${tab.id}`);
      if (bottomNavItem) {
        bottomNavItem.addEventListener('click', () => {
          switchToTab(tab.id);
        });
      }
    });
  }

  function initializeSwipeGestures() {
    const tabContent = document.getElementById('mobile-tab-content-wrapper');
    if (!tabContent) return;

    let isSwipeEnabled = true;

    tabContent.addEventListener(
      'touchstart',
      (e) => {
        if (!isSwipeEnabled || !mobileNavState.swipeEnabled) return;

        mobileNavState.touchStartX = e.changedTouches[0].screenX;
        mobileNavState.touchStartY = e.changedTouches[0].screenY;
      },
      { passive: true }
    );

    tabContent.addEventListener(
      'touchend',
      (e) => {
        if (!isSwipeEnabled || !mobileNavState.swipeEnabled) return;

        mobileNavState.touchEndX = e.changedTouches[0].screenX;
        mobileNavState.touchEndY = e.changedTouches[0].screenY;

        handleSwipeGesture();
      },
      { passive: true }
    );

    const charts = document.querySelectorAll('.plotly-graph-div');
    charts.forEach((chart) => {
      chart.addEventListener('touchstart', () => {
        isSwipeEnabled = false;
      });

      chart.addEventListener('touchend', () => {
        setTimeout(() => {
          isSwipeEnabled = true;
        }, 100);
      });
    });
  }

  function handleSwipeGesture() {
    const deltaX = mobileNavState.touchEndX - mobileNavState.touchStartX;
    const deltaY = mobileNavState.touchEndY - mobileNavState.touchStartY;

    if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > mobileNavState.swipeThreshold) {
      const currentIndex = window.mobileTabsConfig.findIndex(
        (tab) => tab.id === mobileNavState.currentTab
      );

      if (deltaX > 0 && currentIndex > 0) {
        switchToTab(window.mobileTabsConfig[currentIndex - 1].id);
      } else if (deltaX < 0 && currentIndex < window.mobileTabsConfig.length - 1) {
        switchToTab(window.mobileTabsConfig[currentIndex + 1].id);
      }
    }
  }

  function initializeTouchOptimizations() {
    document.addEventListener('touchstart', () => {}, { passive: true });

    const buttons = document.querySelectorAll('button, .btn, .nav-link');
    buttons.forEach((button) => {
      button.addEventListener(
        'touchstart',
        function () {
          this.style.transform = 'scale(0.95)';
        },
        { passive: true }
      );

      button.addEventListener(
        'touchend',
        function () {
          this.style.transform = 'scale(1)';
        },
        { passive: true }
      );
    });
  }

  function openMobileDrawer() {
    const drawer = document.getElementById('mobile-drawer');
    const overlay = document.getElementById('mobile-drawer-overlay');

    if (drawer && overlay) {
      drawer.classList.add('open');
      overlay.style.display = 'block';
      mobileNavState.drawerOpen = true;

      document.body.style.overflow = 'hidden';

      const firstDrawerItem = drawer.querySelector('.mobile-drawer-item');
      if (firstDrawerItem) {
        firstDrawerItem.focus();
      }
    }
  }

  function closeMobileDrawer() {
    const drawer = document.getElementById('mobile-drawer');
    const overlay = document.getElementById('mobile-drawer-overlay');

    if (drawer && overlay) {
      drawer.classList.remove('open');
      overlay.style.display = 'none';
      mobileNavState.drawerOpen = false;

      document.body.style.overflow = '';

      const menuToggle = document.getElementById('mobile-menu-toggle');
      if (menuToggle) {
        menuToggle.focus();
      }
    }
  }

  function openOverflowMenu() {
    const menu = document.getElementById('mobile-overflow-menu');
    const overlay = document.getElementById('mobile-overflow-overlay');

    if (menu && overlay) {
      menu.style.transform = 'translateY(0)';
      overlay.style.display = 'block';

      document.body.style.overflow = 'hidden';
    }
  }

  function closeOverflowMenu() {
    const menu = document.getElementById('mobile-overflow-menu');
    const overlay = document.getElementById('mobile-overflow-overlay');

    if (menu && overlay) {
      menu.style.transform = 'translateY(100%)';
      overlay.style.display = 'none';

      document.body.style.overflow = '';
    }
  }

  function initializeOverflowMenu() {
    const moreButton = document.getElementById('bottom-nav-more-menu');
    const overlay = document.getElementById('mobile-overflow-overlay');
    const header = document.getElementById('mobile-overflow-header');

    if (moreButton) {
      moreButton.addEventListener('click', () => {
        openOverflowMenu();
      });
    }

    if (overlay) {
      overlay.addEventListener('click', () => {
        closeOverflowMenu();
      });
    }

    if (header) {
      header.addEventListener('click', () => {
        closeOverflowMenu();
      });
    }

    const overflowTabs = window.mobileTabsConfig.filter((tab) => !tab.show_in_bottom_nav);
    overflowTabs.forEach((tab) => {
      const menuItem = document.getElementById(`overflow-menu-${tab.id}`);
      if (menuItem) {
        menuItem.addEventListener('click', () => {
          switchToTab(tab.id);
          closeOverflowMenu();
        });
      }
    });
  }

  function switchToTab(tabId) {
    mobileNavState.currentTab = tabId;

    updateTabActiveStates(tabId);
  }

  function updateTabActiveStates(activeTabId) {
    window.mobileTabsConfig.forEach((tab) => {
      const drawerItem = document.getElementById(`drawer-${tab.id}`);
      if (drawerItem) {
        if (tab.id === activeTabId) {
          drawerItem.classList.add('active');
        } else {
          drawerItem.classList.remove('active');
        }
      }

      const bottomNavItem = document.getElementById(`bottom-nav-${tab.id}`);
      if (bottomNavItem) {
        if (tab.id === activeTabId) {
          bottomNavItem.classList.add('active');
          bottomNavItem.style.color = tab.color || '#0d6efd';
        } else {
          bottomNavItem.classList.remove('active');
          bottomNavItem.style.color = '#6c757d';
        }
      }
    });
  }

  function handleOrientationChange() {
    if (mobileNavState.drawerOpen) {
      closeMobileDrawer();
    }

    closeOverflowMenu();

    setTimeout(() => {
      if (window.innerWidth >= 768) {
        mobileNavState.swipeEnabled = false;
      } else {
        mobileNavState.swipeEnabled = true;
      }
    }, 100);
  }

  if (typeof window.resizeTimeout === 'undefined') {
    window.resizeTimeout = null;
  }
  function handleResize() {
    clearTimeout(window.resizeTimeout);
    window.resizeTimeout = setTimeout(handleOrientationChange, 250);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeMobileNavigation);
  } else {
    initializeMobileNavigation();
  }

  window.addEventListener('resize', handleResize);
  window.addEventListener('orientationchange', handleOrientationChange);

  if (typeof window !== 'undefined') {
    window.mobileNavigation = {
      switchToTab,
      openMobileDrawer,
      closeMobileDrawer,
      openOverflowMenu,
      closeOverflowMenu,
      mobileNavState,
    };
  }
})();
