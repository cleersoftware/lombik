/*!
 * DropdownEngine v1.0.4 (Strictly Default + Edge Avoidance)
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
        if (children[i].tagName.toLowerCase() === 'dropdown') {
          return el;
        }
      }
      el = el.parentElement;
    }
    return null;
  }

  function getDropdown(trigger) {
    if (!trigger) return null;
    var children = trigger.children;
    for (var i = 0; i < children.length; i++) {
      if (children[i].tagName.toLowerCase() === 'dropdown') {
        return children[i];
      }
    }
    return null;
  }

  function smartPosition(dd, trigger) {
      // Temporarily display as hidden to calculate real dimensions
      dd.style.visibility = 'hidden';
      dd.style.display = 'block';
      
      // 1. Force your requested default: 
      // Inline with button start (left: 0), 4px below bottom edge.
      dd.style.top = 'calc(100% + 4px)';
      dd.style.bottom = 'auto';
      dd.style.left = '0';
      dd.style.right = 'auto';
      
      // Clear any Tailwind margins (like mt-2) so our 4px math is exact
      dd.style.margin = '0'; 

      // 2. Measure the dropdown in its default state
      var rect = dd.getBoundingClientRect();
      var viewportWidth = window.visualViewport ? window.visualViewport.width : window.innerWidth;
      var viewportHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight;

      // 3. Edge Check: Right side of the screen
      if (rect.right > viewportWidth) {
          // It bleeds off the right edge. Snap to the right edge of the button.
          dd.style.left = 'auto';
          dd.style.right = '0';
      }

      // 4. Edge Check: Bottom of the screen (dvh)
      if (rect.bottom > viewportHeight) {
          // It bleeds off the bottom. Flip it ABOVE the button (with 4px gap).
          dd.style.top = 'auto';
          dd.style.bottom = 'calc(100% + 4px)';
      }

      // 5. Edge Check: Left side (Only happens on tiny mobile screens if right-snap pushed it too far)
      rect = dd.getBoundingClientRect(); // Recalculate just in case
      if (rect.left < 0) {
          dd.style.left = '0';
          dd.style.right = 'auto';
      }

      // Make visible now that it's in the optimal safe spot
      dd.style.visibility = 'visible';
  }

  function open(trigger) {
    var dd = getDropdown(trigger);
    if (!dd) return;
    closeAll();
    trigger.classList.add(ACTIVE_CLASS);
    dd.classList.add(OPEN_CLASS);
    
    smartPosition(dd, trigger);
  }

  function close(trigger) {
    var dd = getDropdown(trigger);
    if (!dd) return;
    trigger.classList.remove(ACTIVE_CLASS);
    dd.classList.remove(OPEN_CLASS);
    dd.style.display = 'none'; 
  }

  function closeAll(exceptTrigger) {
    var activeTriggers = document.querySelectorAll('.' + ACTIVE_CLASS);
    for (var i = 0; i < activeTriggers.length; i++) {
      if (activeTriggers[i] !== exceptTrigger) {
        close(activeTriggers[i]);
      }
    }
  }

  function isOpen(trigger) {
    return trigger && trigger.classList.contains(ACTIVE_CLASS);
  }

  function onClick(e) {
    var trigger = getTrigger(e.target);
    if (!trigger) {
      closeAll();
      return;
    }

    var clickedInDropdown = !!e.target.closest('dropdown');

    if (clickedInDropdown) {
      if (isOpen(trigger)) {
        setTimeout(function () { close(trigger); }, 0);
      }
      return; 
    }

    if (isOpen(trigger)) {
      close(trigger);
    } else {
      open(trigger);
    }
    e.stopPropagation(); 
  }

  function onKeyDown(e) {
    if (e.key === 'Escape') {
      closeAll();
    }
  }

  function onResize() {
    var activeTriggers = document.querySelectorAll('.' + ACTIVE_CLASS);
    for (var i = 0; i < activeTriggers.length; i++) {
      var dd = getDropdown(activeTriggers[i]);
      if (dd) smartPosition(dd, activeTriggers[i]);
    }
  }

  function init(root) {
    root = root || document;
    if (initializedRoots.has(root)) return;
    initializedRoots.add(root);
    root.addEventListener('click', onClick, true);
    document.addEventListener('keydown', onKeyDown);
    window.addEventListener('resize', onResize);
    
    var dropdowns = document.querySelectorAll('dropdown');
    dropdowns.forEach(function(dd) {
      if (!dd.classList.contains(OPEN_CLASS)) {
         dd.style.display = 'none';
      }
    });
  }

  global.DropdownEngine = {
    init: init,
    open: open,
    close: close,
    closeAll: closeAll,
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { init(document); });
  } else {
    init(document);
  }
})(window);

document.body.addEventListener("htmx:afterSwap", function (e) {
  DropdownEngine.init(e.target);
});