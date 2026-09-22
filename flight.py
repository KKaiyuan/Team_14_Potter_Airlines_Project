from util import is_holiday
from config import SEASONAL_FACTOR
from fare import DISTANCE_KM, base_fare
from datetime import date, time, datetime

class Flight:
    def __init__(self, source, destination, seats_remaining, capacity, dep_date, dep_hour):
        self.source = source
        self.destination = destination
        self.seats_remaining = seats_remaining
        self.capacity = capacity
        self.dep_date = dep_date
        self.dep_hour = dep_hour
        # Added: expose distance and base fare on the flight.
        self.distance_km = DISTANCE_KM[tuple(sorted([source, destination]))]
        self.base_fare = base_fare(self.distance_km)
        
    def holiday_factor(self):
        factor = 1.2 if is_holiday(self.dep_date) else 1
        return factor
    
    def seasonal_factor(self):
        # Modified: use the shared BTS factor for the departure month.
        factor = SEASONAL_FACTOR[self.dep_date.month]
        return factor
        
        
    
    def time_till_departure(self):
        dep_datetime = datetime.combine(self.dep_date, self.dep_hour)
        time_until_departure = dep_datetime - datetime.now()
        days = time_until_departure.days
        seconds = time_until_departure.seconds
        hours = seconds // 3600
        return(f"{days} days {hours:02d} hours")
    

f1 = Flight("Toronto", "Montreal", 14, 100, date(year=2027, month=12, day=31), time(hour=4, minute=00, second=00))
print(f1.time_till_departure())
print(f1.holiday_factor())
    