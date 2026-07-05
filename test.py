car = {
    "brand": "Ford",
    "model": "Mustang",
    "year": 1964
}

x = car.setdefault("facts", "Bronco")

print(x)
