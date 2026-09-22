"""
database.py
SQLite persistence for the 'flights' table: SELECT, UPDATE, DELETE.
(INSERT/CREATE TABLE for flights lives in gendb.py; routes.py has its own
CREATE/INSERT for the 'routes' table.)

All values are passed as parameters, never string-built, so this is safe
against SQL injection.

Booking goes through the Flight class (flight.py) so the 3-hour booking
cutoff and overbooking checks are enforced BEFORE the database is touched --
the database only ever stores a state that was already validated.
"""

import sqlite3
import csv

from flight import Flight


def get_connection(db_path="flights_database.db"):
    return sqlite3.connect(db_path)


def create_flights_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS flights (
            flight_id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            seats_remaining INTEGER NOT NULL,
            dep_date TEXT NOT NULL,
            dep_hour TEXT NOT NULL
        );
    """)
    conn.commit()


def load_csv_to_table(conn, csv_path, table_name="flights"):
    """INSERT: bulk-load flights from CSV, parameterized values."""
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        rows = [
            (row["flight_id"], row["source"], row["destination"],
             int(row["capacity"]), int(row["seats_remaining"]),
             row["dep_date"], row["dep_hour"])
            for row in reader
        ]
    sql = f"""
        INSERT OR REPLACE INTO {table_name}
        (flight_id, source, destination, capacity, seats_remaining, dep_date, dep_hour)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    conn.executemany(sql, rows)
    conn.commit()
    print(f"Loaded {len(rows)} rows into {table_name}.")


def select_flight_by_id(conn, flight_id):
    """
    SELECT: fetch a single flight by primary key, joined with its route's
    base_fare and route_popularity (parameterized).
    """
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("""
        SELECT f.*, r.base_fare, r.route_popularity
        FROM flights f
        JOIN routes r ON f.source = r.source AND f.destination = r.destination
        WHERE f.flight_id = ?
    """, (flight_id,))
    row = cursor.fetchone()
    if row is None:
        raise ValueError(f"No flight found with id {flight_id}")
    return row


def _flight_from_row(row):
    return Flight(
        flight_id=row["flight_id"], source=row["source"], destination=row["destination"],
        dep_date=row["dep_date"], dep_hour=row["dep_hour"], capacity=row["capacity"],
        seats_remaining=row["seats_remaining"], base_fare=row["base_fare"],
    )


def update_seats_remaining(conn, flight_id, new_seats_remaining):
    """UPDATE: set a flight's seats_remaining directly (parameterized)."""
    assert new_seats_remaining >= 0, "seats_remaining cannot be negative"
    cursor = conn.execute(
        "UPDATE flights SET seats_remaining = ? WHERE flight_id = ?",
        (new_seats_remaining, flight_id),
    )
    conn.commit()
    if cursor.rowcount == 0:
        raise ValueError(f"No flight found with id {flight_id}")


def book_seats(conn, flight_id, n=1, now=None):
    """
    Book n seats on a flight. Validates through Flight.book_seats() first
    (overbooking + 3h booking cutoff), THEN persists via UPDATE. Raises
    ValueError if the booking is invalid; the database is left unchanged
    in that case.
    """
    row = select_flight_by_id(conn, flight_id)
    flight = _flight_from_row(row)
    flight.book_seats(n, now=now)  # raises ValueError if invalid -- DB untouched
    update_seats_remaining(conn, flight_id, flight.seats_remaining)
    return flight.seats_remaining


def delete_flight(conn, flight_id):
    """DELETE: remove a flight (e.g. a cancelled route), parameterized."""
    cursor = conn.execute("DELETE FROM flights WHERE flight_id = ?", (flight_id,))
    conn.commit()
    if cursor.rowcount == 0:
        raise ValueError(f"No flight found with id {flight_id}")