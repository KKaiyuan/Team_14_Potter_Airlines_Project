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
            route_uuid TEXT PRIMARY KEY,
            origin TEXT NOT NULL,
            destination TEXT NOT NULL,
            base_fare DOUBLE,
            UNIQUE(origin, destination)
        );
    """)
    conn.execute("""
        CREATE TABLE flights (
            flight_uuid TEXT PRIMARY KEY,
            route_uuid TEXT NOT NULL,
            flight_number TEXT,
            capacity INTEGER,
            seats_remaining INTEGER,
            FOREIGN KEY (route_uuid) REFERENCES routes(route_uuid)
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