from dataclasses import dataclass
from datetime import datetime


# Added: a useful class that validates inventory and a booking request.
@dataclass
class Flight:
    flight_id: str
    dep_date: str
    dep_hour: str
    capacity: int
    seats_remaining: int

    def __post_init__(self):
        if type(self.capacity) is not int or self.capacity <= 0:
            raise ValueError("Capacity must be a positive whole number.")
        if type(self.seats_remaining) is not int or not 0 <= self.seats_remaining <= self.capacity:
            raise ValueError("Seats remaining must be between zero and capacity.")

    def validate_booking(self, tickets, now=None):
        if type(tickets) is not int or tickets <= 0:
            raise ValueError("Tickets must be a positive whole number.")
        departure = datetime.fromisoformat(f"{self.dep_date} {self.dep_hour}")
        if departure <= (now or datetime.now()):
            raise ValueError("This flight has already departed.")
        if tickets > self.seats_remaining:
            raise ValueError("Not enough available seats.")
