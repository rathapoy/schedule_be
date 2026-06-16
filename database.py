import pymysql
import pymysql.cursors
from contextlib import contextmanager
from config import DB_HOST, DB_USER, DB_PASSWORD

@contextmanager
def get_db_connection(database: str):
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=database,
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        yield conn
    finally:
        conn.close()
def fetch_as_dict(cursor):
    rows = cursor.fetchall()
    if not rows: return []
    if isinstance(rows[0], dict):
        return rows
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]