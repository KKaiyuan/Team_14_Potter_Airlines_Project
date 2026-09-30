# Acknowledgement: Consulted with Claude for the code in this file.

import sqlite3
import csv
import uuid

DB_PATH = "flights_database.db"
CSV_PATH = "flights.csv"

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
            dep_hour INTEGER,
            origin_airport_code TEXT NOT NULL,
            destination_airport_code TEXT NOT NULL,
            capacity INTEGER,
            seats_remaining INTEGER,
            distance_km INTEGER,
            PRIMARY KEY (flight_id, dep_date),
            FOREIGN KEY (origin_airport_code, destination_airport_code)
                REFERENCES routes(origin_airport_code, destination_airport_code)
        );
    """)
    conn.commit()

def load_data(conn, csv_path):
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        flight_rows = list(reader)

    # --- Step 1: build unique routes from origin/destination pairs ---
    route_lookup = {}
    route_insert_rows = []

    for row in flight_rows:
        key = (row["origin"], row["destination"])
        if key not in route_lookup:
            route_uuid = str(uuid.uuid4())
            route_lookup[key] = route_uuid
            route_insert_rows.append((
                route_uuid,
                row["origin"],
                row["destination"],
                None   # no fare data in CSV yet — NULL for now, update later
            ))

    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO routes (route_uuid, origin, destination, base_fare) VALUES (?, ?, ?, ?)",
        route_insert_rows
    )
    conn.commit()
    print(f"Loaded {len(route_insert_rows)} unique routes.")

    # --- Step 2: insert flights, referencing route_uuid ---
    flight_insert_rows = []
    for row in flight_rows:
        key = (row["origin"], row["destination"])
        route_uuid = route_lookup[key]
        flight_insert_rows.append((
            str(uuid.uuid4()),
            route_uuid,
            row["flight_number"],
            row["capacity"],
            row["seats_remaining"]
        ))

    cursor.executemany(
        """INSERT INTO flights (flight_uuid, route_uuid, flight_number, capacity, seats_remaining)
           VALUES (?, ?, ?, ?, ?)""",
        flight_insert_rows
    )
    conn.commit()
    print(f"Loaded {len(flight_insert_rows)} flights.")

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        create_tables(conn)
        load_data(conn, CSV_PATH)
    finally:
        conn.close()