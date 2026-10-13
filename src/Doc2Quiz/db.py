import os
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row


def get_connection():
    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        row_factory=dict_row,
    )

@contextmanager
def get_cursor(commit: bool = False):
    with get_connection() as conn:
        with conn.cursor() as cur:
            try:
                yield cur
                if commit:
                    conn.commit()
            except Exception:
                conn.rollback()
                raise