"""
app.py
A small Streamlit booking site for Potter Airlines -- an Air Canada-style
"search flights, see the price, book it" UI, built on top of the exact
same pricing/persistence code used everywhere else in this project
(flight.py, routes.py, analysis.py, database.py). Nothing here recomputes
a price or writes to SQLite on its own; every price shown comes from
analysis.price_all_flights(), and every booking goes through
database.book_seats(), so the 3-hour cutoff and overbooking checks apply
here exactly as they do in main.py.

Run with:  streamlit run app.py
"""

import os
from datetime import datetime, date

import pandas as pd
import streamlit as st

import database
import routes
from analysis import load_flights_df, price_all_flights
from flight import MIN_FARE, MAX_FARE, BOOKING_CUTOFF

st.set_page_config(page_title="Potter Airlines", page_icon="\U0001f9f9", layout="wide")


# ---------------------------------------------------------------------
# Make sure flights.csv and flights_database.db actually exist before
# anything tries to query them. This mirrors main.py's Step 1/Step 2,
# so the app can be launched on its own (streamlit run app.py) without
# requiring main.py to have been run first -- and it also repairs a
# stale flights_database.db left over from before routes.py existed
# (one that has a flights table but no routes table).
# ---------------------------------------------------------------------
def ensure_database_ready():
    if not os.path.exists("flights.csv"):
        import gendb  # generates flights.csv as a side effect

    conn = database.get_connection()
    database.create_flights_table(conn)
    database.load_csv_to_table(conn, "flights.csv")

    flights_df = pd.read_csv("flights.csv")
    routes_df = routes.build_routes_df(flights_df)
    routes.create_routes_table(conn)
    routes.load_routes_to_table(conn, routes_df)
    conn.close()


ensure_database_ready()


# ---------------------------------------------------------------------
# Data loading (cached so we don't reprice on every click; cleared after
# a booking so the UI reflects the new seat count immediately)
# ---------------------------------------------------------------------
@st.cache_data(ttl=30)
def get_priced_flights():
    conn = database.get_connection()
    flights_df = load_flights_df(conn)
    flights_df = routes.attach_route_data(flights_df, conn)
    priced = price_all_flights(flights_df)
    conn.close()
    return priced


def refresh():
    get_priced_flights.clear()


# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------
st.title("\U0001f9f9 Potter Airlines")
st.caption(
    "Search a route, watch the price move as inputs change, and book a "
    "seat. Every price and every booking here runs through the same "
    "flight.py / analysis.py / database.py used by main.py."
)

priced = get_priced_flights()
priced["dep_date_parsed"] = pd.to_datetime(priced["dep_date"]).dt.date
cities = sorted(set(priced["source"]) | set(priced["destination"]))
min_date = priced["dep_date_parsed"].min()
max_date = priced["dep_date_parsed"].max()

# ---------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------
st.subheader("Search flights")
col1, col2, col3 = st.columns(3)
with col1:
    source = st.selectbox("From", ["Any"] + cities)
with col2:
    dest_options = ["Any"] + [c for c in cities if c != source]
    destination = st.selectbox("To", dest_options)
with col3:
    sort_by = st.selectbox(
        "Sort by",
        [
            "Price (low to high)", "Price (high to low)",
            "Departure date (soonest first)", "Departure date (latest first)",
        ],
    )

date_range = st.date_input(
    "Departure date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

results = priced.copy()
if source != "Any":
    results = results[results["source"] == source]
if destination != "Any":
    results = results[results["destination"] == destination]

# date_range is a single date while the user has only picked the start of
# the range; only filter once both a start and end date are chosen.
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    results = results[
        (results["dep_date_parsed"] >= start_date)
        & (results["dep_date_parsed"] <= end_date)
    ]

results = results[results["seats_remaining"] > 0]  # only show bookable flights

if sort_by == "Price (low to high)":
    results = results.sort_values("final_price")
elif sort_by == "Price (high to low)":
    results = results.sort_values("final_price", ascending=False)
elif sort_by == "Departure date (soonest first)":
    results = results.sort_values(["dep_date_parsed", "dep_hour"])
else:  # "Departure date (latest first)"
    results = results.sort_values(["dep_date_parsed", "dep_hour"], ascending=False)

st.write(f"**{len(results)}** flights found.")

# ---------------------------------------------------------------------
# Results list
# ---------------------------------------------------------------------
for _, row in results.head(25).iterrows():
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])

        with c1:
            st.markdown(f"**{row['source']} → {row['destination']}**")
            st.caption(f"Flight {row['flight_id']} · {row['dep_date']} at {row['dep_hour']}")

        with c2:
            st.metric("Seats left", f"{int(row['seats_remaining'])} / {int(row['capacity'])}")

        with c3:
            price_label = f"${row['final_price']:.2f}"
            if row["discount_eligible"]:
                st.markdown(f"### ~~${row['raw_price']:.2f}~~ {price_label}")
                st.caption("Last-minute discount applied (15% off)")
            else:
                st.markdown(f"### {price_label}")

        with c4:
            with st.popover("See price breakdown"):
                st.write(f"Base fare: ${row['base_fare']:.2f}")
                st.write(f"Urgency factor: {row['urgency_factor']}")
                st.write(f"Capacity factor: {row['capacity_factor']}")
                st.write(f"Demand factor: {row['demand_factor']}")
                st.write(f"Weekend factor: {row['weekend_factor']}")
                st.write(f"Seasonal factor: {row['seasonal_factor']}")
                st.write(f"Raw price: ${row['raw_price']:.2f}")
                st.write(f"Discount applied: {row['discount_eligible']}")
                st.write(f"Clamped to: ${MIN_FARE}–${MAX_FARE}")

            n_seats = st.number_input(
                "Seats", min_value=1, max_value=int(row["seats_remaining"]),
                value=1, key=f"n_{row['flight_id']}",
            )
            book_col, cancel_col = st.columns(2)

            with book_col:
                if st.button("Book", key=f"book_{row['flight_id']}", type="primary"):
                    try:
                        conn = database.get_connection()
                        new_count = database.book_seats(conn, row["flight_id"], n=int(n_seats))
                        conn.close()
                        refresh()
                        st.success(
                            f"Booked {int(n_seats)} seat(s) on {row['flight_id']}. "
                            f"{new_count} seats now remain."
                        )
                        st.rerun()
                    except ValueError as e:
                        # This is exactly the error Flight.book_seats() raises --
                        # either overbooking or the 3-hour cutoff -- shown to the
                        # user instead of a stack trace.
                        st.error(str(e))

            with cancel_col:
                booked_so_far = int(row["capacity"]) - int(row["seats_remaining"])
                if st.button(
                    "Cancel booking", key=f"cancel_{row['flight_id']}",
                    disabled=(booked_so_far == 0),
                ):
                    try:
                        conn = database.get_connection()
                        new_count = database.cancel_seats(conn, row["flight_id"], n=int(n_seats))
                        conn.close()
                        refresh()
                        st.success(
                            f"Cancelled {int(n_seats)} seat(s) on {row['flight_id']}. "
                            f"{new_count} seats now remain."
                        )
                        st.rerun()
                    except ValueError as e:
                        # Raised by database.cancel_seats() if asked to cancel
                        # more seats than are actually booked.
                        st.error(str(e))

if len(results) == 0:
    st.info("No bookable flights match this search.")

st.divider()
st.caption(
    f"Bookings are refused inside the {BOOKING_CUTOFF} cutoff before "
    f"departure, and can never exceed remaining capacity -- try booking "
    f"a flight departing very soon to see it rejected."
)

# ---------------------------------------------------------------------
# Verify the database directly. This bypasses get_priced_flights()'s
# cache entirely -- it's a fresh, uncached SELECT straight against
# flights_database.db, so it proves a booking actually persisted to
# SQLite rather than just changing something on screen.
# ---------------------------------------------------------------------
with st.expander("Verify the database directly (no caching)"):
    st.caption(
        "This runs a fresh SELECT against flights_database.db every time "
        "you open this, with no cache in between -- proof that a booking "
        "really changed the database, not just this page."
    )
    check_id = st.text_input("Flight ID to look up", value="PA0")
    if st.button("Run SELECT"):
        try:
            conn = database.get_connection()
            row = database.select_flight_by_id(conn, check_id)
            conn.close()
            st.code(dict(row), language="python")
        except ValueError as e:
            st.error(str(e))