window.dash_clientside = Object.assign({}, window.dash_clientside, {
  about_dialog: {
    filterLicenses: function (searchValue) {
      const accordion = document.getElementById('licenses-accordion');
      if (!accordion) {
        setTimeout(() => {
          const acc = document.getElementById('licenses-accordion');
          if (acc) {
            const count = acc.querySelectorAll('.license-item').length;
            const countText = document.getElementById('license-count-text');
            if (countText) {
              countText.textContent = `Showing ${count} dependencies`;
            }
          }
        }, 100);
        return 'Showing dependencies...';
      }

      const searchTerm = (searchValue || '').toLowerCase().trim();
      const items = accordion.querySelectorAll('.license-item');
      let visibleCount = 0;

      items.forEach((item) => {
        if (!searchTerm) {
          item.style.display = '';
          visibleCount++;
        } else {
          const button = item.querySelector('.accordion-button');
          const titleText = button ? button.textContent.toLowerCase() : '';

          const matches = titleText.includes(searchTerm);

          item.style.display = matches ? '' : 'none';
          if (matches) visibleCount++;
        }
      });

      const noResults = document.getElementById('license-no-results');
      if (noResults) {
        noResults.style.display = searchTerm && visibleCount === 0 ? '' : 'none';
      }

      const totalCount = items.length;
      if (searchTerm && visibleCount < totalCount) {
        return `Showing ${visibleCount} of ${totalCount} dependencies`;
      } else {
        return `Showing ${totalCount} dependencies`;
      }
    },
  },
});
