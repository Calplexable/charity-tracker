"""
repository.py

Data access layer: every function here takes a db_path (or uses the
default) and performs one clear operation. Kept separate from any web
framework code so it's independently testable and reusable from a CLI
if needed later.
"""

from .db import db_session

DEFAULT_DB_PATH = "charity_tracker.db"


# ----------------------------------------------------------------------
# People
# ----------------------------------------------------------------------

def add_person(name: str, email: str = "", notes: str = "", db_path: str = DEFAULT_DB_PATH) -> int:
    if not name or not name.strip():
        raise ValueError("Person name is required.")
    with db_session(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO people (name, email, notes) VALUES (?, ?, ?)",
            (name.strip(), email.strip(), notes.strip()),
        )
        return cursor.lastrowid


def get_person(person_id: int, db_path: str = DEFAULT_DB_PATH):
    with db_session(db_path) as conn:
        row = conn.execute("SELECT * FROM people WHERE id = ?", (person_id,)).fetchone()
        return dict(row) if row else None


def list_people(db_path: str = DEFAULT_DB_PATH) -> list:
    with db_session(db_path) as conn:
        rows = conn.execute("SELECT * FROM people ORDER BY name COLLATE NOCASE").fetchall()
        return [dict(r) for r in rows]


def delete_person(person_id: int, db_path: str = DEFAULT_DB_PATH) -> None:
    with db_session(db_path) as conn:
        conn.execute("DELETE FROM people WHERE id = ?", (person_id,))


# ----------------------------------------------------------------------
# Volunteer hours
# ----------------------------------------------------------------------

def log_hours(
    person_id: int,
    activity: str,
    hours: float,
    date_logged: str,
    notes: str = "",
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    if hours <= 0:
        raise ValueError("Hours must be a positive number.")
    if not activity or not activity.strip():
        raise ValueError("Activity description is required.")
    with db_session(db_path) as conn:
        cursor = conn.execute(
            """INSERT INTO volunteer_hours (person_id, activity, hours, date_logged, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (person_id, activity.strip(), hours, date_logged, notes.strip()),
        )
        return cursor.lastrowid


def list_hours(person_id: int = None, db_path: str = DEFAULT_DB_PATH) -> list:
    with db_session(db_path) as conn:
        if person_id is not None:
            rows = conn.execute(
                """SELECT vh.*, p.name AS person_name FROM volunteer_hours vh
                   JOIN people p ON p.id = vh.person_id
                   WHERE vh.person_id = ? ORDER BY vh.date_logged DESC""",
                (person_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT vh.*, p.name AS person_name FROM volunteer_hours vh
                   JOIN people p ON p.id = vh.person_id
                   ORDER BY vh.date_logged DESC"""
            ).fetchall()
        return [dict(r) for r in rows]


def delete_hours_entry(entry_id: int, db_path: str = DEFAULT_DB_PATH) -> None:
    with db_session(db_path) as conn:
        conn.execute("DELETE FROM volunteer_hours WHERE id = ?", (entry_id,))


def total_hours(db_path: str = DEFAULT_DB_PATH) -> float:
    with db_session(db_path) as conn:
        row = conn.execute("SELECT COALESCE(SUM(hours), 0) AS total FROM volunteer_hours").fetchone()
        return row["total"]


def total_hours_by_person(db_path: str = DEFAULT_DB_PATH) -> list:
    with db_session(db_path) as conn:
        rows = conn.execute(
            """SELECT p.id AS person_id, p.name, COALESCE(SUM(vh.hours), 0) AS total_hours
               FROM people p
               LEFT JOIN volunteer_hours vh ON vh.person_id = p.id
               GROUP BY p.id
               ORDER BY total_hours DESC"""
        ).fetchall()
        return [dict(r) for r in rows]


# ----------------------------------------------------------------------
# Donations
# ----------------------------------------------------------------------

def log_donation(
    person_id: int,
    amount: float,
    date_received: str,
    currency: str = "GBP",
    method: str = "",
    notes: str = "",
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    if amount <= 0:
        raise ValueError("Donation amount must be a positive number.")
    with db_session(db_path) as conn:
        cursor = conn.execute(
            """INSERT INTO donations (person_id, amount, currency, method, date_received, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (person_id, amount, currency.strip() or "GBP", method.strip(), date_received, notes.strip()),
        )
        return cursor.lastrowid


def list_donations(person_id: int = None, db_path: str = DEFAULT_DB_PATH) -> list:
    with db_session(db_path) as conn:
        if person_id is not None:
            rows = conn.execute(
                """SELECT d.*, p.name AS person_name FROM donations d
                   JOIN people p ON p.id = d.person_id
                   WHERE d.person_id = ? ORDER BY d.date_received DESC""",
                (person_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT d.*, p.name AS person_name FROM donations d
                   JOIN people p ON p.id = d.person_id
                   ORDER BY d.date_received DESC"""
            ).fetchall()
        return [dict(r) for r in rows]


def delete_donation_entry(entry_id: int, db_path: str = DEFAULT_DB_PATH) -> None:
    with db_session(db_path) as conn:
        conn.execute("DELETE FROM donations WHERE id = ?", (entry_id,))


def total_donations(db_path: str = DEFAULT_DB_PATH) -> float:
    with db_session(db_path) as conn:
        row = conn.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM donations").fetchone()
        return row["total"]


def total_donations_by_person(db_path: str = DEFAULT_DB_PATH) -> list:
    with db_session(db_path) as conn:
        rows = conn.execute(
            """SELECT p.id AS person_id, p.name, COALESCE(SUM(d.amount), 0) AS total_donated
               FROM people p
               LEFT JOIN donations d ON d.person_id = p.id
               GROUP BY p.id
               ORDER BY total_donated DESC"""
        ).fetchall()
        return [dict(r) for r in rows]


# ----------------------------------------------------------------------
# Combined summary
# ----------------------------------------------------------------------

def summary(db_path: str = DEFAULT_DB_PATH) -> dict:
    """High-level dashboard numbers."""
    with db_session(db_path) as conn:
        people_count = conn.execute("SELECT COUNT(*) AS c FROM people").fetchone()["c"]
        hours_total = conn.execute(
            "SELECT COALESCE(SUM(hours), 0) AS total FROM volunteer_hours"
        ).fetchone()["total"]
        donations_total = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM donations"
        ).fetchone()["total"]
        donations_count = conn.execute("SELECT COUNT(*) AS c FROM donations").fetchone()["c"]
        hours_count = conn.execute("SELECT COUNT(*) AS c FROM volunteer_hours").fetchone()["c"]

    return {
        "people_count": people_count,
        "total_hours": hours_total,
        "total_hours_entries": hours_count,
        "total_donations": donations_total,
        "total_donations_entries": donations_count,
    }
