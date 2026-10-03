# # Added: distance lookup and the agreed base-fare function for Matthew's five cities.
# # Assigned approximate straight-line distances in kilometres for Matthew's five cities.
# # Values are rounded modelling inputs, not actual flown distances or published route fares.
# # Each pair is alphabetically ordered; use the same distance in both directions.
# DISTANCE_KM = {
#     ("Calgary", "Montreal"): 3000,
#     ("Calgary", "Ottawa"): 2900,
#     ("Calgary", "Toronto"): 2700,
#     ("Calgary", "Vancouver"): 700,
#     ("Montreal", "Ottawa"): 150,
#     ("Montreal", "Toronto"): 500,
#     ("Montreal", "Vancouver"): 3700,
#     ("Ottawa", "Toronto"): 350,
#     ("Ottawa", "Vancouver"): 3550,
#     ("Toronto", "Vancouver"): 3350,
# }


def base_fare(distance_km):
    if distance_km <= 0:
        raise ValueError("distance_km must be positive.")
    return round(50.0 + 0.08 * distance_km, 2)
