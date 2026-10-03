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
TODO: finish the description for _bookings_ table

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
