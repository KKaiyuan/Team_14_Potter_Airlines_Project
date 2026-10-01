# Potter Airlines: pricing, booking and cancellation

This fictional airline project prices Kevin's 800 generated flight occurrences and lets users search, book and cancel through a simple Streamlit UI. Data is persisted in SQLite. No real tickets or payments are processed.

## Setup and run

Open a terminal in this project folder. Use Python 3.10 or later.

```sh
python -m pip install -r requirements.txt
python main.py
```

Open the local URL printed by Streamlit and keep the terminal running. You can also use VS Code's Run Python File button on main.py (not app.py). The launcher uses the current Python environment and sets the project folder as the working directory. The direct command `python -m streamlit run app.py` still works when run from this folder.

The supplied database retains Kevin's 278 routes and 800 flights, with an empty bookings table added. Startup preserves existing inventory and orders. If no flights table exists, startup creates the schema and loads the supplied CSV once.

Optional commands:

```sh
python potterairline_tables.py
python pricing_function_new.py
python -m unittest -v test_project
```

The pricing command produces a CSV-based pricing export; the UI instead prices current database inventory. Tests use temporary databases and do not modify the project database.

## Workflow and design

Search flights filters by city/airport and date and sorts by price or departure. The display retains Audrey's first-25-results limit; narrow the filters to find other flights. Prices are per seat in CAD.

Book passes a flight number, departure date and ticket quantity to booking.py. The backend validates the request, calculates the current fare, deducts seats and inserts the order in one transaction. The confirmed per-seat fare is saved so a later price change does not alter an existing order's displayed cost.

Booked flights is a separate sidebar page. Its dataframe is loaded from the bookings table, including orders for flights that are now sold out. Cancel booking restores every ticket in that order and executes a parameterized DELETE in one transaction. This removes the order from the active list. Repeating a cancellation cannot restore seats twice. A booking ID is never reused (AUTOINCREMENT).

There is no customer authentication: everyone using this database sees the same shared order list. Authentication is optional in the project specification.

## Schema and SQL operations

- routes: primary key (origin_airport_code, destination_airport_code).
- flights: primary key (flight_id, dep_date), foreign key to routes. Flight numbers can repeat on different dates.
- bookings: booking_id, flight_id, dep_date, tickets, unit_fare, booked_at; composite foreign key to flights. It stores active orders, not cancellation history.

CREATE TABLE is in potterairline_tables.py. INSERT, parameterized SELECT, conditional UPDATE and parameterized DELETE are exercised through booking.py. SQL values are supplied with placeholders. BEGIN IMMEDIATE serializes inventory changes; transaction context managers roll back either operation if its partner fails, and finally closes booking/cancellation connections. Read-only helpers use closing().

Flight in flight.py validates capacity, inventory, quantity and departure time and is used by the booking workflow. Pandas vectorized date arithmetic, load-factor calculations and order-total calculations operate across multiple rows. Row-wise fare calculation is retained for clarity and is not described as vectorized.

## Pricing logic

Kevin's existing fare and discount rules are retained. Base fare is multiplied by time, capacity, route demand, seasonal and holiday factors. A qualifying discount is then applied, subject to his minimum-fare eligibility rule. The final fare is bounded by 80% of base fare and CAD 1,500 for the supplied dataset.

- Time factor: up to 1 day = 1.00; over 1 through 7 days = 1.35; over 7 through 21 days = 1.10; otherwise 1.00.
- Capacity factor: 1 + 0.45 × load factor; load factor = 1 − remaining seats / capacity.
- Demand factor: 0.9 + 0.3 × assumed route popularity; unlisted city pairs default to 0.5. Both directions share a score.
- Seasonal values come from config.py, with its source and modelling caveat retained.
- Canadian default public-holiday calendar: 1.2 on a listed holiday/observed date, otherwise 1.0. The 20% premium is a project assumption.
- Discounts: early booking at least 60 days ahead with load below 30% = 0.90; Tuesday/Wednesday = 0.95; less than four hours before departure = 0.85. Only the strongest discount applies. If it would go below the minimum fare, it is rejected under Kevin's rule.

Route popularity and premium magnitudes are simulation assumptions, not estimated market price elasticities. References for aircraft capacity and seasonality remain in config.py. No LLM or API is used.

## Validation and limitations

Tests cover boundary pricing, discounts, invalid inputs, composite flight identity, persistent orders, sold-out cancellation, repeated cancellation, parameter safety, concurrent booking and rollback on failed INSERT/DELETE. UI integration was separately checked using Kevin's actual dataset.

Times are treated as naive project-local datetimes, without airport time-zone conversion. The synthetic schedule may contain unrealistic routes or aircraft assignments. Initial random occupied seats are baseline inventory, not customer orders; only new recorded orders can be cancelled. Cancellation removes an entire order and has no refund workflow or cancellation-history archive. A shared unauthenticated UI is intended for the class demo, not public airline operations.

The inherited potterairline.ipynb is retained for reference, but contains older incompatible schemas/column names and destructive setup cells. Do not run it against this database. Use app.py and potterairline_tables.py as the supported workflow. Do not regenerate or reload data to refresh the UI: live inventory is read directly from SQLite.

## Suggested 4–5 minute recording

1. Launch the app and explain the route, flight and booking tables (0:00–0:45).
2. Filter flights, compare fares and explain one price breakdown and discount (0:45–1:45).
3. Book two seats; show the saved order, price and reduced availability (1:45–2:45).
4. Cancel on Booked flights; show the order deleted and seats restored. Explain the parameterized DELETE and transaction (2:45–3:30).
5. Run tests; demonstrate rejected overbooking or duplicate cancellation. Show Flight validation and vectorized load-factor calculation (3:30–4:45).

AI assistance was used for UI integration, debugging and tests. The group must understand and explain all submitted code. Record and submit the demo separately.

## Minimal-change revision

This revision restores Kevin's book_flight validation order, cursor.execute style, printed messages and None-on-failure convention. cancel_booking retains his try/with/except/finally layout and False-on-failure convention. The UI checks return values before reporting success. Database errors roll back first, then print a message and return failure, rather than being exposed as exceptions to the UI.

Necessary changes remain: use flight_id plus dep_date, store confirmed fare, DELETE the active order, preserve inventory during startup, adapt pricing to new field names and live data, and add the rubric-required Flight class. Wrapping the existing booking body in a transaction adds indentation; it does not replace the original sequence of checks. The read-only dataframe helpers are appended after the original functions. Existing pricing rules, generators, capacities, route data and seasonal constants are unchanged.
