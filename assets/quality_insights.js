document.addEventListener('DOMContentLoaded', function () {
  document.addEventListener('click', function (event) {
    let headerElement = event.target.closest('[id^="insight-header-"]');

    if (headerElement) {
      let headerId = headerElement.id;
      let index = headerId.replace('insight-header-', '');

      let collapseId = 'insight-collapse-' + index;
      let collapseElement = document.getElementById(collapseId);

      let toggleButton = document.getElementById('insight-toggle-' + index);
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
