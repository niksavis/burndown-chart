(function registerActiveWorkToggleAll() {
  if (window.activeWorkToggleAllInitialized) {
    return;
  }
  window.activeWorkToggleAllInitialized = true;

  document.addEventListener("click", function handleActiveWorkToggle(event) {
    var button = event.target.closest("#active-work-toggle-all");
    if (!button) {
      return;
    }

    var container = document.getElementById("active-work-timeline-tab-content");
    var scope = container || document;
    var details = scope.querySelectorAll("details.active-work-epic-card");
    if (!details.length) {
      return;
    }

    var shouldExpand = Array.prototype.some.call(details, function (item) {
      return !item.open;
    });

    Array.prototype.forEach.call(details, function (item) {
      if (shouldExpand) {
        item.setAttribute("open", "");
        item.open = true;
      } else {
        item.removeAttribute("open");
        item.open = false;
      }
    });

    var label = button.querySelector("#active-work-toggle-label");
    if (label) {
      label.textContent = shouldExpand ? "Collapse all" : "Expand all";
    }

    button.setAttribute("aria-expanded", shouldExpand ? "true" : "false");

    var icon = button.querySelector("i");
    if (icon) {
      icon.classList.toggle("fa-compress-arrows-alt", shouldExpand);
      icon.classList.toggle("fa-expand-arrows-alt", !shouldExpand);
    }
  });
})();
