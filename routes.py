"""
routes.py
Defines the base fare AND route popularity for Potter Airlines routes,
stores both as a 'routes' table in SQLite, and attaches them to a
flights DataFrame.

The set of routes is derived from flights.csv itself (not a hardcoded city
list), so adding new cities in gendb.py automatically produces new routes
here too -- any route without an explicit value below just gets a default,
with a warning printed so it's easy to notice and fill in properly.
"""

import sqlite3
import pandas as pd

DEFAULT_BASE_FARE = 200          # used only for routes not in BASE_FARES
DEFAULT_ROUTE_POPULARITY = 0.5   # used only for routes not in ROUTE_POPULARITY

# Base fare per route ($), assigned directly as a business/policy choice.
# Short regional hops are cheaper; cross-country routes cost more.
# Only need to list each pair once -- the loop below fills in the reverse
# direction (A->B and B->A share the same base fare).
BASE_FARES = {
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
for (a, b), fare in list(BASE_FARES.items()):
    BASE_FARES[(b, a)] = fare

# Route popularity (0-1), assigned directly as a business assumption --
# how in-demand this route generally is, independent of any one flight's
# current bookings. Short, frequently-traveled corridors are more popular;
# longer cross-country routes less so.
ROUTE_POPULARITY = {
    ("Toronto", "Ottawa"): 0.85,
    ("Toronto", "Montreal"): 0.80,
    ("Toronto", "Calgary"): 0.60,
    ("Toronto", "Vancouver"): 0.55,
    ("Vancouver", "Calgary"): 0.65,
    ("Vancouver", "Montreal"): 0.40,
    ("Vancouver", "Ottawa"): 0.35,
    ("Calgary", "Montreal"): 0.45,
    ("Calgary", "Ottawa"): 0.50,
    ("Montreal", "Ottawa"): 0.70,
}
for (a, b), pop in list(ROUTE_POPULARITY.items()):
    ROUTE_POPULARITY[(b, a)] = pop


def _lookup(table, key, default, label):
    if key in table:
        return table[key]
    print(f"No {label} defined for {key[0]} -> {key[1]}; "
          f"using default {default}. Add it to the {label.upper()} dict.")
    return default


def build_routes_df(flights_df):
    """
    Unique (source, destination) pairs actually present in flights_df,
    each with a base_fare and route_popularity. New cities in flights.csv
    show up here automatically -- no hardcoded city list to maintain.
    """
    routes = flights_df[["source", "destination"]].drop_duplicates().reset_index(drop=True)
    routes["base_fare"] = routes.apply(
        lambda r: _lookup(BASE_FARES, (r["source"], r["destination"]),
                           DEFAULT_BASE_FARE, "base fare"), axis=1
    )
    routes["route_popularity"] = routes.apply(
        lambda r: _lookup(ROUTE_POPULARITY, (r["source"], r["destination"]),
                           DEFAULT_ROUTE_POPULARITY, "route popularity"), axis=1
    )
    assert routes["route_popularity"].between(0, 1).all(), \
        "route_popularity must be between 0 and 1"
    return routes


def create_routes_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS routes (
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            base_fare REAL NOT NULL,
            route_popularity REAL NOT NULL,
            PRIMARY KEY (source, destination)
        );
    """)
    conn.commit()


def load_routes_to_table(conn, routes_df, table_name="routes"):
    """INSERT: parameterized, replaces existing rows for idempotent reruns."""
    sql = f"""
        INSERT OR REPLACE INTO {table_name}
        (source, destination, base_fare, route_popularity)
        VALUES (?, ?, ?, ?)
    """
    conn.executemany(sql, routes_df[
        ["source", "destination", "base_fare", "route_popularity"]
    ].itertuples(index=False, name=None))
    conn.commit()
    print(f"Loaded {len(routes_df)} rows into {table_name}.")


def attach_route_data(flights_df, conn):
    """Merge base_fare and route_popularity from routes onto a flights DataFrame."""
    routes_df = pd.read_sql_query("SELECT * FROM routes", conn)
    merged = flights_df.merge(routes_df, on=["source", "destination"], how="left")
    assert merged["base_fare"].notna().all(), "some flights have no matching route (base_fare)"
    assert merged["route_popularity"].notna().all(), "some flights have no matching route (route_popularity)"
    return merged


if __name__ == "__main__":
    conn = sqlite3.connect("flights_database.db")

    flights_df = pd.read_csv("flights.csv")
    routes_df = build_routes_df(flights_df)

    create_routes_table(conn)
    load_routes_to_table(conn, routes_df)

    priced_flights = attach_route_data(flights_df, conn)
    print(priced_flights.head())
    conn.close()