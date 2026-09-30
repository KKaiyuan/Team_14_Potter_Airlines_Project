# Acknowledgement: Consulted with Claude code for the code in this file.

import csv
from math import radians, sin, cos, sqrt, atan2
from itertools import combinations

# Approximate coordinates (latitude, longitude) for each city
city_coords = {
    "Toronto": (43.6532, -79.3832),
    "Ottawa": (45.4215, -75.6972),
    "Waterloo Region": (43.4643, -80.5204),
    "London, Ontario": (42.9849, -81.2453),
    "Hamilton": (43.2557, -79.8711),
    "Vancouver": (49.2827, -123.1207),
    "Abbotsford": (49.0504, -122.3045),
    "Kelowna": (49.8880, -119.4960),
    "Victoria": (48.4284, -123.3656),
    "Nanaimo": (49.1659, -123.9401),
    "Prince George": (53.9171, -122.7497),
    "Calgary": (51.0447, -114.0719),
    "Edmonton": (53.5461, -113.4938),
    "Montreal": (45.5019, -73.5674),
    "Quebec City": (46.8139, -71.2080),
}

def haversine_km(coord1, coord2):
    R = 6371  # Earth's radius in km
    lat1, lon1 = radians(coord1[0]), radians(coord1[1])
    lat2, lon2 = radians(coord2[0]), radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

def generate_distance_csv(output_path="distances.csv"):
    cities = sorted(city_coords.keys())
    rows = []
    for city1, city2 in combinations(cities, 2):
        dist = round(haversine_km(city_coords[city1], city_coords[city2]))
        rows.append((city1, city2, dist))

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["city1", "city2", "distance_km"])
        writer.writerows(rows)

    print(f"Wrote {len(rows)} city-pair distances to {output_path}")

if __name__ == "__main__":
    generate_distance_csv()