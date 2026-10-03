import sqlite3
import importlib

from gendb import generate_flights_csv
from potterairline_tables import create_tables, load_data_into_tables

CSV_PATH = "flights.csv"
DB_PATH = "flights_database.db"

def run_pipeline(n_flights=800):
    # 1. Generate the raw flights CSV
    print("Step 1: Generating flights.csv...")
    flights_df = generate_flights_csv(n=n_flights, output_path=CSV_PATH)

    # 2. Load DataFrame into SQL tables
    print("Step 2: Loading data into SQL tables...")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        create_tables(conn)
        load_data_into_tables(conn, flights_df)
    finally:
        conn.close()

    print("Pipeline complete", DB_PATH)


if __name__ == "__main__":
    run_pipeline()