/**
 * Actionable Insights Interactive Behavior
 *
 * Handles expandable/collapsible insight details with smooth animations.
 */

document.addEventListener("DOMContentLoaded", function () {
  // Add click handlers for actionable insight headers
  document.addEventListener("click", function (event) {
    // Check if clicked element is an actionable insight header or its child
    let headerElement = event.target.closest(
      '[id^="actionable-insight-header-"]',
    );

    if (headerElement) {
      // Prevent event from bubbling to other handlers (e.g., Bootstrap Collapse)
      event.preventDefault();
      event.stopPropagation();

      // Extract index from header id (e.g., "actionable-insight-header-0" -> "0")
      let headerId = headerElement.id;
      let index = headerId.replace("actionable-insight-header-", "");

      // Find the collapse element
      let collapseId = "actionable-insight-collapse-" + index;
      let collapseElement = document.getElementById(collapseId);

      // Find the toggle button icon
      let toggleButton = document.getElementById(
        "actionable-insight-toggle-" + index,
      );
      let toggleIcon = toggleButton ? toggleButton.querySelector("i") : null;

      if (collapseElement) {
        // Toggle the collapse
        let isOpen = collapseElement.classList.contains("show");

        if (isOpen) {
          collapseElement.classList.remove("show");
          if (toggleIcon) {
            toggleIcon.classList.remove("fa-chevron-up");
            toggleIcon.classList.add("fa-chevron-down");
          }
        } else {
          collapseElement.classList.add("show");
          if (toggleIcon) {
            toggleIcon.classList.remove("fa-chevron-down");
            toggleIcon.classList.add("fa-chevron-up");
          }
        }
      }
    }
  });
});
