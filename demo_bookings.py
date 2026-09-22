# Added: optional initial orders, created through the actual booking function.
import random
import sqlite3
from booking import book_flight

NUMBER_OF_DEMO_BOOKINGS = 20

if __name__ == "__main__":
    conn = sqlite3.connect("flights_database.db")
    try:
        count = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
        flights = conn.execute("SELECT flight_id FROM flights WHERE seats_remaining >= 5 ORDER BY flight_id").fetchall()
    finally:
        conn.close()
    if count == 0:
        random.seed(42)
        for flight in random.sample(flights, NUMBER_OF_DEMO_BOOKINGS):
            book_flight(flight[0], random.randint(1, 5))
    else:
        print("Bookings already exist; no demo orders were added.")
