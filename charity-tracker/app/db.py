"""
db.py

SQLite schema and connection handling for the charity tracker.
No ORM — plain sqlite3 with parameterized queries, kept deliberately
simple and easy to read for a small-scale tool.
"""

import sqlite3
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS volunteer_hours (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    activity TEXT NOT NULL,
    hours REAL NOT NULL CHECK (hours > 0),
    date_logged TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    amount REAL NOT NULL CHECK (amount > 0),
    currency TEXT NOT NULL DEFAULT 'GBP',
    method TEXT,
    date_received TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_hours_person ON volunteer_hours(person_id);
CREATE INDEX IF NOT EXISTS idx_donations_person ON donations(person_id);
"""


def get_connection(db_path: str = "charity_tracker.db") -> sqlite3.Connection:
    """
    Open a connection with row access by column name and foreign keys
    enforced (off by default in sqlite3).
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str = "charity_tracker.db") -> None:
    """Create all tables/indexes if they don't already exist."""
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


@contextmanager
def db_session(db_path: str = "charity_tracker.db"):
    """
    Context manager that yields a connection and handles commit/rollback
    and closing automatically.

    Usage:
        with db_session(path) as conn:
            conn.execute(...)
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
