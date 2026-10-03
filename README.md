# Potter Airlines: pricing, booking and cancellation

**RSM 8431 Analytics Colloquia | Team 14**

Potter Airlines is a fictional airline application that calculates dynamic fares and supports flight searches, bookings, and cancellations. The project uses Python functions and a `Flight` class, Pandas for data processing, SQLite for persistent storage, and Streamlit for the interface. Prices are in Canadian dollars.

## Setup and run

Git clone main branch of this project. Open a terminal and "cd" (change directory) into this project folder. Use Python 3.10 or later. Run the following bash code to install the required libraries for this project:

```bash
pip install -r requirements.txt
```

After installing the required libraries, run the following for the backend and the frontend for the web application.
```bash
python main.py
python -m streamlit run app.py
```

Open the local URL displayed in the terminal. Keep the terminal running while using the application; press `Ctrl+C` to stop it. 

The application reads the supplied `flights_database.db`. Streamlit GUI launches and page refreshes preserve bookings and seat inventory. **`main.py` generates data and rebuilds database tables; it is not the UI launcher.**

The generator creates 800 flights (278 routes) occurrences by default and writes `flights.csv`; the pipeline loads them into SQLite.


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


## Using the application

1. Select **Search flights**, choose origin and destination airports, and set a departure date range.
2. Sort by fare or departure date. The interface displays the first 25 matches; narrow the filters to find other flights. Sold-out and departed flights are excluded.
3. Open **See price breakdown** to review fare inputs and the applied discount.
4. Enter the number of seats and click **Book**. The backend checks availability and confirms the current fare.
5. Select **Booked flights** to see orders, ticket quantities, confirmed unit fares, and totals.
6. Click **Cancel booking** to remove an entire order, restore its seats and restore its price.


## Data and design

Flight data is synthetic. Airports, departure dates and times, capacities, and remaining seats are randomly selected. `random.seed(42)` supports repeatable random choices, while generated dates depend on the run date. Aircraft capacities are defined in `config.py`; approximate straight-line city distances are read from `distances.csv`.

SQLite separates route information, flight inventory, and orders:

| Table | Contents | Primary key |
| --- | --- | --- |
| `routes` | Origin/destination airports and cities, base fare | `(origin_airport_code, destination_airport_code)` |
| `flights` | Departure date/time, route reference, distance, capacity, remaining seats | `(flight_id, dep_date)` |
| `bookings` | Flight reference, ticket quantity, confirmed unit fare, booking timestamp | `booking_id` |


# Schema of the SQL tables:

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

```text
base_fare = 50 + 0.08 × distance_km
fare_before_discount = base_fare × time_factor × capacity_factor
                       × demand_factor × seasonal_factor × holiday_factor
```

| Factor | Rule |
| --- | --- |
| Time | Less than 4 hours: 0.85; 4 hours through 1 day: 1.00; over 1 through 7 days: 1.35; over 7 through 21 days: 1.10; over 21 days: 1.00 |
| Capacity | `1 + 0.45 × load_factor`, where `load_factor = 1 − seats_remaining / capacity` |
| Demand | `0.9 + 0.3 × route_popularity`; unlisted city pairs use popularity 0.5, and both directions share a score |
| Season | Monthly multipliers from `SEASONAL_FACTOR` in `config.py` |
| Holiday | 1.20 on dates listed by the configured Canadian holiday calendar; otherwise 1.00 |

Discounts are 10% for departures at least 60 days away with load below 30%, 5% for Tuesday/Wednesday departures, and 15% for departures less than four hours away. Only the strongest qualifying discount is selected. It is rejected if it would reduce the fare below 80% of the base fare. The last-minute time factor and last-minute discount are separate multipliers.

The result is bounded by 80% of base fare and CAD 1,500 for the supplied dataset, then rounded to two decimal places. Departed flights receive no valid fare. For example, a CAD 200 base fare, 30 days until departure, 50 of 100 seats remaining, popularity 0.5, and neutral season/holiday factors gives **CAD 257.25** on a day without a midweek discount.


## Testing:

pytest booking_test.py
python test_project.py
python pricing_test.py



## Main files

| File | Responsibility |
| --- | --- |
| `app.py` | Streamlit interface |
| `booking.py`, `flight.py` | Booking/cancellation transactions and flight validation |
| `functional_queries.py` | Search, filtering, pricing, and sorting |
| `pricing_function_new.py`, `fare.py` | Dynamic pricing and distance-based base fares |
| `config.py` | Capacities, seasonal factors, airport labels, and source notes |
| `gendb.py`, `calculate_distances.py` | Synthetic flights and approximate distances |
| `main.py`, `potterairline_tables.py` | Dataset generation, schema creation, and database loading |
| `flights.csv`, `distances.csv`, `flights_database.db` | Code-generated data and persistent storage |
| `pricing_test.py` | Standalone pricing assertions |
| `assets/`, `docs/` | Interface branding and supporting documentation |


## Assumptions and limitations

- Route popularity and pricing premiums are modelling assumptions, not estimates of real market fares. Capacity and seasonal source notes are recorded in `config.py`; the holiday-calendar reference is recorded in `pricing_function_new.py`.
- Seasonal factors use aggregate U.S. passenger patterns from December 2021 through December 2024 as a proxy for this Canadian simulation. They are not route-specific demand forecasts.
- Distances are approximate city-to-city distances. Random schedules and aircraft assignments may not reflect actual airline operations.
- Times are treated as local naive datetimes, without airport time-zone conversion.
- All users share one booking list. Authentication, payments, refunds, and cancellation history are outside the project scope.
- Initially occupied seats are synthetic baseline inventory, not recorded orders. Only bookings created in the application can be cancelled.
- The fixed upper fare limit is designed for this dataset; substantially larger base fares would require revisiting the minimum/maximum rules.
- The interface uses the supplied database; it does not automatically initialize a missing database. The inherited notebook is not required for the application workflow.


## Acknowledgement

Generative AI tools assisted with development, UI integration, debugging, and test preparation. For the purpose of this project, pricing is determined by rules set by Team 14 members.
