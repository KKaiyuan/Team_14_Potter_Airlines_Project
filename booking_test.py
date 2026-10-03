# import sqlite3
# import pytest
# import booking

# TEST_DEP_DATE = "2026-12-25"  # fixed date used across all tests


# @pytest.fixture
# def test_db(tmp_path, monkeypatch):
#     """
#     Create a temporary database for testing.
#     This prevents the tests from changing the real database.
#     """
#     monkeypatch.chdir(tmp_path)

#     conn = sqlite3.connect("flights_database.db")
#     cursor = conn.cursor()

#     cursor.execute("""
#         CREATE TABLE flights (
#             flight_id INTEGER,
#             dep_date TEXT,
#             seats_remaining INTEGER,
#             PRIMARY KEY (flight_id, dep_date)
#         )
#     """)

#     cursor.execute("""
#         CREATE TABLE bookings (
#             booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
#             flight_id INTEGER,
#             dep_date TEXT,
#             tickets INTEGER,
#             status TEXT
#         )
#     """)

#     # Test flight with 50 seats
#     cursor.execute("""
#         INSERT INTO flights (flight_id, dep_date, seats_remaining)
#         VALUES (1, ?, 50)
#     """, (TEST_DEP_DATE,))

#     conn.commit()
#     conn.close()

#     return tmp_path


import sqlite3
import pytest
import booking

TEST_DEP_DATE = "2026-12-25"


@pytest.fixture
def test_db(tmp_path, monkeypatch):
    """
    Create a temporary database for testing, matching the real schema
    (routes + flights, joined on airport codes).
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
            dep_hour INTEGER,
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
            status TEXT
        )
    """)

    # One route: YYZ -> YVR
    cursor.execute("""
        INSERT INTO routes
            (origin_airport_code, destination_airport_code, origin_city, destination_city, base_fare)
        VALUES ('YYZ', 'YVR', 'Toronto', 'Vancouver', 300.0)
    """)

    # Test flight with 50 seats, on that route
    cursor.execute("""
        INSERT INTO flights
            (flight_id, dep_date, origin_airport_code, destination_airport_code,
             capacity, seats_remaining, dep_hour, distance_km)
        VALUES (1, ?, 'YYZ', 'YVR', 50, 50, 8, 3350)
    """, (TEST_DEP_DATE,))

    conn.commit()
    conn.close()

    return tmp_path


def test_successful_booking(test_db):
    booking_id = booking.book_flight(1, 5, TEST_DEP_DATE)

    assert booking_id is not None

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT seats_remaining FROM flights WHERE flight_id = ? AND dep_date = ?",
        (1, TEST_DEP_DATE)
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
    result = booking.book_flight(1, 0, TEST_DEP_DATE)

    assert result is None

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT seats_remaining FROM flights WHERE flight_id = 1 AND dep_date = ?",
        (TEST_DEP_DATE,)
    )

    assert cursor.fetchone()[0] == 50

    conn.close()


def test_negative_tickets(test_db):
    result = booking.book_flight(1, -1, TEST_DEP_DATE)

    assert result is None

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT seats_remaining FROM flights WHERE flight_id = 1 AND dep_date = ?",
        (TEST_DEP_DATE,)
    )

    assert cursor.fetchone()[0] == 50

    conn.close()


def test_too_many_tickets(test_db):
    result = booking.book_flight(1, 51, TEST_DEP_DATE)

    assert result is None

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT seats_remaining FROM flights WHERE flight_id = 1 AND dep_date = ?",
        (TEST_DEP_DATE,)
    )

    assert cursor.fetchone()[0] == 50

    conn.close()


def test_booking_exactly_remaining_seats(test_db):
    result = booking.book_flight(1, 50, TEST_DEP_DATE)

    assert result is not None

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT seats_remaining FROM flights WHERE flight_id = 1 AND dep_date = ?",
        (TEST_DEP_DATE,)
    )

    assert cursor.fetchone()[0] == 0

    conn.close()


def test_nonexistent_flight(test_db):
    result = booking.book_flight(999, 1, TEST_DEP_DATE)

    assert result is None


def test_cancel_booking(test_db):
    booking_id = booking.book_flight(1, 5, TEST_DEP_DATE)

    result = booking.cancel_booking(booking_id)

    assert result is True

    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT seats_remaining FROM flights WHERE flight_id = 1 AND dep_date = ?",
        (TEST_DEP_DATE,)
    )

    assert cursor.fetchone()[0] == 50

    cursor.execute(
        "SELECT status FROM bookings WHERE booking_id = ?",
        (booking_id,)
    )

    assert cursor.fetchone()[0] == "cancelled"

    conn.close()


def test_cancel_booking_twice(test_db):
    booking_id = booking.book_flight(1, 5, TEST_DEP_DATE)

    first_cancel = booking.cancel_booking(booking_id)
    second_cancel = booking.cancel_booking(booking_id)

    assert first_cancel is True
    assert second_cancel is False