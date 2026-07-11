/*!
 * DragEngine v1.2.0
 * A dependency-free drag & drop / sortable engine built on Pointer Events.
 * ---------------------------------------------------------------------
 * MARKUP CONTRACT
 *   <div class="dragarea">              <-- parent / drop zone
 *     <div class="dragable">...</div>   <-- draggable item
 *     <div class="dragable">...</div>
 *   </div>
 *
 * MODIFIER CLASSES (put these on the .dragarea)
 *   .showgap   Animates siblings sliding out of the way and shows a
 *              placeholder "gap" where the dragged item will land
 *              (a FLIP animation). Without it, reordering is instant.
 *   .snap      Treats children as fixed slots (grid / kanban style).
 *              Dragging near a slot swaps directly into it instead of
 *              shifting every other item. Pairs great with CSS Grid.
 *   .ordered   Same swap behaviour as .snap: the dragged item and the
 *              item you drop it on trade places 1-for-1, nothing else
 *              reflows. Use whichever of .snap/.ordered reads better
 *              in your markup - they are equivalent.
 *   (none)     Default = "insert" mode, classic list reordering:
 *              siblings shift to make room, no animation.
 *
 * MODIFIER CLASSES (put these on the .dragable)
 *   .dragfree          The item becomes a free‑floating element. It can
 *                      be placed anywhere on the screen; no list, no
 *                      placeholder, no snapping. Position resets on reload.
 *   .dragfree-save     Like .dragfree, but the final screen position is
 *                      saved to localStorage and restored on page load.
 *                      Requires a unique `data-dragfree-id` attribute.
 *
 * DATA ATTRIBUTES
 *   data-group="name"     on .dragarea   Allows dragging *between*
 *                          different .dragarea elements that share the
 *                          same group name. Omit it to lock an item to
 *                          its own list (default & safest behaviour).
 *   data-handle=".sel"    on .dragable (or the .dragarea, as a
 *                          fallback default for all its children)
 *                          Restricts drag-start to elements matching
 *                          the selector inside the item, e.g. a small
 *                          drag handle icon.
 *   data-dragfree-id      on .dragfree-save   Unique ID for localStorage
 *                          storage (any string, e.g. "logout-btn").
 *
 * STATE CLASSES (added/removed automatically, style them if you like)
 *   .dragable.dragging          the item currently being dragged
 *   .dragable.drag-disabled     add this yourself to lock an item
 *   .drag-placeholder           the "landing spot" stand-in element
 *   body.dragengine-active      set on <body> for the drag's duration
 *
 * RESET BEHAVIOUR
 *   Double‑click any .dragfree-save element to reset it to its original
 *   position and clear the saved data from localStorage.
 *   Or call DragEngine.resetFree(elementOrId) programmatically.
 *
 * EVENTS (all bubble, all dispatched on the relevant .dragarea)
 *   dragengine:start   { item, from:{area,index} }
 *   dragengine:end     { item, from, to, changed }
 *   dragengine:sort     same shape as :end, only fired when the order
 *                        actually changed (i.e. a real drop happened)
 *
 * PUBLIC API
 *   DragEngine.init(root)        wire up delegated listeners on `root`
 *   DragEngine.cancel()          abort an in-progress drag programmatically
 *   DragEngine.resetFree(id)     reset a saved free element to its
 *                                original position (pass the element or
 *                                the data-dragfree-id string)
 * ---------------------------------------------------------------------
 */
(function (global) {
  'use strict';

  var THRESHOLD = 4; // px of movement before a pointerdown becomes a drag
  var FLIP_MS = 220; // sibling slide animation duration

  var initializedRoots = new WeakSet();
  var pending = null;
  var drag = null;

  // ---------------------------------------------------------------
  // small dom helpers
  // ---------------------------------------------------------------

  function trackedChildren(area) {
    return Array.prototype.filter.call(area.children, function (el) {
      return el.classList.contains('dragable') || el.classList.contains('drag-placeholder');
    });
  }

  function indexOf(node, area) {
    return trackedChildren(area).indexOf(node);
  }

  function getMode(area) {
    return area.classList.contains('snap') || area.classList.contains('ordered') ? 'swap' : 'insert';
  }

  function isAnimated(area) {
    return area.classList.contains('showgap');
  }

  function getAxis(area) {
    var cs = getComputedStyle(area);
    var display = cs.display;
    if (display.indexOf('grid') !== -1) {
      var cols = cs.gridTemplateColumns.split(' ').filter(Boolean).length;
      return cols > 1 ? 'grid' : 'y';
    }
    if (display.indexOf('flex') !== -1) {
      return cs.flexDirection.indexOf('row') === 0 ? 'x' : 'y';
    }
    return 'y';
  }

  function isCompatible(area) {
    if (area === drag.originArea) return true;
    var g1 = drag.originArea ? drag.originArea.dataset.group : null;
    var g2 = area.dataset.group;
    return !!g1 && g1 === g2;
  }

  // FLIP
  function captureRects(area) {
    var map = new Map();
    trackedChildren(area).forEach(function (el) {
      map.set(el, el.getBoundingClientRect());
    });
    return map;
  }

  function playFlip(rectsBefore) {
    if (!rectsBefore) return;
    rectsBefore.forEach(function (before, el) {
      if (!el.isConnected || el === (drag && drag.item)) return;
      var after = el.getBoundingClientRect();
      var dx = before.left - after.left;
      var dy = before.top - after.top;
      if (!dx && !dy) return;
      el.style.transition = 'none';
      el.style.transform = 'translate(' + dx + 'px,' + dy + 'px)';
      // eslint-disable-next-line no-unused-expressions
      el.offsetHeight;
      requestAnimationFrame(function () {
        el.style.transition = 'transform ' + FLIP_MS + 'ms cubic-bezier(.2,.8,.2,1)';
        el.style.transform = '';
      });
      el.addEventListener('transitionend', function handler() {
        el.style.transition = '';
        el.removeEventListener('transitionend', handler);
      });
    });
  }

  function swapNodes(a, b) {
    var parentA = a.parentNode;
    var parentB = b.parentNode;
    if (!parentA || !parentB) return;
    var markerA = document.createComment('');
    parentA.insertBefore(markerA, a);
    parentB.insertBefore(a, b);
    parentA.insertBefore(b, markerA);
    parentA.removeChild(markerA);
  }

  // ---------------------------------------------------------------
  // localStorage helpers for dragfree-save
  // ---------------------------------------------------------------
  function getStorageKey(id) {
    return 'dragfree-pos-' + id;
  }

  function savePosition(item) {
    if (!item.classList.contains('dragfree-save')) return;
    var id = item.getAttribute('data-dragfree-id');
    if (!id) return;
    try {
      localStorage.setItem(getStorageKey(id), JSON.stringify({
        left: item.style.left,
        top: item.style.top
      }));
    } catch (e) { /* ignore */ }
  }

  function clearSavedPosition(item) {
    if (!item.classList.contains('dragfree-save')) return;
    var id = item.getAttribute('data-dragfree-id');
    if (!id) return;
    try {
      localStorage.removeItem(getStorageKey(id));
    } catch (e) { /* ignore */ }
  }

  function restoreDragFreePositions() {
    var items = document.querySelectorAll('.dragable.dragfree-save[data-dragfree-id]');
    for (var i = 0; i < items.length; i++) {
      var el = items[i];
      var id = el.getAttribute('data-dragfree-id');
      try {
        var raw = localStorage.getItem(getStorageKey(id));
        if (raw) {
          var pos = JSON.parse(raw);
          if (pos && typeof pos.left === 'string' && typeof pos.top === 'string') {
            el.style.position = 'fixed';
            el.style.left = pos.left;
            el.style.top = pos.top;
            // Keep other styles intact; we only set fixed and coordinates.
          }
        }
      } catch (e) { /* ignore invalid data */ }
    }
  }

  /**
   * Reset a free‑saved element to its original DOM position.
   * @param {Element|string} elOrId - The element or data-dragfree-id.
   */
  function resetFree(elOrId) {
    var el;
    if (typeof elOrId === 'string') {
      el = document.querySelector('.dragfree-save[data-dragfree-id="' + elOrId + '"]');
    } else if (elOrId instanceof Element) {
      el = elOrId;
    }
    if (!el || !el.classList.contains('dragfree-save')) return;

    // Clear stored position
    clearSavedPosition(el);

    // Remove all inline styles that the engine added, letting CSS take over
    ['position', 'left', 'top', 'width', 'height', 'margin', 'zIndex', 'pointerEvents', 'willChange'].forEach(function (p) {
      el.style[p] = '';
    });
    // Also remove the .dragging class just in case
    el.classList.remove('dragging');

    // If the element was moved to <body> during a previous drag, we need to put it back.
    // The engine's cancel function does that, but we can replicate the logic:
    // Actually, after a drop, the free element stays in <body>. To truly "reset",
    // we should return it to its original parent. However, we didn't store the original
    // parent on drop. We can store it at drag start. Let's add that.
    // Since we now store `freeOriginParent` and `freeOriginNextSibling` in the drag object,
    // we need to preserve them after drop. We'll add a data attribute to remember the origin.
    // Simpler: we can just remove the element from <body> and re-insert it at its
    // original location if we know it. But we didn't save that on drop.
    //
    // For v1.2, we'll do a more reliable reset: store the original parent & next sibling
    // on the element itself via data attributes when dragging starts. Then on reset,
    // we can use those to move it back.
    //
    // We'll implement that in the drag lifecycle.
  }

  // ---------------------------------------------------------------
  // drag lifecycle
  // ---------------------------------------------------------------

  function onPointerDown(e) {
    if (drag || pending) return;
    if (e.button !== undefined && e.button !== 0) return;

    var item = e.target.closest('.dragable');
    if (!item) return;

    var area = item.closest('.dragarea');
    if (!area && !item.classList.contains('dragfree')) return;

    if (item.classList.contains('drag-disabled') || item.getAttribute('aria-disabled') === 'true') return;

    var handleSel = item.dataset.handle || (area ? area.dataset.handle : null);
    if (handleSel) {
      if (!e.target.closest(handleSel)) return;
    } else if (e.target.closest('input, textarea, select, button, a[href], [contenteditable="true"]')) {
      return;
    }

    var rect = item.getBoundingClientRect();
    pending = {
      pointerId: e.pointerId,
      item: item,
      area: area || null,
      startX: e.clientX,
      startY: e.clientY,
      offsetX: e.clientX - rect.left,
      offsetY: e.clientY - rect.top,
      rect: rect,
    };

    document.addEventListener('pointermove', onPointerMove);
    document.addEventListener('pointerup', onPointerUp);
    document.addEventListener('pointercancel', onPointerUp);
  }

  function onPointerMove(e) {
    if (!drag) {
      if (!pending || e.pointerId !== pending.pointerId) return;
      var dx = e.clientX - pending.startX;
      var dy = e.clientY - pending.startY;
      if (Math.hypot(dx, dy) < THRESHOLD) return;
      beginDrag(pending, e);
      pending = null;
    }
    if (!drag || e.pointerId !== drag.pointerId) return;
    e.preventDefault();
    drag.pointerX = e.clientX;
    drag.pointerY = e.clientY;
  }

  function onPointerUp(e) {
    document.removeEventListener('pointermove', onPointerMove);
    document.removeEventListener('pointerup', onPointerUp);
    document.removeEventListener('pointercancel', onPointerUp);

    if (!drag) {
      pending = null;
      return;
    }
    if (e.pointerId !== drag.pointerId) return;
    finishDrag();
  }

  function beginDrag(p, e) {
    var item = p.item;
    var area = p.area;
    var rect = p.rect;
    var isFree = item.classList.contains('dragfree');

    if (isFree) {
      // Store original DOM position for later reset
      var origParent = item.parentNode;
      var origNext = item.nextSibling;
      // Use data attributes to persist across moves (we'll set them on the element)
      item.setAttribute('data-dragfree-orig-parent', ''); // can't store object, store reference? No.
      // Instead, we'll store the parent's identity by marking a unique attribute. Better: just rely on the fact that we'll always keep the element in <body> after drag, and we'll store the original parent as a property on the element itself.
      // Simple: store original parent and next sibling as expando properties.
      item._dragfreeOrigParent = origParent;
      item._dragfreeOrigNext = origNext;

      drag = {
        pointerId: p.pointerId,
        item: item,
        placeholder: null,
        originArea: null,
        originIndex: -1,
        offsetX: p.offsetX,
        offsetY: p.offsetY,
        pointerX: e.clientX,
        pointerY: e.clientY,
        rafId: null,
        free: true,
        freeOriginParent: origParent,
        freeOriginNextSibling: origNext,
      };

      document.body.appendChild(item);
      Object.assign(item.style, {
        position: 'fixed',
        left: rect.left + 'px',
        top: rect.top + 'px',
        width: rect.width + 'px',
        height: rect.height + 'px',
        margin: '0',
        zIndex: '9999',
        pointerEvents: 'none',
        willChange: 'transform, left, top',
      });
      item.classList.add('dragging');
      document.body.classList.add('dragengine-active');

      item.addEventListener('click', function (ce) {
        ce.preventDefault();
        ce.stopPropagation();
      }, { capture: true, once: true });

      document.body.dispatchEvent(new CustomEvent('dragengine:start', {
        bubbles: true,
        detail: { item: item, from: { area: null, index: -1 } },
      }));

      loop();
      return;
    }

    // Normal list mode
    var placeholder = document.createElement('div');
    placeholder.className = 'drag-placeholder';
    placeholder.style.width = rect.width + 'px';
    placeholder.style.height = rect.height + 'px';
    area.insertBefore(placeholder, item);

    document.body.appendChild(item);
    Object.assign(item.style, {
      position: 'fixed',
      left: rect.left + 'px',
      top: rect.top + 'px',
      width: rect.width + 'px',
      height: rect.height + 'px',
      margin: '0',
      zIndex: '9999',
      pointerEvents: 'none',
      willChange: 'transform, left, top',
    });
    item.classList.add('dragging');
    document.body.classList.add('dragengine-active');

    drag = {
      pointerId: p.pointerId,
      item: item,
      placeholder: placeholder,
      originArea: area,
      originIndex: indexOf(placeholder, area),
      offsetX: p.offsetX,
      offsetY: p.offsetY,
      pointerX: e.clientX,
      pointerY: e.clientY,
      rafId: null,
      free: false,
    };

    item.addEventListener('click', function (ce) {
      ce.preventDefault();
      ce.stopPropagation();
    }, { capture: true, once: true });

    area.dispatchEvent(new CustomEvent('dragengine:start', {
      bubbles: true,
      detail: { item: item, from: { area: area, index: drag.originIndex } },
    }));

    loop();
  }

  function loop() {
    if (!drag) return;
    drag.item.style.left = drag.pointerX - drag.offsetX + 'px';
    drag.item.style.top = drag.pointerY - drag.offsetY + 'px';
    if (!drag.free) {
      updateHitTest();
    }
    drag.rafId = requestAnimationFrame(loop);
  }

  function updateHitTest() {
    var el = document.elementFromPoint(drag.pointerX, drag.pointerY);
    if (!el) return;

    var area = el.closest('.dragarea');
    if (!area || !isCompatible(area)) return;

    var targetChild = el.closest('.dragable, .drag-placeholder');
    if (targetChild === drag.item) return;

    if (!targetChild) {
      if (area !== drag.placeholder.parentNode) {
        var animated = isAnimated(area);
        var originAnimated = isAnimated(drag.placeholder.parentNode);
        var rectsHere = animated ? captureRects(area) : null;
        var rectsOrigin = originAnimated ? captureRects(drag.placeholder.parentNode) : null;
        area.appendChild(drag.placeholder);
        playFlip(rectsHere);
        playFlip(rectsOrigin);
      }
      return;
    }

    if (targetChild === drag.placeholder) return;

    var mode = getMode(area);
    var animated2 = isAnimated(area);
    var crossArea = drag.placeholder.parentNode !== area;
    var rectsTarget = animated2 || (crossArea && isAnimated(drag.placeholder.parentNode)) ? captureRects(area) : null;
    var rectsOriginArea = crossArea && isAnimated(drag.placeholder.parentNode) ? captureRects(drag.placeholder.parentNode) : null;

    if (mode === 'swap') {
      swapNodes(drag.placeholder, targetChild);
    } else {
      var axis = getAxis(area);
      var r = targetChild.getBoundingClientRect();
      var before;
      if (axis === 'x') {
        before = drag.pointerX < r.left + r.width / 2;
      } else if (axis === 'grid') {
        var cy = r.top + r.height / 2;
        if (Math.abs(drag.pointerY - cy) > r.height * 0.25) {
          before = drag.pointerY < cy;
        } else {
          before = drag.pointerX < r.left + r.width / 2;
        }
      } else {
        before = drag.pointerY < r.top + r.height / 2;
      }
      if (before) area.insertBefore(drag.placeholder, targetChild);
      else area.insertBefore(drag.placeholder, targetChild.nextSibling);
    }

    playFlip(rectsTarget);
    playFlip(rectsOriginArea);
  }

  function finishDrag() {
    cancelAnimationFrame(drag.rafId);

    var item = drag.item;
    var isFree = drag.free;

    if (isFree) {
      // Cleanup but keep position
      item.style.pointerEvents = '';
      item.style.zIndex = '';
      item.style.willChange = '';
      item.style.width = '';
      item.style.height = '';
      item.style.margin = '';
      item.classList.remove('dragging');
      document.body.classList.remove('dragengine-active');

      // Save if requested
      savePosition(item);

      document.body.dispatchEvent(new CustomEvent('dragengine:end', {
        bubbles: true,
        detail: {
          item: item,
          from: { area: null, index: -1 },
          to: { area: null, index: -1 },
          changed: true,
        },
      }));

      drag = null;
      return;
    }

    // Normal mode
    var placeholder = drag.placeholder;
    var originArea = drag.originArea;
    var originIndex = drag.originIndex;
    var finalArea = placeholder.parentNode || originArea;

    finalArea.insertBefore(item, placeholder);
    placeholder.remove();

    ['position', 'left', 'top', 'width', 'height', 'margin', 'zIndex', 'pointerEvents', 'willChange'].forEach(function (p) {
      item.style[p] = '';
    });
    item.classList.remove('dragging');
    document.body.classList.remove('dragengine-active');

    var finalIndex = indexOf(item, finalArea);
    var changed = finalArea !== originArea || finalIndex !== originIndex;

    var detail = {
      item: item,
      from: { area: originArea, index: originIndex },
      to: { area: finalArea, index: finalIndex },
      changed: changed,
    };
    finalArea.dispatchEvent(new CustomEvent('dragengine:end', { bubbles: true, detail: detail }));
    if (changed) finalArea.dispatchEvent(new CustomEvent('dragengine:sort', { bubbles: true, detail: detail }));

    drag = null;
  }

  function cancel() {
    if (!drag) return;
    cancelAnimationFrame(drag.rafId);

    var item = drag.item;

    if (drag.free) {
      var parent = drag.freeOriginParent;
      var next = drag.freeOriginNextSibling;
      if (next && next.parentNode === parent) {
        parent.insertBefore(item, next);
      } else {
        parent.appendChild(item);
      }
      ['position', 'left', 'top', 'width', 'height', 'margin', 'zIndex', 'pointerEvents', 'willChange'].forEach(function (p) {
        item.style[p] = '';
      });
      item.classList.remove('dragging');
      document.body.classList.remove('dragengine-active');
      drag = null;
      pending = null;
      return;
    }

    drag.originArea.insertBefore(drag.item, drag.placeholder);
    drag.placeholder.remove();
    ['position', 'left', 'top', 'width', 'height', 'margin', 'zIndex', 'pointerEvents', 'willChange'].forEach(function (p) {
      drag.item.style[p] = '';
    });
    drag.item.classList.remove('dragging');
    document.body.classList.remove('dragengine-active');
    drag = null;
    pending = null;
  }

  // ---------------------------------------------------------------
  // Reset logic (double‑click to reset)
  // ---------------------------------------------------------------
  function onDblClick(e) {
    var item = e.target.closest('.dragable.dragfree-save');
    if (!item) return;
    e.preventDefault();
    resetFree(item);
  }

  // Override the previous resetFree to use stored origin info
  function resetFree(elOrId) {
    var el;
    if (typeof elOrId === 'string') {
      el = document.querySelector('.dragfree-save[data-dragfree-id="' + elOrId + '"]');
    } else {
      el = elOrId;
    }
    if (!el || !el.classList.contains('dragfree-save')) return;

    // Clear saved position
    clearSavedPosition(el);

    // If the element is currently in <body> (as it would be after a drag), move it back
    if (el.parentNode === document.body && el._dragfreeOrigParent) {
      var origParent = el._dragfreeOrigParent;
      var origNext = el._dragfreeOrigNext;
      if (origNext && origNext.parentNode === origParent) {
        origParent.insertBefore(el, origNext);
      } else if (origParent) {
        origParent.appendChild(el);
      }
      // Clear stored origin
      delete el._dragfreeOrigParent;
      delete el._dragfreeOrigNext;
    }

    // Remove all inline styles added by dragging
    ['position', 'left', 'top', 'width', 'height', 'margin', 'zIndex', 'pointerEvents', 'willChange'].forEach(function (p) {
      el.style[p] = '';
    });
    el.classList.remove('dragging');
  }

  // ---------------------------------------------------------------
  // public api
  // ---------------------------------------------------------------

  function init(root) {
    root = root || document;
    if (initializedRoots.has(root)) return;
    initializedRoots.add(root);
    root.addEventListener('pointerdown', onPointerDown);
    root.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') cancel();
    });
    root.addEventListener('dblclick', onDblClick); // double‑click to reset free elements
    restoreDragFreePositions();
  }

  global.DragEngine = {
    init: init,
    cancel: cancel,
    resetFree: resetFree,
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { init(document); });
  } else {
    init(document);
  }
})(window);

// ---------------------------------------------------------------
// HTMX bridge (unchanged)
// ---------------------------------------------------------------
document.body.addEventListener('dragengine:sort', function (evt) {
  const { item, to, changed } = evt.detail;
  if (!changed) return;

  const targetArea = to.area;
  const id = item.dataset.id;
  const field = targetArea.dataset.field;
  const value = targetArea.dataset.value;

  if (!id || !field || !value) return;

  const endpoint = targetArea.dataset.endpoint || '/drag-update';
  const csrfMeta = document.querySelector('meta[name="csrf-token"]');
  const csrfToken = csrfMeta ? csrfMeta.content : '';

  const payload = {
    id: id,
    field: field,
    value: value,
    from_index: evt.detail.from.index,
    to_index: to.index,
    csrf_token: csrfToken,
  };

  htmx.ajax('POST', endpoint, {
    target: targetArea,
    swap: 'none',
    values: payload,
  });
});