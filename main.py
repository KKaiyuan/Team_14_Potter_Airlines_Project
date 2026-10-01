import sqlite3
import importlib

from gendb import generate_flights_csv
from potterairline_tables import create_tables, load_data_into_tables

CSV_PATH = "flights.csv"
DB_PATH = "flights_database.db"

def run_pipeline(n_flights=800):
    # 1. Generate the raw flights CSV
    print("Step 1: Generating flights.csv...")
    generate_flights_csv(n=n_flights, output_path=CSV_PATH)

    # 2 & 3. pricing_function_new.py reads flights.csv itself (using
    #        origin_city/destination_city) and computes fare/route_popularity/
    #        etc. at import time -- importing it IS steps 2+3 combined.
    print("Step 2-3: Loading CSV and calculating fares (via pricing_function_new.py)...")
    import pricing_function_new
    importlib.reload(pricing_function_new)  # ensures it re-reads the CSV on repeat runs

    flights_df = pricing_function_new.flights_df  # grab the computed DataFrame

    # 4. Load DataFrame into SQL tables
    print("Step 4: Loading data into SQL tables...")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        create_tables(conn)
        load_data_into_tables(conn, flights_df)
    finally:
        conn.close()

    print("Pipeline complete. Data is in", DB_PATH)


if __name__ == "__main__":
    run_pipeline()