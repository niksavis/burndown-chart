/**
 * Mobile Navigation Enhancement JavaScript
 *
 * This file provides mobile-specific navigation functionality including:
 * - Swipe gesture detection for tab navigation
 * - Mobile drawer navigation controls
 * - Bottom navigation synchronization
 * - Touch interaction improvements
 * - Performance optimized event handling
 * - Accessibility enhancements
 */

// Mobile Navigation State (check if already exists to prevent redeclaration)
if (typeof window.mobileNavState === "undefined") {
  window.mobileNavState = {
    drawerOpen: false,
    currentTab: "tab-dashboard",
    swipeEnabled: true,
    touchStartX: 0,
    touchStartY: 0,
    touchEndX: 0,
    touchEndY: 0,
    swipeThreshold: 50,
  };
}

// Tab configuration for mobile navigation (check if already exists to prevent redeclaration)
if (typeof window.mobileTabsConfig === "undefined") {
  window.mobileTabsConfig = [
    {
      id: "tab-dashboard",
      label: "Project Dashboard",
      short_label: "Dashboard",
      show_in_bottom_nav: true,
    },
    {
      id: "tab-burndown",
      label: "Burndown Chart",
      short_label: "Chart",
      show_in_bottom_nav: true,
    },
    {
      id: "tab-scope-tracking",
      label: "Scope Changes",
      short_label: "Scope",
      show_in_bottom_nav: true,
    },
    {
      id: "tab-bug-analysis",
      label: "Bug Analysis & Quality",
      short_label: "Bugs",
      show_in_bottom_nav: true,
    },
    {
      id: "tab-dora-metrics",
      label: "DORA Metrics",
      short_label: "DORA",
      show_in_bottom_nav: true,
    },
    {
      id: "tab-flow-metrics",
      label: "Flow Metrics",
      short_label: "Flow",
      show_in_bottom_nav: true,
    },
    {
      id: "tab-active-work-timeline",
      label: "Active Work",
      short_label: "Active",
      show_in_bottom_nav: false,
    },
    {
      id: "tab-sprint-tracker",
      label: "Sprint Tracker",
      short_label: "Sprint",
      show_in_bottom_nav: false,
    },
    {
      id: "tab-statistics-data",
      label: "Weekly Data",
      short_label: "Data",
      show_in_bottom_nav: false,
    },
  ];
}

/**
 * Initialize mobile navigation functionality
 */
function initializeMobileNavigation() {
  // Only initialize on mobile devices
  if (window.innerWidth >= 768) return;

  initializeDrawerNavigation();
  initializeBottomNavigation();
  initializeOverflowMenu();
  initializeSwipeGestures();
  initializeTouchOptimizations();
}

/**
 * Initialize mobile drawer navigation
 */
function initializeDrawerNavigation() {
  const menuToggle = document.getElementById("mobile-menu-toggle");
  const drawer = document.getElementById("mobile-drawer");
  const overlay = document.getElementById("mobile-drawer-overlay");
  const closeBtn = document.getElementById("mobile-drawer-close");

  if (!menuToggle || !drawer || !overlay) return;

  // Open drawer
  menuToggle.addEventListener("click", () => {
    openMobileDrawer();
  });

  // Close drawer
  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      closeMobileDrawer();
    });
  }

  // Close on overlay click
  overlay.addEventListener("click", () => {
    closeMobileDrawer();
  });

  // Close on escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && mobileNavState.drawerOpen) {
      closeMobileDrawer();
    }
  });

  // Add drawer item click handlers
  window.mobileTabsConfig.forEach((tab) => {
    const drawerItem = document.getElementById(`drawer-${tab.id}`);
    if (drawerItem) {
      drawerItem.addEventListener("click", () => {
        switchToTab(tab.id);
        closeMobileDrawer();
      });
    }
  });
}

/**
 * Initialize bottom navigation
 */
function initializeBottomNavigation() {
  window.mobileTabsConfig.forEach((tab) => {
    const bottomNavItem = document.getElementById(`bottom-nav-${tab.id}`);
    if (bottomNavItem) {
      bottomNavItem.addEventListener("click", () => {
        switchToTab(tab.id);
      });
    }
  });
}

/**
 * Initialize swipe gesture detection
 */
function initializeSwipeGestures() {
  const tabContent = document.getElementById("mobile-tab-content-wrapper");
  if (!tabContent) return;

  let isSwipeEnabled = true;

  // Touch start
  tabContent.addEventListener(
    "touchstart",
    (e) => {
      if (!isSwipeEnabled || !mobileNavState.swipeEnabled) return;

      mobileNavState.touchStartX = e.changedTouches[0].screenX;
      mobileNavState.touchStartY = e.changedTouches[0].screenY;
    },
    { passive: true },
  );

  // Touch end
  tabContent.addEventListener(
    "touchend",
    (e) => {
      if (!isSwipeEnabled || !mobileNavState.swipeEnabled) return;

      mobileNavState.touchEndX = e.changedTouches[0].screenX;
      mobileNavState.touchEndY = e.changedTouches[0].screenY;

      handleSwipeGesture();
    },
    { passive: true },
  );

  // Prevent swipe during chart interactions
  const charts = document.querySelectorAll(".plotly-graph-div");
  charts.forEach((chart) => {
    chart.addEventListener("touchstart", () => {
      isSwipeEnabled = false;
    });

    chart.addEventListener("touchend", () => {
      setTimeout(() => {
        isSwipeEnabled = true;
      }, 100);
    });
  });
}

/**
 * Handle swipe gesture detection
 */
function handleSwipeGesture() {
  const deltaX = mobileNavState.touchEndX - mobileNavState.touchStartX;
  const deltaY = mobileNavState.touchEndY - mobileNavState.touchStartY;

  // Check if horizontal swipe is more significant than vertical
  if (
    Math.abs(deltaX) > Math.abs(deltaY) &&
    Math.abs(deltaX) > mobileNavState.swipeThreshold
  ) {
    const currentIndex = window.mobileTabsConfig.findIndex(
      (tab) => tab.id === mobileNavState.currentTab,
    );

    if (deltaX > 0 && currentIndex > 0) {
      // Swipe right - go to previous tab
      switchToTab(window.mobileTabsConfig[currentIndex - 1].id);
    } else if (
      deltaX < 0 &&
      currentIndex < window.mobileTabsConfig.length - 1
    ) {
      // Swipe left - go to next tab
      switchToTab(window.mobileTabsConfig[currentIndex + 1].id);
    }
  }
}

/**
 * Initialize touch optimizations
 */
function initializeTouchOptimizations() {
  // Remove 300ms tap delay on mobile
  document.addEventListener("touchstart", () => {}, { passive: true });

  // Improve button touch feedback
  const buttons = document.querySelectorAll("button, .btn, .nav-link");
  buttons.forEach((button) => {
    button.addEventListener(
      "touchstart",
      function () {
        this.style.transform = "scale(0.95)";
      },
      { passive: true },
    );

    button.addEventListener(
      "touchend",
      function () {
        this.style.transform = "scale(1)";
      },
      { passive: true },
    );
  });
}

/**
 * Open mobile drawer
 */
function openMobileDrawer() {
  const drawer = document.getElementById("mobile-drawer");
  const overlay = document.getElementById("mobile-drawer-overlay");

  if (drawer && overlay) {
    drawer.classList.add("open");
    overlay.style.display = "block";
    mobileNavState.drawerOpen = true;

    // Prevent body scroll
    document.body.style.overflow = "hidden";

    // Focus management for accessibility
    const firstDrawerItem = drawer.querySelector(".mobile-drawer-item");
    if (firstDrawerItem) {
      firstDrawerItem.focus();
    }
  }
}

/**
 * Close mobile drawer
 */
function closeMobileDrawer() {
  const drawer = document.getElementById("mobile-drawer");
  const overlay = document.getElementById("mobile-drawer-overlay");

  if (drawer && overlay) {
    drawer.classList.remove("open");
    overlay.style.display = "none";
    mobileNavState.drawerOpen = false;

    // Restore body scroll
    document.body.style.overflow = "";

    // Return focus to menu toggle
    const menuToggle = document.getElementById("mobile-menu-toggle");
    if (menuToggle) {
      menuToggle.focus();
    }
  }
}

/**
 * Open overflow menu
 */
function openOverflowMenu() {
  const menu = document.getElementById("mobile-overflow-menu");
  const overlay = document.getElementById("mobile-overflow-overlay");

  if (menu && overlay) {
    menu.style.transform = "translateY(0)";
    overlay.style.display = "block";

    // Prevent body scroll
    document.body.style.overflow = "hidden";
  }
}

/**
 * Close overflow menu
 */
function closeOverflowMenu() {
  const menu = document.getElementById("mobile-overflow-menu");
  const overlay = document.getElementById("mobile-overflow-overlay");

  if (menu && overlay) {
    menu.style.transform = "translateY(100%)";
    overlay.style.display = "none";

    // Restore body scroll
    document.body.style.overflow = "";
  }
}

/**
 * Initialize overflow menu
 */
function initializeOverflowMenu() {
  const moreButton = document.getElementById("bottom-nav-more-menu");
  const overlay = document.getElementById("mobile-overflow-overlay");
  const header = document.getElementById("mobile-overflow-header");

  // Open overflow menu on More button click
  if (moreButton) {
    moreButton.addEventListener("click", () => {
      openOverflowMenu();
    });
  }

  // Close overflow menu on overlay click
  if (overlay) {
    overlay.addEventListener("click", () => {
      closeOverflowMenu();
    });
  }

  // Close overflow menu on header swipe down
  if (header) {
    header.addEventListener("click", () => {
      closeOverflowMenu();
    });
  }

  // Initialize overflow menu item click handlers
  const overflowTabs = window.mobileTabsConfig.filter(
    (tab) => !tab.show_in_bottom_nav,
  );
  overflowTabs.forEach((tab) => {
    const menuItem = document.getElementById(`overflow-menu-${tab.id}`);
    if (menuItem) {
      menuItem.addEventListener("click", () => {
        switchToTab(tab.id);
        closeOverflowMenu();
      });
    }
  });
}

/**
 * Switch to a specific tab
 */
function switchToTab(tabId) {
  mobileNavState.currentTab = tabId;

  // Update active states
  updateTabActiveStates(tabId);

  // Do NOT directly click tab elements to avoid race conditions
  // Let the mobile navigation callback handle the tab switching
}

/**
 * Update active states across all navigation elements
 */
function updateTabActiveStates(activeTabId) {
  window.mobileTabsConfig.forEach((tab) => {
    // Update drawer items
    const drawerItem = document.getElementById(`drawer-${tab.id}`);
    if (drawerItem) {
      if (tab.id === activeTabId) {
        drawerItem.classList.add("active");
      } else {
        drawerItem.classList.remove("active");
      }
    }

    // Update bottom navigation items
    const bottomNavItem = document.getElementById(`bottom-nav-${tab.id}`);
    if (bottomNavItem) {
      if (tab.id === activeTabId) {
        bottomNavItem.classList.add("active");
        bottomNavItem.style.color = tab.color || "#0d6efd";
      } else {
        bottomNavItem.classList.remove("active");
        bottomNavItem.style.color = "#6c757d";
      }
    }
  });
}

/**
 * Handle orientation change
 */
function handleOrientationChange() {
  // Close drawer on orientation change
  if (mobileNavState.drawerOpen) {
    closeMobileDrawer();
  }

  // Close overflow menu on orientation change
  closeOverflowMenu();

  // Reinitialize if switching between mobile/desktop
  setTimeout(() => {
    if (window.innerWidth >= 768) {
      // Desktop mode - disable mobile features
      mobileNavState.swipeEnabled = false;
    } else {
      // Mobile mode - enable mobile features
      mobileNavState.swipeEnabled = true;
    }
  }, 100);
}

/**
 * Debounced resize handler
 */
if (typeof window.resizeTimeout === "undefined") {
  window.resizeTimeout = null;
}
function handleResize() {
  clearTimeout(window.resizeTimeout);
  window.resizeTimeout = setTimeout(handleOrientationChange, 250);
}

// Initialize when DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeMobileNavigation);
} else {
  initializeMobileNavigation();
}

// Handle window resize and orientation changes
window.addEventListener("resize", handleResize);
window.addEventListener("orientationchange", handleOrientationChange);

// Export for Dash clientside callbacks
if (typeof window !== "undefined") {
  window.mobileNavigation = {
    switchToTab,
    openMobileDrawer,
    closeMobileDrawer,
    openOverflowMenu,
    closeOverflowMenu,
    mobileNavState,
  };
}
