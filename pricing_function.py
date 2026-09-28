import pandas as pd
import holidays
from config import SEASONAL_FACTOR


# Added: read the eight-column flight dataset without creating a route table.
flights_df = pd.read_csv("flights.csv")

# These popularity scores are project assumptions, not observed traffic estimates.
route_popularity_scores = {
    ("Ottawa", "Toronto"): 0.6,
    ("Toronto", "Vancouver"): 0.8,
    ("Calgary", "Toronto"): 0.5,
    ("Montreal", "Toronto"): 0.7,
    ("Calgary", "Vancouver"): 0.5,
    ("Montreal", "Vancouver"): 0.5,
    ("Ottawa", "Vancouver"): 0.5,
    ("Calgary", "Montreal"): 0.5,
    ("Calgary", "Ottawa"): 0.5,
    ("Montreal", "Ottawa"): 0.5,
}



flights_df["route_popularity"] = [
    route_popularity_scores.get(
        tuple(sorted((source, destination))), 0.5
    )
    for source, destination in zip(
        flights_df["source"], flights_df["destination"]
    )
]

departure_date = pd.to_datetime(
    flights_df["dep_date"].astype(str)
    + " "
    + flights_df["dep_hour"].astype(str)
)

now = pd.Timestamp.now()

flights_df["days_until_departure"] = (
    departure_date - now
) / pd.Timedelta(days=1)

# Added: use the shared seasonal factor for the departure month.
flights_df["seasonal_factor"] = (
    departure_date.dt.month.map(SEASONAL_FACTOR)
)

# Added: use Canadian public holidays without province-specific additions.
# Reference: https://holidays.readthedocs.io/en/latest/auto_gen_docs/canada/
canada_holidays = holidays.CA(observed=True)
# Added: the 20% departure-day premium is a project assumption.
flights_df["holiday"] = [
    1.2 if day in canada_holidays else 1.0
    for day in departure_date.dt.date
]


def calculate_fare(
    base_fare,
    days_until_departure,
    seats_remaining,
    capacity,
    route_popularity,
    seasonal_factor,
    holiday=1.0,  # Added: default to no holiday premium.
):
    if base_fare <= 0:
        raise ValueError("base_fare must be greater than 0")

    if capacity <= 0:
        raise ValueError("capacity must be greater than 0")

    # Fixed: check both the lower and upper seat limits.
    if not 0 <= seats_remaining <= capacity:
        raise ValueError("seats_remaining must be between 0 and capacity")

    if not 0 <= route_popularity <= 1:
        raise ValueError("route_popularity must be between 0 and 1")

    if seasonal_factor <= 0:
        raise ValueError("seasonal_factor must be greater than 0")

    # Added: validate the holiday multiplier.
    if holiday <= 0:
        raise ValueError("holiday must be greater than 0")

    if days_until_departure <= 0:
        return float("nan")

    if days_until_departure < 4 / 24:
        time_factor = 0.85
    elif days_until_departure <= 1:
        time_factor = 1.00
    elif days_until_departure <= 7:
        time_factor = 1.35
    elif days_until_departure <= 21:
        time_factor = 1.10
    else:
        time_factor = 1.00

    load_factor = 1 - seats_remaining / capacity
    capacity_factor = 1 + 0.45 * load_factor
    demand_factor = 0.9 + 0.3 * route_popularity

    final_fare = (
        base_fare
        * time_factor
        * capacity_factor
        * demand_factor
        * seasonal_factor
        * holiday  # Added: apply the holiday premium before the fare limits.
    )

    min_fare = base_fare * 0.8
    max_fare = 1500

    return round(min(max(final_fare, min_fare), max_fare), 2)


flights_df["fare"] = flights_df.apply(
    lambda row: calculate_fare(
        base_fare=row["base_fare"],
        days_until_departure=row["days_until_departure"],
        seats_remaining=row["seats_remaining"],
        capacity=row["capacity"],
        route_popularity=row["route_popularity"],
        seasonal_factor=row["seasonal_factor"],
        holiday=row["holiday"],  # Added: pass the departure-day holiday factor.
    ),
    axis=1,
)