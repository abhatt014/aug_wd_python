"""Small client the web app uses to talk to the four API services.

Responses are turned back into what the templates expect: date fields become
`datetime` / `date` objects again.
"""
import os
from datetime import date, datetime

import requests
from flask import abort

SERVICES = {
    'users': os.environ.get('USER_SERVICE_URL', 'http://localhost:5001'),
    'menu': os.environ.get('MENU_SERVICE_URL', 'http://localhost:5002'),
    'orders': os.environ.get('ORDER_SERVICE_URL', 'http://localhost:5003'),
    'messages': os.environ.get('MESSAGE_SERVICE_URL', 'http://localhost:5004'),
}
TIMEOUT = 5  # seconds

DATETIME_KEYS = {'placed', 'created_at', 'order_time', 'changed_at', 'timestamp'}
DATE_KEYS = {'day'}


class ServiceError(Exception):
    """The service refused the request (4xx); `message` is safe to show to the user."""
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


class ServiceUnavailable(Exception):
    """The service could not be reached or failed (5xx)."""
    def __init__(self, service):
        super().__init__(f'{service} service is unavailable')
        self.service = service


def _convert(value, key=None):
    if isinstance(value, dict):
        return {k: _convert(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [_convert(v) for v in value]
    if isinstance(value, str) and key in DATETIME_KEYS:
        return datetime.fromisoformat(value)
    if isinstance(value, str) and key in DATE_KEYS:
        return date.fromisoformat(value)
    return value


def call(service, method, path, params=None, json=None):
    try:
        resp = requests.request(method, SERVICES[service] + path, params=params, json=json,
                                timeout=TIMEOUT)
    except requests.RequestException:
        raise ServiceUnavailable(service)
    try:
        data = resp.json() if resp.content else {}
    except ValueError:
        data = {}
    if resp.status_code == 404:
        abort(404)
    if resp.status_code >= 500 and resp.status_code != 503:
        raise ServiceUnavailable(service)
    if resp.status_code >= 400:
        raise ServiceError(resp.status_code, data.get('error') or 'Something went wrong. Try again.')
    return _convert(data)


def get(service, path, **params):
    return call(service, 'GET', path, params=params or None)


def post(service, path, json=None):
    return call(service, 'POST', path, json=json)


def put(service, path, json=None):
    return call(service, 'PUT', path, json=json)


def patch(service, path, json=None):
    return call(service, 'PATCH', path, json=json)


def delete(service, path):
    return call(service, 'DELETE', path)
