import sqlite3
from contextlib import closing
import pandas as pd
from flight import Flight
from pricing_function_new import price_flights


# Modified: identify Kevin's flight occurrence by number and date.
def book_flight(flight_id, amount_of_tickets_booked, dep_date):
    
    conn = sqlite3.connect("flights_database.db") # Fixed: match the notebook database name.
    cursor = conn.cursor()
        
    # Added: use the same transaction/cleanup structure as Kevin's cancellation.
    try:
        with conn:
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("BEGIN IMMEDIATE")
            cursor.execute(
                        "SELECT seats_remaining FROM flights WHERE flight_id = ? AND dep_date = ?",
                        (flight_id, dep_date)
                        )
            
            flight = cursor.fetchone()
            
            #Check if flight exists
            if flight == None:
                print("Flight not found.")
                return
            
            seats_remaining = flight[0]
            
            #Check if there are still seats remaining
            if seats_remaining <= 0:
                print("No more available seats.")
                return
            
            # Modified: ticket quantities must be positive whole numbers.
            if type(amount_of_tickets_booked) is not int or amount_of_tickets_booked <= 0:
                print("Amount of tickets must be greater than 0.")
                return
            
            #Check if there are enough seats for the booking size
            if amount_of_tickets_booked > seats_remaining:
                print("Not enough available seats.")
                return
            
            # Added: validate departure/inventory and save the current backend price.
            flights_df = pd.read_sql_query(
                FLIGHT_QUERY + " WHERE f.flight_id = ? AND f.dep_date = ?",
                conn, params=(flight_id, dep_date),
            )
            row = flights_df.iloc[0]
            selected_flight = Flight(flight_id, dep_date, str(row["dep_hour"]),
                                     int(row["capacity"]), int(row["seats_remaining"]))
            selected_flight.validate_booking(amount_of_tickets_booked)
            unit_fare = float(price_flights(flights_df).iloc[0]["fare"])

            # Added: record the order and deduct seats together, without overselling.
            
            
            cursor.execute("""
                UPDATE flights
                SET seats_remaining = seats_remaining - ?
                WHERE flight_id = ? AND dep_date = ? AND seats_remaining >= ?
                """,
                (amount_of_tickets_booked, flight_id, dep_date, amount_of_tickets_booked)
                )
            if cursor.rowcount == 0:
                print("Not enough available seats.")
                return
            
            cursor.execute("""
                INSERT INTO bookings (flight_id, dep_date, tickets, unit_fare)
                VALUES (?, ?, ?, ?)
                """, (flight_id, dep_date, amount_of_tickets_booked, unit_fare))
            booking_id = cursor.lastrowid
            
    except (ValueError, sqlite3.Error) as e:
        print("Booking failed:", e)
        return
    finally:
        conn.close()

    print("Booking Successful!")
    return booking_id  # Added: identify this order for later cancellation.


# Added: cancel an existing order and restore its seats exactly once.
def cancel_booking(booking_id):
    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()
    try:
        with conn:
            cursor.execute("BEGIN IMMEDIATE")
            cursor.execute("SELECT flight_id, dep_date, tickets FROM bookings WHERE booking_id = ?",
                           (booking_id,))
            booking = cursor.fetchone()
            if booking is None:
                print("Booking not found.")
                return False
            flight_id, dep_date, tickets = booking
            cursor.execute("UPDATE flights SET seats_remaining = seats_remaining + ? WHERE flight_id = ? AND dep_date = ? AND seats_remaining + ? <= capacity",
                           (tickets, flight_id, dep_date, tickets))
            # Added: a failed restoration must not delete the order.
            if cursor.rowcount != 1:
                raise ValueError("Cannot restore seats: flight inventory is inconsistent.")
            # Modified: delete this active order instead of changing its status.
            cursor.execute("DELETE FROM bookings WHERE booking_id = ?",
                           (booking_id,))
        print("Cancellation Successful!")
        return True
    except (ValueError, sqlite3.Error) as e:
        print("Database error:", e)
        return False
    finally:
        conn.close()

# Added: reuse Kevin's route/flight join for live inventory and pricing.
FLIGHT_QUERY = """
    SELECT f.*, r.origin_city, r.destination_city, r.base_fare
    FROM flights f
    JOIN routes r ON f.origin_airport_code = r.origin_airport_code
                 AND f.destination_airport_code = r.destination_airport_code
"""


def get_priced_flights():
    with closing(sqlite3.connect("flights_database.db")) as conn:
        flights_df = pd.read_sql_query(FLIGHT_QUERY, conn)
    return price_flights(flights_df)


# Added: display a dataframe loaded from persistent orders, not session memory.
def get_bookings():
    with closing(sqlite3.connect("flights_database.db")) as conn:
        bookings_df = pd.read_sql_query("""
            SELECT b.*, f.dep_hour, f.origin_airport_code, f.destination_airport_code,
                   r.origin_city, r.destination_city
            FROM bookings b
            JOIN flights f ON b.flight_id = f.flight_id AND b.dep_date = f.dep_date
            JOIN routes r ON f.origin_airport_code = r.origin_airport_code
                         AND f.destination_airport_code = r.destination_airport_code
            ORDER BY b.booking_id DESC
            """, conn)
    bookings_df["total_fare"] = bookings_df["tickets"] * bookings_df["unit_fare"]
    return bookings_df


