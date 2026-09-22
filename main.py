"""
main.py
Runs the full Potter Airlines dynamic pricing workflow, start to finish:

    1. Load or create flight data
    2. Store/retrieve it in SQLite
    3. Price all flights (vectorized)
    4. Filter/rank flights
    5. Update an operational value (book seats)
    6. Run validation checks + demonstrate an edge case
"""

import os
from datetime import datetime, timedelta

import pandas as pd

import database
import routes
from flight import Flight
from analysis import (
    load_flights_df, price_all_flights,
    top_n_by_price, average_price_by_route, discounted_flights,
)


def step1_load_or_create_data():
    print("\n=== Step 1: Load or create flight data ===")
    if not os.path.exists("flights.csv"):
        import gendb  # running gendb.py generates flights.csv as a side effect
    else:
        print("flights.csv already exists, reusing it.")


def step2_store_and_retrieve():
    print("\n=== Step 2: Store/retrieve in SQLite ===")
    conn = database.get_connection()

    database.create_flights_table(conn)
    database.load_csv_to_table(conn, "flights.csv")

    flights_df = pd.read_csv("flights.csv")
    routes_df = routes.build_routes_df(flights_df)
    routes.create_routes_table(conn)
    routes.load_routes_to_table(conn, routes_df)

    sample = database.select_flight_by_id(conn, flights_df.iloc[0]["flight_id"])
    print("Sample SELECT (joined with routes):", dict(sample))
    return conn


def step3_price_all_flights(conn):
    print("\n=== Step 3: Price all flights (vectorized) ===")
    flights_df = load_flights_df(conn)
    flights_df = routes.attach_route_data(flights_df, conn)
    priced = price_all_flights(flights_df)
    print(priced[["flight_id", "source", "destination", "base_fare", "final_price"]].head())
    return priced


def step4_filter_and_rank(priced):
    print("\n=== Step 4: Filter/rank flights ===")
    print("\nTop 5 most expensive flights right now:")
    print(top_n_by_price(priced, 5)[
        ["flight_id", "source", "destination", "final_price", "load_factor"]
    ])

    print("\nAverage price by route (top 5):")
    print(average_price_by_route(priced).head())

    disc = discounted_flights(priced)
    print(f"\n{len(disc)} of {len(priced)} flights qualify for the last-minute discount.")


def step5_update_operational_value(conn, priced):
    print("\n=== Step 5: Update an operational value (book seats) ===")
    # pick a flight that's comfortably far from departure so the booking succeeds
    candidate = priced[priced["days_until_departure"] > 5].iloc[0]
    flight_id = candidate["flight_id"]

    before = database.select_flight_by_id(conn, flight_id)
    print(f"Before booking: {flight_id} has {before['seats_remaining']} seats remaining")

    new_count = database.book_seats(conn, flight_id, n=2)
    print(f"After booking 2 seats: {new_count} seats remaining")

    confirmed = database.select_flight_by_id(conn, flight_id)
    print("Confirmed in DB:", confirmed["seats_remaining"])
    return flight_id


def step6_validation_and_edge_case(conn, flight_id):
    print("\n=== Step 6: Validation checks + edge case demo ===")

    # Normal validation: constructing an invalid Flight should fail loudly.
    try:
        Flight("BAD1", "Toronto", "Toronto", "2027-11-01", "12:00:00", 150, 50, 100)
        print("ERROR: should have rejected same source/destination")
    except AssertionError as e:
        print(f"Caught expected validation error (same source/destination): {e}")

    try:
        Flight("BAD2", "Toronto", "Ottawa", "2027-11-01", "12:00:00", 150, 500, 100)
        print("ERROR: should have rejected seats_remaining > capacity")
    except AssertionError as e:
        print(f"Caught expected validation error (seats > capacity): {e}")

    # Edge case: try to book a flight 5 minutes before departure.
    row = database.select_flight_by_id(conn, flight_id)
    dep_dt = datetime.strptime(f"{row['dep_date']} {row['dep_hour']}", "%Y-%m-%d %H:%M:%S")
    five_min_before = dep_dt - timedelta(minutes=5)

    before_seats = row["seats_remaining"]
    try:
        database.book_seats(conn, flight_id, n=1, now=five_min_before)
        print("ERROR: should have rejected booking 5 minutes before departure")
    except ValueError as e:
        print(f"Caught expected booking-cutoff error: {e}")

    after = database.select_flight_by_id(conn, flight_id)
    assert after["seats_remaining"] == before_seats, \
        "seats_remaining changed even though the booking was rejected!"
    print(f"Confirmed: seats_remaining unchanged ({after['seats_remaining']}) "
          f"after the rejected booking.")

    # DELETE demonstration on a disposable flight.
    conn.execute(
        "INSERT OR REPLACE INTO flights VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("TEMP1", "Toronto", "Ottawa", 150, 150, "2027-01-01", "12:00:00"),
    )
    conn.commit()
    database.delete_flight(conn, "TEMP1")
    print("Inserted and then deleted a temporary flight (TEMP1) to demonstrate DELETE.")


def main():
    step1_load_or_create_data()
    conn = step2_store_and_retrieve()
    priced = step3_price_all_flights(conn)
    step4_filter_and_rank(priced)
    flight_id = step5_update_operational_value(conn, priced)
    step6_validation_and_edge_case(conn, flight_id)
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()