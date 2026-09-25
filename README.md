# Lombik

A practical Flask scaffold engine with a **hypermedia-first** approach. It
leans on Flask, Jinja2, HTMX, Tailwind CSS and SQLAlchemy to keep application
logic close to the UI — no heavy frontend framework unless you actually need
one.

Lombik generates a complete application and then gets out of your way. Models,
modules, relationships and full CRUD are created from the command line.

---

## Install

```bash
pip install lombik
```

## Create an app

```bash
lombik createapp myapp
cd myapp
pip install -r requirements.txt
```

Then:

```bash
lombik initdb      # create/apply migrations + DB triggers
lombik superuser   # create your first superuser
lombik run         # flask run --debug on localhost:5000
```

By default, local development uses **SQLite** when `DATABASE_URL` is empty.
Production uses **PostgreSQL** via the `DATABASE_URL` environment variable.

---

## Commands

| Command | What it does |
|---|---|
| `lombik createapp <name>` | Generate a new application |
| `lombik run` | Run the development server |
| `lombik initdb` | Initialize the database and migrations |
| `lombik superuser` | Create a superuser interactively |
| `lombik module <name>` | Generate a blueprint module |
| `lombik model <name>` | Generate a model and register it |
| `lombik crud <model>` | Generate a full CRUD blueprint |
| `lombik relate parent.field to child.field [type] [--lazy lazy]` | Create model relationships |
| `lombik db -m "message"` | Create a migration and upgrade |
| `lombik test` | Run the test suite |

### Example: full CRUD in three commands

```bash
lombik model tenant          # creates models/tenants.py + registers it
lombik db -m "add tenants"   # migrate + upgrade
lombik crud tenant           # generates blueprints/tenants/ + templates/tenants/
```

`lombik crud` maps column types to form fields automatically. Foreign keys
become `SelectField` dropdowns, booleans become checkboxes, and dates/numbers
use the right input types.

---

## Project structure

```text
myapp/
  app.py                  # app factory + module-level `app`
  db.py                   # SQLAlchemy + Migrate instances
  application/            # scaffold runtime (auth, forms, filters, crud, themes, ...)
  blueprints/
    auth/                 # login, register, password reset
    core/                 # home + example HTMX partials
    admin/                # owner onboarding + superuser admin panel
  models/                 # SQLAlchemy models
  templates/              # Jinja2 templates
  static/                 # css, js, icons
  tests/                  # pytest suite
  Dockerfile
  docker-compose.yml
  Procfile                # Railway
  railway.json
```

The generated runtime package is called **`application`**, so your app code
reads `from application...` and never collides with the `lombik` CLI package.

---

## Routes and services

Each blueprint keeps two concerns: **routes** handle HTTP, **services** do the
real work. Add a `forms.py` only when a module needs forms.

```text
blueprints/
  auth/
    __init__.py   # the Blueprint object
    routes.py     # page handlers + mutations
    forms.py      # login/register form definitions
  core/
    __init__.py
    routes.py
```

Route handlers stay thin:

```python
# blueprints/core/routes.py
from application.wrappers import login_required, roles_required

@core_bp.route("/members")
@login_required
def members():
    return render_template("core/members.html")

@core_bp.route("/admin")
@login_required
@roles_required("admin", "superuser")
def admin():
    return render_template("core/admin.html")
```

Business logic lives in a service so it can be reused and tested without Flask:

```python
# application/users.py (or a blueprint's services.py)
from application.extensions import cache
from models import User

@cache.memoize(timeout=30)
def get_user_by_email(email):
    return User.query.filter_by(email=email.strip().lower()).first()
```

---

## HTMX by default

Pages are server-rendered; interactions return fragments. A typical pattern:

```html
<section hx-get="{{ url_for('core_bp.quickstart') }}"
         hx-trigger="load"
         hx-swap="innerHTML">
    Loading…
</section>
```

The built-in `htmx_response()` helper sets `HX-Trigger` and `HX-Redirect`
headers. The CSRF token is injected into every HTMX request automatically by
`static/js/csrf.js`.

---

## Admin panel

On a fresh database the app redirects to `/admin`, a graphical owner-onboarding
page. It creates the first **superuser** account and signs you in. Prefer the
terminal? The equivalent command still exists:

```bash
lombik superuser
```

Once an owner exists, `/admin` becomes a live, HTMX-powered admin panel for
superusers, split into four pages:

- **Errors** (the main page) — stats, day-by-day and hour-by-hour error charts
  (using the bundled chart elements), and the full error log newest first,
  auto-refreshing every few seconds. Each record captures the exception type,
  message, traceback, function, request method/path, IP, user and optional
  tenant id.
- **Schema** — collapsible tables with their fields, types and constraints.
- **Appearance** — activate a built-in theme or create a custom one with color
  pickers, name it, and save it to the filesystem.
- **Guide** — a markdown handbook covering the structure, ideology and the
  recommended build flows.

---

## Themes

Themes live in `application/themes.py` and are rendered as CSS custom
properties. The active theme and any custom themes are stored in
`instance/theme.json` — a local filesystem file, not the database. Built-in
themes ship with the scaffold; custom themes can be created, activated and
deleted from the admin panel.

---

## Design system

Generated apps ship with a small semantic token set driven by CSS variables in
`static/css/global.css`. Dark mode is automatic (`.dark` swaps the variables).

| Token | Meaning |
|---|---|
| `canvas` | Page background |
| `surface` | Panel / card background |
| `raised` | Inputs and elevated surfaces |
| `line` | Hairline borders |
| `ink` | Primary text |
| `ink-muted` | Secondary text |
| `brand` | Accent / primary action |
| `success` / `warning` / `danger` | Semantic states |

Use `bg-canvas`, `bg-surface`, `border-line`, `text-ink`, `text-ink-muted`,
`bg-brand`, `bg-ink text-canvas`, etc. Raw hex values should not appear in
templates — reuse the tokens so light/dark always works.

---

## UI engines

Included, dependency-free, in `static/js/`:

- **Drag** — reorderable lists, kanban slot swapping, cross-list moves and
  free-floating elements. See `static/js/drag.js` for the full API.
- **Dropdowns** — the custom `<dropdown>` element with viewport-aware
  positioning.
- **Modals** — `openModal('id')` / `closeModal('id')`.
- **Flash** — auto-dismissing toasts with `Flash.ok()`, `Flash.error()`, etc.
- **Charts** — custom `<bar-chart>`, `<line-chart>`, `<donut-chart>` and
  `<bubble-chart>` elements in `static/js/chart.js`.

---

## Deploying (Docker / Railway)

### Docker

```bash
docker compose up --build
```

This starts Postgres and the web app. The web service sets `DATABASE_URL`
automatically.

### Railway

The repo includes a `Dockerfile`, `Procfile` and `railway.json`. Railway uses
the Dockerfile by default and runs the `release` command (`flask db upgrade`)
on each deploy. Add a Postgres service and set `DATABASE_URL`, `SECRET_KEY` and
`CRKEY` as service variables.

---

## Testing

```bash
lombik test               # pytest
lombik test_report        # pytest + coverage
lombik test_report_html   # pytest + HTML coverage report
```

The default test suite covers string helpers, date utilities, form validation,
security helpers, responses, and the built-in validators.

---

## Philosophy

- Keep logic close to the UI with server-rendered HTML and HTMX.
- Keep `routes.py` thin and put real work in services.
- Generate boilerplate from the command line, then edit real files.
- Keep the graphical surface minimal: a single owner admin panel.
- Ship sensible, secure defaults: hashed passwords, CSRF, sessions, rate
  limiting and structured `Result` responses.

MIT licensed — contributions, fixes, ideas and forks are welcome.
