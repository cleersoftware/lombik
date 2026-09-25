/*!
 * DropdownEngine
 * Small dependency-free engine for the custom <dropdown> element.
 *
 * Usage:
 *   <div class="relative">
 *     <button type="button">Menu</button>
 *     <dropdown class="absolute right-0">
 *       <a href="/x">Item</a>
 *     </dropdown>
 *   </div>
 */
(function (global) {
  'use strict';

  var OPEN_CLASS = 'dropdown-open';
  var ACTIVE_CLASS = 'dropdown-active';
  var initializedRoots = new WeakSet();

  function getTrigger(el) {
    while (el) {
      var children = el.children;
      for (var i = 0; i < children.length; i++) {
        if (children[i].tagName.toLowerCase() === 'dropdown') return el;
      }
      el = el.parentElement;
    }
    return null;
  }

  function getDropdown(trigger) {
    if (!trigger) return null;
    var children = trigger.children;
    for (var i = 0; i < children.length; i++) {
      if (children[i].tagName.toLowerCase() === 'dropdown') return children[i];
    }
    return null;
  }

  function smartPosition(dd) {
    dd.style.visibility = 'hidden';
    dd.style.display = 'block';

    dd.style.top = 'calc(100% + 4px)';
    dd.style.bottom = 'auto';
    dd.style.left = '0';
    dd.style.right = 'auto';
    dd.style.margin = '0';

    var rect = dd.getBoundingClientRect();
    var vw = window.visualViewport ? window.visualViewport.width : window.innerWidth;
    var vh = window.visualViewport ? window.visualViewport.height : window.innerHeight;

    if (rect.right > vw) { dd.style.left = 'auto'; dd.style.right = '0'; }
    if (rect.bottom > vh) { dd.style.top = 'auto'; dd.style.bottom = 'calc(100% + 4px)'; }

    rect = dd.getBoundingClientRect();
    if (rect.left < 0) { dd.style.left = '0'; dd.style.right = 'auto'; }

    dd.style.visibility = 'visible';
  }

  function open(trigger) {
    var dd = getDropdown(trigger);
    if (!dd) return;
    closeAll();
    trigger.classList.add(ACTIVE_CLASS);
    dd.classList.add(OPEN_CLASS);
    smartPosition(dd);
  }

  function close(trigger) {
    var dd = getDropdown(trigger);
    if (!dd) return;
    trigger.classList.remove(ACTIVE_CLASS);
    dd.classList.remove(OPEN_CLASS);
    dd.style.display = 'none';
  }

  function closeAll(exceptTrigger) {
    var active = document.querySelectorAll('.' + ACTIVE_CLASS);
    for (var i = 0; i < active.length; i++) {
      if (active[i] !== exceptTrigger) close(active[i]);
    }
  }

  function isOpen(trigger) {
    return trigger && trigger.classList.contains(ACTIVE_CLASS);
  }

  function onClick(e) {
    var trigger = getTrigger(e.target);
    if (!trigger) { closeAll(); return; }

    if (e.target.closest('dropdown')) {
      if (isOpen(trigger)) setTimeout(function () { close(trigger); }, 0);
      return;
    }

    if (isOpen(trigger)) close(trigger);
    else open(trigger);
    e.stopPropagation();
  }

  function onKeyDown(e) {
    if (e.key === 'Escape') closeAll();
  }

  function onResize() {
    var active = document.querySelectorAll('.' + ACTIVE_CLASS);
    for (var i = 0; i < active.length; i++) {
      var dd = getDropdown(active[i]);
      if (dd) smartPosition(dd);
    }
  }

  function init(root) {
    root = root || document;
    if (initializedRoots.has(root)) return;
    initializedRoots.add(root);
    root.addEventListener('click', onClick, true);
    document.addEventListener('keydown', onKeyDown);
    window.addEventListener('resize', onResize);

    document.querySelectorAll('dropdown').forEach(function (dd) {
      if (!dd.classList.contains(OPEN_CLASS)) dd.style.display = 'none';
    });
  }

  global.DropdownEngine = { init: init, open: open, close: close, closeAll: closeAll };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { init(document); });
  } else {
    init(document);
  }
})(window);

/* Re-init dropdowns inside swapped-in HTMX fragments. */
document.body.addEventListener('htmx:afterSwap', function (e) {
  DropdownEngine.init(e.target);
});
