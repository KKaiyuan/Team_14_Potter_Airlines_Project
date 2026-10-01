"""Run: python -m unittest -v test_project. Uses temporary databases only."""
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing

import pandas as pd

import booking
from flight import Flight
from potterairline_tables import create_tables, initialize_database
from pricing_function_new import calculate_discount, calculate_fare, price_flights


class PricingTests(unittest.TestCase):
    def test_time_boundaries(self):
        for days, factor in [(1, 1), (1.001, 1.35), (7, 1.35), (7.001, 1.1), (21, 1.1), (21.001, 1)]:
            with self.subTest(days=days):
                self.assertEqual(calculate_fare(400, days, 50, 100, .5, 1)[0], round(400*factor*1.225*1.05, 2))

    def test_discounts(self):
        self.assertEqual(calculate_discount(60, 80, 100, 0), .9)
        self.assertEqual(calculate_discount(59, 80, 100, 0), 1)
        self.assertEqual(calculate_discount(60, 70, 100, 0), 1)
        self.assertEqual(calculate_discount(10, 50, 100, 1), .95)
        self.assertEqual(calculate_discount(.1, 80, 100, 2), .85)
        self.assertEqual(calculate_discount(4/24, 80, 100, 0), 1)

    def test_holiday_and_season(self):
        self.assertEqual(calculate_fare(400,30,100,100,.5,1.1,1.2)[0],554.4)

    def test_floor_ceiling_and_rejected_discount(self):
        self.assertEqual(calculate_fare(100,30,100,100,0,.5)[0],80)
        self.assertEqual(calculate_fare(3000,30,100,100,.5,1)[0],1500)
        self.assertEqual(calculate_fare(100,.1,100,100,0,1),(90,1,False))

    def test_invalid_inputs(self):
        for change in [dict(base_fare=0),dict(capacity=0),dict(seats_remaining=-1),dict(seats_remaining=101),dict(route_popularity=2),dict(seasonal_factor=0),dict(holiday=0)]:
            args=dict(base_fare=100,days_until_departure=1,seats_remaining=50,capacity=100,route_popularity=.5,seasonal_factor=1)
            args.update(change)
            with self.subTest(change=change), self.assertRaises(ValueError): calculate_fare(**args)

    def test_departed_price(self):
        self.assertTrue(pd.isna(calculate_fare(100,0,50,100,.5,1)[0]))

    def test_city_lookup_and_vectorized_load(self):
        rows=pd.DataFrame([dict(origin_city='Toronto',destination_city='Vancouver',dep_date='2027-07-01',dep_hour='12:00:00',base_fare=300,capacity=100,seats_remaining=40),dict(origin_city='Vancouver',destination_city='Toronto',dep_date='2027-07-01',dep_hour='12:00:00',base_fare=300,capacity=100,seats_remaining=60)])
        result=price_flights(rows,now='2027-06-01')
        self.assertEqual(result.route_popularity.tolist(),[.8,.8])
        self.assertEqual(result.holiday.tolist(),[1.2,1.2])
        self.assertEqual(result.load_factor.tolist(),[.6,.4])
        self.assertGreater(result.fare.iloc[0],result.fare.iloc[1])


class BookingTests(unittest.TestCase):
    def setUp(self):
        self.old_cwd=Path.cwd()
        self.temp=tempfile.TemporaryDirectory()
        os.chdir(self.temp.name)
        with closing(sqlite3.connect('flights_database.db')) as conn, conn:
            create_tables(conn)
            conn.execute("INSERT INTO routes VALUES (?, ?, ?, ?, ?)",('YYZ','YVR','Toronto','Vancouver',300))
            for day in ['2099-01-01','2099-01-02']:
                conn.execute("INSERT INTO flights VALUES (?, ?, ?, ?, ?, ?, ?, ?)",('PA1',day,'12:00:00','YYZ','YVR',3350,100,10))

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp.cleanup()

    def seats(self, day='2099-01-01'):
        with closing(sqlite3.connect('flights_database.db')) as conn, conn:
            return conn.execute('SELECT seats_remaining FROM flights WHERE flight_id = ? AND dep_date = ?',('PA1',day)).fetchone()[0]

    def test_booking_persists_with_correct_date(self):
        bid=booking.book_flight('PA1',2,'2099-01-01')
        self.assertEqual(self.seats(),8)
        self.assertEqual(self.seats('2099-01-02'),10)
        orders=booking.get_bookings()
        self.assertEqual(orders.booking_id.tolist(),[bid])
        self.assertEqual(orders.tickets.tolist(),[2])
        self.assertAlmostEqual(orders.total_fare.iloc[0],orders.unit_fare.iloc[0]*2)

    def test_cancel_deletes_and_restores_once(self):
        bid=booking.book_flight('PA1',2,'2099-01-01')
        self.assertTrue(booking.cancel_booking(bid))
        self.assertTrue(booking.get_bookings().empty)
        self.assertEqual(self.seats(),10)
        self.assertFalse(booking.cancel_booking(bid))
        self.assertEqual(self.seats(),10)

    def test_invalid_ticket_quantities(self):
        for amount in [0,-1,1.5,True,'2']:
            with self.subTest(amount=amount): self.assertIsNone(booking.book_flight('PA1',amount,'2099-01-01'))
        self.assertEqual(self.seats(),10)

    def test_insufficient_seats(self):
        self.assertIsNone(booking.book_flight('PA1',11,'2099-01-01'))
        self.assertTrue(booking.get_bookings().empty)
        self.assertEqual(self.seats(),10)

    def test_unknown_and_sql_like_ids(self):
        for fid in ['missing', "PA1' OR 1=1 --"]:
            self.assertIsNone(booking.book_flight(fid,1,'2099-01-01'))
        self.assertEqual(self.seats(),10)

    def test_sold_out_order_still_cancellable(self):
        bid=booking.book_flight('PA1',10,'2099-01-01')
        self.assertEqual(self.seats(),0)
        self.assertEqual(len(booking.get_bookings()),1)
        booking.cancel_booking(bid)
        self.assertEqual(self.seats(),10)

    def test_insert_failure_rolls_back_seats(self):
        with closing(sqlite3.connect('flights_database.db')) as conn, conn:
            conn.execute("CREATE TRIGGER reject_booking BEFORE INSERT ON bookings BEGIN SELECT RAISE(ABORT, 'test failure'); END")
        self.assertIsNone(booking.book_flight('PA1',2,'2099-01-01'))
        self.assertEqual(self.seats(),10)

    def test_delete_failure_rolls_back_restoration(self):
        bid=booking.book_flight('PA1',2,'2099-01-01')
        with closing(sqlite3.connect('flights_database.db')) as conn, conn:
            conn.execute("CREATE TRIGGER reject_delete BEFORE DELETE ON bookings BEGIN SELECT RAISE(ABORT, 'test failure'); END")
        self.assertFalse(booking.cancel_booking(bid))
        self.assertEqual(self.seats(),8)
        self.assertEqual(len(booking.get_bookings()),1)

    def test_startup_preserves_booking(self):
        booking.book_flight('PA1',2,'2099-01-01')
        initialize_database()
        self.assertEqual(self.seats(),8)
        self.assertEqual(len(booking.get_bookings()),1)

    def test_concurrent_requests_do_not_oversell(self):
        def reserve(_):
            try: return booking.book_flight('PA1',7,'2099-01-01')
            except ValueError: return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(reserve,range(2)))
        self.assertEqual(sum(x is not None for x in results),1)
        self.assertEqual(self.seats(),3)

    def test_class_validation(self):
        with self.assertRaises(ValueError): Flight('PA1','2099-01-01','12:00:00',0,0)
        with self.assertRaises(ValueError): Flight('PA1','2099-01-01','12:00:00',100,101)
        with self.assertRaises(ValueError): Flight('PA1','2000-01-01','12:00:00',100,10).validate_booking(1)


if __name__=='__main__':
    unittest.main(verbosity=2)
