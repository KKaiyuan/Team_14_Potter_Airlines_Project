import sqlite3

def book_flight(flight_id, amount_of_tickets_booked):
    
    conn = sqlite3.connect("flights_database.db") # Fixed: match the notebook database name.
    cursor = conn.cursor()
        
    cursor.execute(
                "SELECT seats_remaining FROM flights WHERE flight_id = ?",
                (flight_id,)
                )
    
    flight = cursor.fetchone()
    
    #Check if flight exists
    if flight == None:
        print("Flight not found.")
        conn.close()
        return
    
    seats_remaining = flight[0]
    
    #Check if there are still seats remaining
    if seats_remaining <= 0:
        print("No more available seats.")
        conn.close()
        return
    
    # Modified: ticket quantities must be positive whole numbers.
    if type(amount_of_tickets_booked) is not int or amount_of_tickets_booked <= 0:
        print("Amount of tickets must be greater than 0.")
        conn.close()
        return
    
    #Check if there are enough seats for the booking size
    if amount_of_tickets_booked > seats_remaining:
        print("Not enough available seats.")
        conn.close()
        return
    
    # Added: record the order and deduct seats together, without overselling.
    
    
    cursor.execute("""
        UPDATE flights
        SET seats_remaining = seats_remaining - ?
        WHERE flight_id = ? AND seats_remaining >= ?
        """,
        (amount_of_tickets_booked, flight_id, amount_of_tickets_booked)
        )
    if cursor.rowcount == 0:
        print("Not enough available seats.")
        conn.close()
        return
    
    cursor.execute("""
        INSERT INTO bookings (flight_id, tickets, status)
        VALUES (?, ?, 'confirmed')
        """, (flight_id, amount_of_tickets_booked))
    booking_id = cursor.lastrowid
    
    conn.commit()
    conn.close()

    print("Booking Successful!")
    return booking_id  # Added: identify this order for later cancellation.


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