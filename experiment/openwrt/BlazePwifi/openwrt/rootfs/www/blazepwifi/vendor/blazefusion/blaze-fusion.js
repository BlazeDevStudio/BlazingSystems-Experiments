/* BlazeFusion: offline UI preferences only; never reads/writes rental or billing state. */
(function () {
  'use strict';
  const key = 'blazepwifi.console.appearance.v1';
  const permitted = ['fusion', 'compact', 'comfort'];
  const icons = {
    dashboard:'◉',sessions:'◫',sales:'▥',wan:'↗',lan:'◎',remote:'⌁',
    vouchers:'◇',members:'♙',rentals:'▣',controllers:'⊞',
    portal:'▧',multimedia:'▶',games:'✦',storage:'▤',backups:'↺',
    updates:'⇪',tools:'⌘',alerts:'⚑',system:'⚙'
  };
  function normalize(value) { return permitted.indexOf(value) < 0 ? 'fusion' : value; }
  function apply(value) {
    const mode = normalize(value);
    document.body.setAttribute('data-blaze-style', mode);
    const selector = document.getElementById('blazeStyleSelect');
    if (selector) selector.value = mode;
    try { window.localStorage.setItem(key, mode); } catch (_) { /* private mode */ }
  }
  function boot() {
    const selector = document.getElementById('blazeStyleSelect');
    if (!selector) return;
    let current = 'fusion';
    try { current = window.localStorage.getItem(key) || current; } catch (_) { /* private mode */ }
    apply(current);
    selector.addEventListener('change', function () { apply(selector.value); });
    document.querySelectorAll('.nav-btn[data-page]').forEach(function (button) {
      const symbol = icons[button.getAttribute('data-page')];
      if (symbol) button.setAttribute('data-symbol', symbol);
    });
    // Fast local navigation: no network, no new privileges and no API calls.
    const searchInput = document.getElementById('blazeNavSearch');
    const sidebar = document.getElementById('sidebar');
    const appView = document.getElementById('appView');
    if (searchInput && sidebar) {
      const buttons = Array.from(sidebar.querySelectorAll('.nav-btn[data-page]'));
      const labels = Array.from(sidebar.querySelectorAll('.nav-label'));
      const count = document.getElementById('blazeNavCount');
      const empty = document.getElementById('blazeNavEmpty');
      function filterPages() {
        const term = searchInput.value.toLocaleLowerCase().trim();
        let visible = 0;
        buttons.forEach(function (button) {
          const label = (button.textContent + ' ' + button.getAttribute('data-page')).toLocaleLowerCase();
          button.hidden = Boolean(term) && !label.includes(term);
          if (!button.hidden) visible++;
        });
        labels.forEach(function (label) {
          let next = label.nextElementSibling;
          let available = false;
          while (next && !next.classList.contains('nav-label') && !next.classList.contains('sidebar-foot')) {
            if (next.matches('.nav-btn[data-page]') && !next.hidden) available = true;
            next = next.nextElementSibling;
          }
          label.hidden = Boolean(term) && !available;
        });
        if (empty) empty.hidden = visible > 0;
        if (count) count.textContent = term ? visible + (visible === 1 ? ' matching section' : ' matching sections')
                                           : 'Navigate without leaving the console';
      }
      searchInput.addEventListener('input', filterPages);
      searchInput.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
          searchInput.value = '';
          filterPages();
          searchInput.blur();
          sidebar.classList.remove('open');
        } else if (event.key === 'Enter') {
          const target = buttons.find(function (item) { return !item.hidden; });
          if (target) {
            event.preventDefault();
            target.click();
            searchInput.value = '';
            filterPages();
            searchInput.blur();
          }
        }
      });
      document.addEventListener('keydown', function (event) {
        if (appView && appView.classList.contains('hidden')) return;
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
          event.preventDefault();
          sidebar.classList.add('open');
          searchInput.focus();
          searchInput.select();
        } else if (event.key === 'Escape' && event.target !== searchInput) {
          sidebar.classList.remove('open');
        }
      });
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, { once: true });
  } else boot();
})();
