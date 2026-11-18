"""Pieces every JSON API service needs: the Flask app, JSON encoding, errors, /health."""
import re
from datetime import date, datetime
from decimal import Decimal

from flask import Flask, jsonify
from flask.json.provider import DefaultJSONProvider
from werkzeug.exceptions import HTTPException

from common.db import db_cursor

EMAIL_RE = r'[^@\s]+@[^@\s]+\.[^@\s]+'


class ApiJSONProvider(DefaultJSONProvider):
    """Dates as ISO strings, money as plain numbers, keys kept in the order they were built."""
    sort_keys = False

    @staticmethod
    def default(o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, Decimal):
            return int(o) if o == o.to_integral_value() else float(o)
        return DefaultJSONProvider.default(o)


def create_service(name):
    app = Flask(name)
    app.json = ApiJSONProvider(app)

    @app.errorhandler(HTTPException)
    def http_error(e):
        return jsonify(error=e.description), e.code

    @app.get('/health')
    def health():
        with db_cursor() as cursor:
            cursor.execute('SELECT 1 AS ok')
            cursor.fetchone()
        return {'status': 'ok'}

    return app


def clean_phone(raw):
    """'+91 98765 43210' -> '9876543210'. Returns None if it is not an Indian mobile number."""
    digits = re.sub(r'[\s\-]', '', raw or '')
    if digits.startswith('+91'):
        digits = digits[3:]
    return digits if re.fullmatch(r'[6-9]\d{9}', digits) else None


def text(data, key):
    """A stripped string field from a JSON body ('' when missing)."""
    return str(data.get(key) or '').strip()
