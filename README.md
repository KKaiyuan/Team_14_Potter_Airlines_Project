# Potter Airlines Dynamic Revenue Management System

## Purpose
A Python system that prices fictional Potter Airlines flights dynamically,
based on explainable business signals: time to departure, remaining
capacity, route popularity, and weekend/seasonal timing. It also enforces
a real-world booking rule (no bookings within 3 hours of departure) and
applies a targeted last-minute discount to flights genuinely at risk of
flying nearly empty.

## Files
- `gendb.py` — generates fictional flight data (`flights.csv`): routes,
  departure date/hour, capacity, seats remaining.
- `routes.py` — defines `base_fare` and `route_popularity` per route as a
  business/policy choice, stores them in a `routes` SQLite table, and
  attaches them to a flights DataFrame. Routes are derived from whatever
  cities actually appear in `flights.csv`, so adding new cities to
  `gendb.py` doesn't require touching this file — any route without an
  explicit value just falls back to a printed-warning default.
- `flight.py` — the `Flight` class and the fare calculation
  (`price_fare`, `urgency_factor`, `capacity_factor`, `demand_factor`,
  `weekend_factor`, `seasonal_factor`, `is_discount_eligible`), each with
  assertions on their assumptions. Also enforces the 3-hour booking
  cutoff in `Flight.book_seats()`.
- `analysis.py` — prices every flight at once using vectorized
  Pandas/NumPy (`np.select`, `np.where`, no Python loop), reusing the
  exact constants from `flight.py` so the two pricing paths can't drift
  apart. Also has ranking/filtering helpers.
- `database.py` — SQLite persistence for the `flights` table:
  parameterized `CREATE`, `INSERT`, `SELECT` (joined with `routes`),
  `UPDATE`, and `DELETE`. `book_seats()` validates a booking through the
  `Flight` class *before* writing to the database, so an invalid booking
  never touches SQL at all.
- `main.py` — runs the full workflow end to end.

## Setup / Run
```
pip install pandas numpy
python main.py
```
This generates `flights.csv` if it doesn't already exist, builds
`flights_database.db` (`flights` + `routes` tables), prices all 200
flights, prints rankings, books seats on a flight, and demonstrates
validation plus an edge case (booking a flight 5 minutes before
departure, and two invalid `Flight` constructions).

## Pricing logic
```
price = base_fare x urgency_factor x capacity_factor x demand_factor
        x weekend_factor x seasonal_factor
```
then a last-minute discount is applied on top when eligible, and the
result is clamped to a sensible fare range.

- **urgency_factor** — step function on days until departure (1.00 more
  than 30 days out, up to 1.45 inside 3 days). `days_until_departure` is
  never stored; it's computed live from `dep_date`, since "today" changes
  every day the app runs.
- **capacity_factor** — `0.90 + 0.50 x load_factor`, where `load_factor`
  (`1 - seats_remaining/capacity`) is likewise computed live, not stored.
- **demand_factor** — `0.90 + 0.30 x route_popularity`, a fixed per-route
  business value (see Design choices).
- **weekend_factor** — `1.08` if `dep_date` falls on a Saturday/Sunday,
  else `1.00`. Also derived live rather than stored, to avoid it ever
  disagreeing with `dep_date`.
- **seasonal_factor** — `1.15` in peak months (Jul/Aug/Dec), `0.95` in
  deep winter (Jan/Feb), `1.00` otherwise.
- **Last-minute discount** — 15% off, but *only* when a flight is 3 days
  or fewer from departure AND under 30% booked AND still has seats. This is
  deliberately tighter than a looser "14 days / 60% load" rule: it
  targets flights genuinely at risk of flying empty, rather than
  discounting a large share of flights and giving up revenue we didn't
  need to.
- Every fare is clamped to **$45–$1,500** regardless of the factors
  above.

## Design choices
- **`routes` is a separate table from `flights`.** `base_fare` and
  `route_popularity` are properties of a *route*, not a single flight, so
  storing them once avoids duplicating the same value across every
  flight on that route, and keeps static policy data separate from the
  flight data that gendb.py regenerates.
- **Nothing derivable is stored as its own column.**
  `days_until_departure`, `load_factor`, and weekend status are all
  computed on demand from `dep_date`/`seats_remaining`/`capacity` rather
  than persisted, so they can never go stale or disagree with the
  columns they're derived from.
- **Booking validation happens before any SQL runs.**
  `database.book_seats()` rebuilds a `Flight` object from the row and
  calls `Flight.book_seats()` first; if that raises (overbooking, or
  inside the 3-hour cutoff), the database is never touched.
- **The vectorized and per-flight pricing paths share the same
  constants**, imported from `flight.py` into `analysis.py`, and were
  cross-checked to produce identical prices for the same flight.

## Known limitations
- Flight data is synthetic (seeded random generation), not real airline
  data.
- `base_fare` and `route_popularity` are assigned directly as business
  assumptions rather than derived from real distance or historical
  booking data — a reasonable simplification for a class project.
- No optimization/forecasting is attempted; factors are hand-tuned,
  explainable multipliers, as the assignment specifies.
- No LLM/API rationale generation is included in this version.