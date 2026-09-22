# Minimal changes to Matthew's code

This version supersedes the earlier refactored update. Work from this folder: relative paths are retained exactly as in Matthew's workflow.

## Run

The delivered CSV/database contain 200 flights. All initial CSV seats are available; the database additionally contains 20 demo orders for 1-5 tickets each. This order count is a configurable example, not an assignment requirement.

For a fresh dataset in a separate folder: install pandas and holidays; run `python gendb.py`; run the first code cell of `potterairline.ipynb` to create tables and load the CSV; optionally run `python demo_bookings.py`. Then use `book_flight(flight_id, tickets)` and `cancel_booking(booking_id)` from booking.py.

The notebook skips CSV import when flights already exist, preserving inventory and orders. Do not use the old five-column database or the previous refactored database with this version; the supplied database matches this minimal version. The CSV remains an initial snapshot, not live inventory.

## Requested modifications

- gendb.py: replace capacity candidates; initialize all seats as available; add assigned distance and base fare.
- flight.py: replace only the seasonal-factor rule and add distance/base-fare attributes.
- booking.py: save orders and return booking IDs; add cancellation; keep seat deduction and order insertion atomic.
- Notebook: add required columns and bookings table; avoid duplicate imports; fix the query database filename.
- New config.py and fare.py hold the user's constants and base-fare function; demo_bookings.py optionally seeds orders.

## Necessary correctness fixes

- booking.py uses flights_database.db, matching the notebook.
- Ticket quantities must be positive integers.
- The inventory update checks available seats again atomically; cancellation is serialized to prevent double restoration.

## Preserved without refactoring

Matthew's random.seed(42), for loop, variable names, five cities, today-based date range, departure times, tuple/list structure, direct CSV export, Flight constructor order, holiday_factor, time_till_departure, and file-level example remain. Duplicate scheduled slots are not filtered. No new after-departure booking policy or date-string conversion is imposed. Pass date/time objects to Flight as Matthew did.

util.py, .gitignore, and requirements.txt are copied byte-for-byte from the supplied originals. datetime is part of Python's standard library; the original requirements file is retained at the user's request rather than cleaned up.

## Sources and limitations

Capacity source and BTS source links are in config.py. Air Canada 2024 MD&A, printed p.19, is used for the seven model configurations. BTS December 2021-December 2024 unadjusted monthly passenger totals provide the pooled daily-traffic indices. Pandemic recovery and trend affect these indices; applying them as price factors is a modelling assumption. The fare formula CAD 50 + 0.08/km and rounded distance constants in fare.py are project assumptions, not observed tariffs or actual flown paths.

Route popularity and final pricing are not added. The original US-holiday helper is retained. All data here are for demonstration, not production booking or payment processing.
