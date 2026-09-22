"""
analysis.py
Vectorized Pandas/NumPy pricing and ranking across ALL flights at once --
no per-row Python loop. Reuses the exact factor formulas and constants
from flight.py so the per-flight (Flight.current_price) and vectorized
(price_all_flights) pricing can never drift out of sync.
"""

import numpy as np
import pandas as pd

from flight import (
    MIN_FARE, MAX_FARE,
    DISCOUNT_MAX_DAYS, DISCOUNT_LOAD_THRESHOLD, DISCOUNT_RATE,
)


def load_flights_df(conn):
    return pd.read_sql_query("SELECT * FROM flights", conn)


def validate_flights_df(df):
    """
    DataFrame-wide assumption checks, run before pricing. Same idea as
    the course notebook's 'Inspect before calculating' cell, applied to
    our own columns.
    """
    assert df.notna().all().all(), "flights data contains missing values"
    assert df["flight_id"].is_unique, "flight_id must be unique"
    assert (df["capacity"] > 0).all(), "capacity must be positive"
    assert df["seats_remaining"].between(0, df["capacity"]).all(), \
        "seats_remaining must be between 0 and capacity"
    assert (df["base_fare"] > 0).all(), "base_fare must be positive"
    assert df["route_popularity"].between(0, 1).all(), \
        "route_popularity must be between 0 and 1"
    print("Input checks passed.")


def price_all_flights(df, today=None):
    """
    Vectorized pricing of every flight in df using Pandas/NumPy only.
    df must already have base_fare and route_popularity attached
    (see routes.attach_route_data). Returns a new DataFrame with every
    factor and the final_price as columns.
    """
    df = df.copy()
    validate_flights_df(df)

    today = pd.Timestamp(today) if today is not None else pd.Timestamp.now().normalize()
    dep_date = pd.to_datetime(df["dep_date"])
    days = (dep_date - today).dt.days.clip(lower=0)

    load_factor = 1 - (df["seats_remaining"] / df["capacity"])
    assert load_factor.between(0, 1).all(), "load_factor escaped [0, 1]"

    # Same bucket thresholds as flight.urgency_factor()
    urgency_factor = np.select(
        [days <= 3, days <= 14, days <= 30],
        [1.45, 1.20, 1.08],
        default=1.00,
    )

    # Same formulas as flight.capacity_factor() / flight.demand_factor()
    capacity_factor = 0.90 + 0.50 * load_factor
    demand_factor = 0.90 + 0.30 * df["route_popularity"]

    # Same rule as flight.weekend_factor() (Mon=0 ... Sun=6 in pandas too)
    weekday = dep_date.dt.weekday
    weekend_factor = np.where(weekday >= 5, 1.08, 1.00)

    # Same rule as flight.seasonal_factor()
    month = dep_date.dt.month
    seasonal_factor = np.select(
        [month.isin([7, 8, 12]), month.isin([1, 2])],
        [1.15, 0.95],
        default=1.00,
    )

    raw_price = (
        df["base_fare"] * urgency_factor * capacity_factor
        * demand_factor * weekend_factor * seasonal_factor
    )

    # Same rule as flight.is_discount_eligible()
    discount_eligible = (
        (days <= DISCOUNT_MAX_DAYS)
        & (load_factor < DISCOUNT_LOAD_THRESHOLD)
        & (df["seats_remaining"] > 0)
    )
    discount_factor = np.where(discount_eligible, DISCOUNT_RATE, 1.00)
    discounted_price = raw_price * discount_factor

    final_price = discounted_price.clip(lower=MIN_FARE, upper=MAX_FARE)
    assert final_price.between(MIN_FARE, MAX_FARE).all(), "a fare escaped its bounds"

    df["days_until_departure"] = days
    df["load_factor"] = load_factor.round(3)
    df["urgency_factor"] = urgency_factor
    df["capacity_factor"] = capacity_factor.round(3)
    df["demand_factor"] = demand_factor.round(3)
    df["weekend_factor"] = weekend_factor
    df["seasonal_factor"] = seasonal_factor
    df["raw_price"] = raw_price.round(2)
    df["discount_eligible"] = discount_eligible
    df["final_price"] = final_price.round(2)
    return df


def top_n_by_price(priced_df, n=10):
    return priced_df.sort_values("final_price", ascending=False).head(n)


def average_price_by_route(priced_df):
    return (
        priced_df.groupby(["source", "destination"])["final_price"]
        .mean().round(2).sort_values(ascending=False)
    )


def discounted_flights(priced_df):
    """Flights that actually qualified for the last-minute discount."""
    return priced_df[priced_df["discount_eligible"]]


def flights_with_available_seats(priced_df, min_seats=1):
    return priced_df[priced_df["seats_remaining"] >= min_seats]