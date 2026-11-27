/* BlazeFusion EasyMode preview. UI preference only; never accesses ubus/session state. */
(function () {
  'use strict';
  const key = 'blazepwifi.console.appearance.v1';
  const allowed = ['fusion', 'compact', 'comfort'];
  function initialize() {
    const selector = document.getElementById('blazefusion-appearance');
    if (!selector) return;
    function setMode(value) {
      const mode = allowed.includes(value) ? value : 'fusion';
      document.documentElement.setAttribute('data-blaze-style', mode);
      selector.value = mode;
      try { window.localStorage.setItem(key, mode); } catch (_) {}
    }
    let initial = 'fusion';
    try { initial = window.localStorage.getItem(key) || initial; } catch (_) {}
    setMode(initial);
    selector.addEventListener('change', () => setMode(selector.value));
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize, {once:true});
  } else initialize();
})();
