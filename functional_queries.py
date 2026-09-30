import sqlite3
import pandas as pd

DB_PATH = "flights_database.db"


def get_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# Basic filter query
def filter_flights(start_date, end_date, origin_airport_code=None,
                    destination_airport_code=None, db_path=DB_PATH):
    conn = get_connection(db_path)
    try:
        sql = """
            SELECT f.flight_id, f.dep_date, f.dep_hour,
                   f.origin_airport_code, f.destination_airport_code,
                   r.origin_city, r.destination_city,
                   f.capacity, f.seats_remaining,
                   f.distance_km, r.base_fare
            FROM flights f
            JOIN routes r
                ON f.origin_airport_code = r.origin_airport_code
               AND f.destination_airport_code = r.destination_airport_code
            WHERE f.dep_date BETWEEN ? AND ?
        """
        params = [str(start_date), str(end_date)]

        if origin_airport_code:
            sql += " AND f.origin_airport_code = ?"
            params.append(origin_airport_code)

        if destination_airport_code:
            sql += " AND f.destination_airport_code = ?"
            params.append(destination_airport_code)

        sql += " ORDER BY f.dep_date, f.dep_hour"

        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()

