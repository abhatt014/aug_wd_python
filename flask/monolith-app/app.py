import hmac
import os
import re
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from functools import wraps
from urllib.parse import urlparse

import mysql.connector
from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

# DB status values, in order, and the labels shown under the tracker
ORDER_STEPS = ['Pending approval', 'Accepted', 'Preparing', 'Out for delivery', 'Delivered']
STEP_LABELS = ['Waiting for approval', 'Accepted', 'Preparing', 'Out for delivery', 'Delivered']

# The only way an order moves forward: current status -> next status
NEXT_STATUS = {
    'Pending approval': 'Accepted',
    'Accepted': 'Preparing',
    'Preparing': 'Out for delivery',
    'Out for delivery': 'Delivered',
}
# Button text for the step that follows the current status
NEXT_LABEL = {
    'Pending approval': 'Accept',
    'Accepted': 'Start preparing',
    'Preparing': 'Send out for delivery',
    'Out for delivery': 'Mark delivered',
}

MENU_CATEGORIES = {'pizza': 'Pizza', 'sides': 'Sides & drinks'}
MENU_TYPES = ('veg', 'nonveg')
MENU_TAGS = ('Bestseller', 'Spicy', 'New')

ORDERS_PER_PAGE = 25
MESSAGES_PER_PAGE = 25
MAX_QTY_PER_ITEM = 20

app = Flask(__name__)
# Set SECRET_KEY and the DB_* variables in the environment for anything but local use.
app.secret_key = os.environ.get('SECRET_KEY', 'aASDFG45ev3weFwes5ghER%^u')
app.permanent_session_lifetime = timedelta(days=30)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def friendly_time(dt):
    """'Today, 8:41 pm' / 'Yesterday, 2:05 pm' / '12 Nov 2026, 7:30 pm'"""
    if not dt:
        return ''
    t = dt.strftime('%I:%M %p').lstrip('0').lower()
    today = date.today()
    if dt.date() == today:
        return f'Today, {t}'
    if dt.date() == today - timedelta(days=1):
        return f'Yesterday, {t}'
    return f"{dt.strftime('%d %b %Y')}, {t}"


def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'dbuser'),
        password=os.environ.get('DB_PASSWORD', 'redhat'),
        database=os.environ.get('DB_NAME', 'pizza')
    )


@contextmanager
def db_cursor(commit=False):
    """Open a connection + dictionary cursor and always close them.

        with db_cursor() as cursor:              # read
        with db_cursor(commit=True) as cursor:   # write (rolled back on error)
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor
        if commit:
            conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def login_required(view):
    """Send guests to the login page, then back to the page they wanted."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login_form', next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    """Only users with role = 'admin' may open the page."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login_form', next=request.path))
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))
        return view(*args, **kwargs)
    return wrapped


def safe_next(target):
    """Only allow redirects to a path on this site (no 'https://evil.com', no '//evil.com')."""
    if target and target.startswith('/') and not target.startswith('//') and '\\' not in target:
        return target
    return None


def redirect_back(fallback):
    """After a POST, return to the page the form was on."""
    ref = request.referrer
    if ref and urlparse(ref).netloc == request.host:
        return redirect(ref)
    return redirect(fallback)


def clean_phone(raw):
    """'+91 98765 43210' -> '9876543210'. Returns None if it is not an Indian mobile number."""
    digits = re.sub(r'[\s\-]', '', raw or '')
    if digits.startswith('+91'):
        digits = digits[3:]
    return digits if re.fullmatch(r'[6-9]\d{9}', digits) else None


def hash_password(password):
    # salt_length=8 keeps the hash under 100 characters, the size of users.password
    return generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)


def is_hashed(stored):
    return stored.startswith(('pbkdf2:', 'scrypt:'))


def password_matches(stored, given):
    if is_hashed(stored):
        return check_password_hash(stored, given)
    # Account created before hashing was added: the column still holds the plain password
    return hmac.compare_digest(stored.encode(), given.encode())


def load_orders(where='', params=(), order_by='o.created_at DESC, o.id DESC', limit=None, offset=0):
    """Orders with their items, ready for the templates.

    `where` and `order_by` are SQL fragments written in this file, never user input;
    user values go in `params`.
    """
    sql = 'SELECT o.* FROM orders o'
    if where:
        sql += ' WHERE ' + where
    sql += ' ORDER BY ' + order_by
    params = tuple(params)
    if limit is not None:
        sql += ' LIMIT %s OFFSET %s'
        params += (limit, offset)

    with db_cursor() as cursor:
        cursor.execute(sql, params)
        orders = cursor.fetchall()
        items = []
        if orders:
            marks = ', '.join(['%s'] * len(orders))
            cursor.execute(
                'SELECT order_id, item_name, quantity, unit_price, '
                '(quantity * unit_price) AS item_total '
                f'FROM order_items WHERE order_id IN ({marks}) ORDER BY id',
                [o['id'] for o in orders])
            items = cursor.fetchall()

    by_id = {}
    for o in orders:
        status = o['status']
        placed = o.get('created_at') or o.get('order_time')
        o['placed'] = placed
        o['placed_at'] = friendly_time(placed)
        o['step'] = ORDER_STEPS.index(status) if status in ORDER_STEPS else -1
        o['next_status'] = NEXT_STATUS.get(status)
        o['next_label'] = NEXT_LABEL.get(status)
        o['line_items'] = []
        by_id[o['id']] = o
    for item in items:
        by_id[item['order_id']]['line_items'].append(item)
    for o in orders:
        o['items_text'] = ', '.join(f"{i['quantity']}× {i['item_name']}" for i in o['line_items'])
    return orders


@app.template_filter('rupee')
def rupee(value):
    return '₹{:,.0f}'.format(value or 0)


@app.template_filter('status_key')
def status_key(status):
    """Short name used by the CSS and admin.js: 'Pending approval' -> 'Pending'."""
    return 'Pending' if status == 'Pending approval' else status


@app.context_processor
def inject_helpers():
    def pending_count():
        with db_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS n FROM orders WHERE status = 'Pending approval'")
            return cursor.fetchone()['n']
    return {'pending_count': pending_count}


# ---------------------------------------------------------------------------
# Shop pages
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    with db_cursor() as cursor:
        cursor.execute('SELECT * FROM menu_items ORDER BY category, id')
        menu_items = cursor.fetchall()
    return render_template('index.html', menu_items=menu_items)


@app.route('/contact')
def contact():
    user = None
    if session.get('user_id'):
        with db_cursor() as cursor:
            cursor.execute('SELECT name, phone, email FROM users WHERE id = %s', (session['user_id'],))
            user = cursor.fetchone()
    return render_template('contact.html', form=user or {})


@app.route('/processmessage', methods=['POST'])
def process_message():
    form = {
        'name': (request.form.get('name') or '').strip(),
        'phone': (request.form.get('phone') or '').strip(),
        'email': (request.form.get('email') or '').strip(),
        'message': (request.form.get('message') or '').strip(),
    }
    phone = clean_phone(form['phone'])
    error = None
    if len(form['name']) < 2:
        error = 'Enter your name.'
    elif not phone:
        error = 'Enter a 10-digit mobile number.'
    elif form['email'] and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', form['email']):
        error = "That email doesn't look right. Check it or leave it blank."
    elif not 10 <= len(form['message']) <= 600:
        error = 'Write a message of 10 to 600 characters.'
    if error:
        return render_template('contact.html', form=form, error=error)

    with db_cursor(commit=True) as cursor:
        cursor.execute('INSERT INTO messages (name, phone, email, message) VALUES (%s, %s, %s, %s)',
                       (form['name'], phone, form['email'], form['message']))
    return render_template('confirmation.html', name=form['name'])


# ---------------------------------------------------------------------------
# Login, logout, registration
# ---------------------------------------------------------------------------

@app.route('/login')
def login_form():
    return render_template('login.html', next=safe_next(request.args.get('next')))


@app.route('/processlogin', methods=['POST'])
def process_login():
    email = (request.form.get('email') or '').strip()
    password = request.form.get('password') or ''
    next_url = safe_next(request.form.get('next'))

    with db_cursor(commit=True) as cursor:
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        if user and not password_matches(user['password'], password):
            user = None
        if user and not is_hashed(user['password']):
            # First login since hashing was added: replace the plain password with its hash
            cursor.execute('UPDATE users SET password = %s WHERE id = %s',
                           (hash_password(password), user['id']))

    if not user:
        return render_template('login.html', error='Invalid email or password.', next=next_url)

    session.clear()  # never carry a previous user's role into this login
    session['user_id'] = user['id']
    session['user_name'] = user['name']
    session['user_role'] = user['role']
    session.permanent = bool(request.form.get('remember'))

    if user['role'] == 'admin':
        return redirect(next_url or url_for('admin_dashboard'))
    return redirect(next_url or url_for('my_orders'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/register')
def register_form():
    return render_template('register.html', form={}, next=safe_next(request.args.get('next')))


@app.route('/processregistration', methods=['POST'])
def register():
    form = {
        'name': (request.form.get('name') or '').strip(),
        'email': (request.form.get('email') or '').strip(),
        'phone': (request.form.get('phone') or '').strip(),
        'address': (request.form.get('address') or '').strip(),
    }
    password = request.form.get('password') or ''
    next_url = safe_next(request.form.get('next'))
    phone = clean_phone(form['phone'])

    error = None
    if not 2 <= len(form['name']) <= 80:
        error = 'Enter your name.'
    elif not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', form['email']) or len(form['email']) > 100:
        error = 'Enter a valid email, like name@example.com.'
    elif not phone:
        error = 'Enter a 10-digit mobile number.'
    elif not 10 <= len(form['address']) <= 100:
        error = 'Enter your full address (10 to 100 characters).'
    elif len(password) < 6:
        error = 'Use a password of at least 6 characters.'
    elif password != (request.form.get('confirm_password') or ''):
        error = "The two passwords don't match."
    elif not request.form.get('terms'):
        error = 'Tick the box to agree to pay cash on delivery.'

    if not error:
        with db_cursor(commit=True) as cursor:
            # email and phone must both be unique
            cursor.execute('SELECT id FROM users WHERE email = %s OR phone = %s', (form['email'], phone))
            if cursor.fetchone():
                error = 'An account with this email or phone number already exists.'
            else:
                cursor.execute(
                    'INSERT INTO users (name, email, phone, address, password, role) '
                    'VALUES (%s, %s, %s, %s, %s, %s)',
                    (form['name'], form['email'], phone, form['address'],
                     hash_password(password), 'customer'))
    if error:
        return render_template('register.html', form=form, error=error, next=next_url)
    return render_template('confirmation.html', newuser=form['name'], next=next_url)


# ---------------------------------------------------------------------------
# Customer: checkout and orders
# ---------------------------------------------------------------------------

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'GET':
        with db_cursor() as cursor:
            cursor.execute('SELECT name, phone, address FROM users WHERE id = %s', (session['user_id'],))
            user = cursor.fetchone()
        return render_template('checkout.html', form=user or {})

    form = {
        'name': (request.form.get('name') or '').strip(),
        'phone': (request.form.get('phone') or '').strip(),
        'address': (request.form.get('address') or '').strip(),
        'landmark': (request.form.get('landmark') or '').strip(),
        'notes': (request.form.get('notes') or '').strip(),
    }
    phone = clean_phone(form['phone'])

    # The cart arrives as repeated item_id / qty fields. Prices are NOT read from the browser.
    cart = {}
    try:
        for item_id, qty in zip(request.form.getlist('item_id'), request.form.getlist('qty')):
            item_id, qty = int(item_id), int(qty)
            if qty > 0:
                cart[item_id] = cart.get(item_id, 0) + qty
    except ValueError:
        cart = {}

    error = None
    if not cart:
        error = 'Your cart is empty. Add something from the menu first.'
    elif any(qty > MAX_QTY_PER_ITEM for qty in cart.values()):
        error = f'You can order at most {MAX_QTY_PER_ITEM} of one item. Call us for bigger orders.'
    elif len(form['name']) < 2:
        error = 'Enter the name for this order.'
    elif not phone:
        error = 'Enter a 10-digit mobile number.'
    elif not 10 <= len(form['address']) <= 250:
        error = 'Enter your full address so we can deliver.'
    elif len(form['landmark']) > 100 or len(form['notes']) > 255:
        error = 'Keep the landmark under 100 and the notes under 255 characters.'
    if error:
        return render_template('checkout.html', form=form, error=error)

    with db_cursor(commit=True) as cursor:
        marks = ', '.join(['%s'] * len(cart))
        cursor.execute(f'SELECT id, name, price, available FROM menu_items WHERE id IN ({marks})',
                       list(cart))
        menu = {row['id']: row for row in cursor.fetchall()}

        gone = [menu[i]['name'] if i in menu else 'An item'
                for i in cart if i not in menu or not menu[i]['available']]
        if gone:
            error = (', '.join(gone) + ' is no longer available. '
                     'Remove it from your order and try again.')
            return render_template('checkout.html', form=form, error=error)

        total = sum(menu[i]['price'] * qty for i, qty in cart.items())

        cursor.execute('SELECT COALESCE(MAX(CAST(order_number AS UNSIGNED)), 1000) + 1 AS n FROM orders')
        order_number = str(cursor.fetchone()['n'])

        cursor.execute(
            'INSERT INTO orders (order_number, user_id, customer_name, phone, address, landmark, '
            'notes, payment_method, order_time, status, total_amount) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s)',
            (order_number, session['user_id'], form['name'], phone, form['address'],
             form['landmark'] or None, form['notes'] or None, 'Cash on delivery',
             'Pending approval', total))
        order_id = cursor.lastrowid

        cursor.executemany(
            'INSERT INTO order_items (order_id, menu_item_id, item_name, quantity, unit_price) '
            'VALUES (%s, %s, %s, %s, %s)',
            [(order_id, i, menu[i]['name'], qty, menu[i]['price']) for i, qty in cart.items()])

        cursor.execute(
            'INSERT INTO order_status_history (order_id, status, note, changed_by) '
            'VALUES (%s, %s, %s, %s)',
            (order_id, 'Pending approval', 'Placed by the customer', session['user_id']))

    session['clear_cart'] = True  # order-placed.html empties the browser cart once
    return redirect(url_for('order_placed', order_id=order_id))


@app.route('/order/<int:order_id>/placed')
@login_required
def order_placed(order_id):
    orders = load_orders('o.id = %s AND o.user_id = %s', (order_id, session['user_id']))
    if not orders:
        abort(404)
    return render_template('order-placed.html', order=orders[0], step_labels=STEP_LABELS,
                           clear_cart=session.pop('clear_cart', False))


@app.route('/myorders')
@login_required
def my_orders():
    orders = load_orders('o.user_id = %s', (session['user_id'],))
    return render_template('my-orders.html', orders=orders, step_labels=STEP_LABELS)


# ---------------------------------------------------------------------------
# Admin: dashboard and users
# ---------------------------------------------------------------------------

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    pending = load_orders("o.status = 'Pending approval'", order_by='o.created_at, o.id')
    active = load_orders("o.status IN ('Accepted', 'Preparing', 'Out for delivery')",
                         order_by='o.created_at, o.id')
    with db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS n, COALESCE(SUM(total_amount), 0) AS revenue "
                       "FROM orders WHERE status = 'Delivered' AND DATE(created_at) = CURDATE()")
        today = cursor.fetchone()
    return render_template('admin/dashboard.html', pending=pending, active=active,
                           delivered_today=today['n'], revenue_today=today['revenue'],
                           today_label=date.today().strftime('%A, %d %B %Y').replace(' 0', ' '))


@app.route('/admin/users')
@admin_required
def admin_users():
    with db_cursor() as cursor:
        cursor.execute('SELECT id, name, email, phone, address, role, timestamp FROM users ORDER BY id')
        users = cursor.fetchall()
    return render_template('admin/users.html', users=users)


@app.route('/admin/messages')
@admin_required
def admin_messages():
    """Messages sent through the contact form, newest first."""
    page = max(request.args.get('page', 1, type=int), 1)
    with db_cursor() as cursor:
        cursor.execute('SELECT COUNT(*) AS n FROM messages')
        total = cursor.fetchone()['n']
        cursor.execute('SELECT id, name, phone, email, message, created_at FROM messages '
                       'ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s',
                       (MESSAGES_PER_PAGE, (page - 1) * MESSAGES_PER_PAGE))
        messages = cursor.fetchall()
    for m in messages:
        m['sent_at'] = friendly_time(m['created_at'])
    return render_template('admin/messages.html', messages=messages, total=total, page=page,
                           has_older=page * MESSAGES_PER_PAGE < total)


# ---------------------------------------------------------------------------
# Admin: orders
# ---------------------------------------------------------------------------

@app.route('/admin/orders')
@admin_required
def admin_orders():
    page = max(request.args.get('page', 1, type=int), 1)
    with db_cursor() as cursor:
        cursor.execute('SELECT COUNT(*) AS n FROM orders')
        total = cursor.fetchone()['n']
    orders = load_orders(limit=ORDERS_PER_PAGE, offset=(page - 1) * ORDERS_PER_PAGE)
    return render_template('admin/orders.html', orders=orders, total=total, page=page,
                           has_older=page * ORDERS_PER_PAGE < total)


@app.route('/admin/orders/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    orders = load_orders('o.id = %s', (order_id,))
    if not orders:
        abort(404)
    with db_cursor() as cursor:
        cursor.execute(
            'SELECT h.status, h.note, h.changed_at, u.name AS changed_by_name '
            'FROM order_status_history h LEFT JOIN users u ON u.id = h.changed_by '
            'WHERE h.order_id = %s ORDER BY h.changed_at DESC, h.id DESC', (order_id,))
        history = cursor.fetchall()
    for h in history:
        h['when'] = friendly_time(h['changed_at'])
    return render_template('admin/order-detail.html', order=orders[0], history=history,
                           steps=ORDER_STEPS)


@app.route('/admin/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def admin_order_status(order_id):
    new_status = request.form.get('status') or ''
    reason = (request.form.get('reason') or '').strip()

    with db_cursor(commit=True) as cursor:
        cursor.execute('SELECT id, order_number, status FROM orders WHERE id = %s FOR UPDATE', (order_id,))
        order = cursor.fetchone()
        if not order:
            abort(404)

        error = None
        if new_status == 'Rejected':
            if order['status'] != 'Pending approval':
                error = 'Only an order that is waiting for approval can be rejected.'
            elif not 5 <= len(reason) <= 200:
                error = 'Give the customer a reason (5 to 200 characters).'
        elif NEXT_STATUS.get(order['status']) != new_status:
            error = (f"Order #{order['order_number']} is {order['status']}; "
                     f"it cannot be changed to {new_status or 'that status'}.")

        if not error:
            rejected = new_status == 'Rejected'
            cursor.execute('UPDATE orders SET status = %s, reject_reason = %s WHERE id = %s',
                           (new_status, reason if rejected else None, order_id))
            cursor.execute(
                'INSERT INTO order_status_history (order_id, status, note, changed_by) '
                'VALUES (%s, %s, %s, %s)',
                (order_id, new_status, reason if rejected else None, session['user_id']))

    if error:
        flash(error, 'error')
    else:
        flash(f"Order #{order['order_number']}: {new_status}", 'ok')
    return redirect_back(url_for('admin_order_detail', order_id=order_id))


# ---------------------------------------------------------------------------
# Admin: menu
# ---------------------------------------------------------------------------

def read_menu_form():
    """Read and check the add/edit item form. Returns (item, error)."""
    item = {
        'name': (request.form.get('name') or '').strip(),
        'description': (request.form.get('description') or '').strip(),
        'category': request.form.get('category') or '',
        'type': request.form.get('type') or 'veg',
        'price': request.form.get('price', type=int),
        'tag': request.form.get('tag') or None,
        'available': 1 if request.form.get('available') else 0,
    }
    error = None
    if not 2 <= len(item['name']) <= 60:
        error = 'Give the item a name (2 to 60 characters).'
    elif not 1 <= len(item['description']) <= 120:
        error = 'Add a short description (up to 120 characters).'
    elif item['category'] not in MENU_CATEGORIES:
        error = 'Choose a category.'
    elif item['type'] not in MENU_TYPES:
        error = 'Choose veg or non-veg.'
    elif item['price'] is None or not 1 <= item['price'] <= 5000:
        error = 'Enter a price between ₹1 and ₹5,000.'
    elif item['tag'] and item['tag'] not in MENU_TAGS:
        error = 'Choose a label from the list.'
    return item, error


def menu_form_page(item, action, error=None):
    return render_template('admin/menu-form.html', item=item, action=action, error=error,
                           categories=MENU_CATEGORIES, tags=MENU_TAGS)


@app.route('/admin/menu')
@admin_required
def admin_menu():
    with db_cursor() as cursor:
        cursor.execute('SELECT * FROM menu_items ORDER BY category, id')
        menu_items = cursor.fetchall()
    return render_template('admin/menu.html', menu_items=menu_items, categories=MENU_CATEGORIES)


@app.route('/admin/menu/new', methods=['GET', 'POST'])
@admin_required
def admin_menu_new():
    action = url_for('admin_menu_new')
    if request.method == 'GET':
        return menu_form_page(None, action)

    item, error = read_menu_form()
    if not error:
        try:
            with db_cursor(commit=True) as cursor:
                cursor.execute(
                    'INSERT INTO menu_items (name, description, category, type, price, tag, available) '
                    'VALUES (%(name)s, %(description)s, %(category)s, %(type)s, %(price)s, %(tag)s, %(available)s)',
                    item)
        except mysql.connector.IntegrityError:
            error = 'There is already an item with this name.'
    if error:
        return menu_form_page(item, action, error)
    flash(f"{item['name']} added to the menu", 'ok')
    return redirect(url_for('admin_menu'))


@app.route('/admin/menu/<int:item_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_menu_edit(item_id):
    action = url_for('admin_menu_edit', item_id=item_id)
    with db_cursor() as cursor:
        cursor.execute('SELECT * FROM menu_items WHERE id = %s', (item_id,))
        existing = cursor.fetchone()
    if not existing:
        abort(404)
    if request.method == 'GET':
        return menu_form_page(existing, action)

    item, error = read_menu_form()
    item['id'] = item_id
    if not error:
        try:
            with db_cursor(commit=True) as cursor:
                cursor.execute(
                    'UPDATE menu_items SET name = %(name)s, description = %(description)s, '
                    'category = %(category)s, type = %(type)s, price = %(price)s, tag = %(tag)s, '
                    'available = %(available)s WHERE id = %(id)s',
                    item)
        except mysql.connector.IntegrityError:
            error = 'There is already an item with this name.'
    if error:
        return menu_form_page(item, action, error)
    flash(f"{item['name']} saved", 'ok')
    return redirect(url_for('admin_menu'))


@app.route('/admin/menu/<int:item_id>/availability', methods=['POST'])
@admin_required
def admin_menu_availability(item_id):
    available = 1 if request.form.get('available') else 0
    with db_cursor(commit=True) as cursor:
        cursor.execute('SELECT name FROM menu_items WHERE id = %s', (item_id,))
        item = cursor.fetchone()
        if not item:
            abort(404)
        cursor.execute('UPDATE menu_items SET available = %s WHERE id = %s', (available, item_id))
    flash(f"{item['name']} is {'back on the menu' if available else 'marked sold out'}", 'ok')
    return redirect(url_for('admin_menu'))


@app.route('/admin/menu/<int:item_id>/delete', methods=['POST'])
@admin_required
def admin_menu_delete(item_id):
    with db_cursor(commit=True) as cursor:
        cursor.execute('SELECT name FROM menu_items WHERE id = %s', (item_id,))
        item = cursor.fetchone()
        if not item:
            abort(404)
        # Past orders keep the item's name and price; only their link to the menu is cleared.
        cursor.execute('DELETE FROM menu_items WHERE id = %s', (item_id,))
    flash(f"{item['name']} deleted", 'ok')
    return redirect(url_for('admin_menu'))


# ---------------------------------------------------------------------------
# Admin: revenue report
# ---------------------------------------------------------------------------

def parse_day(text):
    try:
        return datetime.strptime(text or '', '%Y-%m-%d').date()
    except ValueError:
        return None


@app.route('/admin/revenue')
@admin_required
def admin_revenue():
    today = date.today()
    start = parse_day(request.args.get('from')) or today.replace(day=1)
    end = parse_day(request.args.get('to')) or today
    if start > end:
        flash('The start date was after the end date, so the two were swapped.', 'error')
        start, end = end, start

    # Only delivered orders count as revenue
    orders = load_orders("o.status = 'Delivered' AND DATE(o.created_at) BETWEEN %s AND %s",
                         (start, end))

    by_day, by_item = {}, {}
    for o in orders:
        day = o['placed'].date()
        o['day'] = day
        row = by_day.setdefault(day, {'day': day, 'orders': 0, 'revenue': 0})
        row['orders'] += 1
        row['revenue'] += o['total_amount']
        for i in o['line_items']:
            item = by_item.setdefault(i['item_name'], {'name': i['item_name'], 'qty': 0, 'revenue': 0})
            item['qty'] += i['quantity']
            item['revenue'] += i['item_total']

    revenue = sum(o['total_amount'] for o in orders)
    return render_template(
        'admin/revenue.html', orders=orders, start=start, end=end, today=today,
        revenue=revenue, average=revenue / len(orders) if orders else 0,
        daily=sorted(by_day.values(), key=lambda r: r['day'], reverse=True),
        items=sorted(by_item.values(), key=lambda r: r['revenue'], reverse=True))


if __name__ == '__main__':
    app.run(debug=True)
