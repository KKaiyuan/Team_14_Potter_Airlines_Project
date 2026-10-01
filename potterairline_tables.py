# Acknowledgement: Consulted with Claude for the code in this file.

import sqlite3
import pandas as pd

DB_PATH = "flights_database.db"
CSV_PATH = "flights.csv"

def load_csv(csv_path):
    return pd.read_csv(csv_path)   # <-- load CSV into a DataFrame first

def create_tables(conn):
    conn.execute("DROP TABLE IF EXISTS flights")  # drop child first (FK dependency)
    conn.execute("DROP TABLE IF EXISTS routes")

    conn.execute("""
        CREATE TABLE routes (
            origin_airport_code TEXT NOT NULL,
            destination_airport_code TEXT NOT NULL,
            origin_city TEXT NOT NULL,
            destination_city TEXT NOT NULL,
            base_fare DOUBLE,
            PRIMARY KEY (origin_airport_code, destination_airport_code)
        );
    """)
    conn.execute("""
        CREATE TABLE flights (
            flight_id TEXT NOT NULL,
            dep_date DATE NOT NULL,
            dep_hour TEXT,
            origin_airport_code TEXT NOT NULL,
            destination_airport_code TEXT NOT NULL,
            distance_km INTEGER,
            capacity INTEGER,
            seats_remaining INTEGER,
            PRIMARY KEY (flight_id, dep_date),
            FOREIGN KEY (origin_airport_code, destination_airport_code)
                REFERENCES routes(origin_airport_code, destination_airport_code)
        );
    """)
    # Added: active orders reference one flight occurrence, not just a flight number.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_id TEXT NOT NULL,
            dep_date DATE NOT NULL,
            tickets INTEGER NOT NULL CHECK (tickets > 0),
            unit_fare REAL NOT NULL CHECK (unit_fare > 0),
            booked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (flight_id, dep_date) REFERENCES flights(flight_id, dep_date)
        );
    """)
    conn.commit()

def load_data_into_tables(conn, flights_df):
    # --- Step 1: unique routes ---
    route_cols = ["origin_airport_code", "destination_airport_code", "origin_city", "destination_city", "base_fare"]
    unique_routes = flights_df[route_cols].drop_duplicates(
        subset=["origin_airport_code", "destination_airport_code"]
    )

    route_insert_rows = [
        (
            row["origin_airport_code"],
            row["destination_airport_code"],
            row["origin_city"],
            row["destination_city"],
            row["base_fare"]
        )
        for _, row in unique_routes.iterrows()
    ]

    cursor = conn.cursor()
    cursor.executemany(
        """INSERT INTO routes
           (origin_airport_code, destination_airport_code, origin_city, destination_city, base_fare)
           VALUES (?, ?, ?, ?, ?)""",
        route_insert_rows
    )
    conn.commit()
    print(f"Loaded {len(route_insert_rows)} unique routes.")

    # --- Step 2: flights, referencing routes via airport codes (no UUID lookup needed) ---
    flight_insert_rows = [
        (
            row["flight_id"],
            str(row["dep_date"]),
            str(row["dep_hour"]),
            row["origin_airport_code"],
            row["destination_airport_code"],
            row["distance_km"],
            row["capacity"],
            row["seats_remaining"],
        )
        for _, row in flights_df.iterrows()
    ]

    cursor.executemany(
        """INSERT INTO flights
           (flight_id, dep_date, dep_hour, origin_airport_code, destination_airport_code, distance_km, capacity, seats_remaining)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        flight_insert_rows
    )
    conn.commit()
    print(f"Loaded {len(flight_insert_rows)} flights.")

# # Added: initialize once; subsequent UI reruns never reload inventory from CSV.
# def initialize_database():
#     conn = sqlite3.connect(DB_PATH)
#     try:
#         conn.execute("PRAGMA foreign_keys = ON")
#         exists = conn.execute(
#             "SELECT name FROM sqlite_master WHERE type = ? AND name = ?",
#             ("table", "flights"),
#         ).fetchone()
#         create_tables(conn)
#         if exists is None:
#             load_data_into_tables(conn, load_csv(CSV_PATH))
#     finally:
#         conn.close()


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        create_tables(conn)

        flights_df = load_csv(CSV_PATH)   # <-- load CSV into a Pandas DataFrame first
        load_data_into_tables(conn, flights_df)           # <-- pass the Pandas DataFrame, not the path, into SQL tables
    finally:
        conn.close()