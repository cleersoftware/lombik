<header>
  <div style="width: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center;">
    <img src="lombik/templates/createapp/static/icons/icon_512x512.png" alt="Lombik icon" width="128" height="128">
  </div>
</header>


## Lombik

Lombik is a practical scaffold engine for Flask that saves you from hours on hours of configurations, integrations and a messy project structure. 

It leans heavily into a **hypermedia-first approach**, using Jinja2, template filters, HTMX, and Tailwind to keep logic close to the UI and reduce frontend complexity.


**To get started run these 4 commands:**

```bash
pip install lombik
lombik createapp my-new-app
cd my-new-app
flask run --debug
```

**And start developing.**


## Structure

Lombik is organized around feature modules. Each module is a self-contained domain containing its own routes, APIs, templates, and logic.
By default, you'll get 3 modules:
- Auth
- Admin
- Core

Each of these modules follow the same file structure:

##### `__init__.py`
Defines the Flask blueprint used across the module.

---

##### `routes.py`
Defines page routes.

Routes represent full page loads and UI entry points.

---

##### `queries.py`
Handles data retrieval.

Typically used for database reads and returning data or partial HTML (often via HTMX).

---

##### `actions.py`
Handles state changes.

Used for operations that modify data such as `POST`, `PUT`, `PATCH`, and `DELETE`.

---

## The toolkit

Inside the lombik directory you'll find the engine of the application.
There is a very light test coverage by default. 
Custom commands to run tests:
  - `lombik test` Run test in the current folder, by default it shall be ran from root
  - `lombik test-report` Generates a coverage report in the terminal
  - `lombik test-report-html` Generates an HTML report about the test coverage
Here some of the default behaviors are defined and yo ucan change them to your liking.

I leave it up to you to read through it and get familiar with the engine. With that said, I'd like to show some examples to display waht it's like to build with lombik.

### Dates & time handling

Instead of formatting timestamps in the backend, you do it directly in the template:

`{{ created_at | localtime }}`        → 2026-05-19 05:15  
`{{ created_at | onlydate }}`         → 2026-05-19  
`{{ created_at | onlytime }}`         → 05:15  
`{{ created_at | shortdatetime }}`    → May 19 05:15  
`{{ created_at | timesince }}`        → Just now // 2 minutes ago // 21 hours ago etc.

Everything defaults to `localtime`, meaning UTC from the backend is automatically shown in the user’s timezone.

Lombik expects the user’s timezone to be available via `g`. To change: `lombik/filters/_localize.`

### String helpers

Make frontend less painful

`{{ g.user.full_name | proper }}`

john_doe → John Doe

`{{ g.user.first_name | possessive }}`

john → john's  
lucas → lucas'  

You can chain them:

`{{ g.user.full_name | proper | possessive }}`

john_doe → John Doe's  

You can also normalize user input:

`{{ user_input | normalize }}`

Hello, world → hello_world
email@example.com → email_example_com

In lombik, Jinja is heavily used to display UI elements and these built in template filters make it very easy and re-usable. 

As an example, let's assume you have two objects: 

`user.name` = **john_doe**<br>
`created_at` = **2026-06-01 13:00:00**

In a single line like this you can format it:

`{{ user.name | proper | possessive }} response • {{ created_at | timesince }}` -->
**John Doe's response • 21 minutes ago** 

---

### Models

#### Create models

You can create a model for example Client by using `lombik model client`
This creates a file called clients.py with a class CLient. The table name and filename is always plural. 
It also automatically injects it into the main model imports.



#### Create relationships

The `relate` command automatically generates SQLAlchemy relationships between two existing models in your Flask project.

It handles:
- Foreign key creation
- Relationship creation
- Back-populates linking
- Naming conventions
- Duplicate prevention

---


lombik relate user.id to client.user_id

Creates:
- Client.user_id → ForeignKey to User.id
- Client.user relationship
- User.clients reverse relationship

---

If fields are omitted, Lombik assumes:

user → user.id  
client → client.user_id

---

user_id = db.Column(
    db.String(36),
    db.ForeignKey("users.id"),
    index=True
)

user = db.relationship(
    "User",
    back_populates="clients"
)

---

clients = db.relationship(
    "Client",
    back_populates="user",
    cascade="all, delete-orphan"
)

---

- Table names are pluralized automatically
- Relationship names follow:
  - parent → plural(child)
  - child → singular(parent)
- Back-populates is always synchronized between both sides

---

- Existing columns are never overwritten
- Existing relationships are never duplicated
- Lombik only edits managed sections when available
- Otherwise it appends safely to the class

---

**Recommended project structure**

Use these markers in your models for best results:

#### <LOMBIK:COLUMNS>
#### </LOMBIK:COLUMNS>

#### <LOMBIK:RELATIONSHIPS>
#### </LOMBIK:RELATIONSHIPS>

This ensures clean and predictable insertions.
