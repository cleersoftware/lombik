Drag‑and‑Drop in Lombik – Practical Overview
=============================================

A dependency‑free drag engine + HTMX bridge + tiny backend helper.
Reorder lists, move items between columns, or float any element freely.

1. List / Column Reordering (Kanban, Categories, etc.)
-------------------------------------------------------

HTML structure::

    <div class="flex flex-col ...">
      <div>Land Animals</div>
      <div class="dragarea flex-1"
           data-group="board"
           data-field="category"
           data-value="land"
           data-endpoint="/update-category">
        <div class="dragable" data-id="1">Meerkat</div>
        <div class="dragable" data-id="2">Lion</div>
      </div>
    </div>

Required attributes:
- ``.dragarea.flex-1`` inside a flex parent.
- ``.dragable`` items with ``data-id`` (primary key).
- ``data-field`` / ``data-value`` define what changes on drop.
- ``data-group`` (optional) allows cross‑column moves.
- ``data-endpoint`` (optional) URL to POST; defaults to ``/drag-update``.

JavaScript (include once):
1. DragEngine (``drag.js``)
2. HTMX
3. Bridge script (listens to ``dragengine:sort`` and calls ``htmx.ajax``).

CSRF meta tag in ``<head>``::

    <meta name="csrf-token" content="{{ csrf_token() }}">

Backend – one generic route using ``lombik.drag.apply_drag_change``::

    from lombik.drag import apply_drag_change
    from models import Animal

    @admin_bp.post('/update-category')
    def update_animal_category():
        item_id = request.form.get('id')
        field   = request.form.get('field')
        value   = request.form.get('value')
        animal = Animal.query.filter_by(id=item_id).first()
        if not animal:
            return '', 404
        res = apply_drag_change(animal, field, value)
        if not res.success:
            return '', 400
        return '', 200

The helper checks ``hasattr`` and calls ``setattr``, then commits.
Works for any model (tasks, assets, …).

2. Free‑floating Elements (.dragfree / .dragfree-save)
------------------------------------------------------

Classes on any ``.dragable`` (no ``.dragarea`` needed):

- ``.dragfree``         Freely draggable; resets on page reload.
- ``.dragfree-save``    Saves position to localStorage (requires ``data-dragfree-id``).

Example (persistent logout button)::

    <div class="dragable dragfree dragfree-save"
         data-dragfree-id="logout-btn"
         style="position:fixed; bottom:20px; right:20px; cursor:grab;"
         hx-post="/auth/logout"
         hx-vals='{"csrf_token": "{{ csrf_token() }}"}'>
      Log out
    </div>

- Double‑click the element to reset it to its original position
  (or call ``DragEngine.resetFree('logout-btn')``).
- No backend involved – all client‑side.