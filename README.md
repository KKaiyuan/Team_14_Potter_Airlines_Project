# Potter Airlines: pricing, booking and cancellation

This fictional airline project prices Kevin's 800 generated flight occurrences and lets users search, book and cancel through a simple Streamlit UI. Data is persisted in SQLite. No real tickets or payments are processed.

## Setup and run

Open a terminal in this project folder. Use Python 3.10 or later.

```sh
python -m pip install -r requirements.txt
python main.py
python -m streamlit run app.py
```

After running the streamlit command above, open the local URL printed by Streamlit and keep the terminal running. You can also use VS Code's Run Python File button (the Play button on the top-right corner) on main.py (not app.py). The launcher uses the current Python environment and sets the project folder as the working directory. The direct command `python -m streamlit run app.py` still works when running from this folder.

The supplied database retains Kevin's 278 routes and 800 flights, with an empty bookings table added. Startup preserves existing inventory and orders. If no flights table exists, startup creates the schema and loads the supplied CSV once.

Optional commands:

```sh
python potterairline_tables.py
python pricing_function_new.py
python -m unittest -v test_project # TODO: Fix the error "Database error: test failure"
```

The pricing command produces a CSV-based pricing export; the prices are calculated from the filtered flights dataframe returned by the SQL queries. Tests use temporary databases and do not modify the project database.

## Workflow and design

1. Generate Pandas dataframe from gendb.py, and save it to csv file "flights.csv"

2. Load Pandas dataframe to SQL tables

3. SQL queries:
    - filtering - returns a Pandas dataframe:
        - Using the Pandas dataframe to calculate the prices with discounting
    - Updates the Pandas dataframe by adding the prices columnn (i.e. calculate prices on the fly)
    - booking
    - update price
    - etc.

Search flights filters by city/airport and date and sorts by price or departure. The display retains Audrey's first-25-results limit; narrow the filters to find other flights. Prices are per seat in CAD.

Book passes a flight number, departure date and ticket quantity to booking.py. The backend validates the request, calculates the current fare, deducts seats and inserts the order in one transaction. The confirmed per-seat fare is saved so a later price change does not alter an existing order's displayed cost.

Booked flights is a separate sidebar page. Its dataframe is loaded from the bookings table, including orders for flights that are now sold out. Cancel booking restores every ticket in that order and executes a parameterized DELETE in one transaction. This removes the order from the active list. Repeating a cancellation cannot restore seats twice. A booking ID is never reused (AUTOINCREMENT).

There is no customer authentication: everyone using this database sees the same shared order list. Authentication is optional in the project specification.

# Schema of the SQL tables:

- routes: primary key (origin_airport_code, destination_airport_code).
- flights: primary key (flight_id, dep_date), foreign key to routes. Flight numbers can repeat on different dates.
- bookings: booking_id, flight_id, dep_date, tickets, unit_fare, booked_at; composite foreign key to flights. It stores active orders, not cancellation history.

CREATE TABLE is in potterairline_tables.py. INSERT, parameterized SELECT, conditional UPDATE and parameterized DELETE are exercised through booking.py. SQL values are supplied with placeholders. BEGIN IMMEDIATE serializes inventory changes; transaction context managers roll back either operation if its partner fails, and finally closes booking/cancellation connections. Read-only helpers use closing().

Flight in flight.py validates capacity, inventory, quantity and departure time and is used by the booking workflow. Pandas vectorized date arithmetic, load-factor calculations and order-total calculations operate across multiple rows. Row-wise fare calculation is retained for clarity and is not described as vectorized.

## _routes_ table
The _routes_ SQL table stores the unique flight routes. It has the following fields: `origin_airport_code`, `destination_airport_code`, `origin_city`, `destination_city`, `base_fare`. The primary key of the _routes_ SQL table is the tuple *(origin_airport_code, destination_airport_code)*, since for a single airline (i.e. Potter Airlines), there should not be duplicated routes with the same origin airport and destination airport. Please note that there might be multiple flights for a particular route (i.e. generally the same flight number), either recurring flights or flights on the same route occurring at different times (i.e. different flight number). We have taken this into consideration, and it is possible for multiple flights to correspond to one route. In order to retrieve the information only stored in the routes table (i.e. *base_fare*), we join the two tables on the foreign key of _flights_ table (i.e. the tuple *(origin_airport_code, destination_airport_code)*) which is the primary key of the _routes_ table.

CREATE TABLE routes (
            origin_airport_code TEXT NOT NULL,
            destination_airport_code TEXT NOT NULL,
            origin_city TEXT NOT NULL,
            destination_city TEXT NOT NULL,
            base_fare DOUBLE,
            PRIMARY KEY (origin_airport_code, destination_airport_code)
        );

## _flights_ table
The _flights_ SQL table stores all of the flights. It has the following fields: `flight_id`, `dep_date`, `dep_hour`, `origin_airport_code`, `destination_airport_code`, `distance_km`, `capacity`, `seats_remaining`. The primary key of the _flights_ SQL table is the tuple *(flight_id, dep_date)*, since there should be no flight with the same flight number (i.e. *flight_id*) that happens more than once on any single day (recurring flights for any particular air route of an airline happen at most once per day). The tuple *(origin_airport_code, destination_airport_code)* may not be unique in _flights_ table, but is unqiue in _routes_ table. As a result, we use the *(origin_airport_code, destination_airport_code)* as the foreign key of _flights_ table that references the tuple of the same name in _routes_ table.

CREATE TABLE flights (
            flight_id TEXT NOT NULL,
            dep_date DATE NOT NULL,
            dep_hour INTEGER,
            origin_airport_code TEXT NOT NULL,
            destination_airport_code TEXT NOT NULL,
            distance_km INTEGER,
            capacity INTEGER,
            seats_remaining INTEGER,
            PRIMARY KEY (flight_id, dep_date),
            FOREIGN KEY (origin_airport_code, destination_airport_code)
                REFERENCES routes(origin_airport_code, destination_airport_code)
        );

## _bookings_ table
The _bookings_ SQL table stores all of the active bookings. It has the following fields: `booking_id`, `flight_id`, `dep_date`, `tickets`, `unit_fare`, `booked_at`. The _bookings_ table has the foreign key *(flight_id, dep_date)* tuple that refers to the primary key *(flight_id, dep_date)* tuple of the *flights* table.

CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            flight_id TEXT NOT NULL,
            dep_date DATE NOT NULL,
            tickets INTEGER NOT NULL CHECK (tickets > 0),
            unit_fare REAL NOT NULL CHECK (unit_fare > 0),
            booked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (flight_id, dep_date) REFERENCES flights(flight_id, dep_date)
        );

Side Notes:
We originally decided to include UUIDs for these tables, but we found out that these are not necessary. Reasons are described below:
- The tuple *(origin_airport_code, destination_airport_code)* is inherently unqiue for _routes_ table
- The tuple *(flight_id, dep_date)* is inherently unqiue for _flights_ table
- UUIDs are hard to reference from other tables, i.e. they are very different and randomly generated for each data entry for each table. Keeping unique tuples as described above makes it much easier to reference between tables and perform JOIN operations.


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
