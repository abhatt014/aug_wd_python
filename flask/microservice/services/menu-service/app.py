"""menu-service: owns the `menu_items` table. Menu listing and admin CRUD."""
import mysql.connector
from flask import abort, request

from common.db import db_cursor
from common.service import create_service, text

app = create_service(__name__)

MENU_CATEGORIES = {'pizza': 'Pizza', 'sides': 'Sides & drinks'}
MENU_TYPES = ('veg', 'nonveg')
MENU_TAGS = ('Bestseller', 'Spicy', 'New')


def read_item(data):
    """Read and check an add/edit body. Returns (item, error)."""
    try:
        price = int(data.get('price'))
    except (TypeError, ValueError):
        price = None
    item = {
        'name': text(data, 'name'),
        'description': text(data, 'description'),
        'category': text(data, 'category'),
        'type': text(data, 'type') or 'veg',
        'price': price,
        'tag': text(data, 'tag') or None,
        'available': 1 if data.get('available') else 0,
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


def find_item(cursor, item_id):
    cursor.execute('SELECT * FROM menu_items WHERE id = %s', (item_id,))
    item = cursor.fetchone()
    if not item:
        abort(404, 'No such menu item.')
    return item


@app.get('/meta')
def meta():
    return {'categories': MENU_CATEGORIES, 'types': MENU_TYPES, 'tags': MENU_TAGS}


@app.get('/items')
def list_items():
    """The whole menu, or only ?ids=1,4,9 (used by order-service to price a cart)."""
    sql = 'SELECT * FROM menu_items'
    params = []
    if request.args.get('ids'):
        try:
            params = [int(i) for i in request.args['ids'].split(',') if i]
        except ValueError:
            abort(400, 'ids must be numbers separated by commas.')
        if not params:
            return {'items': []}
        sql += ' WHERE id IN (' + ', '.join(['%s'] * len(params)) + ')'
    sql += ' ORDER BY category, id'
    with db_cursor() as cursor:
        cursor.execute(sql, params)
        return {'items': cursor.fetchall()}


@app.get('/items/<int:item_id>')
def get_item(item_id):
    with db_cursor() as cursor:
        return find_item(cursor, item_id)


@app.post('/items')
def create_item():
    item, error = read_item(request.get_json(silent=True) or {})
    if error:
        return {'error': error}, 400
    try:
        with db_cursor(commit=True) as cursor:
            cursor.execute(
                'INSERT INTO menu_items (name, description, category, type, price, tag, available) '
                'VALUES (%(name)s, %(description)s, %(category)s, %(type)s, %(price)s, %(tag)s, %(available)s)',
                item)
            item['id'] = cursor.lastrowid
    except mysql.connector.IntegrityError:
        return {'error': 'There is already an item with this name.'}, 409
    return item, 201


@app.put('/items/<int:item_id>')
def update_item(item_id):
    item, error = read_item(request.get_json(silent=True) or {})
    item['id'] = item_id
    with db_cursor() as cursor:
        find_item(cursor, item_id)
    if error:
        return {'error': error}, 400
    try:
        with db_cursor(commit=True) as cursor:
            cursor.execute(
                'UPDATE menu_items SET name = %(name)s, description = %(description)s, '
                'category = %(category)s, type = %(type)s, price = %(price)s, tag = %(tag)s, '
                'available = %(available)s WHERE id = %(id)s',
                item)
    except mysql.connector.IntegrityError:
        return {'error': 'There is already an item with this name.'}, 409
    return item


@app.patch('/items/<int:item_id>/availability')
def set_availability(item_id):
    available = 1 if (request.get_json(silent=True) or {}).get('available') else 0
    with db_cursor(commit=True) as cursor:
        item = find_item(cursor, item_id)
        cursor.execute('UPDATE menu_items SET available = %s WHERE id = %s', (available, item_id))
    return {'id': item_id, 'name': item['name'], 'available': available}


@app.delete('/items/<int:item_id>')
def delete_item(item_id):
    with db_cursor(commit=True) as cursor:
        item = find_item(cursor, item_id)
        # Past orders keep the item's name and price; the database clears only their link to the menu.
        cursor.execute('DELETE FROM menu_items WHERE id = %s', (item_id,))
    return {'id': item_id, 'name': item['name']}
