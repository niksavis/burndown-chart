/**
 * License Search/Filter - Clientside Callback
 *
 * Filters license accordion items by name or license type in real-time.
 */

window.dash_clientside = Object.assign({}, window.dash_clientside, {
  about_dialog: {
    /**
     * Filter license accordion items based on search input
     *
     * @param {string} searchValue - Current search input value
     * @returns {string} - Formatted count text
     */
    filterLicenses: function (searchValue) {
      const accordion = document.getElementById("licenses-accordion");
      if (!accordion) {
        // DOM not ready yet, retry after a short delay
        setTimeout(() => {
          const acc = document.getElementById("licenses-accordion");
          if (acc) {
            const count = acc.querySelectorAll(".license-item").length;
            const countText = document.getElementById("license-count-text");
            if (countText) {
              countText.textContent = `Showing ${count} dependencies`;
            }
          }
        }, 100);
        return "Showing dependencies...";
      }

      const searchTerm = (searchValue || "").toLowerCase().trim();
      const items = accordion.querySelectorAll(".license-item");
      let visibleCount = 0;

      items.forEach((item) => {
        if (!searchTerm) {
          // No search term - show all
          item.style.display = "";
          visibleCount++;
        } else {
          // Search in the accordion button title text (contains name, version, license type)
          const button = item.querySelector(".accordion-button");
          const titleText = button ? button.textContent.toLowerCase() : "";

          const matches = titleText.includes(searchTerm);

          item.style.display = matches ? "" : "none";
          if (matches) visibleCount++;
        }
      });

      // Show/hide no results message
      const noResults = document.getElementById("license-no-results");
      if (noResults) {
        noResults.style.display =
          searchTerm && visibleCount === 0 ? "" : "none";
      }

      // Return formatted count text
      const totalCount = items.length;
      if (searchTerm && visibleCount < totalCount) {
        return `Showing ${visibleCount} of ${totalCount} dependencies`;
      } else {
        return `Showing ${totalCount} dependencies`;
      }
    },
  },
});
