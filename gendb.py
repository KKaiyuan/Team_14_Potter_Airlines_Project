import pandas as pd
import random
from datetime import date, time, timedelta
from config import PLANE_CAPACITY
from fare import DISTANCE_KM, base_fare

random.seed(42)

flights =[]
size = list(PLANE_CAPACITY.values())  # Modified: use the seven agreed aircraft capacities.
cities = ["Toronto", "Vancouver", "Calgary", "Montreal", "Ottawa"]
today = date.today()
departure_hours = [time(hour=0, minute=0), time(hour=4, minute=0), 
                   time(hour=8, minute=0), time(hour=12, minute=0), 
                   time(hour=16, minute=0), time(hour=20, minute=0)]

n=800

for i in range(n):
    
    flight_id = "PA" + str(random.randint(1, 399))
    
    #Seats remaining  and capacity
    capacity = random.choice(size)
    seats_remaining = random.randint(0, capacity)
    
    #Origin and destination cities
    origin, destination = random.sample(cities, 2)
    
    #Time until departure
    dep_date = today + timedelta(days=random.randint(0, 365))
    dep_hour = random.choice(departure_hours)
    

    # Added: assigned distance and the agreed distance-based base fare.
    distance_km = DISTANCE_KM[tuple(sorted([origin, destination]))]
    fare = base_fare(distance_km)
    flights.append((flight_id,origin, destination, capacity, seats_remaining, dep_date, dep_hour, distance_km, fare))

# print(flights)

flights_df = pd.DataFrame(flights, columns=["flight_id", "origin", "destination", "capacity", "seats_remaining", "dep_date", "dep_hour", "distance_km", "base_fare"])

export_path = "flights.csv"
flights_df.to_csv(export_path, index=False)


