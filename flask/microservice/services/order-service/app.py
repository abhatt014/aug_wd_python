"""order-service: owns `orders`, `order_items` and `order_status_history`.

Placing an order asks menu-service for current prices; it never reads `menu_items` itself.
"""
import os
from datetime import datetime

import requests
from flask import abort, request

from common.db import db_cursor
from common.service import clean_phone, create_service, text

app = create_service(__name__)

MENU_SERVICE_URL = os.environ.get('MENU_SERVICE_URL', 'http://localhost:5002')

# DB status values, in order
ORDER_STEPS = ['Pending approval', 'Accepted', 'Preparing', 'Out for delivery', 'Delivered']

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

ORDERS_PER_PAGE = 25
MAX_QTY_PER_ITEM = 20
SORTS = {'newest': 'o.created_at DESC, o.id DESC', 'oldest': 'o.created_at, o.id'}


def load_orders(where='', params=(), order_by=SORTS['newest'], limit=None, offset=0):
    """Orders with their items.

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
        o['placed'] = o.get('created_at') or o.get('order_time')
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


def parse_day(value):
    try:
        return datetime.strptime(value or '', '%Y-%m-%d').date()
    except ValueError:
        abort(400, 'Dates must look like 2026-11-17.')


# ---------------------------------------------------------------------------
# Reading orders
# ---------------------------------------------------------------------------

@app.get('/orders')
def list_orders():
    """Filters: ?user_id=, ?status=A,B (comma separated), ?sort=newest|oldest, ?page= (25 per page)."""
    where, params = [], []
    if request.args.get('user_id'):
        where.append('o.user_id = %s')
        params.append(request.args.get('user_id', type=int))
    if request.args.get('status'):
        statuses = request.args['status'].split(',')
        where.append('o.status IN (' + ', '.join(['%s'] * len(statuses)) + ')')
        params += statuses
    where_sql = ' AND '.join(where)
    order_by = SORTS.get(request.args.get('sort'), SORTS['newest'])

    page = request.args.get('page', type=int)
    if page is None:
        orders = load_orders(where_sql, params, order_by)
        return {'orders': orders, 'total': len(orders)}

    page = max(page, 1)
    with db_cursor() as cursor:
        cursor.execute('SELECT COUNT(*) AS n FROM orders o' + (' WHERE ' + where_sql if where_sql else ''),
                       params)
        total = cursor.fetchone()['n']
    orders = load_orders(where_sql, params, order_by,
                         limit=ORDERS_PER_PAGE, offset=(page - 1) * ORDERS_PER_PAGE)
    return {'orders': orders, 'total': total, 'page': page,
            'has_older': page * ORDERS_PER_PAGE < total}


@app.get('/orders/<int:order_id>')
def get_order(order_id):
    """One order with its status history. ?user_id= limits it to that customer's own orders."""
    where, params = 'o.id = %s', [order_id]
    if request.args.get('user_id'):
        where += ' AND o.user_id = %s'
        params.append(request.args.get('user_id', type=int))
    orders = load_orders(where, params)
    if not orders:
        abort(404, 'No such order.')
    with db_cursor() as cursor:
        cursor.execute(
            'SELECT status, note, changed_by, changed_at FROM order_status_history '
            'WHERE order_id = %s ORDER BY changed_at DESC, id DESC', (order_id,))
        orders[0]['history'] = cursor.fetchall()
    return orders[0]


@app.get('/orders/pending-count')
def pending_count():
    with db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS n FROM orders WHERE status = 'Pending approval'")
        return {'count': cursor.fetchone()['n']}


@app.get('/orders/stats/today')
def stats_today():
    with db_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS n, COALESCE(SUM(total_amount), 0) AS revenue "
                       "FROM orders WHERE status = 'Delivered' AND DATE(created_at) = CURDATE()")
        row = cursor.fetchone()
    return {'delivered': row['n'], 'revenue': row['revenue']}


# ---------------------------------------------------------------------------
# Placing an order and moving it along
# ---------------------------------------------------------------------------

@app.post('/orders')
def place_order():
    """Body: {user_id, name, phone, address, landmark, notes, cart: [{item_id, qty}]}.

    Prices are never taken from the caller: menu-service is asked for them.
    """
    data = request.get_json(silent=True) or {}
    form = {k: text(data, k) for k in ('name', 'phone', 'address', 'landmark', 'notes')}
    phone = clean_phone(form['phone'])
    user_id = data.get('user_id')

    cart = {}
    try:
        for line in data.get('cart') or []:
            item_id, qty = int(line['item_id']), int(line['qty'])
            if qty > 0:
                cart[item_id] = cart.get(item_id, 0) + qty
    except (KeyError, TypeError, ValueError):
        cart = {}

    error = None
    if not isinstance(user_id, int):
        error = 'user_id is missing.'
    elif not cart:
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
        return {'error': error}, 400

    try:
        resp = requests.get(f'{MENU_SERVICE_URL}/items',
                            params={'ids': ','.join(map(str, cart))}, timeout=5)
        resp.raise_for_status()
    except requests.RequestException:
        return {'error': 'We could not check the menu just now. Try again in a minute.'}, 503
    menu = {row['id']: row for row in resp.json()['items']}

    gone = [menu[i]['name'] if i in menu else 'An item'
            for i in cart if i not in menu or not menu[i]['available']]
    if gone:
        return {'error': ', '.join(gone) + ' is no longer available. '
                         'Remove it from your order and try again.'}, 400

    total = sum(menu[i]['price'] * qty for i, qty in cart.items())

    with db_cursor(commit=True) as cursor:
        cursor.execute('SELECT COALESCE(MAX(CAST(order_number AS UNSIGNED)), 1000) + 1 AS n FROM orders')
        order_number = str(cursor.fetchone()['n'])

        cursor.execute(
            'INSERT INTO orders (order_number, user_id, customer_name, phone, address, landmark, '
            'notes, payment_method, order_time, status, total_amount) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s)',
            (order_number, user_id, form['name'], phone, form['address'],
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
            (order_id, 'Pending approval', 'Placed by the customer', user_id))

    return {'id': order_id, 'order_number': order_number, 'total_amount': total}, 201


@app.post('/orders/<int:order_id>/status')
def change_status(order_id):
    """Body: {status, reason, changed_by}. Only the next step is allowed; reject needs a reason."""
    data = request.get_json(silent=True) or {}
    new_status = text(data, 'status')
    reason = text(data, 'reason')

    with db_cursor(commit=True) as cursor:
        cursor.execute('SELECT id, order_number, status FROM orders WHERE id = %s FOR UPDATE', (order_id,))
        order = cursor.fetchone()
        if not order:
            abort(404, 'No such order.')

        error = None
        if new_status == 'Rejected':
            if order['status'] != 'Pending approval':
                error = 'Only an order that is waiting for approval can be rejected.'
            elif not 5 <= len(reason) <= 200:
                error = 'Give the customer a reason (5 to 200 characters).'
        elif NEXT_STATUS.get(order['status']) != new_status:
            error = (f"Order #{order['order_number']} is {order['status']}; "
                     f"it cannot be changed to {new_status or 'that status'}.")
        if error:
            return {'error': error}, 409

        rejected = new_status == 'Rejected'
        cursor.execute('UPDATE orders SET status = %s, reject_reason = %s WHERE id = %s',
                       (new_status, reason if rejected else None, order_id))
        cursor.execute(
            'INSERT INTO order_status_history (order_id, status, note, changed_by) '
            'VALUES (%s, %s, %s, %s)',
            (order_id, new_status, reason if rejected else None, data.get('changed_by')))

    return {'id': order_id, 'order_number': order['order_number'], 'status': new_status}


# ---------------------------------------------------------------------------
# Revenue report
# ---------------------------------------------------------------------------

@app.get('/reports/revenue')
def revenue_report():
    """?from=YYYY-MM-DD&to=YYYY-MM-DD. An order counts on the day it was placed, once delivered."""
    start, end = parse_day(request.args.get('from')), parse_day(request.args.get('to'))
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
    return {
        'orders': orders,
        'revenue': revenue,
        'average': revenue / len(orders) if orders else 0,
        'daily': sorted(by_day.values(), key=lambda r: r['day'], reverse=True),
        'items': sorted(by_item.values(), key=lambda r: r['revenue'], reverse=True),
    }
