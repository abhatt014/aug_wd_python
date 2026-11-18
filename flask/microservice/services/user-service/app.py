"""user-service: owns the `users` table. Login check, registration, user lookups."""
import hmac
import re

from flask import abort, request
from werkzeug.security import check_password_hash, generate_password_hash

from common.db import db_cursor
from common.service import EMAIL_RE, clean_phone, create_service, text

app = create_service(__name__)

PUBLIC_FIELDS = 'id, name, email, phone, address, role, timestamp'


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


@app.post('/auth/login')
def login():
    """Body: {email, password}. 200 with the user, or 401."""
    data = request.get_json(silent=True) or {}
    email = text(data, 'email')
    password = str(data.get('password') or '')

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
        return {'error': 'Invalid email or password.'}, 401
    user.pop('password')
    return user


@app.post('/users')
def register():
    """Body: the registration form. 201 with the new user, 400 or 409 with {error}."""
    data = request.get_json(silent=True) or {}
    form = {k: text(data, k) for k in ('name', 'email', 'phone', 'address')}
    password = str(data.get('password') or '')
    phone = clean_phone(form['phone'])

    error = None
    if not 2 <= len(form['name']) <= 80:
        error = 'Enter your name.'
    elif not re.fullmatch(EMAIL_RE, form['email']) or len(form['email']) > 100:
        error = 'Enter a valid email, like name@example.com.'
    elif not phone:
        error = 'Enter a 10-digit mobile number.'
    elif not 10 <= len(form['address']) <= 100:
        error = 'Enter your full address (10 to 100 characters).'
    elif len(password) < 6:
        error = 'Use a password of at least 6 characters.'
    elif password != str(data.get('confirm_password') or ''):
        error = "The two passwords don't match."
    elif not data.get('terms'):
        error = 'Tick the box to agree to pay cash on delivery.'
    if error:
        return {'error': error}, 400

    with db_cursor(commit=True) as cursor:
        # email and phone must both be unique
        cursor.execute('SELECT id FROM users WHERE email = %s OR phone = %s', (form['email'], phone))
        if cursor.fetchone():
            return {'error': 'An account with this email or phone number already exists.'}, 409
        cursor.execute(
            'INSERT INTO users (name, email, phone, address, password, role) '
            'VALUES (%s, %s, %s, %s, %s, %s)',
            (form['name'], form['email'], phone, form['address'], hash_password(password), 'customer'))
        user_id = cursor.lastrowid
    return {'id': user_id, 'name': form['name'], 'email': form['email'], 'role': 'customer'}, 201


@app.get('/users')
def list_users():
    """All users, or only ?ids=1,3,7."""
    sql = f'SELECT {PUBLIC_FIELDS} FROM users'
    params = []
    if request.args.get('ids'):
        try:
            params = [int(i) for i in request.args['ids'].split(',') if i]
        except ValueError:
            abort(400, 'ids must be numbers separated by commas.')
        if not params:
            return {'users': []}
        sql += ' WHERE id IN (' + ', '.join(['%s'] * len(params)) + ')'
    sql += ' ORDER BY id'
    with db_cursor() as cursor:
        cursor.execute(sql, params)
        return {'users': cursor.fetchall()}


@app.get('/users/<int:user_id>')
def get_user(user_id):
    with db_cursor() as cursor:
        cursor.execute(f'SELECT {PUBLIC_FIELDS} FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
    if not user:
        abort(404, 'No such user.')
    return user
