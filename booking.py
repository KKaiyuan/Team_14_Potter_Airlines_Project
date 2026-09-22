import sqlite3

def book_flight(flight_id, amount_of_tickets_booked):
    
    conn = sqlite3.connect("flight_database.db")
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
    
    #Check that tickets being bought is > 0
    if amount_of_tickets_booked <= 0:
        print("Amount of tickets must be greater than 0.")
        conn.close()
        return
    
    #Check if there are enough seats for the booking size
    if amount_of_tickets_booked > seats_remaining:
        print("Not enough available seats.")
        conn.close()
        return
    
    cursor.execute("""
                 UPDATE flights
                 SET seats_remaining = seats_remaining - ?
                 WHERE flight_id = ?
                 """,
                 (amount_of_tickets_booked, flight_id)
                 )
    conn.commit()
    conn.close()
    
    print("Booking Successful!")