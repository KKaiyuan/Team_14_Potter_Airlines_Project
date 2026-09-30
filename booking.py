import sqlite3

def book_flight(flight_id, dep_date, amount_of_tickets_booked):
    
    conn = sqlite3.connect("flights_database.db") # Fixed: match the notebook database name.
    cursor = conn.cursor()
        
    cursor.execute(
                "SELECT seats_remaining FROM flights WHERE flight_id = ? AND dep_date = ?",
                (flight_id, dep_date)
                )
    
    flight = cursor.fetchone()
    
    #Check if flight exists
    if flight == None:
        conn.close()
        raise ValueError("Flight not found.")
    
    seats_remaining = flight[0]
    
    #Check if there are still seats remaining
    if seats_remaining <= 0:
        conn.close()
        raise ValueError("No more available seats.")
    
    # Modified: ticket quantities must be positive whole numbers.
    if type(amount_of_tickets_booked) is not int or amount_of_tickets_booked <= 0:
        conn.close()
        raise ValueError("Amount of tickets must be greater than 0.")
    
    #Check if there are enough seats for the booking size
    if amount_of_tickets_booked > seats_remaining:
        conn.close()
        raise ValueError("Not enough available seats.")
    
    # Added: record the order and deduct seats together, without overselling.
    
    
    cursor.execute("""
        UPDATE flights
        SET seats_remaining = seats_remaining - ?
        WHERE flight_id = ? AND dep_date = ? AND seats_remaining >= ?
        """,
        (amount_of_tickets_booked, flight_id, dep_date, amount_of_tickets_booked)
        )
    if cursor.rowcount == 0:
        conn.close()
        raise ValueError("Not enough available seats.")
    
    cursor.execute("""
        INSERT INTO bookings (flight_id, dep_date, tickets, status)
        VALUES (?, ?, ?, 'confirmed')
        """, (flight_id, dep_date, amount_of_tickets_booked))
    booking_id = cursor.lastrowid
    
    conn.commit()
    conn.close()

    print("Booking Successful!")
    return booking_id, seats_remaining-amount_of_tickets_booked  # Added: identify this order for later cancellation.


# Added: cancel an existing order and restore its seats exactly once.
def cancel_booking(booking_id):
    conn = sqlite3.connect("flights_database.db")
    cursor = conn.cursor()
    try:
        with conn:
            cursor.execute("BEGIN IMMEDIATE")
            cursor.execute("SELECT flight_id, tickets, status FROM bookings WHERE booking_id = ?",
                           (booking_id,))
            booking = cursor.fetchone()
            if booking is None:
                print("Booking not found.")
                return False
            flight_id, tickets, status = booking
            if status == "cancelled":
                print("Booking already cancelled.")
                return False
            cursor.execute("UPDATE flights SET seats_remaining = seats_remaining + ? WHERE flight_id = ?",
                           (tickets, flight_id))
            cursor.execute("UPDATE bookings SET status = 'cancelled' WHERE booking_id = ?",
                           (booking_id,))
        print("Cancellation Successful!")
        return True
    except sqlite3.Error as e:
        print("Database error:", e)
        return False
    finally:
        conn.close()