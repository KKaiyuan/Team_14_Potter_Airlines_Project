"""Potter Airlines UI. Run from this folder: python -m streamlit run app.py"""

import sqlite3
import booking

from config import CITY_CODES
from functional_queries import search_flights, get_flight_date_range


import pandas as pd
import streamlit as st

import base64

import base64
import os

# st.set_page_config(page_title="Potter Airlines", page_icon="\U0001f9f9", layout="wide")
# Acknowledgement: Potter Airlines brand icon designed by Kevin Kaiyuan Chen
st.set_page_config(
    page_title="PotterAirline",
    page_icon="assets/potterairline_favicon_italic_v3_32.png", # NOTE by Kevin: This sets the custom icon for the browser tab of this app
    layout="wide",
)


# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------
# st.title("\U0001f9f9 Potter Airlines")

# Function to convert image file to base64 encoding
def get_image_base64(path):
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# Resolve absolute path to assets/potterairline_favicon_32.png
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
icon_path = os.path.join(BASE_DIR, "assets", "potterairline_logo_italic_v3.png")

img_base64 = get_image_base64(icon_path)

# Render HTML header with unsafe_allow_html=True
st.markdown(
    f"""
    <h1 style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem;">
        <img src="data:image/png;base64,{img_base64}" width="40" height="40" style="object-fit: contain;">
        <span>Potter Airlines</span>
    </h1>
    """,
    unsafe_allow_html=True
)


# Modified: show customer-facing text instead of Audrey's backend module names.
st.caption("Search flights, compare fares, and choose your seats. Prices are in CAD.")

if "message" in st.session_state:
    st.success(st.session_state.pop("message"))

# Added: a separate view of persistent orders, including sold-out flights.
# page = st.sidebar.radio("Page", ["Search flights", "Booked flights"])

# Modified: full-width navigation buttons highlight the selected page.
if "page" not in st.session_state:
    st.session_state.page = "Search flights"

st.sidebar.subheader("Menu")
for label, icon in [("Search flights", ":material/search:"),
                    ("Booked flights", ":material/confirmation_number:")]:
    if st.sidebar.button(
        label, icon=icon, use_container_width=True,
        type="primary" if st.session_state.page == label else "secondary",
        key=f"nav_{label}",
    ):
        st.session_state.page = label
        st.rerun()

page = st.session_state.page

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



try:
    min_date, max_date = get_flight_date_range()
except sqlite3.Error as error:
    st.error(f"Could not load flight dates: {error}")
    st.stop()

if min_date is None or max_date is None:
    st.info("No flights are available to display.")
    st.stop()

min_date = pd.to_datetime(min_date).date()
max_date = pd.to_datetime(max_date).date()

# ---------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------
st.subheader("Search flights")
city_codes = CITY_CODES
col1, col2, col3 = st.columns(3)
with col1:
    source = st.selectbox("From", ["Any"] + city_codes)
with col2:
    dest_options = ["Any"] + [c for c in city_codes if c != source]
    destination = st.selectbox("To", dest_options)
with col3:
    sort_by = st.selectbox(
        "Sort by",
        [
            "Price (low to high)", "Price (high to low)",
            "Departure date (soonest first)", "Departure date (latest first)",
        ],
    )
    
origin_code = None if source == "Any" else source.split(" - ")[-1]
destination_code = None if destination == "Any" else destination.split(" - ")[-1]

date_range = st.date_input(
    "Departure date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)


if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range

    try:
        results = search_flights(
            start_date=start_date,
            end_date=end_date,
            origin_airport_code=origin_code,
            destination_airport_code=destination_code,
            sort_by=sort_by,
        )
    except (ValueError, sqlite3.Error, pd.errors.DatabaseError) as error:
        st.error(f"Could not search flights: {error}")
        st.stop()
else:
    results = pd.DataFrame()

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
            st.markdown(
        f"**{row['origin_city']} ({row['origin_airport_code']}) → "
        f"{row['destination_city']} ({row['destination_airport_code']})**")
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
                "Seats", min_value=1, 
                # max_value=int(row["seats_remaining"]),
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
