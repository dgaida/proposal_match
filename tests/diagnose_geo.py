import os

from app.utils.geo_utils import get_coordinates

# Ensure we start fresh for the diagnostic
if os.path.exists("data/geo_cache.json"):
    os.remove("data/geo_cache.json")

cities = ["Houston", "Plano", "Berlin", "Paris", "London"]
for city in cities:
    print(f"Geocoding {city}...")
    coords = get_coordinates(city, "USA" if city in ["Houston", "Plano"] else "Europe")
    print(f"Result for {city}: {coords}")
