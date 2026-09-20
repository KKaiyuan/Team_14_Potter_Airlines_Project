

# DISTANCE REFERENCE: OurAirports. (n.d.). Airport data (airports.csv). Retrieved September 17, 2026.
# https://ourairports.com/data/
# https://davidmegginson.github.io/ourairports-data/airports.csv
# Approximate straight-line distances were derived from YYZ, YVR, YUL, JFK, ORD, and LAX coordinates.
# Values were rounded to the nearest 50 km and assigned below.
# Use pair = tuple(sorted([source, destination])) for BOTH distance and popularity lookups.
DISTANCE_KM = {
    ('Toronto', 'Vancouver'): 3350, 
    ('Montreal', 'Toronto'): 500,
    ('New York', 'Toronto'): 600,
    ('Chicago', 'Toronto'): 700,
    ('Los Angeles', 'Toronto'): 3500,
    ('Montreal', 'Vancouver'): 3700,
    ('New York', 'Vancouver'): 3950,
    ('Chicago', 'Vancouver'): 2850,
    ('Los Angeles', 'Vancouver'): 1750,
    ('Montreal', 'New York'): 550,
    ('Chicago', 'Montreal'): 1200,
    ('Los Angeles', 'Montreal'): 3950,
    ('Chicago', 'New York'): 1200,
    ('Los Angeles', 'New York'): 3950,
    ('Chicago', 'Los Angeles'): 2800,
}

FIXED_FARE_CAD = 50.0  # Set a project-assumed fixed charge; this is not a sourced airline tariff.
FARE_PER_KM_CAD = 0.08  # Set a project-assumed kilometre charge; this is not an empirical estimate.


def base_fare(distance_km):  # Calculate a simulated one-way base fare in CAD from a positive distance.
    if distance_km <= 0:  # Reject zero or negative route distances.
        raise ValueError("distance_km must be positive.")  # Explain the invalid input.
    return round(FIXED_FARE_CAD + FARE_PER_KM_CAD * distance_km, 2)  # Return the fare rounded to cents.


# CAPACITY REFERENCE: Air Canada. (2025, February 13). 2024 Management's Discussion and Analysis.
# Section 7, Fleet, printed page 19 (PDF page 21), fleet as at December 31, 2024.
# https://content.presspage.com/uploads/3167/ea8e8729-33cd-48a7-a4ca-4168b2631560/q42024aircanadamdampa-english.pdf?10000=
# These are selected Air Canada configurations, not universal capacities or verified 2027 assignments.
# Seats remaining must be simulated separately with random.randint(0, capacity).
PLANE_CAPACITY = {
    'Boeing 737 MAX 8': 169,
    'Airbus A220-300': 137,
    'Boeing 787-9': 298,
    'Airbus A320': 133,
    'Airbus A321': 183,
    'Airbus A330-300': 295,
    'Boeing 777-300ER': 418,
}



# SEASONAL REFERENCE: Bureau of Transportation Statistics. (2025, March 14).
# December 2024 U.S. Airline Traffic Data Up 5.9% from December 2023.
# https://www.bts.gov/newsroom/december-2024-us-airline-traffic-data-59-december-2023
# Use all 37 monthly observations from December 2021 through December 2024, inclusive.
# Coverage: unadjusted U.S.-carrier scheduled domestic + international passengers, in millions.
# For each calendar month, combine its passenger totals and divide by its combined calendar days.
# Divide that monthly daily average by the daily average across the full 37-month period.
# December has four observations; January-November have three. February 2024 has 29 days.
# Pandemic recovery and growth affect these pooled indices; they are not detrended seasonal estimates.
# Using this broad traffic index as a fare multiplier on all project routes is a modelling assumption.
# This is not a BTS fare formula, Canada-US-specific demand, or a 2027 forecast.
# Source 2021: {12: 66.6}.
# Source 2022: {1: 51.9, 2: 54.8, 3: 72.5, 4: 71.9, 5: 75.8, 6: 77.4, 7: 80.4, 8: 76.6, 9: 71.4, 10: 76.4, 11: 71.9, 12: 71.9}.
# Source 2023: {1: 67.4, 2: 64.8, 3: 79.8, 4: 77.6, 5: 81.8, 6: 84.0, 7: 87.8, 8: 83.1, 9: 76.3, 10: 82.6, 11: 77.7, 12: 78.7}.
# Source 2024: {1: 70.1, 2: 70.4, 3: 84.9, 4: 81.2, 5: 87.1, 6: 89.7, 7: 91.8, 8: 86.8, 9: 77.5, 10: 82.8, 11: 77.1, 12: 83.3}.
SEASONAL_FACTOR = {  # Apply the same departure-month lookup to all cities.
    1: 0.8071,  # January: 189.4 million passengers / 93 days, divided by the full-period daily average.
    2: 0.8858,  # February: 190.0 million passengers / 85 days, divided by the full-period daily average.
    3: 1.0108,  # March: 237.2 million passengers / 93 days, divided by the full-period daily average.
    4: 1.0159,  # April: 230.7 million passengers / 90 days, divided by the full-period daily average.
    5: 1.0427,  # May: 244.7 million passengers / 93 days, divided by the full-period daily average.
    6: 1.1057,  # June: 251.1 million passengers / 90 days, divided by the full-period daily average.
    7: 1.1079,  # July: 260.0 million passengers / 93 days, divided by the full-period daily average.
    8: 1.0504,  # August: 246.5 million passengers / 93 days, divided by the full-period daily average.
    9: 0.9916,  # September: 225.2 million passengers / 90 days, divided by the full-period daily average.
    10: 1.0304,  # October: 241.8 million passengers / 93 days, divided by the full-period daily average.
    11: 0.9982,  # November: 226.7 million passengers / 90 days, divided by the full-period daily average.
    12: 0.9604,  # December: 300.5 million passengers / 124 days, divided by the full-period daily average.
}  # Finish the twelve monthly factors.
