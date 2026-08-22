/*!
 * DragEngine v2.0.0
 * A dependency-free drag & drop / sortable engine built on Pointer Events.
 * ---------------------------------------------------------------------
 * HOW TO USE
 * ---------------------------------------------------------------------
 * 1. DROP ZONES
 *    <dragarea family="animals" field="category" value="land"></dragarea>
 *    Or use a div:
 *    <div class="dragarea" data-family="animals" data-field="category" data-value="land"></div>
 *
 *    - `family` allows dragging between different dragareas with the same family.
 *    - `field` / `value` are sent to htmx as dynamic payload keys.
 *
 * 2. DRAGGABLE ITEMS
 *    <div class="dragable" data-id="101">Aardvark</div>
 *    `.draggable` is also supported as an alias for `.dragable`.
 *
 * 3. FREE-FLOATING ELEMENTS
 *    <dragfree id="my-widget">...</dragfree>
 *    - If `id` or `data-dragfree-id` is present, position is saved to localStorage.
 *    - Double-click a free element to reset it to its original position.
 *
 * 4. HTMX INTEGRATION
 *    Put hx-patch / hx-post / hx-put / hx-delete on the <dragarea>.
 *    Example:
 *      <dragarea family="animals"
 *                hx-patch="/update-animal-category"
 *                hx-vals='{"csrf_token": "{{ csrf_token }}"}'
 *                field="category"
 *                value="land">
 *    When a drop changes something, DragEngine automatically calls:
 *      htmx.ajax(PATCH, endpoint, {
 *        target: area,
 *        swap: area.getAttribute('hx-swap') || 'none',
 *        values: {
 *          id: item.dataset.id,             // from dragged item
 *          category: "land",                // field / value from target area
 *          from_index: 0,
 *          to_index: 1,
 *          from_field: "category",
 *          from_value: "water"
 *        }
 *      })
 *    Static hx-vals (like csrf_token) are merged automatically by htmx.
 *
 * 5. MODIFIERS
 *    Add to <dragarea> (classes or attributes both work):
 *      showgap  → animated FLIP reordering
 *      snap     → swap slots instead of shifting
 *      ordered  → same as snap
 *
 * 6. DRAG HANDLE
 *    Add `handle=".drag-handle"` to an item or area.
 *
 * 7. PUBLIC API
 *    DragEngine.init(root)      wire delegated listeners
 *    DragEngine.cancel()        abort an in-progress drag
 *    DragEngine.resetFree(id)   reset a saved free element
 *
 * STATE CLASSES
 *    .dragging                  current dragged item
 *    body.dragengine-active     active drag session
 * ---------------------------------------------------------------------
 */
(function (global) {
  'use strict';

  var THRESHOLD = 4;
  var FLIP_MS = 220;

  var initializedRoots = new WeakSet();
  var pending = null;
  var drag = null;

  var AREA_SELECTOR = 'dragarea, .dragarea';
  var ITEM_SELECTOR = '.dragable, .draggable, dragfree, .dragfree, .dragfree-save';

  var RESET_STYLES = [
    'position', 'left', 'top', 'width', 'height', 'margin',
    'zIndex', 'pointerEvents', 'willChange', 'transition', 'transform'
  ];
  var FREE_KEEP_STYLES = [
    'width', 'height', 'margin', 'zIndex', 'pointerEvents',
    'willChange', 'transition', 'transform'
  ];

  function isItem(el) {
    return el && el.matches && el.matches(ITEM_SELECTOR);
  }

  function isFree(el) {
    return el && el.matches && el.matches(
      'dragfree, .dragfree, .dragfree-save, .dragable.dragfree, .draggable.dragfree, .dragable.dragfree-save, .draggable.dragfree-save'
    );
  }

  function findArea(el) {
    return el.closest ? el.closest(AREA_SELECTOR) : null;
  }

  function trackedChildren(area) {
    return Array.prototype.filter.call(area.children, function (el) {
      if (el.classList.contains('drag-placeholder')) return true;
      return isItem(el) && !isFree(el);
    });
  }

  function indexOf(node, area) {
    return trackedChildren(area).indexOf(node);
  }

  function hasModifier(area, name) {
    return area.classList.contains(name) || area.hasAttribute(name);
  }

  function getMode(area) {
    if (
      hasModifier(area, 'snap') ||
      hasModifier(area, 'ordered') ||
      getAxis(area) === 'grid'
    ) {
      return 'swap';
    }

    return 'insert';
  }

  function isAnimated(area) {
    return hasModifier(area, 'showgap');
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

  function getFamily(area) {
    return area.getAttribute('family') ||
           area.dataset.family ||
           area.getAttribute('data-group') ||
           area.dataset.group ||
           null;
  }

  function isCompatible(area) {
    if (area === drag.originArea) return true;
    var f1 = drag.originArea ? getFamily(drag.originArea) : null;
    var f2 = getFamily(area);
    return !!f1 && f1 === f2;
  }

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
      void el.offsetHeight;
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

    var marker = document.createComment('');

    parentA.insertBefore(marker, a);
    parentB.insertBefore(a, b);
    parentA.insertBefore(b, marker);
    parentA.removeChild(marker);
  }

  function getFreeId(item) {
    return item.id || item.getAttribute('data-dragfree-id') || null;
  }

  function getStorageKey(id) {
    return 'dragfree-pos-' + id;
  }

  function savePosition(item) {
    if (!isFree(item)) return;
    var id = getFreeId(item);
    if (!id) return;
    try {
      localStorage.setItem(getStorageKey(id), JSON.stringify({
        left: item.style.left,
        top: item.style.top
      }));
    } catch (e) { /* ignore */ }
  }

  function clearSavedPosition(item) {
    if (!isFree(item)) return;
    var id = getFreeId(item);
    if (!id) return;
    try {
      localStorage.removeItem(getStorageKey(id));
    } catch (e) { /* ignore */ }
  }

  function restoreDragFreePositions() {
    var items = document.querySelectorAll(ITEM_SELECTOR);
    for (var i = 0; i < items.length; i++) {
      var el = items[i];
      if (!isFree(el)) continue;
      var id = getFreeId(el);
      if (!id) continue;
      try {
        var raw = localStorage.getItem(getStorageKey(id));
        if (!raw) continue;
        var pos = JSON.parse(raw);
        if (pos && typeof pos.left === 'string' && typeof pos.top === 'string') {
          el.style.position = 'fixed';
          el.style.left = pos.left;
          el.style.top = pos.top;
        }
      } catch (e) { /* ignore */ }
    }
  }

  function setItemFixed(item, rect) {
    item.style.position = 'fixed';
    item.style.left = rect.left + 'px';
    item.style.top = rect.top + 'px';
    item.style.width = rect.width + 'px';
    item.style.height = rect.height + 'px';
    item.style.margin = '0';
    item.style.zIndex = '9999';
    item.style.pointerEvents = 'none';
    item.style.willChange = 'transform, left, top';
  }

  function clearInlineStyles(item) {
    RESET_STYLES.forEach(function (p) {
      item.style[p] = '';
    });
  }

  function clearFreeStyles(item) {
    FREE_KEEP_STYLES.forEach(function (p) {
      item.style[p] = '';
    });
  }

  function resetFree(elOrId) {
    var el;
    if (typeof elOrId === 'string') {
      el = document.getElementById(elOrId) ||
           document.querySelector('[data-dragfree-id="' + elOrId + '"]');
    } else if (elOrId instanceof Element) {
      el = elOrId;
    }
    if (!el || !isFree(el)) return;

    clearSavedPosition(el);

    if (el.parentNode === document.body && el._dragfreeOriginParent) {
      var origParent = el._dragfreeOriginParent;
      var origNext = el._dragfreeOriginNextSibling;
      if (origNext && origNext.parentNode === origParent) {
        origParent.insertBefore(el, origNext);
      } else if (origParent) {
        origParent.appendChild(el);
      }
      delete el._dragfreeOriginParent;
      delete el._dragfreeOriginNextSibling;
    }

    clearInlineStyles(el);
    el.classList.remove('dragging');
  }


  function onPointerDown(e) {
    if (drag || pending) return;
    if (e.button !== undefined && e.button !== 0) return;

    var item = e.target.closest ? e.target.closest(ITEM_SELECTOR) : null;
    if (!item) return;

    var area = findArea(item);
    if (!area && !isFree(item)) return;

    if (item.classList.contains('drag-disabled') ||
        item.getAttribute('aria-disabled') === 'true') return;

    var handleSel = item.getAttribute('data-handle') ||
                    item.getAttribute('handle') ||
                    (area ? area.getAttribute('data-handle') || area.getAttribute('handle') : null);

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
      rect: rect
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

  function suppressClick(item) {
    item.addEventListener('click', function (ce) {
      ce.preventDefault();
      ce.stopPropagation();
    }, { capture: true, once: true });
  }

  function beginDrag(p, e) {
    var item = p.item;
    var area = p.area;
    var rect = p.rect;
    var free = isFree(item);

    if (free) {
      if (!item._dragfreeOriginParent) {
        item._dragfreeOriginParent = item.parentNode;
        item._dragfreeOriginNextSibling = item.nextSibling;
      }

      document.body.appendChild(item);
      setItemFixed(item, rect);
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
        lastSwapTarget: null
      };

      suppressClick(item);

      item.dispatchEvent(new CustomEvent('dragengine:start', {
        bubbles: true,
        detail: { item: item, from: { area: null, index: -1 } }
      }));

      loop();
      return;
    }

    var placeholder = document.createElement('div');
    placeholder.className = 'drag-placeholder';
    placeholder.style.width = rect.width + 'px';
    placeholder.style.height = rect.height + 'px';
    area.insertBefore(placeholder, item);

    document.body.appendChild(item);
    setItemFixed(item, rect);
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
      free: false
    };

    suppressClick(item);

    area.dispatchEvent(new CustomEvent('dragengine:start', {
      bubbles: true,
      detail: { item: item, from: { area: area, index: drag.originIndex } }
    }));

    loop();
  }

  function loop() {
    if (!drag) return;
    drag.item.style.left = (drag.pointerX - drag.offsetX) + 'px';
    drag.item.style.top = (drag.pointerY - drag.offsetY) + 'px';
    if (!drag.free) updateHitTest();
    drag.rafId = requestAnimationFrame(loop);
  }

  function updateHitTest() {
    var el = document.elementFromPoint(drag.pointerX, drag.pointerY);
    if (!el) return;

    var area = el.closest ? el.closest(AREA_SELECTOR) : null;
    if (!area || !isCompatible(area)) return;

    var targetChild = el.closest
      ? el.closest(ITEM_SELECTOR + ', .drag-placeholder')
      : null;

    if (targetChild === drag.item) return;

    /*
    * Not currently over an item.
    * This is important for allowing another swap after
    * moving away from the previous target.
    */
    if (!targetChild) {
      drag.lastSwapTarget = null;

      if (area !== drag.placeholder.parentNode) {
        var animatedTarget = isAnimated(area);
        var animatedOrigin = isAnimated(drag.placeholder.parentNode);

        var rectsTarget = animatedTarget
          ? captureRects(area)
          : null;

        var rectsOrigin = animatedOrigin
          ? captureRects(drag.placeholder.parentNode)
          : null;

        area.appendChild(drag.placeholder);

        playFlip(rectsTarget);
        playFlip(rectsOrigin);
      }

      return;
    }

    if (targetChild === drag.placeholder) {
      drag.lastSwapTarget = null;
      return;
    }

    var mode = getMode(area);
    var animated2 = isAnimated(area);
    var crossArea = drag.placeholder.parentNode !== area;

    var rectsTarget =
      (animated2 || (crossArea && isAnimated(drag.placeholder.parentNode)))
        ? captureRects(area)
        : null;

    var rectsOrigin =
      (crossArea && isAnimated(drag.placeholder.parentNode))
        ? captureRects(drag.placeholder.parentNode)
        : null;

    /*
    * Only exchange the dragged item's placeholder
    * with the item currently underneath the pointer.
    *
    * No other items are shifted.
    */
    if (mode === 'swap') {
      if (drag.lastSwapTarget !== targetChild) {
        swapNodes(drag.placeholder, targetChild);
        drag.lastSwapTarget = targetChild;
      }

      playFlip(rectsTarget);
      playFlip(rectsOrigin);

      return;
    }

    var axis = getAxis(area);
    var r = targetChild.getBoundingClientRect();
    var before;

    if (axis === 'x') {
      before = drag.pointerX < r.left + r.width / 2;
    } else if (axis === 'grid') {
      var cy = r.top + r.height / 2;

      before =
        (Math.abs(drag.pointerY - cy) > r.height * 0.25)
          ? (drag.pointerY < cy)
          : (drag.pointerX < r.left + r.width / 2);
    } else {
      before = drag.pointerY < r.top + r.height / 2;
    }

    if (before) {
      area.insertBefore(drag.placeholder, targetChild);
    } else {
      area.insertBefore(drag.placeholder, targetChild.nextSibling);
    }

    playFlip(rectsTarget);
    playFlip(rectsOrigin);
  }

  function finishDrag() {
    cancelAnimationFrame(drag.rafId);
    var item = drag.item;

    if (drag.free) {
      clearFreeStyles(item);
      item.classList.remove('dragging');
      document.body.classList.remove('dragengine-active');
      savePosition(item);

      item.dispatchEvent(new CustomEvent('dragengine:end', {
        bubbles: true,
        detail: {
          item: item,
          from: { area: null, index: -1 },
          to: { area: null, index: -1 },
          changed: true
        }
      }));

      drag = null;
      return;
    }

    var placeholder = drag.placeholder;
    var originArea = drag.originArea;
    var originIndex = drag.originIndex;
    var finalArea = placeholder.parentNode || originArea;

    finalArea.insertBefore(item, placeholder);
    placeholder.remove();

    clearInlineStyles(item);
    item.classList.remove('dragging');
    document.body.classList.remove('dragengine-active');

    var finalIndex = indexOf(item, finalArea);
    var changed = finalArea !== originArea || finalIndex !== originIndex;

    var detail = {
      item: item,
      from: { area: originArea, index: originIndex },
      to: { area: finalArea, index: finalIndex },
      changed: changed
    };

    finalArea.dispatchEvent(new CustomEvent('dragengine:end', {
      bubbles: true,
      detail: detail
    }));

    if (changed) {
      finalArea.dispatchEvent(new CustomEvent('dragengine:sort', {
        bubbles: true,
        detail: detail
      }));
      sendHtmxUpdate(detail);
    }

    drag = null;
  }

  function cancel() {
    if (!drag) return;
    cancelAnimationFrame(drag.rafId);

    var item = drag.item;

    if (drag.free) {
      var parent = drag._dragfreeOriginParent;
      var next = drag._dragfreeOriginNextSibling;
      if (next && next.parentNode === parent) {
        parent.insertBefore(item, next);
      } else if (parent) {
        parent.appendChild(item);
      }
      clearInlineStyles(item);
      item.classList.remove('dragging');
      document.body.classList.remove('dragengine-active');
      drag = null;
      pending = null;
      return;
    }

    drag.originArea.insertBefore(drag.item, drag.placeholder);
    drag.placeholder.remove();
    clearInlineStyles(drag.item);
    drag.item.classList.remove('dragging');
    document.body.classList.remove('dragengine-active');
    drag = null;
    pending = null;
  }


  function sendHtmxUpdate(detail) {
    if (typeof global.htmx === 'undefined') return;

    var targetArea = detail.to.area;
    if (!targetArea) return;

    var method = null;
    var endpoint = null;

    if (targetArea.hasAttribute('hx-patch')) {
      method = 'PATCH';
      endpoint = targetArea.getAttribute('hx-patch');
    } else if (targetArea.hasAttribute('hx-post')) {
      method = 'POST';
      endpoint = targetArea.getAttribute('hx-post');
    } else if (targetArea.hasAttribute('hx-put')) {
      method = 'PUT';
      endpoint = targetArea.getAttribute('hx-put');
    } else if (targetArea.hasAttribute('hx-delete')) {
      method = 'DELETE';
      endpoint = targetArea.getAttribute('hx-delete');
    }

    if (!method || !endpoint) return;

    var item = detail.item;
    var fromArea = detail.from.area;

    var field = targetArea.getAttribute('field') ||
                targetArea.getAttribute('data-field') ||
                targetArea.getAttribute('drag-field') ||
                'field';

    var value = targetArea.getAttribute('value') ||
                targetArea.getAttribute('data-value') ||
                targetArea.getAttribute('drag-value') ||
                '';

    var fromField = fromArea
      ? (fromArea.getAttribute('field') ||
         fromArea.getAttribute('data-field') ||
         fromArea.getAttribute('drag-field') ||
         'field')
      : field;

    var fromValue = fromArea
      ? (fromArea.getAttribute('value') ||
         fromArea.getAttribute('data-value') ||
         fromArea.getAttribute('drag-value') ||
         '')
      : '';

    var payload = {};

    if (item.dataset.id) payload.id = item.dataset.id;
    else if (item.id) payload.id = item.id;

    payload[field] = value;
    payload.from_index = detail.from.index;
    payload.to_index = detail.to.index;

    if (fromArea) {
      payload.from_field = fromField;
      payload.from_value = fromValue;
    }

    var swap = targetArea.getAttribute('hx-swap') || 'none';

    global.htmx.ajax(method, endpoint, {
      target: targetArea,
      swap: swap,
      values: payload
    });
  }


  function onDblClick(e) {
    var item = e.target.closest
      ? e.target.closest('dragfree, .dragfree, .dragfree-save, .dragable.dragfree, .draggable.dragfree, .dragable.dragfree-save, .draggable.dragfree-save')
      : null;
    if (!item) return;
    e.preventDefault();
    resetFree(item);
  }

  // public API
  function init(root) {
    root = root || document;
    if (initializedRoots.has(root)) return;
    initializedRoots.add(root);

    root.addEventListener('pointerdown', onPointerDown);
    root.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') cancel();
    });
    root.addEventListener('dblclick', onDblClick);

    restoreDragFreePositions();
  }

  global.DragEngine = {
    init: init,
    cancel: cancel,
    resetFree: resetFree
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      init(document);
    });
  } else {
    init(document);
  }
})(window);