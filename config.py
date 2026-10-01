# Air Canada (2025), 2024 MD&A, section 7, printed page 19.
# https://content.presspage.com/uploads/3167/ea8e8729-33cd-48a7-a4ca-4168b2631560/q42024aircanadamdampa-english.pdf?10000=
# The seven mainline passenger models with the most operating aircraft in that table.
PLANE_CAPACITY = {
    "Boeing 737 MAX 8": 169,
    "Airbus A220-300": 137,
    "Boeing 787-9": 298,
    "Airbus A320": 133,
    "Airbus A321": 183,
    "Airbus A330-300": 295,
    "Boeing 777-300ER": 418,
}

# BTS (March 14, 2025), unadjusted scheduled U.S.-carrier domestic + international passengers.
# https://www.bts.gov/newsroom/december-2024-us-airline-traffic-data-59-december-2023
# Period: December 2021 through December 2024, inclusive (37 observations).
# Index = pooled daily passengers for the calendar month / daily passengers over the full period.
# December has four observations; other months have three. February 2024 has 29 days.
# These indices include pandemic recovery and trend; using them for prices is a project assumption.
SEASONAL_FACTOR = {
    1: 0.8071,
    2: 0.8858,
    3: 1.0108,
    4: 1.0159,
    5: 1.0427,
    6: 1.1057,
    7: 1.1079,
    8: 1.0504,
    9: 0.9916,
    10: 1.0304,
    11: 0.9982,
    12: 0.9604,
}

city_codes = [
    # Ontario: 
    "Toronto - YYZ", "Toronto - YTZ", # Toronto
    "Ottawa - YOW", # Ottawa
    "Waterloo Region - YKF", # Waterloo Region
    "London, Ontario - YXU", # London, Ontario
    "Hamilton - YHM", # Hamilton
    # British Columbia: 
    "Vancouver - YVR", # Vancouver
    "Abbotsford - YXX", # Abbotsford
    "Kelowna - YLW", # Kelowna
    "Victoria - YYJ", # Victoria
    "Nanaimo - YCD", # Nanaimo
    "Prince George - YXS", # Prince George
    # Alberta: 
    "Calgary - YYC", # Calgary
    "Edmonton - YEG", # Edmonton
    # Quebec: 
    "Montreal - YUL", "Montreal - YHU", "Montreal - YMX", # Montreal
    "Quebec City - YQB" # Quebec City
]