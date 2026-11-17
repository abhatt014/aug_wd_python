# Development phases

Status of converting the Crust & Co. pizza app from a browser-only demo (`data-demo` on `<body>`, data in localStorage) to a working Flask + MySQL app. Updated whenever a phase starts, finishes or changes scope.

Last updated: 2026-11-17

## Status

| Phase | What | Status |
|---|---|---|
| 0 | Analysis and gap list | Done (2026-11-16) |
| 1 | Database schema | Done (2026-11-16). `backup.sql` is a real `mysqldump` of the live database (2026-11-17) |
| 2 | Auth helpers | Done (2026-11-17) |
| 3 | Customer flow | Done (2026-11-17) |
| 4 | Admin orders | Done (2026-11-17) |
| 5 | Admin menu CRUD | Done (2026-11-17) |
| 6 | Revenue report | Done (2026-11-17) |
| 7 | Template cleanup | Done (2026-11-17); CSV download and date presets still to be clicked in a browser |

Phases 2 to 7 were checked on 2026-11-17 against the real MySQL database: the 8-step Verification list below was run over HTTP with a script (separate customer, demo and admin sessions), and every step passed. Browser-only behaviour (the cart count going back to 0, the revenue CSV download and date presets) was checked only as far as the server sends the data it needs.

## Next steps

1. Click through the cart, the revenue CSV download and the date presets once in a real browser.
2. Work on the known gaps below, CSRF protection first.

## Changes on 2026-11-17

- Seeded phone numbers fixed to valid 10-digit numbers: `demo` 9856547520 (also on sample order #1049), `admin` 9123456789.
- `backup.sql` replaced with a `mysqldump` of the live database. It now holds the verification data: customer `verify.customer@example.com`, order #1050 (Delivered), and sample order #1049 (Rejected). The `demo` and `admin` passwords are now stored as hashes; they are still `123456`.

## Phase details

### 0. Analysis (done)

Found 12 missing routes, schema gaps, incomplete functions and unconverted templates.

### 1. Database schema

The code assumes this schema:

- `users.phone` is `varchar(15)` (was `int`)
- `menu_items` (id, name, description, category `pizza|sides`, type `veg|nonveg`, price, tag, available)
- `orders` has `customer_name`, `phone`, `address`, `landmark`, `notes`, `payment_method`, `reject_reason`, and `Rejected` in the `status` enum
- `order_items.menu_item_id` (nullable, set to NULL when the menu item is deleted)
- `order_status_history` (order_id, status, note, changed_by, changed_at)

### 2. Auth helpers

- `login_required` and `admin_required` decorators in `app.py` replace the copy-pasted session checks
- Login clears the old session first; logout clears everything (role no longer leaks between users)
- Guests are sent to `/login?next=...` and returned to the page they wanted; `next` only accepts paths on this site
- Passwords are stored as hashes (`pbkdf2:sha256`, 95 characters, fits `users.password varchar(100)`)
- Accounts that still hold a plain-text password keep working: the first successful login replaces it with a hash
- "Keep me logged in" makes the session last 30 days
- `SECRET_KEY`, `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` can be set as environment variables; the old values are the defaults

### 3. Customer flow

- `/` reads the menu from `menu_items`; sold-out items are shown but cannot be added
- `/checkout` GET pre-fills name, phone and address from the account
- `/checkout` POST re-prices every item from the database, refuses sold-out or unknown items, then writes `orders`, `order_items` and the first `order_status_history` row in one transaction
- `/order/<id>/placed` shows the real order and empties the browser cart once
- `/myorders` shows the reject reason for rejected orders
- Register and contact forms are validated on the server as well as in the browser

### 4. Admin orders

- `/admin/dashboard` shows live counts, the approval queue and in-progress orders
- `/admin/orders` lists orders, 25 per page; status tabs and search filter the current page in the browser
- `/admin/orders/<id>` shows items, delivery details, next step and history
- `/admin/orders/<id>/status` POST: only the next step in the flow is allowed; reject is only possible while pending and needs a reason
- The database says `Pending approval`; CSS and `admin.js` use the short key `Pending`. The `status_key` template filter converts between them.

### 5. Admin menu CRUD

- `/admin/menu`, `/admin/menu/new`, `/admin/menu/<id>/edit`, `/admin/menu/<id>/availability`, `/admin/menu/<id>/delete`
- Duplicate names are refused with a message

### 6. Revenue report

- `/admin/revenue?from=&to=` (defaults to this month): totals, by day, by item, and the delivered orders, with CSV download
- An order counts on the day it was placed, and only once it is delivered

### 7. Template cleanup

- No template has `data-demo` any more; every link, form action and static file uses `url_for`
- Shared pieces moved to partials: `_head.html`, `_header.html`, `_footer.html`, `_flash.html`, `admin/_sidebar.html`, `admin/_reject_dialog.html`, `admin/_scripts.html`
- `requirements.txt` added

## Verification

On the machine that runs the app (`pip install -r requirements.txt`, then `python app.py`):

1. Home page shows the 12 menu items; Tiramisu is marked sold out.
2. Register a new customer with a 10-digit mobile number; check the `users` row has a hashed password.
3. Log in, add items, check out; the order appears on the order-placed page and in `/myorders`, and the cart count returns to 0.
4. Log in as `admin@demo.com`; accept the order and move it through to Delivered; reject the older sample order with a reason.
5. As the customer, `/myorders` shows the new statuses and the reject reason.
6. Add, edit, switch off and delete a menu item; the home page follows.
7. `/admin/revenue` shows the delivered order; try the date presets and a CSV download.
8. Log out; `/admin/dashboard` and `/checkout` redirect to the login page.

## Known gaps

- No custom 404 or 500 pages.
- The order number is "highest number + 1"; two orders placed in the same instant could collide (the second one would fail on the unique key rather than be saved wrongly).
- Admins cannot cancel an order after accepting it; `Cancelled` exists in the database but nothing sets it.
- No CSRF protection on the forms.

## Notes

- The MySQL server runs on Linux; the project is edited on Windows. Dumps and imports are run by hand with `mysqldump` and `mysql`.
- App database access: user `dbuser`, database `pizza`, host `localhost`.
