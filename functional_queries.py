import sqlite3
import pandas as pd
from pricing_function_new import price_flights

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
        
def search_flights(
    start_date,
    end_date,
    origin_airport_code=None,
    destination_airport_code=None,
    sort_by="Departure date (soonest first)",
    db_path=DB_PATH,
):
    # Get only flights matching the user's search
    flights_df = filter_flights(
        start_date=start_date,
        end_date=end_date,
        origin_airport_code=origin_airport_code,
        destination_airport_code=destination_airport_code,
        db_path=db_path,
    )

    if flights_df.empty:
        return flights_df

    # Calculate current fares
    flights_df = price_flights(flights_df)

    # Remove sold-out and already-departed flights
    flights_df = flights_df[
        (flights_df["seats_remaining"] > 0)
        & (flights_df["days_until_departure"] > 0)
    ]

    # Sort the final results
    if sort_by == "Price (low to high)":
        flights_df = flights_df.sort_values("fare")

    elif sort_by == "Price (high to low)":
        flights_df = flights_df.sort_values(
            "fare",
            ascending=False,
        )

    elif sort_by == "Departure date (latest first)":
        flights_df = flights_df.sort_values(
            ["dep_date", "dep_hour"],
            ascending=False,
        )

    else:
        flights_df = flights_df.sort_values(
            ["dep_date", "dep_hour"]
        )

    return flights_df

