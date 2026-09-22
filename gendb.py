import pandas as pd
import random
from datetime import date, time, timedelta

random.seed(42)

flights =[]
size = [100, 150, 200, 250]
cities = ["Toronto", "Vancouver", "Calgary", "Montreal", "Ottawa"]
today = date.today()
departure_hours = [time(hour=0, minute=0), time(hour=4, minute=0), 
                   time(hour=8, minute=0), time(hour=12, minute=0), 
                   time(hour=16, minute=0), time(hour=20, minute=0)]
base_fares = {
   ("Toronto", "Ottawa"): 150,
   ("Toronto", "Montreal"): 180,
   ("Toronto", "Calgary"): 220,
   ("Toronto", "Vancouver"): 300,
   ("Vancouver", "Calgary"): 250,
   ("Vancouver", "Montreal"): 350,
   ("Vancouver", "Ottawa"): 400,
   ("Calgary", "Montreal"): 280,
   ("Calgary", "Ottawa"): 300,
   ("Montreal", "Ottawa"): 130,
}
for (a, b), fare in list(base_fares.items()):
   base_fares[(b, a)] = fare

n=200

for i in range(n):
    
    flight_id = "PA" + str(i)
    
    #Seats remaining  and capacity
    capacity = random.choice(size)
    seats_remaining = random.randint(0, capacity)
    
    #Source and destination cities
    source, destination = random.sample(cities, 2)
    
    #Time until departure
    dep_date = today + timedelta(days=random.randint(0, 365))
    dep_hour = random.choice(departure_hours)

    #Base fares from source to destination
    base_fare = base_fares.get((source, destination), 0)

    flights.append((flight_id,source, destination, capacity, seats_remaining, dep_date, dep_hour, base_fare))

# print(flights)

flights_df = pd.DataFrame(flights, columns=["flight_id", "source", "destination", "capacity", "seats_remaining", "dep_date", "dep_hour","base_fare"])

export_path = "flights.csv"
flights_df.to_csv(export_path, index=False)


