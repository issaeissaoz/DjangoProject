# University Appointment System (Django)

A small Django application where students and staff can create an account, log in, and book
and manage their own university appointments (general consultation, dental, eye, physiotherapy
and counselling). Every appointment belongs to the signed-in user: the dashboard only ever
shows that user's bookings, and one user can never edit or delete another user's record.

## Features

### Phase 1 — UI: auth forms and dashboard
- Hand-written CSS design system (no Bootstrap or CDN assets) in `Appointment/static/Appointment/css/style.css`.
- Shared `templates/base.html` layout with a header, flash messages, and footer.
- Login, sign-up and dashboard pages.
- `Appointment` model, initial migration and Django admin registration.

### Phase 2 — Authentication
- Real sign-up, login and logout using Django's auth system (`pbkdf2` password hashing).
- `SignUpForm` (a `UserCreationForm`) validates the username/email uniqueness case-insensitively,
  normalises the email to lowercase, and title-cases the first/last name.
- `LoginForm` (an `AuthenticationForm`) with friendlier error messages.
- Logout is POST-only, and the `?next=` redirect is restricted to the current host.

### Phase 3 — Persistent sessions
- Sessions live for 14 days (`SESSION_COOKIE_AGE`), are refreshed on every request
  (`SESSION_SAVE_EVERY_REQUEST`), and survive a browser restart
  (`SESSION_EXPIRE_AT_BROWSER_CLOSE = False`).
- Cookies are `HttpOnly` with `SameSite=Lax`.
- The dashboard is `@login_required` and shows only the signed-in user's appointments,
  with counts for total, pending, confirmed and completed bookings.

### Phase 4 — Booking form and CRUD
- `/appointments/new/` — a booking form (title, service, date, time, description) that saves the
  appointment for the signed-in user.
- `/appointments/<id>/edit/` — update an existing booking.
- `/appointments/<id>/delete/` — confirmation page, then POST-only deletion.
- The dashboard lists each booking with its title, a description snippet, service, date, time,
  status and per-row Edit/Delete links.

## Tech stack

| Part     | Choice                                  |
| -------- | --------------------------------------- |
| Language | Python 3                              |
| Framework| Django 6.1                             |
| Database | SQLite (`db.sqlite3`, not committed)    |
| Frontend | Django templates + plain CSS            |
| Auth     | `django.contrib.auth` (sessions)        |

## Getting started

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create the database schema
python manage.py migrate

# 4. Create an admin account (optional, for the Django admin)
python manage.py createsuperuser

# 5. Run the development server
python manage.py runserver
```

Then open <http://127.0.0.1:8000/>. The admin site is at `/admin/`.

## URL map

| URL                        | View                 | Access        | Purpose                          |
| -------------------------- | -------------------- | ------------- | -------------------------------- |
| `/`                        | `home_view`          | signed in     | Appointment dashboard            |
| `/signup/`                 | `signup_view`        | public        | Create an account                |
| `/login/`                  | `login_view`         | public        | Log in (supports safe `?next=`)  |
| `/logout/`                 | `logout_view`        | POST          | End the session                  |
| `/appointments/new/`       | `appointment_create` | signed in     | Book an appointment              |
| `/appointments/<id>/edit/` | `appointment_update` | owner only    | Edit a booking                   |
| `/appointments/<id>/delete/`| `appointment_delete`| owner only    | Confirm, then delete a booking   |
| `/admin/`                  | Django admin         | staff         | Manage users and appointments    |

Requests for another user's appointment return **404**, and anonymous visitors are redirected to
the login page with a `?next=` back to the page they asked for.

## Booking rules

`AppointmentForm` validates every submission:

- **Title** — required, trimmed, 3 to 120 characters.
- **Description** — optional, trimmed, up to 1000 characters.
- **Service** — one of the model's choices.
- **Date** — today or later; past dates are rejected.
- **Time** — if the date is today, the time must be later than the current time.
- **Clash** — the same user cannot hold two appointments on the same date and time
  (editing a booking ignores its own row, so saving without changes is fine).
- **Status** — not editable by users; it stays `pending` until staff change it in the admin.

## Data model

`Appointment` (`Appointment/models.py`):

| Field         | Type                          | Notes                                     |
| ------------- | ----------------------------- | ----------------------------------------- |
| `user`        | `ForeignKey(User, null=True)` | Owner; related name `appointments`        |
| `title`       | `CharField(120)`              | Short booking name                        |
| `service`     | `CharField(32, choices)`      | general / dental / eye / physio / counselling |
| `date`        | `DateField`                   | Appointment date                          |
| `time`        | `TimeField`                   | Appointment time                          |
| `status`      | `CharField(16, choices)`      | pending / confirmed / completed / cancelled; defaults to `pending` |
| `description` | `TextField(blank=True)`       | Optional details                          |
| `created_at`  | `DateTimeField(auto_now_add)` | When the booking was created              |

Bookings are ordered by date, then time.

## Accounts and sessions

- Passwords are hashed with Django's default hasher; plain-text passwords are never stored.
- Sign-up enforces the standard Django password validators (length, common passwords, numeric-only).
- Sessions persist for 14 days, are refreshed on activity, and end when the user logs out.
- Logout is only accepted as a POST with a CSRF token, so a link cannot sign a user out.

## Tests

```bash
python manage.py test
```

The suite covers the pages, the model and its ordering, form validation (required fields, past
dates, same-day past times, duplicate slots), the booking CRUD views (ownership, 404s, login
requirements, delete confirmation), sign-up/login/logout, and session persistence.

Useful checks while developing:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
```

## Project structure

```
.
├── config/                     # Project settings and root URLconf
│   ├── settings.py
│   └── urls.py
├── Appointment/                # The app
│   ├── admin.py
│   ├── forms.py                # LoginForm, SignUpForm, AppointmentForm
│   ├── migrations/
│   ├── models.py               # Appointment
│   ├── static/Appointment/css/style.css
│   ├── templates/core/         # home, login, signup, appointment_form, confirm delete
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── templates/base.html         # Shared layout
├── manage.py
├── requirements.txt
└── README.md
```

## Notes

- `db.sqlite3` is intentionally git-ignored; run `migrate` after cloning.
- Appointment data created in earlier phases is preserved by the Phase 4 migration, which renames
  `notes` to `description` and adds `title`.
- Not included (out of scope): password reset, email notifications, a staff-side approval UI,
  pagination and deployment.
