from contextlib import contextmanager

import mysql.connector

from config import DB_CONFIG

_conn = None


def get_conn():
    """Open the connection once and reuse it (reconnects if it dropped)."""
    global _conn
    if _conn is None or not _conn.is_connected():
        _conn = mysql.connector.connect(**DB_CONFIG, autocommit=True)
    return _conn


def query(sql, params=None):
    """Run a SELECT. Returns (column_names, rows)."""
    cur = get_conn().cursor()
    try:
        cur.execute(sql, params or ())
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall() if cur.description else []
        return cols, rows
    finally:
        cur.close()


def execute(sql, params=None):
    """Run an INSERT/UPDATE/DELETE. Returns the new AUTO_INCREMENT id (0 if none)."""
    cur = get_conn().cursor()
    try:
        cur.execute(sql, params or ())
        return cur.lastrowid
    finally:
        cur.close()


def call_proc(name, args):
    """Call a stored procedure. Returns a list of (columns, rows), one per result set."""
    cur = get_conn().cursor()
    try:
        cur.callproc(name, args)
        results = []
        for rs in cur.stored_results():
            results.append(([d[0] for d in rs.description], rs.fetchall()))
        return results
    finally:
        cur.close()


@contextmanager
def transaction():
    """Several statements as one unit:  with db.transaction() as cur: cur.execute(...)"""
    conn = get_conn()
    conn.start_transaction()
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()