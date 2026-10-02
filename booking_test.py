import sqlite3
import pytest
import booking


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """
    Create a temporary database for testing.
    This prevents the tests from changing the real database.
    """
    monkeypatch.chdir(tmp_path)

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE flights (
            flight_id INTEGER PRIMARY KEY,
            seats_remaining INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_id INTEGER,
            tickets INTEGER,
            status TEXT
        )
    """)

    # Test flight with 50 seats
    cursor.execute("""
        INSERT INTO flights (flight_id, seats_remaining)
        VALUES (1, 50)
    """)

    conn.commit()
    conn.close()

    return tmp_path


def test_successful_booking(test_db):
    booking_id = booking.book_flight(1, 5)

    assert booking_id is not None

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT seats_remaining FROM flights WHERE flight_id = ?",
        (1,)
    )
    seats = cursor.fetchone()[0]

    assert seats == 45

    cursor.execute(
        "SELECT tickets, status FROM bookings WHERE booking_id = ?",
        (booking_id,)
    )
    booking_record = cursor.fetchone()

    assert booking_record == (5, "confirmed")

    conn.close()


def test_zero_tickets(test_db):
    result = booking.book_flight(1, 0)

    assert result is None

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT seats_remaining FROM flights WHERE flight_id = 1"
    )

    assert cursor.fetchone()[0] == 50

    conn.close()


def test_negative_tickets(test_db):
    result = booking.book_flight(1, -1)

    assert result is None

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT seats_remaining FROM flights WHERE flight_id = 1"
    )

    assert cursor.fetchone()[0] == 50

    conn.close()


def test_too_many_tickets(test_db):
    result = booking.book_flight(1, 51)

    assert result is None

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT seats_remaining FROM flights WHERE flight_id = 1"
    )

    assert cursor.fetchone()[0] == 50

    conn.close()


def test_booking_exactly_remaining_seats(test_db):
    result = booking.book_flight(1, 50)

    assert result is not None

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT seats_remaining FROM flights WHERE flight_id = 1"
    )

    assert cursor.fetchone()[0] == 0

    conn.close()


def test_nonexistent_flight(test_db):
    result = booking.book_flight(999, 1)

    assert result is None


def test_cancel_booking(test_db):
    booking_id = booking.book_flight(1, 5)

    result = booking.cancel_booking(booking_id)

    assert result is True

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT seats_remaining FROM flights WHERE flight_id = 1"
    )

    assert cursor.fetchone()[0] == 50

    cursor.execute(
        "SELECT status FROM bookings WHERE booking_id = ?",
        (booking_id,)
    )

    assert cursor.fetchone()[0] == "cancelled"

    conn.close()


def test_cancel_booking_twice(test_db):
    booking_id = booking.book_flight(1, 5)

    first_cancel = booking.cancel_booking(booking_id)
    second_cancel = booking.cancel_booking(booking_id)

    assert first_cancel is True
    assert second_cancel is False