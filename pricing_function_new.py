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
        tuple(sorted((origin, destination))), 0.5
    )
    for origin, destination in zip(
        flights_df["origin"], flights_df["destination"]
    )
]

departure_date = pd.to_datetime(
    flights_df["dep_date"].astype(str)
    + " "
    + flights_df["dep_hour"].astype(str)
)

flights_df["day_of_week"] = departure_date.dt.dayofweek
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


# Modified: price current database rows without reading or overwriting CSV on import.
def price_flights(flights_df, now=None):
    flights_df = flights_df.copy()
    if flights_df.empty:
        return flights_df
    flights_df["route_popularity"] = [
        route_popularity_scores.get(
            tuple(sorted((source, destination))), 0.5
        )
        for source, destination in zip(
            flights_df["origin_city"], flights_df["destination_city"]
        )
    ]

    departure_date = pd.to_datetime(
        flights_df["dep_date"].astype(str)
        + " "
        + flights_df["dep_hour"].astype(str)
    )

    flights_df["day_of_week"] = departure_date.dt.dayofweek
    now = pd.Timestamp.now() if now is None else pd.Timestamp(now)


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

    flights_df[
        ["fare", "discount_factor", "discount_eligible"]
    ] = flights_df.apply(
        lambda row: calculate_fare(
            base_fare=row["base_fare"],
            days_until_departure=row["days_until_departure"],
            seats_remaining=row["seats_remaining"],
            capacity=row["capacity"],
            route_popularity=row["route_popularity"],
            seasonal_factor=row["seasonal_factor"],
            holiday=row["holiday"],
            day_of_week=row["day_of_week"],
        ),
        axis=1,
        result_type="expand",
    )
    
    # Added: meaningful vectorized analysis across all flights.
    flights_df["load_factor"] = 1 - flights_df["seats_remaining"] / flights_df["capacity"]
    return flights_df

def calculate_discount(
    days_until_departure,
    seats_remaining,
    capacity,
    day_of_week
):
    if days_until_departure <= 0 or seats_remaining <= 0:
        return 1.00
    
    load_factor = 1 - seats_remaining / capacity

    early_bird_discount = (
        0.9
        if days_until_departure >= 60 and load_factor < 0.30
        else 1.00
    )  

    midweek_discount = (
        0.95
        if day_of_week in [1, 2] else 1.00
    )

    last_minute_discount = (
        0.85 if days_until_departure < 4 / 24 else 1.00
    )

    return min(
        early_bird_discount,
        midweek_discount,
        last_minute_discount
    )



def calculate_fare(
    base_fare,
    days_until_departure,
    seats_remaining,
    capacity,
    route_popularity,
    seasonal_factor,
    holiday=1.0,
    day_of_week=0
     # Added: default to no holiday premium.
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

    # Return: fare, applied discount factor, discount eligibility.
    if days_until_departure <= 0:
        # return float("nan"), 1.00, False
        return -1 # TODO: deal with past flights

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

    fare_before_discount = (
        base_fare
        * time_factor
        * capacity_factor
        * demand_factor
        * seasonal_factor
        * holiday
    )

    discount_factor = calculate_discount(
        days_until_departure,
        seats_remaining,
        capacity,
        day_of_week,
    )

    min_fare = base_fare * 0.8
    max_fare = 1500

    discounted_fare = fare_before_discount * discount_factor

    # A discount is eligible only if the discounted fare is above the minimum fare and the factor is less than 1.00. 
    discount_eligible = (
        discount_factor < 1.00
        and discounted_fare >= min_fare
    )

    if discount_eligible:
        final_fare = discounted_fare
    else:
        # Reject the discount and restore the undiscounted price.
        discount_factor = 1.00
        final_fare = fare_before_discount

    final_fare = round(
        min(max(final_fare, min_fare), max_fare),
        2,
    )

    return final_fare, discount_factor, discount_eligible



flights_df[
    ["fare", "discount_factor", "discount_eligible"]
] = flights_df.apply(
    lambda row: calculate_fare(
        base_fare=row["base_fare"],
        days_until_departure=row["days_until_departure"],
        seats_remaining=row["seats_remaining"],
        capacity=row["capacity"],
        route_popularity=row["route_popularity"],
        seasonal_factor=row["seasonal_factor"],
        holiday=row["holiday"],
        day_of_week=row["day_of_week"],
    ),
    axis=1,
    result_type="expand",
)

# flights_df.to_csv("priced_flights.csv", index=False)


if __name__ == "__main__":
    flights_df = price_flights(pd.read_csv("flights.csv"))
    flights_df.to_csv("priced_flights.csv", index=False)
