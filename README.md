<header>
  <div style="width: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center;">
    <img src="lombik/templates/createapp/static/icons/icon_512x512.png" alt="Lombik icon" width="128" height="128">
  </div>
</header>


## Lombik

Lombik is a practical scaffold engine for Flask that saves you from hours on hours of configurations, integrations and a messy project structure. 

It leans heavily into a **hypermedia-first approach**, using Jinja2, template filters, HTMX, and Tailwind to keep logic close to the UI and reduce frontend complexity.

As an example, our commercial product called **proov** - *a digital delivery note/ proof of delivery platform for logistics* has 50% of its code being html.
The entire application is just about 20K lines. 


Language                     Files  Lines      Extension
--------------------------------------------------------
HTML                              58      11622   .html
Python                            87       7871   .py
JavaScript                         6        957   .js
Markdown                           6        281   .md
CSS                                1        276   .css
Text                               3        238   .txt
Shell Script                       1        146   .sh
JSON                               1         37   .json
XML                                1         22   .xml
TOML                               1          2   .toml
--------------------------------------------------------
TOTAL:                        165      21452
========================================================


**Here is how to build with lombik:**

1. First off, install it.

`pip install lombik`

I try to keep dependencies as low as possible. Currently it will downlaod these packages on install:

- Flask>=3.0
- Flask-SQLAlchemy>=3.1
- Flask-Migrate>=4.0
- Flask-Session>=0.6
- Flask-WTF>=1.2
- Flask-Caching>=2.3
- Flask-Limiter>=3.8
- SQLAlchemy>=2.0
- python-dotenv>=1.0
- pytest>=7.1.0
- pytest-cov>=7.1.0
- click>=8.1
- resend
- python-dateutil>=2.9.0

2. Navigate to your desired folder

`lombik createapp myapp`

This will generate the entier project structure for you. 
The app can now be ran:

`lombik run`

However, before doing so, it's best to create your superuser account.

If your app is running, quit it `ctrl + c`

3. Initialize the database

`lombik initdb`

By default, the environment is set to test/default for which sqlite3 is used. 
Production db by default is MySQL, but you can change this in `lombik/configuration.py`
Don't forget to update your credentials in your environment variables.

4. Create a superuser account

`lombik superuser`

Now it's time to run the app.

`lombik run`

---

### Routes

The app is running, and you can log in.
Let's add one where only registered / logged in users can access.

Just add the following import on the top of your file
`from lombik.wrappers import login_required`

Create a new route

```python
@core_bp.route("/members")
@login_required
def members():
  return render_template("...")
```

**Simple isn't it?**

Now let's add one only for admins and superusers.
Back at the top of the file

`from lombik.wrappers import login_required, roles_required`

Then create another route for admins

```python
@core_bp.route("/admin")
@login_required
@roles_required("admin", "superuser")
def admin():
  return render_template("...")
```

**However**, I do not recommend mixing admin pages with the core application so this flows well into the next step.
Create a separate module for admin related activities.

`lombik module admin`

This will generate an admin folder in your blueprints with the default structure. Keeps things organized.
Blueprints are automatically registered so no further action is needed.

You can protect your routes with an in memory rate limiter (for proudction you may want to use redis or alike)

`from lombik.extensions import limiter`

```python
@core_bp.route("/admin")
@limiter.limit("60 per minute")
@login_required
@roles_required("admin", "superuser")
def admin():
  return render_template("...")
```


---

### Actions

By default, lombik suggests to keep routes, actions and queries separately. 
An action is for example changing a users timezone. When signing up, the standard timezone for users is UTC.
Let's create a way to change it end-to-end, in the lombik/hypermedia first approach.

1. We start where the user starts, back at `/members`

We should pass all timezones to the template so the user can select from an existing list.
We use the page context for this. Timezones are available in `lombik/constants.py`. 
Since timezone don't really change, we can just save them on startup into a list without the need to re-fetch them every time.

`from lombik.constants import TIMEZONES`

then in context

```python
@core_bp.route("/members")
def members():
    context = {
        "selected": "members",
        "timezones: TIMEZONES
    }
    return render_template("/core/members.html", **context)
```

Python automatically unpacks the context so we can reference it in the template as `{{ timezones }}`

2. Now let's create `core/members.html`

Use Jinja to extend the base template and a selectbox with timezones listed

```html
{% extends "base/base.html" %}

{% block title %}
  Members
{% endblock %}

{% block content %}

<div class="space-y-6">

    <h1>Hello {{ g.user.username }}</h1>
    
    <select
        hx-patch="{{ url_for('core_bp.update_timezone') }}"
        hx-vals='{
            "csrf_token": "{{ csrf_token() }}"
        }'
        hx-trigger="change"
        hx-target="#timezoneUpdateError"
        hx-swap="#innerHTML"
        name="tz">
        {% for tz in timezones %}
        <option value="{{ tz }}" 
            {% if g.user.timezone == tz %}
                selected
            {% endif %}
            >
            {{ tz }}
        </option>
    {% endfor %}
</select>
<div id="timezoneUpdateError"></div>

</div>

{% endblock %}
```

*ps.: We could use forms.py within the module but personally for such small action I like to keep it simple.*

Alright, now we need to create this action in `blueprints/core/actions.py`

```python
from . import core_bp
from flask import g, request
from lombik.responses import Result, htmx_response
from lombik.users import change_user_timezone
from db import db

@core_bp.patch("/users/me/timezone")
def update_timezone():
    def _timezone_message(message, color):
        return htmx_response(html=f"""
            <button
                onclick="this.classList.add('hidden');"
                class="text-xs -mt-2 flex items-center gap-1 {color}">
                {message}
                <ion-icon name="close-circle-outline"></ion-icon>
            </button>
        """)

    new_timezone = request.values.get("tz", "")

    res = change_user_timezone(user_id=g.user.id, new_timezone=new_timezone)

    return htmx_response(
        html=_timezone_message(
            message=res.message,
            color="green" if res.success == True else "red"
        )
    )
```
**Done**

We used the built in function to change the user's timezone. It does all the validation and returns the `Result` object.
In lombik, we use the Result object when performing actions.
The structrue is very simple:

```python
Result(
    success=True, # bool
    data={"new_timezone": new_timezone}, # dict or None on success=False
    message="Timezone changed successfully." #str
)
```  

Before we move on, let's look at some of the filters that lombik comes with. 
Let's say we wanted to have a dynamic title showing something like **John's dashboard**:

We can use a filter called **proper** which capitalizes each word and replaces underscores with spaces.
With proper, `{{ john_doe | proper }}` becomes: **John Doe**

Next up we can add the **possessive** filter.
This will turn `{{ john_doe | proper | possessive }}` into John Doe's appropriately.

To create it, simply add this into your title block 

```html
{% block title %}
  {{ g.user.full_name | proper | possessive }} dashboard
{% endblock %}
```
Now we should create a card showing the user how long they've been members for, something like **You became a member 3 months ago**

We can use the `{{ g.user.created_at }}` timestmap in combination with a filter called timesince, so isntead of showing *2026-08-19 13:33:44.763467* it will show *5 hours ago*. 

It has a nice progression from: *just now* -> *few minutes ago* -> *N minutes ago* -> *N hours ago* etc.

`<p>You became a member {{ g.user.created_at | timesince }}</p>`

To get the same effect but for the future, use **timeuntil**.

There are more filters that make frontend work easier, you'll find them all in `lombik/filters.py`.

---

### Queries

Queries are quite straightforward, all resources shall be queried through these endpoints unless it's highly inconvinient.

```python
@core_bp.get("/users")
def get_users():
    status = request.args.get("status")
    return get_users_by_status(status=status)
```


```python
from lombik.extensions import cache

@core_bp.get("/users")
@cache.memoize(timeout=30)
def get_users():
    status = request.args.get("status")
    users = get_users_by_status(status=status)
    return render_template("core/partials/users.html", users=users)
```
Then you'd create this partials in `core/partials/users.html`
```html
{% for user in users %}
    <li>{{ user.username | proper }}</li>
{% endfor %}
```

And ready to be used in `members.html`

```html
<div>
    <p>Active members</p>
    <ul 
        hx-get="{{ url_for('core_bp.get_users', status='active') }}"
        hx-trigger="load, every 30s">
        <!-- htmx populates-->
    </ul>
</div>
```

---

### Models

Next up, let's turn lombik into a multi tenant platform. In order to do that, we'll need a new table called tenants. 
Instead of manually creating one, use the built in model generator and add the name of you model. Use singular names. Lombik automatically generates the plurar version of it for the actual SQL architecture, but will use the singular for the class.

`lombik model tenant`

This creates a default model structure and registeres it automatically in the `models/__init__.py`

Add your columns and do not delete the relationship marker from the bottom.

```python
from db import db
import uuid
from lombik.utils import utc_now        

class Tenant(db.Model):
    __tablename__ = "tenants"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        unique=True
    )

    name = db.Column(
        db.String(255)
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=utc_now
    )

    # <LOMBIK:RELATIONSHIPS>
```
Don't forget to update the users class to add tenant_id:
```python
tenant_id = db.Column(
    db.String(36)
)

# In production you'd make this nullable=False and re-create the superuser.

```

When done, run:

`lombik db -m"added tenants"`

This command will run migration and upgrade at once.
To create relationship fast, you can use lombik's relationship generator which looks like this.

`lombik relate parent.field to child.field [one-to-many|many-to-one|one-to-one|many-to-many] [--lazy LAZY]`

Here are a few examples:

```python
lombik relate tenant.id to user.tenant_id one-to-many
lombik relate user.tenant_id to tenant.id many-to-one
lombik relate tenant.id to setting.tenant_id one-to-one
lombik relate user.id to role.user_id many-to-many
```
If you run this, you'll notice that it added relationships below the marker in both models.

`lombik relate tenant.id to user.tenant_id one-to-many`


---

### UI

Lombik comes with a built in light & dark theme handler in `static/js/theme.js`
You can easily use tailwinds default `dark:...`

To haev a toggle button for the user you can use this snippet

```html
<button onclick="toggleDarkMode()" id="changeThemeBtn">
  <ion-icon id="themeIcon" name="moon-outline"></ion-icon>
  <span id="themeText">Dark mode</span>
</button>
```

#### Dropdown

I tried making dropdown in a way I always thought HTML should have it. 
You can use a custom tag `<dropdown></dropdown>` and populate it with links or buttons. 

When using it with a button, it is important to set the button type to be 'button', otherwise in interferes. Parent shall also be relative.

Here is an example how I use it in my production application (without styling, you can style them as you wish):

```html
<div class="relative">
  <button type="button">
    <ion-icon
      name="settings-outline"
    ></ion-icon>
  </button>

  <dropdown class="absolute right-0 w-40">
    <a href="/">Home</a>
    <a href="/apis">API</a>
    <a href="/settings">Settings</a>

    <hr class="my-1 dark:border-darkaccent" />

    <button
        onclick="toggleDarkMode()"
        id="changeThemeBtn">
        <ion-icon id="themeIcon" name="moon-outline"></ion-icon>
        <span id="themeText">Dark mode</span>
    </button>

    <hr class="my-1"/>

    <button type="button"
      hx-post="{{ url_for('auth_bp.logout') }}"
      hx-vals='{
          "csrf_token": "{{ csrf_token() }}"
      }'>
      Log out
    </button>

  </dropdown>
</div>

```

#### Draggin & Dropping

Similar to the dropdown, I also thought html should have a standard for this. I recommend you to read the how to use section in `static/js/drag.js` 

The core idea is that you can use a custom html tag `<dragarea>..</dragarea>`. Within it, you can drag anything that has a class `.dragable` or `.draggable`.

If you wanted to have dragable cards interact with other boards, eg.: you have a **dragarea** for open tasks, one for in progress etc. 
You can assign a family to it like this: `<dragarea family="tasks">` Now every dragarea of the same family can interact with each other.

To store the state, you need two things.
First you need to haev each card a unique id, something like this:

`<div class="dragable .." data-id="{{ task.id }}"`  

Then you can use htmx on the **dragarea** element like this:

```html
<dragarea 
  family="tasks"
  hx-patch="/update-task-status"
  hx-vals='{"csrf_token": "{{ csrf_token }}"}'
  field="status"
  value="open">

```
It will automatically inject the ID of the dropped element into an ajax request with values:

```json
{
  id: item.dataset.id,
  status: open, (it took the status from field and assign the value open to it)
  from_index: 0,
  to_index: 1,
  from_field: "status",
  from_value: "new"
}
```
Another custom tag is `<dragfree>..</dragfree>`
This allows anything inside to be dragged around freely without snapping to anything. You can also store its location by giving it an id.

`<dragfree id="note-{{ note.id }}">...</dragfree>`

Now wherever you move it to, it will save it localstorage. Double click it to reset it's location.

---

### Other

Just a few tips:

- Disable/comment out the exception error handler in `lombik/errors.py` to see the debug screen during development. (or add {e} inot the 500.html file)

- Flash messages have their own class and can easily be used across routes. Just import it form `lombik.flash import Flash` and on re-directs yo ucan use `Flash.ok("..message here..")` or `Flash.error("..")` etc. Explore the class to see all. It comes with a predesigned look, icon, animation etc. and injected into the base template.

- Modals are also simple, you just use `<button onclick="openModal('id_of_your_modal');"`. It will open, listen to close and for clicks outside of the modal area. There is a default modal template in `base/partials/modal.html`

- Tests. Lombik uses standard flask tests we jsut have soem custom commands for it: 
> `lombik test` Runs the tests
> `lombik test_report` Runs the tests and generates report
> `lombik test_report_html` Runs the tests and generates html report

- Session expiry. When CSRF tokens expire (set it in configurations) user will be shown a page to refresh their session.

- Resend is configured as a default email engine. You can jsut update your API key and use `from lombik.mail import send_email`

- Forms. Lombik has a ligth version of form validation, review the default login / register pages to learn more about it. It's failty simple and keeps things organized

- Image saving and compression functions are in `lombik/images`

- Validation functions are in `lombik.validation`. It has built in email pattern valdiator, role validator, password strength etc.

There is more, I recommend you discover it as you go, it's a small engine but I liek to think it's powerful. At least for my own use cases.

I hope you find it useful too. It's MIT licensed so contributions, fixes, forks are more than welcome.




