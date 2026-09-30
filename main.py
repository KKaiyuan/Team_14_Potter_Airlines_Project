import sqlite3
import pandas as pd

from gendb import generate_flights_csv          # step 1
from pricing_function_new import calculate_fare  # step 3
from potterairline_tables import create_tables, load_data  # steps 4-5 helpers

CSV_PATH = "flights.csv"
DB_PATH = "flights_database.db"

def run_pipeline(n_flights=800):
    # 1. Generate the raw flights CSV
    print("Step 1: Generating flights.csv...")
    generate_flights_csv(n=n_flights, output_path=CSV_PATH)

    # 2. Load CSV into a pandas DataFrame
    print("Step 2: Loading CSV into DataFrame...")
    flights_df = pd.read_csv(CSV_PATH)

    # 3. Calculate prices (with discounting) -> updates the DataFrame
    print("Step 3: Calculating fares...")
    flights_df = calculate_fare(flights_df)

    # 4. Load DataFrame into SQL tables (DataFrame itself isn't persisted anywhere)
    print("Step 4: Loading data into SQL tables...")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        create_tables(conn)
        load_data(conn, flights_df)
    finally:
        conn.close()

    print("Pipeline complete. Data is in", DB_PATH)


if __name__ == "__main__":
    run_pipeline()