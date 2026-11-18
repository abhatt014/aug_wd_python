"""web: the pages people see. Holds the login session and renders the templates.

It has no database access: every read and write goes to one of the API services
through api.py (user-service, menu-service, order-service, message-service).
"""
import os
from datetime import date, datetime, timedelta
from functools import wraps
from urllib.parse import urlparse

from flask import (Flask, flash, redirect, render_template, request, session,
                   url_for)

import api
from api import ServiceError, ServiceUnavailable

# Labels shown under the order tracker, one per step
STEP_LABELS = ['Waiting for approval', 'Accepted', 'Preparing', 'Out for delivery', 'Delivered']
ORDER_STEPS = ['Pending approval', 'Accepted', 'Preparing', 'Out for delivery', 'Delivered']

app = Flask(__name__)
# Set SECRET_KEY in the environment for anything but local use.
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


def with_times(orders):
    for o in orders:
        o['placed_at'] = friendly_time(o.get('placed'))
    return orders


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


def form_fields(*names):
    return {n: (request.form.get(n) or '').strip() for n in names}


def current_user():
    return api.get('users', f"/users/{session['user_id']}")


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
        try:
            return api.get('orders', '/orders/pending-count')['count']
        except (ServiceError, ServiceUnavailable):
            return 0
    return {'pending_count': pending_count}


@app.errorhandler(ServiceUnavailable)
def service_unavailable(e):
    app.logger.error('%s', e)
    return ('<h1>Sorry, something is down</h1>'
            '<p>Part of the shop is not responding right now. Try again in a minute.</p>'
            f'<p><a href="{url_for("index")}">Back to the menu</a></p>'), 503


# ---------------------------------------------------------------------------
# Shop pages
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    menu_items = api.get('menu', '/items')['items']
    return render_template('index.html', menu_items=menu_items)


@app.route('/contact')
def contact():
    user = current_user() if session.get('user_id') else None
    return render_template('contact.html', form=user or {})


@app.route('/processmessage', methods=['POST'])
def process_message():
    form = form_fields('name', 'phone', 'email', 'message')
    try:
        api.post('messages', '/messages', form)
    except ServiceError as e:
        return render_template('contact.html', form=form, error=e.message)
    return render_template('confirmation.html', name=form['name'])


# ---------------------------------------------------------------------------
# Login, logout, registration
# ---------------------------------------------------------------------------

@app.route('/login')
def login_form():
    return render_template('login.html', next=safe_next(request.args.get('next')))


@app.route('/processlogin', methods=['POST'])
def process_login():
    next_url = safe_next(request.form.get('next'))
    try:
        user = api.post('users', '/auth/login', {
            'email': (request.form.get('email') or '').strip(),
            'password': request.form.get('password') or '',
        })
    except ServiceError as e:
        return render_template('login.html', error=e.message, next=next_url)

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
    form = form_fields('name', 'email', 'phone', 'address')
    next_url = safe_next(request.form.get('next'))
    try:
        api.post('users', '/users', dict(
            form,
            password=request.form.get('password') or '',
            confirm_password=request.form.get('confirm_password') or '',
            terms=bool(request.form.get('terms'))))
    except ServiceError as e:
        return render_template('register.html', form=form, error=e.message, next=next_url)
    return render_template('confirmation.html', newuser=form['name'], next=next_url)


# ---------------------------------------------------------------------------
# Customer: checkout and orders
# ---------------------------------------------------------------------------

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'GET':
        return render_template('checkout.html', form=current_user())

    form = form_fields('name', 'phone', 'address', 'landmark', 'notes')
    # The cart arrives as repeated item_id / qty fields. Prices are NOT read from the browser:
    # order-service gets them from menu-service.
    cart = []
    try:
        for item_id, qty in zip(request.form.getlist('item_id'), request.form.getlist('qty')):
            cart.append({'item_id': int(item_id), 'qty': int(qty)})
    except ValueError:
        cart = []

    try:
        order = api.post('orders', '/orders', dict(form, user_id=session['user_id'], cart=cart))
    except ServiceError as e:
        return render_template('checkout.html', form=form, error=e.message)

    session['clear_cart'] = True  # order-placed.html empties the browser cart once
    return redirect(url_for('order_placed', order_id=order['id']))


@app.route('/order/<int:order_id>/placed')
@login_required
def order_placed(order_id):
    order = api.get('orders', f'/orders/{order_id}', user_id=session['user_id'])
    return render_template('order-placed.html', order=with_times([order])[0],
                           step_labels=STEP_LABELS, clear_cart=session.pop('clear_cart', False))


@app.route('/myorders')
@login_required
def my_orders():
    orders = api.get('orders', '/orders', user_id=session['user_id'])['orders']
    return render_template('my-orders.html', orders=with_times(orders), step_labels=STEP_LABELS)


# ---------------------------------------------------------------------------
# Admin: dashboard, users, messages
# ---------------------------------------------------------------------------

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    pending = api.get('orders', '/orders', status='Pending approval', sort='oldest')['orders']
    active = api.get('orders', '/orders', status='Accepted,Preparing,Out for delivery',
                     sort='oldest')['orders']
    today = api.get('orders', '/orders/stats/today')
    return render_template('admin/dashboard.html', pending=with_times(pending),
                           active=with_times(active),
                           delivered_today=today['delivered'], revenue_today=today['revenue'],
                           today_label=date.today().strftime('%A, %d %B %Y').replace(' 0', ' '))


@app.route('/admin/users')
@admin_required
def admin_users():
    return render_template('admin/users.html', users=api.get('users', '/users')['users'])


@app.route('/admin/messages')
@admin_required
def admin_messages():
    """Messages sent through the contact form, newest first."""
    data = api.get('messages', '/messages', page=max(request.args.get('page', 1, type=int), 1))
    for m in data['messages']:
        m['sent_at'] = friendly_time(m['created_at'])
    return render_template('admin/messages.html', messages=data['messages'], total=data['total'],
                           page=data['page'], has_older=data['has_older'])


# ---------------------------------------------------------------------------
# Admin: orders
# ---------------------------------------------------------------------------

@app.route('/admin/orders')
@admin_required
def admin_orders():
    data = api.get('orders', '/orders', page=max(request.args.get('page', 1, type=int), 1))
    return render_template('admin/orders.html', orders=with_times(data['orders']),
                           total=data['total'], page=data['page'], has_older=data['has_older'])


@app.route('/admin/orders/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    order = with_times([api.get('orders', f'/orders/{order_id}')])[0]
    history = order.pop('history')
    # The history only holds user ids; user-service knows their names.
    ids = sorted({h['changed_by'] for h in history if h['changed_by']})
    names = {}
    if ids:
        names = {u['id']: u['name']
                 for u in api.get('users', '/users', ids=','.join(map(str, ids)))['users']}
    for h in history:
        h['changed_by_name'] = names.get(h['changed_by'])
        h['when'] = friendly_time(h['changed_at'])
    return render_template('admin/order-detail.html', order=order, history=history,
                           steps=ORDER_STEPS)


@app.route('/admin/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def admin_order_status(order_id):
    new_status = request.form.get('status') or ''
    try:
        result = api.post('orders', f'/orders/{order_id}/status', {
            'status': new_status,
            'reason': (request.form.get('reason') or '').strip(),
            'changed_by': session['user_id'],
        })
        flash(f"Order #{result['order_number']}: {new_status}", 'ok')
    except ServiceError as e:
        flash(e.message, 'error')
    return redirect_back(url_for('admin_order_detail', order_id=order_id))


# ---------------------------------------------------------------------------
# Admin: menu
# ---------------------------------------------------------------------------

def read_menu_form():
    """The add/edit item form as sent to menu-service (which checks it)."""
    return {
        'name': (request.form.get('name') or '').strip(),
        'description': (request.form.get('description') or '').strip(),
        'category': request.form.get('category') or '',
        'type': request.form.get('type') or 'veg',
        'price': request.form.get('price', type=int),
        'tag': request.form.get('tag') or None,
        'available': 1 if request.form.get('available') else 0,
    }


def menu_form_page(item, action, error=None):
    meta = api.get('menu', '/meta')
    return render_template('admin/menu-form.html', item=item, action=action, error=error,
                           categories=meta['categories'], tags=meta['tags'])


@app.route('/admin/menu')
@admin_required
def admin_menu():
    return render_template('admin/menu.html', menu_items=api.get('menu', '/items')['items'],
                           categories=api.get('menu', '/meta')['categories'])


@app.route('/admin/menu/new', methods=['GET', 'POST'])
@admin_required
def admin_menu_new():
    action = url_for('admin_menu_new')
    if request.method == 'GET':
        return menu_form_page(None, action)

    item = read_menu_form()
    try:
        api.post('menu', '/items', item)
    except ServiceError as e:
        return menu_form_page(item, action, e.message)
    flash(f"{item['name']} added to the menu", 'ok')
    return redirect(url_for('admin_menu'))


@app.route('/admin/menu/<int:item_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_menu_edit(item_id):
    action = url_for('admin_menu_edit', item_id=item_id)
    if request.method == 'GET':
        return menu_form_page(api.get('menu', f'/items/{item_id}'), action)

    item = read_menu_form()
    item['id'] = item_id
    try:
        api.put('menu', f'/items/{item_id}', item)
    except ServiceError as e:
        return menu_form_page(item, action, e.message)
    flash(f"{item['name']} saved", 'ok')
    return redirect(url_for('admin_menu'))


@app.route('/admin/menu/<int:item_id>/availability', methods=['POST'])
@admin_required
def admin_menu_availability(item_id):
    available = bool(request.form.get('available'))
    item = api.patch('menu', f'/items/{item_id}/availability', {'available': available})
    flash(f"{item['name']} is {'back on the menu' if available else 'marked sold out'}", 'ok')
    return redirect(url_for('admin_menu'))


@app.route('/admin/menu/<int:item_id>/delete', methods=['POST'])
@admin_required
def admin_menu_delete(item_id):
    item = api.delete('menu', f'/items/{item_id}')
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

    report = api.get('orders', '/reports/revenue', **{'from': start.isoformat(), 'to': end.isoformat()})
    return render_template(
        'admin/revenue.html', orders=report['orders'], start=start, end=end, today=today,
        revenue=report['revenue'], average=report['average'],
        daily=report['daily'], items=report['items'])


if __name__ == '__main__':
    app.run(debug=True)
