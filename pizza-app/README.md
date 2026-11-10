# Crust & Co. — pizza ordering app (UI only)

These are the HTML, CSS and JavaScript pages for the pizza ordering system. There is no Python here. Each page is laid out so it can be moved into Flask's `templates/` folder and turned into a Jinja template.

## Try it first

Open `START-HERE.html` in a browser. It links to every screen and lets you switch between a logged-out visitor, a customer and the shop owner. Nothing is sent to a server. The cart, the logged-in user and the last order are saved in the browser's localStorage.

Demo logins (any password of 6+ characters):

- `admin@crustandco.in` opens the admin dashboard
- `rahul@example.com`, or any other email, logs in as a customer

## Folder layout

```
pizza-app/
  START-HERE.html          preview launcher (not part of the Flask app)
  templates/
    index.html             home and menu, with the cart drawer
    contact.html
    login.html             one login for customers and the owner
    register.html
    checkout.html
    order-placed.html
    my-orders.html
    admin/
      dashboard.html
      orders.html
      order-detail.html
      users.html
      menu.html
      menu-form.html       add or edit a menu item
      revenue.html
  static/
    css/style.css          all customer pages, plus the base for admin
    css/admin.css          admin pages only (load after style.css)
    js/validate.js         checks form fields before sending
    js/app.js              demo mode, login state, small helpers
    js/cart.js             menu filter, cart, checkout
    js/admin.js            admin tabs, search, accept/reject, status changes
    js/revenue.js          revenue date presets and CSV download
    js/contact.js          contact form extras
```

The folder already matches Flask's layout. Load scripts in this order: `validate.js`, then `app.js`, then any page script.

## How the JavaScript works with Flask

None of the JavaScript calls Python, and there are no `fetch` calls. Every action is an ordinary HTML form, so Flask reads it with `request.form`. The JavaScript only does work in the browser:

| Script | What it does | Changes needed for Flask |
|---|---|---|
| validate.js | Shows field errors before sending | None. Still check every field again in Flask |
| cart.js | Keeps the cart in localStorage and writes it into hidden `item_id` / `qty` inputs at checkout | None |
| admin.js | Status tabs, table search, reject pop-up, confirm-before-delete, sold-out switches | None |
| revenue.js | Date presets and **Download CSV** (reads the rows shown in the table) | None |
| app.js | Demo mode: fakes logins and form results | Turns itself off when `data-demo` is removed |

### Demo mode

Every page has `<body data-demo>`. While that attribute is there:

- forms with `data-demo="..."` don't submit. A small handler fakes the result, for example accepting an order changes its status on the page.
- elements marked `data-auth="guest"`, `"user"`, `"customer"` or `"admin"` show or hide based on the demo login.

**When you move a page into Flask, delete `data-demo` from `<body>`.** Forms then submit to their `action` URL, and the `data-demo` attributes on forms do nothing. You can leave them or delete them.

## Converting a page to a Jinja template

1. **Make `base.html` and `admin/base.html`.** Each page marks its header and footer with a comment. Cut them into a base file with `{% block content %}{% endblock %}`, then start each page with `{% extends "base.html" %}`.
2. **Static files.** Change `../static/css/style.css` to `{{ url_for('static', filename='css/style.css') }}`. Do the same for each script.
3. **Links.** Change `href="checkout.html"` to `href="{{ url_for('checkout') }}"`. Use the route table below.
4. **Logged-in parts.** Replace `data-auth` blocks with Jinja, for example `{% if session.user_id %} ... {% else %} ... {% endif %}`. The comments in `index.html` show where each one goes.
5. **Sample data.** Each table or list holds sample rows. Keep one row as the pattern, wrap it in `{% for ... %}` and delete the rest. Comments above each table say which variable to pass from Flask.
6. **Flash messages.** `login.html` and `register.html` include a hidden `.form-alert` box and a comment showing the `get_flashed_messages()` loop. The CSS classes are `error` and `ok`.

## Routes and forms

### Customer side

| Page | Route | Form | Fields sent |
|---|---|---|---|
| index.html | `GET /` | none (cart is in the browser) | |
| register.html | `GET, POST /register` | `POST /register` | `name, email, phone, address, password, confirm_password, terms, next` |
| login.html | `GET, POST /login` | `POST /login` | `email, password, remember, next` |
| | `GET /logout` | link | Clears the session |
| checkout.html | `GET, POST /checkout` (login required) | `POST /checkout` | `name, phone, address, landmark, notes, payment_method` (always `COD`), `item_id` (repeated), `qty` (repeated) |
| order-placed.html | `GET /order/<id>/placed` | | |
| my-orders.html | `GET /my-orders` (login required) | | |
| contact.html | `GET, POST /contact` | `POST /contact` | `topic, name, phone, email, event_date, guests, message` |

To read the cart in Flask, use `request.form.getlist("item_id")` and `request.form.getlist("qty")`. **Look up each item's price in MySQL. Never trust a price sent from the browser.**

After login, send users with `is_admin = 1` to `/admin`, and everyone else to `next` (or `/`). Only follow `next` when it's a path on your own site.

### Admin side (protect every route with an is_admin check)

| Page | Route | Form | Fields sent |
|---|---|---|---|
| dashboard.html | `GET /admin` | status forms (below) | |
| orders.html | `GET /admin/orders?status=&page=` | status forms | |
| order-detail.html | `GET /admin/orders/<id>` | status forms | |
| all three | | `POST /admin/orders/<id>/status` | `status`, plus `reason` when rejecting |
| users.html | `GET /admin/users` | | |
| menu.html | `GET /admin/menu` | `POST /admin/menu/<id>/availability` | `available` (`1` when on, missing when off) |
| | | `POST /admin/menu/<id>/delete` | |
| menu-form.html | `GET, POST /admin/menu/new` and `/admin/menu/<id>/edit` | same URL | `name, description, category, type, price, tag, available` |
| revenue.html | `GET /admin/revenue?from=YYYY-MM-DD&to=YYYY-MM-DD` | `GET` filter form | `from, to` |

All accept, reject and process buttons post to the same route, `/admin/orders/<id>/status`. The `status` field says what to do.

## Order statuses

```
Pending ──► Accepted ──► Preparing ──► Out for delivery ──► Delivered
   │
   └──► Rejected (reason is shown to the customer)
```

Use these exact words. They're used in `data-status` attributes and the colour of each status pill. In Flask, allow only the next step: reject an `Accepted` order that jumps straight to `Delivered`, and only allow `Rejected` from `Pending`.

## Data each page needs (suggested MySQL tables)

These are the fields the pages display. Name your columns however you like.

**users:** id, name, email (unique), phone, address, password_hash, is_admin, created_at

**menu_items:** id, name, description, category (`pizza` / `sides`), type (`veg` / `nonveg`), price, tag, available

**orders:** id, user_id, name, phone, address, landmark, notes, payment_method, total, status, reject_reason, created_at

**order_items:** id, order_id, menu_item_id, item_name, qty, unit_price, line_total. Copy the name and price into this table when the order is placed, so old orders don't change when the menu does.

**order_status_history** (optional, for the History panel): id, order_id, status, changed_at, changed_by

**contact_messages:** id, topic, name, phone, email, event_date, guests, message, created_at

Revenue counts **Delivered** orders only. The comments in `revenue.html` and `users.html` describe the GROUP BY queries.

## Data attributes used by the JavaScript

| Attribute | Used on | Meaning |
|---|---|---|
| `data-id, data-name, data-price, data-type, data-category` | `.item` on the menu | Read by cart.js and the menu filter |
| `data-validate` | `<form>` | Check fields before sending (add `novalidate` too) |
| `data-match="#id"` | `<input>` | Must equal another field (confirm password) |
| `data-status` | rows, cards, `.status` pills | Current order status |
| `data-order-id` | rows, cards, detail page | Order number, used to update every copy on the page |
| `data-tabs-for, data-key, data-search-for` | tabs and search box | Filter a table by an attribute or by text |
| `data-reject="1048" data-action="/admin/orders/1048/status"` | Reject button | Opens the reject pop-up and sets its form action |
| `data-confirm="Delete X?"` | `<form>` | Ask before sending |
| `data-autosubmit` | checkbox | Send the form when it's switched |
| `data-csv="#table" data-filename` | button | Download that table as CSV |
| `data-csv="value"` | `<td>`, `<th>` | Value written to the CSV instead of the cell text |
