# Lombik  
#### A scaffold engine for Flask — because starting from scratch is overrated.

Lombik exists to remove the boring parts of starting a Flask project. It gives you a ready-to-use structure so you can focus on building, not wiring things together.

It leans heavily into a **hypermedia-first approach**, using Jinja2, template filters, HTMX, and Tailwind to keep logic close to the UI and reduce frontend complexity.

---

## What you get out of the box

- Flask project structure pre-wired and ready to run  
- Simple authentication system  
- MySQL integration  
- Tailwind + HTMX setup  
- Error handling  
- CSRF protection + session expiry  
- Pre-imported common utilities  
- Base templates for desktop and mobile  

---

## Template filters (the fun part)

Lombik ships with a set of Jinja filters designed to keep your templates clean and expressive.

### Dates & time handling

Instead of formatting timestamps in Python, you do it directly in the template:

{{ created_at | localtime }}        → 2026-05-19 05:15  
{{ created_at | onlydate }}         → 2026-05-19  
{{ created_at | onlytime }}         → 05:15  
{{ created_at | shortdatetime }}    → May 19 05:15  

Everything defaults to `localtime`, meaning UTC from the backend is automatically shown in the user’s timezone.

Lombik expects the user’s timezone to be available via `g`.

---

### String helpers

Make frontend display logic less painful:

{{ g.user.full_name | proper }}

john_doe → John Doe

{{ g.user.first_name | possessive }}

john → john's  
lucas → lucas'  

You can chain them:

{{ g.user.full_name | proper | possessive }}

john_doe → John Doe's  

---

## Installation

pip install lombik

---

## Create a project

1. `lombik createapp myapp`
2. `cd myapp`
3. `flask run --debug`

This generates a full application structure so you can start immediately.
To log in, you need a superuser account so you can exit the app and follow the next steps.

---

## Add modules

1. `lombik module new_module`

Creates a new module in blueprints that is registered automatically in app.py with the default file structure and a few core imports.
The following names are prohibited by default: "core", "auth", "settings".

---

## Database setup

Lombik uses MySQL by default.

1. Update your `.env` with your database credentials (at least dev for development)
2. Initialize the database:

`flask initdb`

3. Create your admin user:

`flask superuser`

After that, you can log in and start building.

Note: the auth system is intentionally simple. It’s meant for development scaffolding, not production security.

---

## Models

When adding new models, don’t forget to register them:

`models/__init__.py`

Otherwise they won’t be picked up.

