document.addEventListener('DOMContentLoaded', function () {
  document.addEventListener('click', function (event) {
    let headerElement = event.target.closest('[id^="actionable-insight-header-"]');

    if (headerElement) {
      event.preventDefault();
      event.stopPropagation();

      let headerId = headerElement.id;
      let index = headerId.replace('actionable-insight-header-', '');

      let collapseId = 'actionable-insight-collapse-' + index;
      let collapseElement = document.getElementById(collapseId);

      let toggleButton = document.getElementById('actionable-insight-toggle-' + index);
      let toggleIcon = toggleButton ? toggleButton.querySelector('i') : null;

      if (collapseElement) {
        let isOpen = collapseElement.classList.contains('show');

        if (isOpen) {
          collapseElement.classList.remove('show');
          if (toggleIcon) {
            toggleIcon.classList.remove('fa-chevron-up');
            toggleIcon.classList.add('fa-chevron-down');
          }
        } else {
          collapseElement.classList.add('show');
          if (toggleIcon) {
            toggleIcon.classList.remove('fa-chevron-down');
            toggleIcon.classList.add('fa-chevron-up');
          }
        }
      }
    }
  });
});
