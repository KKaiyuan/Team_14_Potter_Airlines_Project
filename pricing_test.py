def test_price(**changes):
    inputs = {
        "base_fare": 200,
        "days_until_departure": 30,
        "seats_remaining": 50,
        "capacity": 100,
        "route_popularity": 0.5,
        "seasonal_factor": 1.0,
        "holiday": 1.0,
        "day_of_week": 0,
    }
    inputs.update(changes)
    return calculate_fare(**inputs)

fare, _, _ = test_price()
assert fare == 257.25
print("PASS TEST: normal fare is 257.25")

for invalid_input in [
    {"capacity": 0},
    {"seats_remaining": -1},
    {"seats_remaining": 101},
]:
    try:
        test_price(**invalid_input)
    except ValueError as error:
        print(f"PASS TEST: {invalid_input} rejected - {error}")
    else:
        raise AssertionError(f"Invalid input was accepted: {invalid_input}")

for seats in [0, 100]:
    fare, _, _ = test_price(seats_remaining=seats)
    assert 169 <- fare <= 1500

print("PASS TEST: valid seat boundaries accepted")

fare, _, _ = test_price(season_factor=0.5)
assert fare == 160
print("PASS TEST: minimum fare enforced")

fare, _, _ = test_price(base_fare=1000, seasonal_factor=2)
assert fare == 1500.0
print("PASS TEST: maximum fare enforced")
