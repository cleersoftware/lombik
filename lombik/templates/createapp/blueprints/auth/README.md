# Auth module

Lombik is organized around feature modules. Each module is a self-contained domain containing its own routes, APIs, templates, and logic.

By default, Lombik ships with three modules:

- Admin
- Auth
- Core

The **Auth** module is responsible for all authentication-related functionality.

It handles user identity, session lifecycle, and access control flows such as login, registration, logout, password management, and invitations.

---

## Module structure

Each module follows a simple structure:

---

### `__init__.py`
Defines the Flask blueprint used across the module.

---

### `routes.py`
Defines authentication pages and entry points.

This includes views such as:
- login page
- registration page
- password reset page

Routes represent full page loads and UI entry points.

---

### `actions.py`
Handles authentication-related state changes.

This includes operations such as:
- login authentication
- user registration
- logout
- password changes
- password reset flows
- invitation acceptance

All mutation-based HTTP actions (`POST`, `PUT`, `PATCH`, `DELETE`) live here.

---

### `queries.py`
Handles authentication-related data retrieval.

Typically used for:
- fetching user identity data
- validating authentication state
- checking permissions or roles

May return raw data or partial HTML depending on HTMX usage.

---

### `templates/<module>`
All templates are stored in the global `templates` directory.

Each module has its own subfolder to keep templates organized and isolated.