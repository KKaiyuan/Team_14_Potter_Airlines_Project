import pandas as pd
import random
from datetime import date, datetime, timedelta

random.seed(42)

flights =[]
size = [100, 150, 200, 250]
cities = ["Toronto", "Vancouver", "Calgary", "Montreal", "Ottawa"]
today = date.today()

n=200

for i in range(n):
    
    flight_id = "PA" + str(i)
    capacity = random.choice(size)
    seats_remaining = random.randint(0, capacity)
    source, destination = random.sample(cities, 2)
    dep_date = today + timedelta(days=random.randint(0, 365))

    flights.append((flight_id,source, destination, capacity, seats_remaining, dep_date))
    
# print(flights)

flights_df = pd.DataFrame(flights, columns=["flight_id", "source", "destination", "capacity", "seats_remaining", "dep_date"])

export_path = "flights.csv"
flights_df.to_csv(export_path, index=False)


