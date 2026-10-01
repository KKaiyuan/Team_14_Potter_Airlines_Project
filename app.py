"""Potter Airlines UI. Run from this folder: python -m streamlit run app.py"""

import sqlite3
import booking
# from potterairline_tables import initialize_database

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Potter Airlines", page_icon="\U0001f9f9", layout="wide")


# Modified: read live SQLite inventory; the backend owns all pricing and SQL.
def get_priced_flights():
    return booking.get_priced_flights()


# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------
st.title("\U0001f9f9 Potter Airlines")
# Modified: show customer-facing text instead of Audrey's backend module names.
st.caption("Search flights, compare fares, and choose your seats. Prices are in CAD.")
# Added: safe startup adds the bookings table without resetting flight inventory.
# try:
#     initialize_database()
# except (sqlite3.Error, OSError, ValueError) as error:
#     st.error(f"Could not initialize the database: {error}")
#     st.stop()

if "message" in st.session_state:
    st.success(st.session_state.pop("message"))

# Added: a separate view of persistent orders, including sold-out flights.
page = st.sidebar.radio("Page", ["Search flights", "Booked flights"])
if page == "Booked flights":
    st.subheader("Booked flights")
    st.caption("Shared project booking list. Cancelling an order cancels all its tickets.")
    try:
        bookings_df = booking.get_bookings()
    except (sqlite3.Error, pd.errors.DatabaseError) as error:
        st.error(f"Could not load bookings: {error}")
        st.stop()
    if bookings_df.empty:
        st.info("No bookings yet. Choose Search flights to make a booking.")
    for _, order in bookings_df.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([4, 2, 2])
            with c1:
                st.markdown(f"**{order['origin_city']} ({order['origin_airport_code']}) → "
                            f"{order['destination_city']} ({order['destination_airport_code']})**")
                st.caption(f"Booking #{order['booking_id']} · Flight {order['flight_id']} · "
                           f"{order['dep_date']} at {order['dep_hour']}")
            with c2:
                st.write(f"Tickets: {order['tickets']}")
                st.write(f"Booked fare: CAD ${order['unit_fare']:.2f} per seat")
                st.write(f"Total: CAD ${order['total_fare']:.2f}")
            with c3:
                if st.button("Cancel booking", key=f"cancel_{order['booking_id']}"):
                    try:
                        if not booking.cancel_booking(int(order["booking_id"])):
                            st.error("Cancellation failed. The booking may already be cancelled; refresh and check.")
                            st.stop()
                        st.session_state["message"] = f"Booking #{order['booking_id']} cancelled. Seats restored."
                        st.rerun()
                    except (ValueError, sqlite3.Error) as error:
                        st.error(str(error))
    st.stop()

# Added: show a useful message if preview data is missing or empty.
try:
    priced = get_priced_flights()
except (FileNotFoundError, KeyError, ValueError, sqlite3.Error, pd.errors.DatabaseError):
    st.error("Flight data could not be loaded. Please check the project data files.")
    st.stop()

if priced.empty:
    st.info("No flights are available to display.")
    st.stop()

# Modified: display Kevin's city and airport fields without changing the database.
priced["source"] = priced["origin_city"] + " (" + priced["origin_airport_code"] + ")"
priced["destination"] = priced["destination_city"] + " (" + priced["destination_airport_code"] + ")"
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

# Modified: hide sold-out flights and departures with no valid fare.
results = results[(results["seats_remaining"] > 0) & results["fare"].notna()]

if sort_by == "Price (low to high)":
    results = results.sort_values("fare")
elif sort_by == "Price (high to low)":
    results = results.sort_values("fare", ascending=False)
elif sort_by == "Departure date (soonest first)":
    results = results.sort_values(["dep_date_parsed", "dep_hour"])
else:  # "Departure date (latest first)"
    results = results.sort_values(["dep_date_parsed", "dep_hour"], ascending=False)

st.write(f"**{len(results)}** flights found.")
# Added: make Audrey's existing 25-result display limit clear.
if len(results) > 25:
    st.caption("Showing the first 25 flights. Narrow your search to see other matches.")

# ---------------------------------------------------------------------
# Results list
# ---------------------------------------------------------------------
for _, row in results.head(25).iterrows():
    # Modified: each widget identifies a flight number AND departure date.
    flight_key = f"{row['flight_id']}_{row['dep_date']}"
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([3, 2, 2, 2])

        with c1:
            st.markdown(f"**{row['source']} → {row['destination']}**")
            st.caption(f"Flight {row['flight_id']} · {row['dep_date']} at {row['dep_hour']}")

        with c2:
            st.metric("Seats left", f"{int(row['seats_remaining'])} / {int(row['capacity'])}")

        with c3:
            # Modified: display the fare already calculated by the final branch.
            st.markdown(f"### ${row['fare']:.2f}")

        with c4:
            with st.popover("See price breakdown"):
                st.write(f"Base fare: ${row['base_fare']:.2f}")
                # Modified: show only values returned by the existing pricing script.
                st.write(f"Route popularity score: {row['route_popularity']}")
                st.write(f"Load factor: {row['load_factor']:.0%}")
                st.write(f"Seasonal factor: {row['seasonal_factor']}")
                st.write(f"Holiday factor: {row['holiday']}")
                st.write(f"Applied discount factor: {row['discount_factor']}")
                st.write(f"Final fare per seat: ${row['fare']:.2f}")

            n_seats = st.number_input(
                "Seats", min_value=1, max_value=int(row["seats_remaining"]),
                value=1, key=f"n_{flight_key}",
            )
            # Modified: call the backend; cancellation belongs on the orders page.
            if st.button("Book", key=f"book_{flight_key}", type="primary"):
                try:
                    booking_id = booking.book_flight(
                        row["flight_id"], int(n_seats), row["dep_date"],
                    )
                    if booking_id is None:
                        st.error("Booking failed. Refresh the flight list and check the available seats and departure time.")
                        st.stop()
                    st.session_state["message"] = (
                        f"Booking #{booking_id} confirmed for {int(n_seats)} ticket(s). "
                        "View Booked flights for your order and confirmed fare."
                    )
                    st.rerun()
                except (ValueError, sqlite3.Error) as error:
                    st.error(str(error))

if len(results) == 0:
    st.info("No available flights match this search.")

st.divider()
st.caption("Fares are per seat in CAD. The current fare is confirmed when you book.")
