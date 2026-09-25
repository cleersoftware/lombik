# Building with Lombik

Lombik is a hypermedia-first Flask scaffold. It generates a complete
application, then stays out of your way while you build with the command line.

## The idea in one line

Render HTML on the server, swap fragments with HTMX, and generate the boring
parts from the terminal. No SPA, no heavy frontend framework.

## How the code is organised

Every feature lives in a **blueprint**:

```text
blueprints/
  auth/          # login, register, password reset
  core/          # home page + example HTMX partials
  admin/         # owner onboarding + admin panel
  <module>/      # your own features
```

Inside a blueprint:

| File | Purpose |
|---|---|
| `__init__.py` | The Blueprint object |
| `routes.py` | HTTP handlers — pages and mutations, kept thin |
| `services.py` | Business logic (reusable, testable) |
| `forms.py` | Optional form definitions |

Shared app-wide helpers live in `application/` (`auth.py`, `users.py`,
`responses.py`, `filters.py`, …).

## The mental model

- **Routes handle HTTP.** Parse the request, call a service, return a response.
- **Services do the work.** Query the database, validate, mutate, return a
  `Result`.
- **Forms describe input.** Use `InputField`, `SelectField`, `CheckboxField`
  and `TextareaField`.

## A typical build flow

Start from the data model and work outwards:

```bash
# 1. Create a model
lombik model tenant

# 2. Add columns to models/tenants.py, then migrate
lombik db -m "add tenants"

# 3. Generate a full CRUD module
lombik crud tenant

# 4. Wire up relationships
lombik relate tenant.id to user.tenant_id one-to-many

# 5. Add a custom module when CRUD isn't enough
lombik module billing
```

Now edit the generated `routes.py` and `services.py` to match your product.

## Adding a page

1. Add a handler in `blueprints/<module>/routes.py`.
2. Return `render_template("<module>/page.html")`.
3. Create the template and `{% extends 'base/base.html' %}`.

## Adding an interaction

Use HTMX attributes in the template and return a fragment or an
`htmx_response()`:

```python
from application.responses import htmx_response

@billing_bp.post("/invoices/<invoice_id>/pay")
def pay(invoice_id):
    result = services.pay_invoice(invoice_id)
    if not result.success:
        return htmx_response(html="<p class='text-danger'>Failed</p>", status=400)
    return htmx_response(html="<p>Paid ✓</p>", trigger="invoicePaid")
```

## Styling

Use semantic tokens, never raw hex:

`bg-canvas` · `bg-surface` · `bg-raised` · `border-line` · `text-ink` ·
`text-ink-muted` · `bg-brand` · `text-danger` · `text-success`.

Dark mode is automatic — `.dark` swaps the CSS variables.

## Admin panel

`/admin` is owner-only. It shows live error logs, stats, the database schema,
and theme management. Errors are stored in the `errors` table; keep an eye on
them during development and in production.

## Deploying

- Local: SQLite fallback, `lombik run`.
- Production: set `DATABASE_URL` to Postgres and run the bundled Dockerfile or
  deploy straight to Railway (`Procfile` + `railway.json` included).
