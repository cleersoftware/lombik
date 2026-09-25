# Lombik — Agent Skills

Lombik is a Flask scaffold engine with a hypermedia-first stack: Flask, Jinja2,
HTMX, Tailwind CSS and SQLAlchemy. It generates a complete application and then
stays out of your way — most of the "framework" work (models, modules,
relationships, CRUD) happens through the command line.

Use this file as the source of truth when working on Lombik itself, or when
helping a user build an app with it.

---

## What Lombik is

- A **scaffold engine**, not a runtime framework. The `lombik` CLI copies
  `lombik/templates/createapp/` into a new project and fills in placeholders.
- A **command-based generator**. There is no admin UI; everything is done with
  `lombik <command>` or `flask <command>`.
- An **HTMX-first** application template. Pages are server-rendered Jinja2
  templates that swap fragments via `hx-*` attributes — no SPA.

---

## Repository layout

```text
lombik/
  cli.py                         # installed CLI (createapp, module, model, crud, relate, ...)
  templates/
    createapp/                   # the generated Flask app scaffold (copied on createapp)
      app.py
      db.py
      requirements.txt
      Dockerfile
      docker-compose.yml
      Procfile                   # Railway deploy
      railway.json
      application/               # scaffold runtime (auth, forms, filters, crud, themes, ...)
      blueprints/
        auth/
        core/
        admin/                    # owner onboarding + superuser admin panel
      models/
      templates/                 # app templates (auth, base, core, errors, admin)
      static/
        css/global.css           # design tokens + engine styles
        js/                      # drag, dropdown, theme, modal, flash, csrf, chart
      tests/
    module/                      # `lombik module` blueprint template
    module_templates/            # `lombik module` template files
    model_templates/             # `lombik model` model template
pyproject.toml
README.md
```

Key concept: `lombik/templates/createapp/` is what gets copied when a user runs
`lombik createapp`. Changes to the scaffold only affect **new** generated apps.

The generated app's runtime package is called **`application`** (not `lombik`),
so generated apps stay generic and don't collide with the CLI package.

---

## CLI commands

| Command | Purpose |
|---|---|
| `lombik createapp <name>` | Generate a new Flask app |
| `lombik run` | Run `flask run --debug` |
| `lombik initdb` | Initialize DB + migrations + triggers |
| `lombik superuser` | Interactive superuser creation |
| `lombik module <name>` | Generate a blueprint module |
| `lombik model <name>` | Generate a model and register it |
| `lombik crud <model>` | Generate full CRUD for a model (delegates to `flask crud`) |
| `lombik relate parent.field to child.field [type] [--lazy lazy]` | Create relationships |
| `lombik db -m "msg"` | Migrate + upgrade |
| `lombik test` | Run pytest |

The generated app also registers its own `flask` commands: `initdb`,
`superuser`, `triggers`, `crud`.

---

## Design system

Generated apps use a small set of **semantic tokens**, driven by CSS variables
in `static/css/global.css`. Dark mode is automatic: add `.dark` to `<html>` and
the variables swap. Tailwind consumes the tokens in `base/base.html`:

| Token | Meaning |
|---|---|
| `canvas` | Page background |
| `surface` | Panel / card background |
| `raised` | Inputs and elevated surfaces |
| `line` | Hairline borders |
| `line-strong` | Emphasised borders |
| `ink` | Primary text |
| `ink-muted` | Secondary text |
| `brand` | Accent / primary action |
| `brand-ink` | Text on top of the accent |
| `success` / `warning` / `danger` | Semantic states |

Example classes: `bg-canvas`, `bg-surface`, `border-line`, `text-ink`,
`text-ink-muted`, `bg-brand`, `text-brand-ink`, `bg-ink text-canvas`.

The visual style is the proov look: a centered, max-width app shell with a
sticky header, warm neutral canvas, and hairline borders. Auth pages use a
split-card layout (`templates/auth/base.html`).

### Design principles

- **Hypermedia first.** A page is HTML. Interaction is a request that returns a
  fragment. Prefer `hx-get`/`hx-post` + `hx-target` over writing JS.
- **Routes + services.** Keep `routes.py` thin (HTTP in/out); put business logic
  in `application/<domain>.py` or a blueprint's `services.py`. Add `forms.py`
  only when a module needs forms.
- **Command line over GUI.** Generate structure with the CLI, then edit files.
  The only graphical surface is the owner admin panel (first-run setup,
  live error log, schema and appearance).
- **Semantic tokens, never raw hex.** Reuse `canvas`, `surface`, `ink`, `brand`,
  etc. so light/dark works automatically.

### Themes

Themes are defined in `application/themes.py` and rendered as CSS custom
properties. The active theme is stored in `instance/theme.json` (filesystem,
not the database) and can be changed by superusers on the admin page.

---

## Client-side engines

All engines live in `static/js/` and are dependency-free.

- `drag.js` — `DragEngine` for reorderable lists, kanban/slot swapping,
  cross-list moves (`data-group`), and free-floating `.dragfree` elements.
  Drops are sent to the server via the `dragengine:sort` HTMX bridge.
- `dropdown.js` — `DropdownEngine` for the custom `<dropdown>` element with
  viewport edge avoidance.
- `theme.js` — light/dark toggle backed by `localStorage`.
- `modal.js` — `openModal` / `closeModal` helpers.
- `flash.js` — auto-dismisses flash toasts.
- `csrf.js` — injects the CSRF token into every HTMX request.

The backend helper for drag persistence is `application/drag.py`:
`apply_drag_change(instance, field, value)`.

---

## Local development loop

```bash
# 1. Create a fresh generated app for testing
python -m lombik.cli createapp /tmp/lombik_test_app
cd /tmp/lombik_test_app

# 2. Initialize the database (SQLite fallback by default)
python -m flask initdb

# 3. Create a superuser
printf 'admin@example.com\nadmin\nczechia\nPassword123!\nPassword123!\n' | python -m flask superuser

# 4. Create a model and generate CRUD
python -m lombik.cli model tenant
# add columns to models/tenants.py if needed
python -m lombik.cli crud tenant

# 5. Migrate
python -m flask db migrate -m "add tenants"
python -m flask db upgrade

# 6. Run tests
python -m pytest -q
```

Use the generated app as the integration test bed.

---

## Database / deploy

- Local dev defaults to **SQLite** when `DATABASE_URL` is empty.
- Production uses **PostgreSQL** via the `DATABASE_URL` env var.
- `docker-compose.yml` provides Postgres + the web app.
- `Dockerfile` runs the app with gunicorn.
- `Procfile` / `railway.json` are ready for Railway (the `release` phase runs
  `flask db upgrade`).

---

## Testing checklist before a PR

- [ ] `python -m compileall -q lombik/templates/createapp`
- [ ] Create a fresh app with `lombik createapp`
- [ ] `flask initdb`, `flask superuser`, `flask db upgrade`
- [ ] `lombik model <name>` and `lombik crud <name>`
- [ ] Exercise `lombik relate ...`
- [ ] Run `pytest` in the generated app
- [ ] Remove `__pycache__` from `lombik/templates` before committing

---

## Creating a PR

1. Branch from `main`:
   ```bash
   git checkout -b feature/my-change
   ```
2. Make focused changes. Prefer small, reviewable commits.
3. Test with the checklist above.
4. Clean template pycache:
   ```bash
   find lombik/templates -type d -name __pycache__ -exec rm -rf {} +
   ```
5. Commit and push:
   ```bash
   git add -A
   git commit -m "feat: describe the change"
   git push origin feature/my-change
   ```
6. PR description should include what changed, why, how to test it, and any
   screenshots if the UI changed.
