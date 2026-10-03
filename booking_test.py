import sqlite3
import pytest
import booking

TEST_DEP_DATE = "2026-12-25"
TEST_DEP_HOUR = "08:00:00"


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """
    Create a temporary database for testing, matching the real schema
    (routes + flights joined on airport codes, bookings with unit_fare).
    This prevents the tests from changing the real database.
    """
    monkeypatch.chdir(tmp_path)

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE routes (
            origin_airport_code TEXT NOT NULL,
            destination_airport_code TEXT NOT NULL,
            origin_city TEXT NOT NULL,
            destination_city TEXT NOT NULL,
            base_fare DOUBLE,
            PRIMARY KEY (origin_airport_code, destination_airport_code)
        )
    """)

    cursor.execute("""
        CREATE TABLE flights (
            flight_id TEXT NOT NULL,
            dep_date DATE NOT NULL,
            origin_airport_code TEXT NOT NULL,
            destination_airport_code TEXT NOT NULL,
            capacity INTEGER,
            seats_remaining INTEGER,
            dep_hour TEXT,
            distance_km INTEGER,
            PRIMARY KEY (flight_id, dep_date),
            FOREIGN KEY (origin_airport_code, destination_airport_code)
                REFERENCES routes(origin_airport_code, destination_airport_code)
        )
    """)

    cursor.execute("""
        CREATE TABLE bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_id TEXT,
            dep_date DATE,
            tickets INTEGER,
            unit_fare REAL
        )
    """)

    cursor.execute("""
        INSERT INTO routes
            (origin_airport_code, destination_airport_code, origin_city, destination_city, base_fare)
        VALUES ('YYZ', 'YVR', 'Toronto', 'Vancouver', 300.0)
    """)

    # Test flight with 50 seats, far enough in the future to book/validate against "now"
    cursor.execute("""
        INSERT INTO flights
            (flight_id, dep_date, origin_airport_code, destination_airport_code,
             capacity, seats_remaining, dep_hour, distance_km)
        VALUES ('1', ?, 'YYZ', 'YVR', 50, 50, ?, 3350)
    """, (TEST_DEP_DATE, TEST_DEP_HOUR))

    conn.commit()
    conn.close()

    return tmp_path


def test_successful_booking(test_db):
    booking_id = booking.book_flight('1', 5, TEST_DEP_DATE)

    assert booking_id is not None

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT seats_remaining FROM flights WHERE flight_id = '1' AND dep_date = ?",
        (TEST_DEP_DATE,)
    )
    seats = cursor.fetchone()[0]

    assert seats == 45

    cursor.execute(
        "SELECT tickets, unit_fare FROM bookings WHERE booking_id = ?",
        (booking_id,)
    )
    tickets, unit_fare = cursor.fetchone()

    assert tickets == 5
    assert unit_fare > 0  # exact fare varies with "now", just check it's a real positive price

    conn.close()


def test_zero_tickets(test_db):
    result = booking.book_flight('1', 0, TEST_DEP_DATE)

    assert result is None

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT seats_remaining FROM flights WHERE flight_id = '1' AND dep_date = ?",
        (TEST_DEP_DATE,)
    )

    assert cursor.fetchone()[0] == 50

    conn.close()


def test_negative_tickets(test_db):
    result = booking.book_flight('1', -1, TEST_DEP_DATE)

    assert result is None

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT seats_remaining FROM flights WHERE flight_id = '1' AND dep_date = ?",
        (TEST_DEP_DATE,)
    )

    assert cursor.fetchone()[0] == 50

    conn.close()


def test_too_many_tickets(test_db):
    result = booking.book_flight('1', 51, TEST_DEP_DATE)

    assert result is None

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT seats_remaining FROM flights WHERE flight_id = '1' AND dep_date = ?",
        (TEST_DEP_DATE,)
    )

    assert cursor.fetchone()[0] == 50

    conn.close()


def test_booking_exactly_remaining_seats(test_db):
    result = booking.book_flight('1', 50, TEST_DEP_DATE)

    assert result is not None

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT seats_remaining FROM flights WHERE flight_id = '1' AND dep_date = ?",
        (TEST_DEP_DATE,)
    )

    assert cursor.fetchone()[0] == 0

    conn.close()


def test_nonexistent_flight(test_db):
    result = booking.book_flight('999', 1, TEST_DEP_DATE)

    assert result is None


def test_cancel_booking(test_db):
    booking_id = booking.book_flight('1', 5, TEST_DEP_DATE)
    assert booking_id is not None

    result = booking.cancel_booking(booking_id)

    assert result is True

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT seats_remaining FROM flights WHERE flight_id = '1' AND dep_date = ?",
        (TEST_DEP_DATE,)
    )
    assert cursor.fetchone()[0] == 50

    # cancel_booking DELETEs the row -- no "status" column exists in this schema
    cursor.execute(
        "SELECT * FROM bookings WHERE booking_id = ?",
        (booking_id,)
    )
    assert cursor.fetchone() is None

    conn.close()


def test_cancel_booking_twice(test_db):
    booking_id = booking.book_flight('1', 5, TEST_DEP_DATE)
    assert booking_id is not None

    first_cancel = booking.cancel_booking(booking_id)
    second_cancel = booking.cancel_booking(booking_id)

    assert first_cancel is True
    assert second_cancel is False  # booking row no longer exists after first cancel