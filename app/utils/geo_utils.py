import json
import os
import time
from typing import Optional, Tuple, Dict
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

CACHE_FILE = "data/geo_cache.json"

def load_cache() -> Dict[str, Tuple[float, float]]:
    """Loads the geocoding cache from a JSON file.

    Returns:
        Dict[str, Tuple[float, float]]: The cached coordinates.
    """
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache: Dict[str, Tuple[float, float]]):
    """Saves the geocoding cache to a JSON file.

    Args:
        cache (Dict[str, Tuple[float, float]]): The cache to save.
    """
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)

def get_coordinates(city: str, country: str = "Germany") -> Optional[Tuple[float, float]]:
    """Fetches GPS coordinates for a city, using a local cache.

    Args:
        city (str): The name of the city.
        country (str): The name of the country. Defaults to "Germany".

    Returns:
        Optional[Tuple[float, float]]: (latitude, longitude) or None if not found.
    """
    if not city:
        return None

    cache = load_cache()
    key = f"{city.strip()}, {country.strip()}"

    if key in cache:
        return tuple(cache[key])

    try:
        # Respect Nominatim usage policy: 1 second delay between non-cached requests
        time.sleep(1)
        geolocator = Nominatim(user_agent="funding_research_app", timeout=10)
        location = geolocator.geocode(key)
        if location:
            coords = (location.latitude, location.longitude)
            cache[key] = coords
            save_cache(cache)
            return coords
    except GeocoderTimedOut:
        return None
    except Exception as e:
        print(f"Error geocoding {key}: {e}")
        return None

    return None
