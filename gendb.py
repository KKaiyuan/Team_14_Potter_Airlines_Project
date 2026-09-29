import pandas as pd
import random
from datetime import date, time, timedelta
from config import PLANE_CAPACITY
from fare import DISTANCE_KM, base_fare

random.seed(42)

flights = []
size = list(PLANE_CAPACITY.values())  # Modified: use the seven agreed aircraft capacities.
# cities = [
#     # Ontario: 
#     "Toronto", 
#     "Ottawa", 
#     "Waterloo Region", 
#     "London, Ontario", 
#     "Hamilton", 
#     # British Columbia: 
#     "Vancouver", 
#     "Abbortsford", 
#     "Kelowna", 
#     "Victoria", 
#     "Nanaimo", 
#     "Prince George", 
#     # Alberta: 
#     "Calgary", 
#     "Edmonton",
#     # Quebec:  
#     "Montreal", 
#     "Quebec City"
#     ]
airport_codes = [
    # Ontario: 
    "YYZ", "YTZ", # Toronto
    "YOW", # Ottawa
    "YKF", # Waterloo Region
    "YXU", # London, Ontario
    "YHM", # Hamilton
    # British Columbia: 
    "YVR", # Vancouver
    "YXX", # Abbotsford
    "YLW", # Kelowna
    "YYJ", # Victoria
    "YCD", # Nanaimo
    "YXS", # Prince George
    # Alberta: 
    "YYC", # Calgary
    "YEG", # Edmonton
    # Quebec: 
    "YUL", "YHU", "YMX", # Montreal
    "YQB" # Quebec City
    ]
airport_code_to_city_dict = {
    # Ontario: 
    "YYZ": "Toronto", "YTZ": "Toronto", 
    "YOW": "Ottawa", 
    "YKF": "Waterloo Region", 
    "YXU": "London, Ontario", 
    "YHM": "Hamilton", 
    # British Columbia: 
    "YVR": "Vancouver", 
    "YXX": "Abbotsford", 
    "YLW": "Kelowna", 
    "YYJ": "Victoria", 
    "YCD": "Nanaimo", 
    "YXS": "Prince George", 
    # Alberta: 
    "YYC": "Calgary", 
    "YEG": "Edmonton", 
    # Quebec: 
    "YUL": "Montreal", "YHU": "Montreal", "YMX": "Montreal",
    "YQB": "Quebec City"
}


today = date.today()
departure_hours = [time(hour=0, minute=0), time(hour=4, minute=0), 
                   time(hour=8, minute=0), time(hour=12, minute=0), 
                   time(hour=16, minute=0), time(hour=20, minute=0)]

n=800

seen_flight_date_pairs = set()

flights = []
i = 0
max_attempts_per_row = 1000  # safety valve to avoid infinite loop if space gets too crowded

while i < n:
    flight_id = "PA" + str(random.randint(1, 399))
    dep_date = today + timedelta(days=random.randint(0, 365))

    # Retry if this (flight_id, date) combo already exists
    attempts = 0
    while (flight_id, dep_date) in seen_flight_date_pairs:
        flight_id = "PA" + str(random.randint(1, 399))
        dep_date = today + timedelta(days=random.randint(0, 365))
        attempts += 1
        if attempts >= max_attempts_per_row:
            raise RuntimeError(
                "Could not find a unique (flight_id, date) pair after many attempts — "
                "consider increasing the flight_id range or date range."
            )

    seen_flight_date_pairs.add((flight_id, dep_date))

    # Seats remaining and capacity
    capacity = random.choice(size)
    seats_remaining = random.randint(0, capacity)

    """
    NOTE by Kevin: 
        I realized that: 
            - there are no flights from YYZ to YTZ (i.e. too short for a flight), 
            - there are no flights from YTZ to YVR (YTZ is a small airport not handling flights to Vancouver), 
            - there are no longer passenger flights out of YMX (only cargo flights now), 
            - etc.
        For the sake of this project, we will not include these constraints, i.e. these flights might be included.
        TODO in the future: add constraints not to include non-realistic flights
    """
    
    origin_airport_code = ""
    destination_airport_code = ""
    # Ensure that none of the same airport code is repeated
    while True:
        # Origin and destination airport codes
        origin_airport_code, destination_airport_code = random.sample(airport_codes, 2)
        if origin_airport_code != destination_airport_code:
            break

    # Origin and destination cities
    origin_city = airport_code_to_city_dict[origin_airport_code]
    destination_city = airport_code_to_city_dict[destination_airport_code]

    # Time until departure
    dep_hour = random.choice(departure_hours)

    # Assigned distance and the agreed distance-based base fare
    distance_km = DISTANCE_KM[tuple(sorted([origin_city, destination_city]))]
    fare = base_fare(distance_km)

    flights.append((
        flight_id, 
        origin_city, origin_airport_code, 
        destination_city, destination_airport_code, 
        capacity, seats_remaining, 
        dep_date, dep_hour, 
        distance_km, fare
    ))

    i += 1

# print(flights)

flights_df = pd.DataFrame(flights, columns=["flight_id", "origin", "destination", "capacity", "seats_remaining", "dep_date", "dep_hour", "distance_km", "base_fare"])

export_path = "flights.csv"
flights_df.to_csv(export_path, index=False)
