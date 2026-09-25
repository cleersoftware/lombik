/*!
 * DragEngine
 * Dependency-free drag & drop / sortable engine built on Pointer Events.
 *
 * MARKUP
 *   <div class="dragarea" data-group="board" data-field="status" data-value="open" data-endpoint="/update">
 *     <div class="dragable" data-id="1">...</div>
 *     <div class="dragable" data-id="2">...</div>
 *   </div>
 *
 * MODIFIERS ON .dragarea
 *   .showgap   FLIP-animate siblings out of the way and show a placeholder.
 *   .snap      Swap into grid/kanban slots instead of reflowing everything.
 *   .ordered   Alias for .snap.
 *
 * MODIFIERS ON .dragable
 *   .dragfree        Free-floating element (no list, no placeholder).
 *   .dragfree-save   Persist free position to localStorage.
 *                    Requires a unique data-dragfree-id.
 *
 * ATTRIBUTES
 *   data-group          Allow dragging between areas sharing the same group.
 *   data-handle=".sel"  Restrict drag-start to a handle inside the item.
 *   data-dragfree-id    Unique id used to save/restore a free element.
 *
 * EVENTS (dispatched on the relevant .dragarea, all bubbling)
 *   dragengine:start  { item, from }
 *   dragengine:end    { item, from, to, changed }
 *   dragengine:sort   fired only when the order actually changed
 *
 * PUBLIC
 *   DragEngine.init(root)
 *   DragEngine.cancel()
 *   DragEngine.resetFree(elementOrId)
 */
(function (global) {
  'use strict';

  var THRESHOLD = 4;
  var FLIP_MS = 220;
  var FREE_INLINE = ['position', 'left', 'top', 'width', 'height', 'margin', 'zIndex', 'pointerEvents', 'willChange'];

  var initializedRoots = new WeakSet();
  var pending = null;
  var drag = null;

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
    if (cs.display.indexOf('grid') !== -1) {
      var cols = cs.gridTemplateColumns.split(' ').filter(Boolean).length;
      return cols > 1 ? 'grid' : 'y';
    }
    if (cs.display.indexOf('flex') !== -1) {
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

  function storageKey(id) { return 'dragfree-pos-' + id; }

  function savePosition(item) {
    if (!item.classList.contains('dragfree-save')) return;
    var id = item.getAttribute('data-dragfree-id');
    if (!id) return;
    try {
      localStorage.setItem(storageKey(id), JSON.stringify({ left: item.style.left, top: item.style.top }));
    } catch (e) { /* ignore */ }
  }

  function clearSavedPosition(item) {
    if (!item.classList.contains('dragfree-save')) return;
    var id = item.getAttribute('data-dragfree-id');
    if (!id) return;
    try { localStorage.removeItem(storageKey(id)); } catch (e) { /* ignore */ }
  }

  function restoreFreePositions() {
    var items = document.querySelectorAll('.dragable.dragfree-save[data-dragfree-id]');
    for (var i = 0; i < items.length; i++) {
      var el = items[i];
      try {
        var raw = localStorage.getItem(storageKey(el.getAttribute('data-dragfree-id')));
        if (raw) {
          var pos = JSON.parse(raw);
          if (pos && typeof pos.left === 'string' && typeof pos.top === 'string') {
            el.style.position = 'fixed';
            el.style.left = pos.left;
            el.style.top = pos.top;
          }
        }
      } catch (e) { /* ignore */ }
    }
  }

  function resetFree(elOrId) {
    var el = typeof elOrId === 'string'
      ? document.querySelector('.dragfree-save[data-dragfree-id="' + elOrId + '"]')
      : elOrId;
    if (!el || !el.classList.contains('dragfree-save')) return;

    clearSavedPosition(el);

    if (el.parentNode === document.body && el._dragfreeOriginParent) {
      var parent = el._dragfreeOriginParent;
      var next = el._dragfreeOriginNext;
      if (next && next.parentNode === parent) parent.insertBefore(el, next);
      else if (parent) parent.appendChild(el);
    }

    delete el._dragfreeOriginParent;
    delete el._dragfreeOriginNext;
    FREE_INLINE.forEach(function (p) { el.style[p] = ''; });
    el.classList.remove('dragging');
  }

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
      rect: rect
    };

    document.addEventListener('pointermove', onPointerMove);
    document.addEventListener('pointerup', onPointerUp);
    document.addEventListener('pointercancel', onPointerUp);
  }

  function onPointerMove(e) {
    if (!drag) {
      if (!pending || e.pointerId !== pending.pointerId) return;
      if (Math.hypot(e.clientX - pending.startX, e.clientY - pending.startY) < THRESHOLD) return;
      beginDrag(pending);
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
    if (!drag) { pending = null; return; }
    if (e.pointerId !== drag.pointerId) return;
    finishDrag();
  }

  function beginDrag(p) {
    var item = p.item;
    var area = p.area;
    var rect = p.rect;
    var isFree = item.classList.contains('dragfree');

    if (isFree) {
      item._dragfreeOriginParent = item.parentNode;
      item._dragfreeOriginNext = item.nextSibling;

      drag = {
        pointerId: p.pointerId, item: item, placeholder: null,
        originArea: null, originIndex: -1,
        offsetX: p.offsetX, offsetY: p.offsetY,
        pointerX: p.pointerX, pointerY: p.pointerY, rafId: null,
        free: true, freeOriginParent: item._dragfreeOriginParent, freeOriginNextSibling: item._dragfreeOriginNext
      };

      document.body.appendChild(item);
      Object.assign(item.style, {
        position: 'fixed', left: rect.left + 'px', top: rect.top + 'px',
        width: rect.width + 'px', height: rect.height + 'px',
        margin: '0', zIndex: '9999', pointerEvents: 'none', willChange: 'transform, left, top'
      });
      item.classList.add('dragging');
      document.body.classList.add('dragengine-active');
      suppressClick(item);
      document.body.dispatchEvent(new CustomEvent('dragengine:start', {
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
    Object.assign(item.style, {
      position: 'fixed', left: rect.left + 'px', top: rect.top + 'px',
      width: rect.width + 'px', height: rect.height + 'px',
      margin: '0', zIndex: '9999', pointerEvents: 'none', willChange: 'transform, left, top'
    });
    item.classList.add('dragging');
    document.body.classList.add('dragengine-active');

    drag = {
      pointerId: p.pointerId, item: item, placeholder: placeholder,
      originArea: area, originIndex: indexOf(placeholder, area),
      offsetX: p.offsetX, offsetY: p.offsetY,
      pointerX: p.pointerX, pointerY: p.pointerY, rafId: null, free: false
    };

    suppressClick(item);
    area.dispatchEvent(new CustomEvent('dragengine:start', {
      bubbles: true,
      detail: { item: item, from: { area: area, index: drag.originIndex } }
    }));
    loop();
  }

  function suppressClick(item) {
    item.addEventListener('click', function (ce) {
      ce.preventDefault();
      ce.stopPropagation();
    }, { capture: true, once: true });
  }

  function loop() {
    if (!drag) return;
    drag.item.style.left = drag.pointerX - drag.offsetX + 'px';
    drag.item.style.top = drag.pointerY - drag.offsetY + 'px';
    if (!drag.free) updateHitTest();
    drag.rafId = requestAnimationFrame(loop);
  }

  function updateHitTest() {
    var el = document.elementFromPoint(drag.pointerX, drag.pointerY);
    if (!el) return;

    var area = el.closest('.dragarea');
    if (!area || !isCompatible(area)) return;

    var target = el.closest('.dragable, .drag-placeholder');
    if (target === drag.item) return;

    if (!target) {
      if (area !== drag.placeholder.parentNode) {
        var rectsHere = isAnimated(area) ? captureRects(area) : null;
        var rectsOrigin = isAnimated(drag.placeholder.parentNode) ? captureRects(drag.placeholder.parentNode) : null;
        area.appendChild(drag.placeholder);
        playFlip(rectsHere);
        playFlip(rectsOrigin);
      }
      return;
    }

    if (target === drag.placeholder) return;

    var mode = getMode(area);
    var crossArea = drag.placeholder.parentNode !== area;
    var rectsTarget = (isAnimated(area) || (crossArea && isAnimated(drag.placeholder.parentNode))) ? captureRects(area) : null;
    var rectsOriginArea = crossArea && isAnimated(drag.placeholder.parentNode) ? captureRects(drag.placeholder.parentNode) : null;

    if (mode === 'swap') {
      swapNodes(drag.placeholder, target);
    } else {
      var axis = getAxis(area);
      var r = target.getBoundingClientRect();
      var before;
      if (axis === 'x') before = drag.pointerX < r.left + r.width / 2;
      else if (axis === 'grid') {
        var cy = r.top + r.height / 2;
        before = Math.abs(drag.pointerY - cy) > r.height * 0.25
          ? drag.pointerY < cy
          : drag.pointerX < r.left + r.width / 2;
      } else before = drag.pointerY < r.top + r.height / 2;

      if (before) area.insertBefore(drag.placeholder, target);
      else area.insertBefore(drag.placeholder, target.nextSibling);
    }

    playFlip(rectsTarget);
    playFlip(rectsOriginArea);
  }

  function finishDrag() {
    cancelAnimationFrame(drag.rafId);
    var item = drag.item;

    if (drag.free) {
      FREE_INLINE.forEach(function (p) { item.style[p] = ''; });
      item.classList.remove('dragging');
      document.body.classList.remove('dragengine-active');
      savePosition(item);
      document.body.dispatchEvent(new CustomEvent('dragengine:end', {
        bubbles: true,
        detail: { item: item, from: { area: null, index: -1 }, to: { area: null, index: -1 }, changed: true }
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
    FREE_INLINE.forEach(function (p) { item.style[p] = ''; });
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
      if (next && next.parentNode === parent) parent.insertBefore(item, next);
      else parent.appendChild(item);
    } else {
      drag.originArea.insertBefore(item, drag.placeholder);
      drag.placeholder.remove();
    }

    FREE_INLINE.forEach(function (p) { item.style[p] = ''; });
    item.classList.remove('dragging');
    document.body.classList.remove('dragengine-active');
    drag = null;
    pending = null;
  }

  function onDblClick(e) {
    var item = e.target.closest('.dragable.dragfree-save');
    if (!item) return;
    e.preventDefault();
    resetFree(item);
  }

  function init(root) {
    root = root || document;
    if (initializedRoots.has(root)) return;
    initializedRoots.add(root);
    root.addEventListener('pointerdown', onPointerDown);
    root.addEventListener('keydown', function (e) { if (e.key === 'Escape') cancel(); });
    root.addEventListener('dblclick', onDblClick);
    restoreFreePositions();
  }

  global.DragEngine = { init: init, cancel: cancel, resetFree: resetFree };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { init(document); });
  } else {
    init(document);
  }
})(window);

/* HTMX bridge: persist a drop back to the server. */
document.body.addEventListener('dragengine:sort', function (evt) {
  var detail = evt.detail;
  if (!detail.changed) return;

  var area = detail.to.area;
  var id = detail.item.dataset.id;
  var field = area.dataset.field;
  var value = area.dataset.value;
  if (!id || !field || !value) return;

  var endpoint = area.dataset.endpoint || '/drag-update';
  var meta = document.querySelector('meta[name="csrf-token"]');
  var payload = {
    id: id,
    field: field,
    value: value,
    from_index: detail.from.index,
    to_index: detail.to.index,
    csrf_token: meta ? meta.content : ''
  };

  htmx.ajax('POST', endpoint, { target: area, swap: 'none', values: payload });
});
