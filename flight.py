from util import is_holiday
from datetime import date, time, datetime

class Flight:
    def __init__(self, source, destination, seats_remaining, capacity, dep_date, dep_hour):
        self.source = source
        self.destination = destination
        self.seats_remaining = seats_remaining
        self.capacity = capacity
        self.dep_date = dep_date
        self.dep_hour = dep_hour
        
    def holiday_factor(self):
        factor = 1.2 if is_holiday(self.dep_date) else 1
        return factor
    
    def seasonal_factor(self):
        month_day = (self.dep_date.month, self.dep_date.day)
        if month_day >= (12, 15) or month_day <= (1, 15) or ((6,21) <= month_day <= (8, 25)):
            factor = 1.2
        else:
            factor = 1
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
    