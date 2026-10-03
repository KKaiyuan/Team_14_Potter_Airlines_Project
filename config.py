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


ROUTE_POPULARITY_SCORES = {
    # Toronto
    ("Ottawa", "Toronto"): 0.6,
    ("Toronto", "Vancouver"): 0.8,
    ("Calgary", "Toronto"): 0.5,
    ("Montreal", "Toronto"): 0.7,
    ("Toronto", "Waterloo Region"): 0.4,
    ("London, Ontario", "Toronto"): 0.4,
    ("Hamilton", "Toronto"): 0.4,
    ("Abbotsford", "Toronto"): 0.5,
    ("Kelowna", "Toronto"): 0.6,
    ("Toronto", "Victoria"): 0.6,
    ("Nanaimo", "Toronto"): 0.4,
    ("Prince George", "Toronto"): 0.4,
    ("Edmonton", "Toronto"): 0.6,
    ("Quebec City", "Toronto"): 0.5,

    # Ottawa
    ("Calgary", "Ottawa"): 0.5,
    ("Montreal", "Ottawa"): 0.5,
    ("Ottawa", "Vancouver"): 0.5,
    ("Ottawa", "Waterloo Region"): 0.3,
    ("London, Ontario", "Ottawa"): 0.3,
    ("Hamilton", "Ottawa"): 0.3,
    ("Abbotsford", "Ottawa"): 0.3,
    ("Kelowna", "Ottawa"): 0.4,
    ("Ottawa", "Victoria"): 0.4,
    ("Nanaimo", "Ottawa"): 0.3,
    ("Ottawa", "Prince George"): 0.3,
    ("Edmonton", "Ottawa"): 0.5,
    ("Ottawa", "Quebec City"): 0.4,

    # Vancouver
    ("Calgary", "Vancouver"): 0.5,
    ("Montreal", "Vancouver"): 0.5,
    ("Vancouver", "Waterloo Region"): 0.3,
    ("London, Ontario", "Vancouver"): 0.3,
    ("Hamilton", "Vancouver"): 0.4,
    ("Abbotsford", "Vancouver"): 0.3,
    ("Kelowna", "Vancouver"): 0.6,
    ("Vancouver", "Victoria"): 0.6,
    ("Nanaimo", "Vancouver"): 0.5,
    ("Prince George", "Vancouver"): 0.5,
    ("Edmonton", "Vancouver"): 0.6,
    ("Quebec City", "Vancouver"): 0.4,

    # Calgary
    ("Calgary", "Montreal"): 0.5,
    ("Calgary", "Waterloo Region"): 0.3,
    ("Calgary", "London, Ontario"): 0.3,
    ("Calgary", "Hamilton"): 0.4,
    ("Abbotsford", "Calgary"): 0.4,
    ("Calgary", "Kelowna"): 0.6,
    ("Calgary", "Victoria"): 0.5,
    ("Calgary", "Nanaimo"): 0.4,
    ("Calgary", "Prince George"): 0.4,
    ("Calgary", "Edmonton"): 0.6,
    ("Calgary", "Quebec City"): 0.4,

    # Montreal
    ("Montreal", "Waterloo Region"): 0.3,
    ("London, Ontario", "Montreal"): 0.3,
    ("Hamilton", "Montreal"): 0.4,
    ("Abbotsford", "Montreal"): 0.3,
    ("Kelowna", "Montreal"): 0.4,
    ("Montreal", "Victoria"): 0.4,
    ("Montreal", "Nanaimo"): 0.3,
    ("Montreal", "Prince George"): 0.3,
    ("Edmonton", "Montreal"): 0.5,
    ("Montreal", "Quebec City"): 0.6,

    # Remaining cities
    ("London, Ontario", "Waterloo Region"): 0.3,
    ("Hamilton", "Waterloo Region"): 0.3,
    ("Abbotsford", "Waterloo Region"): 0.2,
    ("Kelowna", "Waterloo Region"): 0.3,
    ("Victoria", "Waterloo Region"): 0.3,
    ("Nanaimo", "Waterloo Region"): 0.2,
    ("Prince George", "Waterloo Region"): 0.2,
    ("Edmonton", "Waterloo Region"): 0.3,
    ("Quebec City", "Waterloo Region"): 0.3,

    ("Hamilton", "London, Ontario"): 0.3,
    ("Abbotsford", "London, Ontario"): 0.2,
    ("Kelowna", "London, Ontario"): 0.3,
    ("London, Ontario", "Victoria"): 0.3,
    ("London, Ontario", "Nanaimo"): 0.2,
    ("London, Ontario", "Prince George"): 0.2,
    ("Edmonton", "London, Ontario"): 0.3,
    ("London, Ontario", "Quebec City"): 0.3,

    ("Abbotsford", "Hamilton"): 0.3,
    ("Hamilton", "Kelowna"): 0.3,
    ("Hamilton", "Victoria"): 0.3,
    ("Hamilton", "Nanaimo"): 0.2,
    ("Hamilton", "Prince George"): 0.2,
    ("Edmonton", "Hamilton"): 0.4,
    ("Hamilton", "Quebec City"): 0.3,

    ("Abbotsford", "Kelowna"): 0.4,
    ("Abbotsford", "Victoria"): 0.4,
    ("Abbotsford", "Nanaimo"): 0.3,
    ("Abbotsford", "Prince George"): 0.3,
    ("Abbotsford", "Edmonton"): 0.4,
    ("Abbotsford", "Quebec City"): 0.2,

    ("Kelowna", "Victoria"): 0.5,
    ("Kelowna", "Nanaimo"): 0.4,
    ("Kelowna", "Prince George"): 0.4,
    ("Edmonton", "Kelowna"): 0.5,
    ("Kelowna", "Quebec City"): 0.3,

    ("Nanaimo", "Victoria"): 0.4,
    ("Prince George", "Victoria"): 0.4,
    ("Edmonton", "Victoria"): 0.5,
    ("Quebec City", "Victoria"): 0.3,

    ("Nanaimo", "Prince George"): 0.3,
    ("Edmonton", "Nanaimo"): 0.3,
    ("Nanaimo", "Quebec City"): 0.2,

    ("Edmonton", "Prince George"): 0.4,
    ("Prince George", "Quebec City"): 0.2,

    ("Edmonton", "Quebec City"): 0.4,
}