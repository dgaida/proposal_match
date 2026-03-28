import json
import os
import time
import threading
from typing import Optional, Tuple, Dict, List
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

CACHE_FILE = "data/geo_cache.json"
_geo_cache: Dict[str, Tuple[float, float]] = {}
_cache_lock = threading.Lock()

def load_cache() -> Dict[str, Tuple[float, float]]:
    """Loads the geocoding cache from a JSON file."""
    global _geo_cache
    with _cache_lock:
        if _geo_cache:
            return _geo_cache

        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    _geo_cache = {k: tuple(v) for k, v in data.items()}
                    return _geo_cache
            except Exception:
                return {}
    return {}

def save_cache(cache: Dict[str, Tuple[float, float]]):
    """Saves the geocoding cache to a JSON file."""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with _cache_lock:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=4)

def get_coordinates(city: str, country: str = "Germany") -> Optional[Tuple[float, float]]:
    """Fetches GPS coordinates for a city, using a local cache."""
    if not city:
        return None

    cache = load_cache()
    key = f"{city.strip()}, {country.strip()}"

    if key in cache:
        return cache[key]

    try:
        # Respect Nominatim usage policy: 1 second delay between non-cached requests
        time.sleep(1)
        geolocator = Nominatim(user_agent="funding_research_app", timeout=10)
        location = geolocator.geocode(key)
        if location:
            coords = (location.latitude, location.longitude)
            with _cache_lock:
                _geo_cache[key] = coords
            save_cache(_geo_cache)
            return coords
    except GeocoderTimedOut:
        return None
    except Exception as e:
        print(f"Error geocoding {key}: {e}")
        return None

    return None

def batch_geocode(companies: List[any]):
    """Background task to pre-geocode all company locations."""
    for company in companies:
        if company.city:
            get_coordinates(company.city, company.country or "Germany")
