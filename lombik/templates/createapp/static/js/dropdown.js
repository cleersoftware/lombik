/*!
 * DropdownEngine v1.0.1
 * A dependency-free custom dropdown built on the native <dropdown> element.
 * ---------------------------------------------------------------------
 * MARKUP CONTRACT
 *   <button>                <-- trigger (any element)
 *     Options
 *     <dropdown>            <-- hidden until click, positioned absolute
 *       <a href="#">...</a>
 *     </dropdown>
 *   </button>
 *
 * STATE CLASSES (auto‑managed)
 *   .dropdown-active      added to the trigger when open
 *   .dropdown-open        added to <dropdown> for CSS transitions
 *
 * BEHAVIOUR
 *   - Click trigger: toggle dropdown.
 *   - Click outside: close all dropdowns.
 *   - Escape key: close all dropdowns.
 *   - Multiple triggers: only one open at a time.
 *
 * PUBLIC API
 *   DropdownEngine.init(root)   enable delegated listeners on `root`
 *                                (defaults to `document`)
 * ---------------------------------------------------------------------
 */
(function (global) {
    'use strict';
  
    var OPEN_CLASS = 'dropdown-open';
    var ACTIVE_CLASS = 'dropdown-active';
    var initializedRoots = new WeakSet();
  
    /**
     * Returns the trigger element if `el` or any ancestor contains a
     * direct child <dropdown>, otherwise null.
     */
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
  
    function positionDropdown(dropdown, trigger) {
      if (!trigger || !dropdown) return;
      var triggerRect = trigger.getBoundingClientRect();
      var ddStyle = dropdown.style;
      ddStyle.position = 'fixed';
      ddStyle.top = (triggerRect.bottom + 4) + 'px';
      ddStyle.left = triggerRect.left + 'px';
      ddStyle.minWidth = triggerRect.width + 'px';
  
      requestAnimationFrame(function () {
        var ddRect = dropdown.getBoundingClientRect();
        if (ddRect.right > window.innerWidth) {
          ddStyle.left = (window.innerWidth - ddRect.width - 8) + 'px';
        }
        if (ddRect.bottom > window.innerHeight) {
          ddStyle.top = (triggerRect.top - ddRect.height - 4) + 'px';
        }
      });
    }
  
    function open(trigger) {
      var dd = getDropdown(trigger);
      if (!dd) return;
      closeAll();
      trigger.classList.add(ACTIVE_CLASS);
      dd.classList.add(OPEN_CLASS);
      dd.style.display = 'block';
      positionDropdown(dd, trigger);
    }
  
    function close(trigger) {
      var dd = getDropdown(trigger);
      if (!dd) return;
      trigger.classList.remove(ACTIVE_CLASS);
      dd.classList.remove(OPEN_CLASS);
      dd.style.display = '';
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
  
    // Event handler
    function onClick(e) {
      var trigger = getTrigger(e.target);
      if (!trigger) {
        // Click outside any trigger → close all
        closeAll();
        return;
      }
  
      // Determine if the click is inside the dropdown itself
      var clickedInDropdown = !!e.target.closest('dropdown');
  
      if (clickedInDropdown) {
        // Click on an item inside the dropdown – let its default action happen,
        // then close the dropdown after a micro‑task delay.
        if (isOpen(trigger)) {
          setTimeout(function () { close(trigger); }, 0);
        }
        return; // Do not toggle, let the link/button work normally
      }
  
      // Click was on the trigger itself (or its non‑dropdown children) → toggle
      if (isOpen(trigger)) {
        close(trigger);
      } else {
        open(trigger);
      }
      e.stopPropagation(); // prevent immediate re‑close from body listener
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
        if (dd) positionDropdown(dd, activeTriggers[i]);
      }
    }
  
    function init(root) {
      root = root || document;
      if (initializedRoots.has(root)) return;
      initializedRoots.add(root);
      root.addEventListener('click', onClick, true);
      document.addEventListener('keydown', onKeyDown);
      window.addEventListener('resize', onResize);
      window.addEventListener('scroll', onResize, true);
    }
  
    global.DropdownEngine = {
      init: init,
      open: open,
      close: close,
      closeAll: closeAll,
    };
  
    // Auto‑init
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function () { init(document); });
    } else {
      init(document);
    }
  })(window);