# Lombik — Agent Skills

Lombik is a Flask scaffold engine with a hypermedia-first stack (Flask, Jinja2,
HTMX, Tailwind, SQLAlchemy). It also ships **Lombik Studio**, a browser-based
model/data/CRUD workspace for superusers.

Use this file as the source of truth when working on Lombik itself or when
helping a user build an app with it.

---

## Repository layout

```text
lombik/
  cli.py                        # installed CLI (createapp, module, model, crud, run, ...)
  templates/
    createapp/                  # the generated Flask app scaffold
      app.py
      blueprints/
        auth/
        core/
        studio/                 # Studio routes + JSON API
      lombik/                   # scaffold runtime (auth, forms, studio, crud, history, ...)
      models/
      templates/                # app templates (auth, core, studio, errors)
      static/
    module/                     # `lombik module` blueprint template
    module_templates/           # `lombik module` template files
    model_templates/            # `lombik model` model template
pyproject.toml
README.md
```

Key concept: `lombik/templates/createapp/` is what gets copied when a user runs
`lombik createapp`. Changes to the scaffold only affect **new** generated apps.

---

## Local development loop

```bash
# 1. Create a fresh generated app for testing
python -m lombik.cli createapp /tmp/lombik_test_app
cd /tmp/lombik_test_app

# 2. Initialize the database
python -m flask initdb

# 3. Create a superuser
printf 'admin@example.com\nadmin\nczechia\nPassword123!\nPassword123!\n' | python -m flask superuser

# 4. Create a model, add columns, generate CRUD
python -m lombik.cli model tenant
# edit models/tenants.py to add columns as needed
python -m lombik.cli crud tenant

# 5. Migrate
python -m flask db migrate -m "add tenants"
python -m flask db upgrade

# 6. Run tests
python -m pytest -q
```

Use the generated app as the integration test bed. The Studio UI lives there,
not in the installed CLI package.

---

## CLI commands

| Command | Purpose |
|---|---|
| `lombik createapp <name>` | Generate a new Flask app |
| `lombik run` | Run `flask run --debug` |
| `lombik initdb` | Initialize DB + migrations |
| `lombik superuser` | Interactive superuser creation |
| `lombik module <name>` | Generate a blueprint module |
| `lombik model <name>` | Generate a model and register it |
| `lombik crud <model>` | Generate full CRUD for a model (delegates to `flask crud`) |
| `lombik relate parent.field to child.field [type] [--lazy lazy]` | Create relationships |
| `lombik db -m "msg"` | Migrate + upgrade |
| `lombik test` | Run pytest |

---

## Studio

Studio is reachable at `/studio` and is superuser-only.

- **Canvas** — visual model overview with an interactive relationship graph.
  - Drag a model node onto another to prefill the relationship form.
  - Click an edge to view/remove relationship lines.
  - Double-click a node to open the model detail.
  - `+ Column` adds a column inline; `×` removes a column.
  - `Generate CRUD` generates a CRUD blueprint and restarts the dev server.
- **Models** — model detail, columns, relationships.
- **Data** — browse/edit live rows.
- **SQL** — read/write SQL console.
- **Migrations** — run migrations from the browser.
- **Routes** — list registered routes.

Studio file changes are recorded in `studio_history.json` (gitignored) and can be
undone/redone from the sidebar.

---

## Important Studio APIs

- `POST /studio/api/models` — create model
- `POST /studio/api/models/<module>/columns` — add column
- `DELETE /studio/api/models/<module>/columns/<name>` — remove column
- `POST /studio/api/models/<module>/crud/preview` — preview CRUD files
- `POST /studio/api/models/<module>/crud` — generate CRUD
- `POST /studio/api/history/undo` / `redo` — undo/redo file edits
- `POST /studio/api/restart` — trigger Werkzeug reloader (debug mode only)

---

## Testing checklist before a PR

- [ ] `python -m py_compile lombik/cli.py`
- [ ] `python -m compileall -q lombik/templates/createapp`
- [ ] Create a fresh app with `lombik createapp`
- [ ] `flask initdb`, `flask superuser`, `flask db upgrade`
- [ ] Exercise the changed Studio/CLI flow
- [ ] Run `pytest` in the generated app
- [ ] Remove `__pycache__` from `lombik/templates` before committing

---

## Creating a PR

1. Create a branch from `main`:
   ```bash
   git checkout -b feature/my-change
   ```
2. Make focused changes. Prefer small, reviewable commits.
3. Test with the checklist above.
4. Clean template pycache:
   ```bash
   find lombik/templates -type d -name __pycache__ -exec rm -rf {} +
   ```
5. Commit:
   ```bash
   git add -A
   git commit -m "feat: describe the change"
   ```
6. Push and open a PR:
   ```bash
   git push origin feature/my-change
   ```
7. PR description should include:
   - what changed and why
   - how to test it
   - screenshots/GIFs if UI changed
   - any caveats (e.g., dev-server restart required)
