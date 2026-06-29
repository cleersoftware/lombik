# Core module

Lombik is organized around feature modules. Each module is a self-contained domain containing its own routes, APIs, templates, and logic.

By default, Lombik ships with three modules:

- Admin
- Auth
- Core

The **Core** module contains the main features of your application.

After successful authentication, users are redirected to `core_bp.home`, which serves as the default `/` route.

> Optional: Lombik does not ship with it by default, but it is recommended to create a `guest` module for unauthenticated pages and public content.

---

## Module structure

Each module follows a simple structure:

### `__init__.py`
Defines the Flask blueprint used across the module.

---

### `routes.py`
Defines page routes.

Routes represent full page loads and UI entry points.

---

### `queries.py`
Handles data retrieval.

Typically used for database reads and returning data or partial HTML (often via HTMX).

---

### `actions.py`
Handles state changes.

Used for operations that modify data such as `POST`, `PUT`, `PATCH`, and `DELETE`.

---

### `templates/<module>`
All templates are stored in the global `templates` directory.

Each module has its own subfolder to keep templates organized and isolated.