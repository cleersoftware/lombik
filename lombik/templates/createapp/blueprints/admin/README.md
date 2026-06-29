# Admin module# Admin module

Lombik is organized around feature modules. Each module is a self-contained domain containing its own routes, APIs, templates, and logic.

By default, Lombik ships with three modules:

- Admin
- Auth
- Core

The **Admin** module contains all administrative functionality of the application.

It is responsible for managing users, system state, and application-level operations that require elevated permissions.

Only authorized roles (such as `admin` or `superuser`) should have access to this module.

---

## Module structure

Each module follows a simple structure:

---

### `__init__.py`
Defines the Flask blueprint used across the module.

This blueprint typically enforces access control for administrative routes.

---

### `routes.py`
Defines admin pages and dashboards.

This includes views such as:
- admin dashboard
- user management pages
- system overview pages
- configuration panels

Routes represent full page loads and UI entry points.

---

### `actions.py`
Handles administrative state changes.

This includes operations such as:
- activating / deactivating users
- changing user roles
- managing system settings
- deleting or restoring resources

All mutation-based HTTP actions (`POST`, `PUT`, `PATCH`, `DELETE`) live here.

---

### `queries.py`
Handles administrative data retrieval.

Typically used for:
- fetching user lists
- system statistics
- audit logs
- filtered datasets for dashboards

May return raw data or partial HTML depending on HTMX usage.

---

### `templates/<module>`
All templates are stored in the global `templates` directory.

Each module has its own subfolder to keep templates organized and isolated.