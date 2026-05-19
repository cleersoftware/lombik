# Lombik
#### A cli based scaffold engine for Flask, the greatest framework of all times.

This readme will serve perfectly as a self documentation file as I go, and at the end of it I will re-write it with the final details. 
That means that if you see this, either my company cleersoftware has taken off and you might work with me on enhancing the scaffold for our apps. 
Another possibility is that lombik took off, and you are reading the early commits. Have fun, there is probably a lot of them.
Anyways, I'm gonan actually start on explaning / plannign how thigns will work.

> Install lombik
Run `pip install lombik`

> Create app
To create an app called *myapp*, run `lombik createapp myapp` then `cd myapp`
This creates the entire structure of your application in one go and you can run `flask run --debug`

> Create superuser
Lombik comes with MySQL as a default db. In the generated .env file you'll find the credentials for local development.
Replace those placeholders with your actual dev credentials and production if you have it already.
When done, initialize the database by running `flask initdb` and then you can run `flask superuser` to create your owner account.
With this, you'll be able to log in to your app and start developing from there.

This is a quite simple auth system, in fact it is simple by design and meant to be replaced for production apps with something more robust.

> Features and benefits
On top of the structural guidance, lombik comes with a few built in goodies.

- User authentication and session handling
- CSRF / session expiry
- Error handling
- Structure
- Template filters for frontend development
- Pre-imported libraries
- General templates for desktop and mobile

