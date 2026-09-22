"""
flight.py
The Flight class and the fare calculation.

price = base_fare x urgency_factor x capacity_factor x demand_factor
        x weekend_factor x seasonal_factor

Style matches the course notebook: step-function urgency via bucketed
thresholds, simple linear factors for the rest, clipped to a min/max fare.
"""

from datetime import date, datetime, time, timedelta

MIN_FARE = 45
MAX_FARE = 1500
BOOKING_CUTOFF = timedelta(hours=3)  # can't book within 3h of departure

# Last-minute discount: only for flights that are genuinely at risk of
# flying nearly empty -- close to departure AND well under-booked.
# Deliberately tighter than "14 days / 60% load" so it targets real risk
# instead of discounting a large share of flights and giving up revenue
# we didn't need to.
DISCOUNT_MAX_DAYS = 3
DISCOUNT_LOAD_THRESHOLD = 0.30
DISCOUNT_RATE = 0.85  # 15% off the raw price


def _parse_date(d):
    if isinstance(d, date):
        return d
    return datetime.strptime(str(d), "%Y-%m-%d").date()


def urgency_factor(days_until_departure):
    """Same bucket thresholds as the course notebook."""
    assert days_until_departure >= 0, "days_until_departure cannot be negative"
    if days_until_departure <= 3:
        return 1.45
    if days_until_departure <= 14:
        return 1.20
    if days_until_departure <= 30:
        return 1.08
    return 1.00


def capacity_factor(load_factor):
    """0.90 + 0.50 x load_factor, same as the course notebook."""
    assert 0.0 <= load_factor <= 1.0, "load_factor must be in [0, 1]"
    return 0.90 + 0.50 * load_factor


def demand_factor(route_popularity):
    """0.90 + 0.30 x route_popularity, same as the course notebook."""
    assert 0.0 <= route_popularity <= 1.0, "route_popularity must be in [0, 1]"
    return 0.90 + 0.30 * route_popularity


def weekend_factor(departure_date):
    d = _parse_date(departure_date)
    return 1.08 if d.weekday() >= 5 else 1.00  # Sat/Sun


def seasonal_factor(departure_date):
    """Peak months (summer + December) cost more; deep winter costs less."""
    d = _parse_date(departure_date)
    if d.month in (7, 8, 12):
        return 1.15
    if d.month in (1, 2):
        return 0.95
    return 1.00


def is_discount_eligible(days_until_departure, load_factor, seats_remaining):
    """
    True only for flights at real risk of flying nearly empty: close to
    departure, well under-booked, and still has seats to sell.
    """
    assert days_until_departure >= 0, "days_until_departure cannot be negative"
    assert 0.0 <= load_factor <= 1.0, "load_factor must be in [0, 1]"
    assert seats_remaining >= 0, "seats_remaining cannot be negative"
    return (
        days_until_departure <= DISCOUNT_MAX_DAYS
        and load_factor < DISCOUNT_LOAD_THRESHOLD
        and seats_remaining > 0
    )


def price_fare(base_fare, days_until_departure, load_factor,
                route_popularity, departure_date, seats_remaining):
    """Compute the bounded final fare for one flight, applying the
    last-minute discount when eligible."""
    assert base_fare > 0, "base_fare must be positive"

    uf = urgency_factor(days_until_departure)
    cf = capacity_factor(load_factor)
    df = demand_factor(route_popularity)
    wf = weekend_factor(departure_date)
    sf = seasonal_factor(departure_date)

    raw_price = base_fare * uf * cf * df * wf * sf

    eligible = is_discount_eligible(days_until_departure, load_factor, seats_remaining)
    discount_factor = DISCOUNT_RATE if eligible else 1.00
    discounted_price = raw_price * discount_factor

    final_price = round(min(max(discounted_price, MIN_FARE), MAX_FARE), 2)

    assert MIN_FARE <= final_price <= MAX_FARE, "fare escaped its bounds"
    return final_price, {
        "urgency_factor": uf, "capacity_factor": round(cf, 3),
        "demand_factor": round(df, 3), "weekend_factor": wf,
        "seasonal_factor": sf, "raw_price": round(raw_price, 2),
        "discount_eligible": eligible, "discount_factor": discount_factor,
    }


class Flight:
    """One Potter Airlines flight; knows how to price itself."""

    def __init__(self, flight_id, source, destination, dep_date, dep_hour,
                 capacity, seats_remaining, base_fare):
        assert capacity > 0, f"{flight_id}: capacity must be positive"
        assert 0 <= seats_remaining <= capacity, \
            f"{flight_id}: seats_remaining out of range for capacity"
        assert base_fare > 0, f"{flight_id}: base_fare must be positive"
        assert source != destination, f"{flight_id}: source and destination must differ"

        self.flight_id = flight_id
        self.source = source
        self.destination = destination
        self.dep_date = _parse_date(dep_date)
        self.dep_hour = dep_hour
        self.capacity = int(capacity)
        self.seats_remaining = int(seats_remaining)
        self.base_fare = float(base_fare)

    @property
    def load_factor(self):
        return 1 - (self.seats_remaining / self.capacity)

    @property
    def is_weekend(self):
        """True if dep_date falls on a Saturday or Sunday. Derived, not stored."""
        return self.dep_date.weekday() >= 5

    @property
    def departure_datetime(self):
        """Combine dep_date + dep_hour into one timestamp. Derived, not stored."""
        dep_hour = self.dep_hour
        if isinstance(dep_hour, str):
            dep_hour = datetime.strptime(dep_hour, "%H:%M:%S").time()
        return datetime.combine(self.dep_date, dep_hour)

    def days_until_departure(self, today=None):
        today = today or date.today()
        return max((self.dep_date - today).days, 0)

    def book_seats(self, n=1, now=None):
        """
        Reduce seats_remaining by n. Raises if it would go negative, or if
        the flight is inside the 3-hour booking cutoff before departure.
        """
        assert n > 0, "must book at least one seat"
        now = now or datetime.now()

        time_to_departure = self.departure_datetime - now
        if time_to_departure < BOOKING_CUTOFF:
            raise ValueError(
                f"{self.flight_id}: booking closed -- departs "
                f"{self.departure_datetime}, which is within the "
                f"{BOOKING_CUTOFF} cutoff (now: {now})"
            )

        if n > self.seats_remaining:
            raise ValueError(
                f"{self.flight_id}: cannot book {n} seats, only "
                f"{self.seats_remaining} remaining"
            )
        self.seats_remaining -= n

    def current_price(self, route_popularity, today=None):
        return price_fare(
            base_fare=self.base_fare,
            days_until_departure=self.days_until_departure(today),
            load_factor=self.load_factor,
            route_popularity=route_popularity,
            departure_date=self.dep_date,
            seats_remaining=self.seats_remaining,
        )

    def __repr__(self):
        return (f"Flight({self.flight_id}, {self.source}->{self.destination}, "
                f"{self.dep_date}, seats={self.seats_remaining}/{self.capacity})")