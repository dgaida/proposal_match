import json
import os
import threading
import time
from typing import Any

from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim, Photon

CACHE_FILE = "data/geo_cache.json"
_geo_cache: dict[str, tuple[float, float]] = {}
_failed_keys: set[str] = set()
_cache_lock = threading.Lock()

# Global geolocator instances to reuse connections
USER_AGENT = "funding_research_app_v2_1"
_nominatim = Nominatim(user_agent=USER_AGENT, timeout=10)
_photon = Photon(user_agent=USER_AGENT, timeout=10)

# Circuit breaker for Nominatim
_nominatim_disabled = False
_nominatim_lock = threading.Lock()


def load_cache() -> dict[str, tuple[float, float]]:
    """
    Loads the geocoding cache from a JSON file.

    Returns:
        Dict[str, Tuple[float, float]]: The loaded geocoding cache.
    """
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


def save_cache(cache: dict[str, tuple[float, float]]):
    """
    Saves the geocoding cache to a JSON file.

    Args:
        cache (Dict[str, Tuple[float, float]]): The geocoding cache to save.
    """
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with _cache_lock, open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)


def get_coordinates(
    city: str, country: str = "Germany", retries: int = 1, only_from_cache: bool = False
) -> tuple[float, float] | None:
    """
    Fetches GPS coordinates for a city with multiple strategies and fallbacks.

    Strategies:
    1. Local cache
    2. Nominatim (Primary, with circuit breaker)
    3. Photon (Fallback)

    Args:
        city (str): The city to geocode.
        country (str): The country the city is in. Defaults to "Germany".
        retries (int): Number of retries for the geocoding service. Defaults to 1.
        only_from_cache (bool): If True, only search in the local cache. Defaults to False.

    Returns:
        Optional[Tuple[float, float]]: The (latitude, longitude) coordinates or None if not found.
    """
    global _nominatim_disabled
    if not city:
        return None

    cache = load_cache()
    key = f"{city.strip()}, {country.strip()}"

    with _cache_lock:
        if key in cache:
            return cache[key]
        if only_from_cache:
            return None
        if key in _failed_keys:
            return None

    # Primary Strategy: Nominatim (if not disabled)
    use_nominatim = False
    with _nominatim_lock:
        use_nominatim = not _nominatim_disabled

    if use_nominatim:
        for attempt in range(retries + 1):
            try:
                # Respect Nominatim usage policy: more conservative 2.0 second delay
                time.sleep(2.0)
                location = _nominatim.geocode(key)
                if location:
                    coords = (location.latitude, location.longitude)
                    with _cache_lock:
                        _geo_cache[key] = coords
                        # save_cache(_geo_cache) # Moved out of hot path
                    return coords
                break  # Not found
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                err_str = str(e)
                if "429" in err_str:
                    print(
                        "Nominatim rate limited (429). Switching to circuit breaker for this session."
                    )
                    with _nominatim_lock:
                        _nominatim_disabled = True
                    break  # Trigger fallback
                if attempt < retries:
                    time.sleep(2)
                    continue
                break

    # Fallback Strategy: Photon (Komoot)
    try:
        time.sleep(1.0)  # Play nice with Photon too
        location = _photon.geocode(key)
        if location:
            coords = (location.latitude, location.longitude)
            with _cache_lock:
                _geo_cache[key] = coords
                # save_cache(_geo_cache) # Moved out of hot path
            return coords
    except Exception as e:
        print(f"Photon fallback failed for {key}: {e}")

    # Mark as failed for this session to avoid redundant calls
    with _cache_lock:
        _failed_keys.add(key)
    return None


def batch_geocode(companies: list[Any]):
    """
    Background task to pre-geocode unique NRW company locations.

    Args:
        companies (List[Any]): List of company objects or dictionaries.
    """
    nrw_variants = ["nrw", "nordrhein-westfalen", "north rhine-westphalia"]

    # Extract unique cities to geocode
    unique_cities_to_geocode = set()
    for company in companies:
        # Check both attribute and dict access to be safe
        state = getattr(company, "state", None) or (
            company.get("State") if isinstance(company, dict) else None
        )
        state = (state or "").lower()

        if state in nrw_variants:
            city = getattr(company, "city", None) or (
                company.get("City") if isinstance(company, dict) else None
            )
            country = getattr(company, "country", None) or (
                company.get("Land") if isinstance(company, dict) else None
            )

            if city:
                unique_cities_to_geocode.add((city.strip(), country or "Germany"))

    # Pre-geocode unique locations
    if unique_cities_to_geocode:
        for city, country in unique_cities_to_geocode:
            get_coordinates(city, country)

        # Save cache once after batch
        save_cache(_geo_cache)
