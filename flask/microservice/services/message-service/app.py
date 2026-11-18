"""message-service: owns the `messages` table (the contact form)."""
import re

from flask import request

from common.db import db_cursor
from common.service import EMAIL_RE, clean_phone, create_service, text

app = create_service(__name__)

MESSAGES_PER_PAGE = 25


@app.post('/messages')
def create_message():
    data = request.get_json(silent=True) or {}
    form = {k: text(data, k) for k in ('name', 'phone', 'email', 'message')}
    phone = clean_phone(form['phone'])
    error = None
    if len(form['name']) < 2:
        error = 'Enter your name.'
    elif not phone:
        error = 'Enter a 10-digit mobile number.'
    elif form['email'] and not re.fullmatch(EMAIL_RE, form['email']):
        error = "That email doesn't look right. Check it or leave it blank."
    elif not 10 <= len(form['message']) <= 600:
        error = 'Write a message of 10 to 600 characters.'
    if error:
        return {'error': error}, 400

    with db_cursor(commit=True) as cursor:
        cursor.execute('INSERT INTO messages (name, phone, email, message) VALUES (%s, %s, %s, %s)',
                       (form['name'], phone, form['email'], form['message']))
        message_id = cursor.lastrowid
    return {'id': message_id, 'name': form['name']}, 201


@app.get('/messages')
def list_messages():
    """Newest first, MESSAGES_PER_PAGE per ?page=."""
    page = max(request.args.get('page', 1, type=int), 1)
    with db_cursor() as cursor:
        cursor.execute('SELECT COUNT(*) AS n FROM messages')
        total = cursor.fetchone()['n']
        cursor.execute('SELECT id, name, phone, email, message, created_at FROM messages '
                       'ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s',
                       (MESSAGES_PER_PAGE, (page - 1) * MESSAGES_PER_PAGE))
        messages = cursor.fetchall()
    return {'messages': messages, 'total': total, 'page': page,
            'has_older': page * MESSAGES_PER_PAGE < total}
