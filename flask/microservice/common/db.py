"""Database access shared by every service (copied from the monolith's app.py).

All services use the one `pizza` database, but each service only touches its own tables.
"""
import os
from contextlib import contextmanager

import mysql.connector


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
