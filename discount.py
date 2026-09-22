import numpy as np
import pandas as pd

flights = pd.read_csv("priced_flights.csv")

baseline = flights.copy()

baseline["dep_date"] = pd.to_datetime(baseline["dep_date"])
baseline["day_of_week"] = baseline["dep_date"].dt.dayofweek
baseline["load_factor"] = 1 - baseline["seats_remaining"] / baseline["capacity"]
baseline[["flight_id", "seats_remaining", "capacity", "load_factor"]]

#Discount 1 early bird: 10% off for flights booked 60 days in advance and with load factor < 30%
eligible_early_bird = (
    (baseline["days_until_departure"] >= 60)
    & (baseline["load_factor"] < 0.30)
)

baseline["discount_early_bird"] = np.where(
    eligible_early_bird,
    0.90,
    1.00
)


#Discount 2 midweek: 5% off for flights departing on Tuesday or Wednesday and with seats remaining > 0
eligible_midweek = (
    (baseline["day_of_week"].isin([1, 2]))
    & (baseline["seats_remaining"] > 0)
)

baseline["discount_midweek"] = np.where(
    eligible_midweek, 
    0.95, 
    1.00
)

comparison = baseline.copy()

comparison["eligible_early_bird"] = eligible_early_bird
comparison["eligible_midweek"] = eligible_midweek

comparison["early_bird_price"] = np.clip(
    comparison["fare"] * comparison["discount_early_bird"],
    45,
    4000
).round(2)

comparison["midweek_price"] = np.clip(
    comparison["fare"] * comparison["discount_midweek"],
    45,
    4000
).round(2)

# Apply the discount that results in the lowest price
comparison["discount_price"] = np.minimum(
    comparison["early_bird_price"],
    comparison["midweek_price"]
).round(2)

baseline["discount_price"] = comparison["discount_price"]

baseline.to_csv("priced_flights.csv", index=False)